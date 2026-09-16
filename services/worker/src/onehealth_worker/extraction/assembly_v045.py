from __future__ import annotations

from copy import deepcopy
from typing import Any

from .atomic_claims import assemble_claims_payload as assemble_claims_payload_v044


_TEXTUAL_EVIDENCE_TYPES = {"quote", "text"}


def assemble_claims_payload(claim_payload: dict[str, Any]) -> dict[str, Any]:
    """Assemble atomic claims with the deterministic v0.4.5 hardening layer.

    v0.4.5 deliberately keeps the provider-facing atomic-claims contract unchanged.
    The sidecar remains the auditable LLM output; this function only prepares a deep
    copy for deterministic canonical signal assembly and never mutates the sidecar.
    """
    prepared = _prepare_claims_for_assembly(claim_payload)
    payload = assemble_claims_payload_v044(prepared)
    _canonicalize_signal_evidence(payload)
    return payload


def _prepare_claims_for_assembly(claim_payload: dict[str, Any]) -> dict[str, Any]:
    prepared = deepcopy(claim_payload)
    claims = list(prepared.get("claims") or [])
    groups: dict[str, list[dict[str, Any]]] = {}
    for claim in claims:
        group = str(claim.get("group_id") or claim.get("claim_id") or "?")
        groups.setdefault(group, []).append(claim)

    kept: list[dict[str, Any]] = []
    for group_claims in groups.values():
        _prepare_group(group_claims)
        for claim in group_claims:
            if _suppress_from_canonical_signals(claim):
                continue
            kept.append(claim)

    prepared["claims"] = kept
    return prepared


def _prepare_group(group: list[dict[str, Any]]) -> None:
    kinds = {str(c.get("claim_kind") or "") for c in group}

    # ASM-045-01: deaths belonging to an explicitly reported syndromic cluster are
    # metrics of that cluster, not an independent mortality signal.
    if "syndromic_cluster" in kinds and "death_count" in kinds:
        for claim in group:
            if claim.get("claim_kind") == "death_count":
                claim["claim_kind"] = "syndromic_cluster"

    # ASM-045-02/03: a positive human diagnostic result is a confirmed case report.
    # Do not copy a vessel's current location into the epidemiologic case signal.
    for claim in group:
        if _is_positive_human_diagnostic(claim):
            claim["claim_kind"] = "case_status"
            _ensure_confirmed_case_metric(claim)
            _drop_location_role(claim, "current_location")
        elif claim.get("claim_kind") == "transmission_statement":
            _drop_location_role(claim, "current_location")

        _derive_disease_from_explicit_pathogen(claim)
        _normalize_laboratory_target(claim)

    # ASM-045-05: a closed historical count is background context, not a live
    # surveillance baseline.
    for claim in group:
        if _is_closed_historical_baseline(claim):
            claim["claim_kind"] = "historical_context"

    # ASM-045-06: mobility claims sharing a group represent one observed itinerary.
    mobility = [c for c in group if c.get("claim_kind") == "mobility"]
    if len(mobility) > 1:
        _prepare_mobility_window(mobility)

    # Tierra del Fuego / general wildlife rule: capture effort and explicit absence
    # from the same sampling group belong to one negative wildlife observation.
    negative_presence = [
        c for c in group
        if c.get("claim_kind") == "wildlife_presence_absence" and c.get("polarity") == "negative"
    ]
    if negative_presence:
        for claim in group:
            if claim.get("claim_kind") == "wildlife_sampling":
                claim["claim_kind"] = "wildlife_presence_absence"
                claim["polarity"] = "negative"

    # Genomic claims from one group should use the most specific taxon explicitly
    # present anywhere in those claims and preserve a reported novel-variant lineage.
    genomic = [c for c in group if c.get("claim_kind") == "genomic_finding"]
    if genomic:
        _prepare_genomic_group(genomic)


def _is_positive_human_diagnostic(claim: dict[str, Any]) -> bool:
    if claim.get("claim_kind") != "diagnostic_result":
        return False
    if claim.get("polarity") == "negative":
        return False
    subject = claim.get("subject") or {}
    diagnostics = claim.get("diagnostics") or {}
    return subject.get("subject_type") == "human" and diagnostics.get("result") == "positive"


def _ensure_confirmed_case_metric(claim: dict[str, Any]) -> None:
    metric = claim.get("metric") or {}
    if metric.get("reported"):
        return
    event_date = claim.get("event_date") or {}
    start = event_date.get("start")
    claim["metric"] = {
        "reported": True,
        "name": "confirmed_cases",
        "value_numeric": 1,
        "value_text": (claim.get("subject") or {}).get("verbatim"),
        "unit": "persons",
        "as_of_date": start if event_date.get("precision") == "day" else None,
        "as_of_year": int(start[:4]) if isinstance(start, str) and len(start) >= 4 else None,
        "as_of_month": int(start[5:7]) if isinstance(start, str) and len(start) >= 7 else None,
        "as_of_precision": "day" if event_date.get("precision") == "day" else "unknown",
        "as_of_verbatim": None,
    }


