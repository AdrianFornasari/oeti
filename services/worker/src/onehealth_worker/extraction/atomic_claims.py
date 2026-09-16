from __future__ import annotations

from copy import deepcopy
from statistics import mean
from typing import Any
import re


_OUTBREAK_KINDS = {"outbreak_update", "case_status", "death_count"}
_WILDLIFE_NEGATIVE_KINDS = {"wildlife_sampling", "wildlife_presence_absence"}


def assemble_claims_payload(claim_payload: dict[str, Any]) -> dict[str, Any]:
    """Assemble atomic provider claims into canonical OETI signal-extractor v0.4 output.

    The LLM extracts source-grounded claims. This function owns signal role/type
    assignment, consolidation of counts from the same epidemiologic update, and
    deterministic normalization of common hantavirus entities.
    """
    warnings = list(claim_payload.get("warnings") or [])
    claims = list(claim_payload.get("claims") or [])
    buckets: list[list[dict[str, Any]]] = []
    index: dict[tuple[str, str], int] = {}

    for claim in claims:
        key = _bucket_key(claim)
        if key not in index:
            index[key] = len(buckets)
            buckets.append([])
        buckets[index[key]].append(claim)

    signals: list[dict[str, Any]] = []
    raw_item_id = claim_payload.get("document", {}).get("raw_item_id") or "claim"
    for ordinal, bucket in enumerate(buckets, 1):
        signal = _assemble_bucket(bucket, raw_item_id=str(raw_item_id), ordinal=ordinal, warnings=warnings)
        if signal is not None:
            signals.append(signal)

    return {
        "schema_version": "0.4",
        "document": deepcopy(claim_payload.get("document") or {}),
        "signals": signals,
        "warnings": warnings,
    }


def _bucket_key(claim: dict[str, Any]) -> tuple[str, str]:
    kind = str(claim.get("claim_kind") or "")
    group = str(claim.get("group_id") or claim.get("claim_id") or "?")
    polarity = str(claim.get("polarity") or "not_applicable")

    if kind in _OUTBREAK_KINDS:
        return ("outbreak", group)
    if kind == "surveillance_baseline":
        return ("baseline", group)
    if kind in _WILDLIFE_NEGATIVE_KINDS and polarity == "negative":
        return ("wildlife_negative", group)
    # Repeated claims of the same semantic nature may be merged deterministically.
    return (kind, group)


def _assemble_bucket(
    bucket: list[dict[str, Any]], *, raw_item_id: str, ordinal: int, warnings: list[str]
) -> dict[str, Any] | None:
    if not bucket:
        return None
    kind = _dominant_kind(bucket)
    role, signal_type = _role_and_type(kind, bucket)
    domains = _unique(v for c in bucket for v in (c.get("domains") or [])) or ["human"]
    disease = _normalized_entity(_first_text(bucket, "disease_verbatim"), entity="disease")
    pathogen = _normalized_entity(_first_text(bucket, "pathogen_verbatim"), entity="pathogen")
    hosts = _assemble_hosts(bucket)
    locations = _merge_locations(bucket)
    metrics = _merge_metrics(bucket)
    event_date = _best_event_date(bucket)
    reference_period = _best_reference_period(bucket)
    diagnostics = _merge_diagnostics(bucket)
    genomics = _merge_genomics(bucket)
    transmission = _merge_transmission(bucket)
    evidence = _merge_evidence(bucket)
    verification = _strongest_verification(bucket)
    summary = _summary_for_bucket(bucket, signal_type=signal_type)
    confidence = round(mean(float(c.get("confidence") or 0.5) for c in bucket), 4)

    # Negative diagnostic results and explicit negative wildlife findings are not
    # primary events even if the provider's polarity is inconsistent elsewhere.
    if diagnostics.get("result") == "negative" or (
        kind == "wildlife_negative"
    ):
        role = "negative_evidence"

    # A laboratory diagnostic claim that explicitly includes genomic methods can
    # carry the genomic domain, but remains a laboratory_result signal.
    if signal_type == "genomic_observation" and "genomic" not in domains:
        domains.append("genomic")

    return {
        "local_signal_id": f"{raw_item_id}-asm-{ordinal:02d}",
        "domains": domains,
        "signal_role": role,
        "signal_type": signal_type,
        "disease": disease,
        "pathogen": pathogen,
        "hosts": hosts,
        "locations": locations,
        "event_date": event_date,
        "reference_period": reference_period,
        "metrics": metrics,
        "transmission": transmission,
        "genomics": genomics,
        "verification_status": verification,
        "signal_summary": summary,
        "evidence": evidence,
        "extraction_confidence": confidence,
        "diagnostics": diagnostics,
    }


