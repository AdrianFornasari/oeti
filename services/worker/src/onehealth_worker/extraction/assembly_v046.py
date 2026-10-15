from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from .assembly_v045 import assemble_claims_payload as assemble_claims_payload_v045
from .animal_multisite import prepare_animal_multisite_claims


_TEXTUAL_EVIDENCE_TYPES = {"text", "quote", "excerpt", "document_text"}


def assemble_claims_payload(claim_payload: dict[str, Any]) -> dict[str, Any]:
    """Assemble atomic claims with deterministic v0.4.6 benchmark hardening.

    v0.4.6 keeps provider-facing atomic claims unchanged on disk. It prepares a deep
    copy before v0.4.5 assembly, applies deterministic hardening and conservative
    animal-claim guards, then canonicalizes textual evidence labels.
    """
    prepared = _prepare_claims_for_v046(claim_payload)
    payload = assemble_claims_payload_v045(prepared)
    _canonicalize_textual_evidence(payload)
    return payload


def _prepare_claims_for_v046(claim_payload: dict[str, Any]) -> dict[str, Any]:
    prepared = deepcopy(claim_payload)
    claims = list(prepared.get("claims") or [])
    claims = prepare_animal_multisite_claims(claims, prepared.setdefault("warnings", []))
    kept = []
    for claim in claims:
        if _is_nonbiological_facility_inventory(claim):
            prepared.setdefault("warnings", []).append(
                f"ASM-FACILITY-01 {claim.get('claim_id')}: facility inventory excluded from wildlife findings."
            )
            continue
        if _is_explicit_confirmed_animal_outbreak(claim):
            claim["claim_kind"] = "outbreak_update"
            prepared.setdefault("warnings", []).append(
                f"ASM-ANIMAL-01 {claim.get('claim_id')}: confirmed animal focal event retained as outbreak."
            )
        kept.append(claim)
    claims = kept

    groups: dict[str, list[dict[str, Any]]] = {}
    for claim in claims:
        group_id = str(claim.get("group_id") or claim.get("claim_id") or "?")
        groups.setdefault(group_id, []).append(claim)

    for group in groups.values():
        _attach_supporting_animal_lab_confirmation(group, prepared.setdefault("warnings", []))
        _prepare_collective_lab_characterization(group)
        _merge_operational_mobility_into_intervention(group)

    claims = [claim for claim in claims if not _is_generic_investigation_context(claim)]
    _merge_current_surveillance_snapshots(claims)
    prepared["claims"] = claims
    return prepared


def _claim_evidence_text(claim: dict[str, Any]) -> str:
    return " ".join(" ".join(str(ev.get("text") or "") for ev in
        (claim.get("evidence") or [])).casefold().split())


def _is_explicit_confirmed_animal_outbreak(claim: dict[str, Any]) -> bool:
    """Require explicit outbreak or facility detection, not just an animal test."""
    if (claim.get("claim_kind") != "diagnostic_result"
        or claim.get("polarity") != "positive"
        or claim.get("verification_status") != "confirmed"
        or (claim.get("diagnostics") or {}).get("result") != "positive"
        or (claim.get("reference_period") or {}).get("period_type") == "historical_period"
        or (claim.get("subject") or {}).get("subject_type") not in {"animal", "wildlife"}
        or "animal" not in (claim.get("domains") or [])):
        return False
    event_locations = [loc for loc in (claim.get("locations") or []) if loc.get("role") == "event_location"]
    if not event_locations or any(not loc.get("locality") for loc in event_locations):
        return False
    locations = {tuple(loc.get(key) for key in ("country_iso2", "admin1", "admin2", "locality"))
        for loc in event_locations}
    if len(locations) != 1:
        return False
    text = _claim_evidence_text(claim)
    if re.search(r"\b(no|not|sin|posible|possible|sospech\w*|presunt\w*|pasado|historical)\b", text):
        return False
    if re.search(r"\b(confirmó|confirmaron|confirmed)\b.{0,40}\b(brote|outbreak)\b", text):
        return True
    # Operational focal-event representation, not a biological outbreak threshold.
    return _is_reported_single_facility_detection(claim, text, event_locations[0]["locality"])


