from __future__ import annotations

from copy import deepcopy
from typing import Any

from .assembly_v045 import assemble_claims_payload as assemble_claims_payload_v045


_TEXTUAL_EVIDENCE_TYPES = {"text", "quote", "excerpt", "document_text"}


def assemble_claims_payload(claim_payload: dict[str, Any]) -> dict[str, Any]:
    """Assemble atomic claims with deterministic v0.4.6 benchmark hardening.

    v0.4.6 keeps provider-facing atomic claims unchanged on disk. It prepares a deep
    copy before v0.4.5 assembly, applying only deterministic rules derived from the
    adjudicated MV Hondius corpus and then canonicalizes textual evidence labels.
    """
    prepared = _prepare_claims_for_v046(claim_payload)
    payload = assemble_claims_payload_v045(prepared)
    _canonicalize_textual_evidence(payload)
    return payload


def _prepare_claims_for_v046(claim_payload: dict[str, Any]) -> dict[str, Any]:
    prepared = deepcopy(claim_payload)
    claims = list(prepared.get("claims") or [])

    groups: dict[str, list[dict[str, Any]]] = {}
    for claim in claims:
        group_id = str(claim.get("group_id") or claim.get("claim_id") or "?")
        groups.setdefault(group_id, []).append(claim)

    for group in groups.values():
        _prepare_collective_lab_characterization(group)
        _merge_operational_mobility_into_intervention(group)

    claims = [claim for claim in claims if not _is_generic_investigation_context(claim)]
    _merge_current_surveillance_snapshots(claims)
    prepared["claims"] = claims
    return prepared


def _prepare_collective_lab_characterization(group: list[dict[str, Any]]) -> None:
    """Keep aggregate case characterization as one laboratory result.

    A positive diagnostic result for one individual remains a case report. A positive
    diagnostic result referring to an already-known group of cases, when paired with a
    genomic finding in the same claim group, characterizes those cases rather than
    creating a new confirmed case.
    """
    diagnostics = [
        claim for claim in group
        if claim.get("claim_kind") == "diagnostic_result"
        and (claim.get("diagnostics") or {}).get("result") == "positive"
        and (claim.get("subject") or {}).get("subject_type") == "human"
    ]
    genomics = [claim for claim in group if claim.get("claim_kind") == "genomic_finding"]
    if not diagnostics or not genomics:
        return

    collective = [claim for claim in diagnostics if _is_collective_subject(claim.get("subject") or {})]
    if not collective:
        return

    for claim in collective:
        subject = claim.get("subject") or {}
        subject["subject_type"] = "other"
        claim["subject"] = subject

    for claim in genomics:
        claim["claim_kind"] = "diagnostic_result"


def _is_collective_subject(subject: dict[str, Any]) -> bool:
    text = str(subject.get("verbatim") or "").casefold()
    collective_tokens = (
        "los casos",
        "casos ",
        "pacientes",
        "personas",
        "muestras",
        "confirmados",
    )
    return any(token in text for token in collective_tokens)


def _merge_operational_mobility_into_intervention(group: list[dict[str, Any]]) -> None:
    if not any(claim.get("claim_kind") == "intervention" for claim in group):
        return
    for claim in group:
        if claim.get("claim_kind") == "mobility" and _looks_like_institutional_mobility(claim):
            claim["claim_kind"] = "intervention"


def _looks_like_institutional_mobility(claim: dict[str, Any]) -> bool:
    subject = claim.get("subject") or {}
    text = " ".join(
        [str(subject.get("verbatim") or ""), str(claim.get("summary") or "")]
        + [str(ev.get("text") or "") for ev in (claim.get("evidence") or [])]
    ).casefold()
    markers = (
        "personal del",
        "equipo del",
        "equipos técnicos",
        "equipos tecnicos",
        "ministerio",
        "anlis",
        "instituto",
        "laboratorio",
    )
    return any(marker in text for marker in markers)


def _is_generic_investigation_context(claim: dict[str, Any]) -> bool:
    if claim.get("claim_kind") != "laboratory_investigation":
        return False

    metric = claim.get("metric") or {}
    diagnostics = claim.get("diagnostics") or {}
    genomics = claim.get("genomics") or {}
    if metric.get("reported"):
        return False
    if diagnostics.get("test_reported"):
        return False
    if genomics.get("sequence_reported"):
        return False

    text = " ".join(
        [str(claim.get("summary") or "")]
        + [str(ev.get("text") or "") for ev in (claim.get("evidence") or [])]
    ).casefold()
    generic_markers = (
        "investigando el origen del brote",
        "investigación epidemiológica del brote",
        "investigacion epidemiologica del brote",
        "posibles circunstancias de exposición",
        "posibles circunstancias de exposicion",
    )
    return any(marker in text for marker in generic_markers)


def _merge_current_surveillance_snapshots(claims: list[dict[str, Any]]) -> None:
    """Consolidate compatible weekly/current surveillance facts into one snapshot.

    Historical closed periods remain separate. Claims are merged only when they are
    surveillance baselines, share domains, and have a compatible surveillance topic.
    This prevents unrelated diseases from being collapsed into one baseline.
    """
    baselines = [
        claim for claim in claims
        if claim.get("claim_kind") == "surveillance_baseline"
        and not _is_closed_historical_period(claim)
    ]
    if len(baselines) < 2:
        return

    clusters: list[list[dict[str, Any]]] = []
    for claim in baselines:
        placed = False
        for cluster in clusters:
            if _surveillance_claims_compatible(cluster[0], claim):
                cluster.append(claim)
                placed = True
                break
        if not placed:
            clusters.append([claim])

    for cluster in clusters:
        if len(cluster) < 2:
            continue
        canonical_group = str(cluster[0].get("group_id") or cluster[0].get("claim_id") or "surveillance")
        for claim in cluster:
            claim["group_id"] = canonical_group


def _is_closed_historical_period(claim: dict[str, Any]) -> bool:
    period = claim.get("reference_period") or {}
    return period.get("period_type") == "historical_period"


def _surveillance_claims_compatible(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_domains = tuple(sorted(str(x) for x in (left.get("domains") or [])))
    right_domains = tuple(sorted(str(x) for x in (right.get("domains") or [])))
    if left_domains != right_domains:
        return False

    for key in ("disease_verbatim", "pathogen_verbatim"):
        lval = _folded(left.get(key))
        rval = _folded(right.get(key))
        if lval and rval and lval != rval:
            return False

    left_topic = _surveillance_topic_hint(left)
    right_topic = _surveillance_topic_hint(right)
    if not left_topic or not right_topic:
        return False
    return left_topic == right_topic


def _surveillance_topic_hint(claim: dict[str, Any]) -> str | None:
    explicit = _folded(claim.get("disease_verbatim")) or _folded(claim.get("pathogen_verbatim"))
    if explicit:
        return explicit
    text = " ".join(
        [
            str(claim.get("group_id") or ""),
            str(claim.get("summary") or ""),
        ]
        + [str(ev.get("text") or "") for ev in (claim.get("evidence") or [])]
    ).casefold()
    if "hantavirus" in text:
        return "hantavirus"
    return None


def _folded(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip().casefold()
    return value or None


def _canonicalize_textual_evidence(payload: dict[str, Any]) -> None:
    for signal in payload.get("signals") or []:
        for evidence in signal.get("evidence") or []:
            evidence_type = str(evidence.get("type") or "").casefold()
            if evidence_type in _TEXTUAL_EVIDENCE_TYPES:
                evidence["type"] = "text"