def _derive_disease_from_explicit_pathogen(claim: dict[str, Any]) -> None:
    if claim.get("disease_verbatim"):
        return
    pathogen = str(claim.get("pathogen_verbatim") or "").casefold()
    if "hantavirus" in pathogen or "andes" in pathogen or "orthohantavirus" in pathogen:
        claim["disease_verbatim"] = "hantavirus"


def _normalize_laboratory_target(claim: dict[str, Any]) -> None:
    if claim.get("claim_kind") != "laboratory_investigation":
        return
    diagnostics = claim.get("diagnostics") or {}
    target = str(diagnostics.get("target") or "")
    folded = target.casefold()
    if "cepa" in folded and "origen" in folded:
        diagnostics["target"] = "cepa"
        claim["diagnostics"] = diagnostics


def _drop_location_role(claim: dict[str, Any], role: str) -> None:
    claim["locations"] = [
        loc for loc in (claim.get("locations") or []) if loc.get("role") != role
    ]


def _is_closed_historical_baseline(claim: dict[str, Any]) -> bool:
    if claim.get("claim_kind") != "surveillance_baseline" or claim.get("polarity") == "negative":
        return False
    metric = claim.get("metric") or {}
    if not metric.get("reported"):
        return False
    period = claim.get("reference_period") or {}
    if period.get("period_type") != "historical_period":
        return False
    start = period.get("start") or {}
    end = period.get("end") or {}
    return bool((start.get("date") or start.get("year")) and (end.get("date") or end.get("year")))


def _prepare_mobility_window(claims: list[dict[str, Any]]) -> None:
    dates = [
        (c.get("event_date") or {}).get("start")
        for c in claims
        if (c.get("event_date") or {}).get("start")
    ]
    if len(dates) < 2:
        return
    start = min(dates)
    end = max(dates)
    evidence_texts = [
        str(ev.get("text") or "").strip()
        for claim in claims for ev in (claim.get("evidence") or [])
        if str(ev.get("text") or "").strip()
    ]
    verbatim = " ".join(evidence_texts) or None
    period = {
        "start": {"date": None, "year": None, "month": None, "precision": "unknown", "verbatim": None},
        "end": {"date": None, "year": None, "month": None, "precision": "unknown", "verbatim": None},
        "period_type": "observation_window",
        "verbatim": verbatim,
    }
    for claim in claims:
        claim["event_date"] = {"start": start, "end": end, "precision": "day"}
        claim["reference_period"] = deepcopy(period)


def _prepare_genomic_group(claims: list[dict[str, Any]]) -> None:
    combined = " ".join(
        [str(c.get("pathogen_verbatim") or "") for c in claims]
        + [str(c.get("summary") or "") for c in claims]
        + [str(ev.get("text") or "") for c in claims for ev in (c.get("evidence") or [])]
    ).casefold()
    if "orthohantavirus andesense" in combined:
        for claim in claims:
            claim["pathogen_verbatim"] = "Orthohantavirus andesense"
    elif "virus andes" in combined:
        for claim in claims:
            claim["pathogen_verbatim"] = "virus Andes"

    if "variante viral no descripta previamente" in combined:
        for claim in claims:
            genomics = claim.get("genomics") or {}
            if genomics.get("sequence_reported"):
                genomics["lineage"] = genomics.get("lineage") or "variante viral no descripta previamente"
                claim["genomics"] = genomics


def _suppress_from_canonical_signals(claim: dict[str, Any]) -> bool:
    # ASM-045-04: a negative historical narrative without a quantified observation
    # remains auditable in the claims sidecar but is not a canonical signal.
    if claim.get("claim_kind") == "surveillance_baseline" and claim.get("polarity") == "negative":
        if not (claim.get("metric") or {}).get("reported"):
            return True

    # Training/technology-transfer actions are operational context, not an emerging
    # epidemiologic signal. Field interventions with actual sampling metrics remain.
    if claim.get("claim_kind") == "intervention" and not (claim.get("metric") or {}).get("reported"):
        text = " ".join(
            [str(claim.get("summary") or "")]
            + [str(ev.get("text") or "") for ev in (claim.get("evidence") or [])]
        ).casefold()
        if "capacit" in text or "transferencia de la técnica" in text:
            return True
    return False


def _canonicalize_signal_evidence(payload: dict[str, Any]) -> None:
    for signal in payload.get("signals") or []:
        for evidence in signal.get("evidence") or []:
            evidence_type = str(evidence.get("type") or "").casefold()
            if evidence_type in _TEXTUAL_EVIDENCE_TYPES:
                evidence["type"] = "text"