def _dominant_kind(bucket: list[dict[str, Any]]) -> str:
    kinds = [str(c.get("claim_kind") or "") for c in bucket]
    if "outbreak_update" in kinds:
        return "outbreak"
    if set(kinds).issubset({"case_status", "death_count"}) and len(bucket) > 1:
        return "outbreak"
    if len(bucket) == 1 and kinds[0] in {"case_status", "death_count"}:
        return kinds[0]
    if all(k == "surveillance_baseline" for k in kinds):
        return "baseline"
    if any(k == "wildlife_presence_absence" and c.get("polarity") == "negative" for k, c in zip(kinds, bucket)):
        return "wildlife_negative"
    return kinds[0]


def _role_and_type(kind: str, bucket: list[dict[str, Any]]) -> tuple[str, str]:
    polarity = "negative" if any(c.get("polarity") == "negative" for c in bucket) else None
    if kind == "syndromic_cluster":
        return "primary_event", "cluster"
    if kind == "outbreak":
        return "primary_event", "outbreak"
    if kind == "baseline":
        return "surveillance_baseline", "case_report"
    if kind == "diagnostic_result":
        return ("negative_evidence" if polarity else "primary_event"), "laboratory_result"
    if kind == "laboratory_investigation":
        return "primary_event", "laboratory_investigation"
    if kind == "genomic_finding":
        return "primary_event", "genomic_observation"
    if kind == "transmission_statement":
        return ("negative_evidence" if polarity else "primary_event"), "transmission_observation"
    if kind == "wildlife_negative":
        return "negative_evidence", "wildlife_event"
    if kind == "wildlife_sampling":
        return "primary_event", "wildlife_event"
    if kind == "wildlife_presence_absence":
        return ("negative_evidence" if polarity else "primary_event"), "wildlife_event"
    if kind == "mobility":
        return "primary_event", "travel_or_mobility"
    if kind == "historical_context":
        return "background_context", "case_report"
    if kind == "intervention":
        return "primary_event", "intervention"
    if kind == "official_action":
        return "primary_event", "official_alert"
    if kind == "case_status":
        return "primary_event", "case_report"
    if kind == "death_count":
        return "primary_event", "mortality_event"
    return "primary_event", "other"


def _normalized_entity(verbatim: str | None, *, entity: str) -> dict[str, Any]:
    if not verbatim:
        return {"verbatim": None, "canonical_name": None, "normalization_status": "unresolved", "confidence": 0.3}
    text = verbatim.strip()
    folded = text.casefold()
    canonical: str | None = None
    status = "ambiguous"
    confidence = 0.72

    if entity == "disease" and "hantavirus" in folded:
        canonical, status, confidence = "Hantavirus disease", "resolved", 0.82
    elif entity == "pathogen":
        if "orthohantavirus andesense" in folded:
            canonical, status, confidence = "Orthohantavirus andesense", "resolved", 0.92
        elif re.search(r"\b(cepa|virus|variante)?\s*andes\b", folded):
            canonical, status, confidence = "Andes virus", "resolved", 0.9
        elif "hantavirus" in folded:
            canonical, status, confidence = "Hantavirus", "resolved", 0.78
        else:
            status, confidence = "unresolved", 0.4
    else:
        status, confidence = "unresolved", 0.4

    return {
        "verbatim": text,
        "canonical_name": canonical,
        "normalization_status": status,
        "confidence": confidence,
    }