def _is_reported_single_facility_detection(claim: dict[str, Any], text: str, locality: str) -> bool:
    subject = claim.get("subject") or {}
    if subject.get("subject_type") != "animal":
        return False
    verbatim = " ".join(str(subject.get("verbatim") or "").casefold().split())
    if not re.search(r"\b(aves|cerdos|bovinos|ovinos|caprinos|equinos|animales|rebaño|piara|parvada|poultry|livestock|cattle|pigs|birds|herd|flock)\b", verbatim):
        return False
    # Require a complete locality in the facility clause, not a name prefix
    # or a laboratory location in another clause of the same sentence.
    for sentence in re.split(r"[.!?]", text):
        # Parenthetical animal lists inside em dashes may contain commas; they
        # do not establish a location. Keep the original sentence for population
        # matching, and remove only these asides from the location-clause check.
        asides = re.findall(r"—([^—]*)—", sentence)
        if any(re.search(r"\b(en|in|localidad|located|ubicad\w*|situad\w*)\b", aside) for aside in asides):
            continue
        location_text = re.sub(r"—[^—]*—", " ", sentence)
        location_text = " ".join(location_text.split())
        facility_location = (r"\b(un predio|un establecimiento|una granja|a farm|an establishment)\b"
            r"(?:\s+(?:multiespecie|avícola|comercial|rural)){0,2}\s+"
            r"(?:(?:ubicado|ubicada|situado|situada|located)\s+)?"
            r"(?:(?:en\s+)?(?:la\s+)?localidad\s+de\s+|(?:de|en|in)\s+)"
            + re.escape(locality.casefold())
            + r"(?=\s*(?:[,;]|$))")
        if (verbatim in sentence
            and re.search(r"\b(confirmó|detectó|confirmed|detected)\b.{0,60}\b(caso positivo|positive case)\b", sentence)
            and re.search(facility_location, location_text)):
            return True
    return False


def _attach_supporting_animal_lab_confirmation(group: list[dict[str, Any]], warnings: list[str]) -> None:
    anchors = [claim for claim in group if claim.get("claim_kind") == "outbreak_update"
        and (claim.get("subject") or {}).get("subject_type") == "animal"
        and claim.get("polarity") == "positive" and claim.get("verification_status") == "confirmed"
        and (claim.get("diagnostics") or {}).get("result") == "positive"]
    if len(anchors) != 1:
        return
    anchor = anchors[0]
    event_locations = [loc for loc in (anchor.get("locations") or []) if loc.get("role") == "event_location"]
    if (not event_locations or any(not loc.get("locality") for loc in event_locations)
        or len({tuple(loc.get(key) for key in ("country_iso2", "admin1", "admin2", "locality"))
            for loc in event_locations}) != 1):
        return
    pathogen = _folded(anchor.get("pathogen_verbatim"))
    if not pathogen:
        return
    for claim in group:
        locations = claim.get("locations") or []
        if (claim.get("claim_kind") != "diagnostic_result" or claim.get("polarity") != "positive"
            or claim.get("verification_status") != "confirmed"
            or (claim.get("subject") or {}).get("subject_type") != "other"
            or _folded(claim.get("pathogen_verbatim")) != pathogen
            or (claim.get("diagnostics") or {}).get("result") != "positive"
            or not (claim.get("diagnostics") or {}).get("test_reported")
            or (claim.get("reference_period") or {}).get("period_type") == "historical_period"
            or (claim.get("metric") or {}).get("reported")
            or (claim.get("genomics") or {}).get("sequence_reported")
            or not locations or any(loc.get("role") != "laboratory_location" for loc in locations)):
            continue
        anchor_date, support_date = anchor.get("event_date") or {}, claim.get("event_date") or {}
        if any(support_date.get(key) and support_date.get(key) != anchor_date.get(key) for key in ("start", "end")):
            continue
        text = _claim_evidence_text(claim)
        if not re.search(r"\b(confirmó el resultado|confirmed the result)\b", text):
            continue
        if re.search(r"\b(no|not|sin|posible|possible)\b", text):
            continue
        claim["claim_kind"] = "outbreak_update"
        warnings.append(f"ASM-ANIMAL-02 {claim.get('claim_id')}: supporting laboratory confirmation attached to focal event.")