def _assemble_hosts(bucket: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hosts: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for claim in bucket:
        subject = claim.get("subject") or {}
        stype = subject.get("subject_type")
        if stype not in {"human", "animal", "wildlife", "vector"}:
            continue
        verbatim = subject.get("verbatim")
        canonical = subject.get("canonical_name")
        if stype == "human":
            canonical = canonical or "Homo sapiens"
        host_type = "wildlife" if stype == "wildlife" else stype
        key = (verbatim, canonical, host_type)
        if key in seen:
            continue
        seen.add(key)
        hosts.append({
            "verbatim": verbatim,
            "canonical_name": canonical,
            "host_type": host_type,
            "confidence": subject.get("confidence", 0.65),
        })
    return hosts


def _merge_locations(bucket: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for claim in bucket:
        for loc in claim.get("locations") or []:
            key = tuple(loc.get(k) for k in ("country", "country_iso2", "admin1", "admin2", "locality", "region", "role"))
            if key in seen:
                continue
            seen.add(key)
            out.append(deepcopy(loc))
    return out


def _merge_metrics(bucket: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for claim in bucket:
        metric = claim.get("metric")
        if not isinstance(metric, dict) or not metric.get("reported"):
            continue
        key = (metric.get("name"), metric.get("value_numeric"), metric.get("value_text"), metric.get("unit"))
        if key in seen:
            continue
        seen.add(key)
        cleaned = {k: deepcopy(v) for k, v in metric.items() if k != "reported"}
        out.append(cleaned)
    return out


def _best_event_date(bucket: list[dict[str, Any]]) -> dict[str, Any]:
    rank = {"day": 3, "month": 2, "year": 1, "unknown": 0}
    candidates = [c.get("event_date") for c in bucket if isinstance(c.get("event_date"), dict)]
    if not candidates:
        return {"start": None, "end": None, "precision": "unknown"}
    return deepcopy(max(candidates, key=lambda d: rank.get(d.get("precision"), 0)))


def _best_reference_period(bucket: list[dict[str, Any]]) -> dict[str, Any]:
    for claim in bucket:
        rp = claim.get("reference_period")
        if isinstance(rp, dict) and (rp.get("period_type") not in {None, "unknown"} or rp.get("verbatim")):
            return deepcopy(rp)
    return {
        "start": {"date": None, "year": None, "month": None, "precision": "unknown", "verbatim": None},
        "end": {"date": None, "year": None, "month": None, "precision": "unknown", "verbatim": None},
        "period_type": "unknown",
        "verbatim": None,
    }


def _merge_diagnostics(bucket: list[dict[str, Any]]) -> dict[str, Any]:
    default = {"test_reported": False, "test_type": None, "method": None, "target": None, "specimen": None, "result": "unknown"}
    for claim in bucket:
        d = claim.get("diagnostics") or {}
        if d.get("test_reported") or d.get("result") not in {None, "unknown", "not_applicable"}:
            return deepcopy({**default, **d})
    return default


def _merge_genomics(bucket: list[dict[str, Any]]) -> dict[str, Any]:
    default = {"sequence_reported": False, "lineage": None, "clade": None, "accession": None, "test_result": "not_applicable"}
    for claim in bucket:
        g = claim.get("genomics") or {}
        if g.get("sequence_reported") or g.get("lineage") or g.get("clade") or g.get("accession") or g.get("test_result") not in {None, "unknown", "not_applicable"}:
            return deepcopy({**default, **g})
    return default


def _merge_transmission(bucket: list[dict[str, Any]]) -> dict[str, Any]:
    default = {"human_to_human": "unknown", "animal_to_human": "unknown", "vector_borne": "unknown"}
    result = dict(default)
    for claim in bucket:
        t = claim.get("transmission") or {}
        for key in result:
            if t.get(key) not in {None, "unknown"}:
                result[key] = t[key]
    return result


def _merge_evidence(bucket: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for claim in bucket:
        for ev in claim.get("evidence") or []:
            key = (ev.get("type"), ev.get("text"), ev.get("page_number"))
            if key in seen:
                continue
            seen.add(key)
            out.append(deepcopy(ev))
    return out


def _strongest_verification(bucket: list[dict[str, Any]]) -> str:
    rank = {"confirmed": 6, "probable": 5, "suspected": 4, "reported": 3, "unknown": 2, "refuted": 1}
    values = [str(c.get("verification_status") or "unknown") for c in bucket]
    return max(values, key=lambda v: rank.get(v, 0)) if values else "unknown"


def _summary_for_bucket(bucket: list[dict[str, Any]], *, signal_type: str) -> str:
    summaries = _unique(str(c.get("summary") or "").strip() for c in bucket if str(c.get("summary") or "").strip())
    if len(summaries) == 1:
        return summaries[0]
    if signal_type in {"outbreak", "case_report"} and summaries:
        # Keep the first concise provider statement; metrics preserve the remaining atomic facts.
        return summaries[0]
    return " ".join(summaries)


def _first_text(bucket: list[dict[str, Any]], key: str) -> str | None:
    for claim in bucket:
        value = claim.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _unique(values):
    seen = set()
    out = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out