def _is_nonbiological_facility_inventory(claim: dict[str, Any]) -> bool:
    """Exclude explicit zero inventories of facilities, never absence of infection."""
    subject = claim.get("subject") or {}
    metric = claim.get("metric") or {}
    diagnostics = claim.get("diagnostics") or {}
    if (claim.get("claim_kind") != "wildlife_presence_absence"
        or claim.get("polarity") != "negative" or subject.get("subject_type") != "other"
        or str(subject.get("verbatim") or "").strip().casefold() not in
            {"granjas", "granjas comerciales", "farms", "commercial farms"}
        or not metric.get("reported") or metric.get("value_numeric") != 0
        or metric.get("unit") not in {"granjas", "farms"}
        or diagnostics.get("test_reported") or diagnostics.get("result") == "negative"
        or (claim.get("genomics") or {}).get("sequence_reported")):
        return False
    text = _claim_evidence_text(claim)
    if re.search(r"\b(brotes?|casos?|infect\w*|virus|aves|animales|outbreaks?|cases?|animals)\b", text):
        return False
    return bool(re.search(r"\b(no se (encuentran|encontraron|registran|registraron)|there (are|were) no)\s+(granjas|farms)\b", text))


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

    Historical closed periods remain separate. Claims are merged only when they share
    surveillance topic and compatible geographic scope. This allows a weekly national
    count and the corresponding national seasonal total to form one snapshot without
    collapsing a regional observation (for example NOA) into the national baseline.
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
    if not left_topic or not right_topic or left_topic != right_topic:
        return False

    left_scope = _surveillance_scope_hint(left)
    right_scope = _surveillance_scope_hint(right)
    if _is_subnational_scope(left_scope) or _is_subnational_scope(right_scope):
        return bool(left_scope and right_scope and left_scope == right_scope)
    if left_scope and right_scope and left_scope != right_scope:
        return False
    return True


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


def _surveillance_scope_hint(claim: dict[str, Any]) -> str | None:
    for location in claim.get("locations") or []:
        locality = _folded(location.get("locality"))
        admin2 = _folded(location.get("admin2"))
        admin1 = _folded(location.get("admin1"))
        region = _folded(location.get("region"))
        if locality:
            return f"locality:{locality}"
        if admin2:
            return f"admin2:{admin2}"
        if admin1:
            return f"admin1:{admin1}"
        if region:
            return f"region:{region}"

    text = " ".join(
        [
            str(claim.get("group_id") or ""),
            str(claim.get("summary") or ""),
        ]
        + [str(ev.get("text") or "") for ev in (claim.get("evidence") or [])]
    ).casefold()

    regional_markers = {
        "noa": "region:noa",
        "nea": "region:nea",
        "cuyo": "region:cuyo",
        "patagonia": "region:patagonia",
        "región centro": "region:centro",
        "region centro": "region:centro",
    }
    for marker, scope in regional_markers.items():
        if marker in text:
            return scope

    for location in claim.get("locations") or []:
        country_iso2 = _folded(location.get("country_iso2"))
        country = _folded(location.get("country"))
        if country_iso2:
            return f"country:{country_iso2}"
        if country:
            return f"country:{country}"

    national_markers = (
        "a nivel nacional",
        "nivel nacional",
        "vigilancia nacional",
        "total de casos de toda la temporada",
        "argentina",
    )
    if any(marker in text for marker in national_markers):
        return "country:ar"
    return None


def _is_subnational_scope(scope: str | None) -> bool:
    if not scope:
        return False
    return scope.startswith(("region:", "admin1:", "admin2:", "locality:"))


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
