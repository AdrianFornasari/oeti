from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


WEIGHT_KEYS = {
    "etiology",
    "geography",
    "temporality",
    "host",
    "epidemiology",
    "shared_context",
}

RELATIONS = {
    "supports",
    "duplicates",
    "refines",
    "contradicts",
    "possibly_related",
    "unrelated",
    "unknown",
}

DECISIONS = {
    "auto_linked",
    "review_required",
    "rejected",
}

GATES = {
    "eligible",
    "ineligible",
}


class EventMatchingBenchmarkError(ValueError):
    """Invalid v0.4.8 event-matching benchmark."""


@dataclass(frozen=True)
class EventMatchingBenchmark:
    manifest_path: Path
    manifest: dict[str, Any]
    gold_paths: tuple[Path, ...]
    gold_documents: tuple[dict[str, Any], ...]
    signal_index: dict[str, dict[str, Any]]
    signal_sources: dict[str, Path]
    adjudicated_pairs: tuple[dict[str, Any], ...]

    @property
    def signal_count(self) -> int:
        return len(self.signal_index)

    @property
    def pair_count(self) -> int:
        return len(self.adjudicated_pairs)


def _error(message: str) -> None:
    raise EventMatchingBenchmarkError(message)


def _string_list(
    value: Any,
    field: str,
) -> list[str]:
    if not isinstance(value, list):
        _error(f"{field} must be an array.")

    if any(
        not isinstance(item, str)
        or not item.strip()
        for item in value
    ):
        _error(
            f"{field} must contain only non-empty strings."
        )

    if len(value) != len(set(value)):
        _error(
            f"{field} must not contain duplicates."
        )

    return value


def _mapping(
    value: Any,
    field: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _error(f"{field} must be an object.")

    return value


def _probability(
    value: Any,
    field: str,
) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
    ):
        _error(f"{field} must be numeric.")

    value = float(value)

    if (
        not math.isfinite(value)
        or not 0.0 <= value <= 1.0
    ):
        _error(
            f"{field} must be between 0 and 1."
        )

    return value


def signal_matching_eligible(
    signal: Mapping[str, Any],
    eligibility: Mapping[str, Any],
) -> bool:
    """Apply the deterministic eligibility gate before any scoring."""

    role = signal.get("signal_role")
    signal_type = signal.get("signal_type")

    eligible_roles = set(
        _string_list(
            eligibility.get(
                "eligible_signal_roles"
            ),
            "eligibility.eligible_signal_roles",
        )
    )

    ineligible_roles = set(
        _string_list(
            eligibility.get(
                "ineligible_signal_roles"
            ),
            "eligibility.ineligible_signal_roles",
        )
    )

    ineligible_types = set(
        _string_list(
            eligibility.get(
                "ineligible_signal_types"
            ),
            "eligibility.ineligible_signal_types",
        )
    )

    return (
        role in eligible_roles
        and role not in ineligible_roles
        and signal_type not in ineligible_types
    )


def validate_event_matching_manifest(
    manifest: Mapping[str, Any],
) -> None:
    """Validate the structural contract of the v0.4.8 manifest."""

    if manifest.get("benchmark_version") != "0.4.8":
        _error(
            "benchmark_version must be '0.4.8'."
        )

    if manifest.get("benchmark_kind") != "event_matching":
        _error(
            "benchmark_kind must be 'event_matching'."
        )

    if manifest.get("signal_source") != "adjudicated_gold":
        _error(
            "signal_source must be 'adjudicated_gold'."
        )

    if not isinstance(
        manifest.get("case_code"),
        str,
    ):
        _error("case_code must be a string.")

    if not isinstance(
        manifest.get("architecture"),
        str,
    ):
        _error("architecture must be a string.")

    gold_paths = _string_list(
        manifest.get("source_gold_documents"),
        "source_gold_documents",
    )

    if not gold_paths:
        _error(
            "source_gold_documents must not be empty."
        )

    eligibility = _mapping(
        manifest.get("eligibility"),
        "eligibility",
    )

    eligible_roles = set(
        _string_list(
            eligibility.get(
                "eligible_signal_roles"
            ),
            "eligibility.eligible_signal_roles",
        )
    )

    ineligible_roles = set(
        _string_list(
            eligibility.get(
                "ineligible_signal_roles"
            ),
            "eligibility.ineligible_signal_roles",
        )
    )

    ineligible_types = set(
        _string_list(
            eligibility.get(
                "ineligible_signal_types"
            ),
            "eligibility.ineligible_signal_types",
        )
    )

    if eligible_roles & ineligible_roles:
        _error(
            "eligible and ineligible signal roles must be disjoint."
        )

    if (
        "official_alert" in eligible_roles
        or "official_alert" in ineligible_roles
    ):
        _error(
            "official_alert is a signal_type, not a signal_role."
        )

    if "official_alert" not in ineligible_types:
        _error(
            "official_alert must be an ineligible signal_type."
        )

    if (
        eligibility.get(
            "short_circuit_ineligible"
        )
        is not True
    ):
        _error(
            "short_circuit_ineligible must be true."
        )

    scoring = _mapping(
        manifest.get("scoring"),
        "scoring",
    )

    weights = _mapping(
        scoring.get("weights"),
        "scoring.weights",
    )

    if set(weights) != WEIGHT_KEYS:
        _error(
            "scoring.weights has unexpected component keys."
        )

    total = sum(
        _probability(
            weights[key],
            f"scoring.weights.{key}",
        )
        for key in WEIGHT_KEYS
    )

    if not math.isclose(
        total,
        1.0,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        _error(
            f"scoring weights must sum to 1.0; got {total}."
        )

    thresholds = _mapping(
        scoring.get("thresholds"),
        "scoring.thresholds",
    )

    auto_link = _probability(
        thresholds.get("auto_link_min"),
        "scoring.thresholds.auto_link_min",
    )

    review = _probability(
        thresholds.get("review_min"),
        "scoring.thresholds.review_min",
    )

    if auto_link <= review:
        _error(
            "auto_link_min must be greater than review_min."
        )

    rules = _mapping(
        scoring.get("decision_rules"),
        "scoring.decision_rules",
    )

    expected_rules = {
        "score_gte_auto_link_min": "auto_linked",
        "score_gte_review_min_and_lt_auto_link_min": "review_required",
        "score_lt_review_min": "rejected",
        "hard_conflict_blocks_auto_link": True,
        "hard_conflict_forces_rejected_merge": True,
    }

    for key, expected in expected_rules.items():
        if rules.get(key) != expected:
            _error(
                f"invalid scoring.decision_rules.{key}."
            )

    policy = _mapping(
        manifest.get("hard_conflict_policy"),
        "hard_conflict_policy",
    )

    expected_policy = {
        "explicit_genomic_incompatibility": True,
        "explicit_official_non_relation": True,
        "explicit_source_refutation": True,
        "host_difference_alone": False,
        "domain_difference_alone": False,
        "geographic_difference_alone": False,
    }

    for key, expected in expected_policy.items():
        if policy.get(key) is not expected:
            _error(
                f"invalid hard_conflict_policy.{key}."
            )

    pairs = manifest.get(
        "adjudicated_pairs"
    )

    if (
        not isinstance(pairs, list)
        or not pairs
    ):
        _error(
            "adjudicated_pairs must be a non-empty array."
        )

    seen_pair_ids: set[str] = set()

    for pair in pairs:
        pair = _mapping(
            pair,
            "adjudicated_pair",
        )

        pair_id = pair.get("pair_id")
        source_id = pair.get(
            "source_signal_id"
        )
        target_id = pair.get(
            "target_signal_id"
        )

        if (
            not isinstance(pair_id, str)
            or not pair_id
        ):
            _error(
                "every pair must have pair_id."
            )

        if pair_id in seen_pair_ids:
            _error(
                f"duplicate pair_id: {pair_id}."
            )

        seen_pair_ids.add(pair_id)

        if (
            not isinstance(source_id, str)
            or not isinstance(target_id, str)
        ):
            _error(
                f"{pair_id} must reference string signal IDs."
            )

        if source_id == target_id:
            _error(
                f"{pair_id} cannot compare a signal with itself."
            )

        gate = pair.get(
            "expected_gate"
        )
        relation = pair.get(
            "expected_relation"
        )
        decision = pair.get(
            "expected_decision"
        )
        merge_allowed = pair.get(
            "expected_merge_allowed"
        )
        hard_conflict = pair.get(
            "expected_hard_conflict"
        )

        if gate not in GATES:
            _error(
                f"{pair_id} has invalid expected_gate."
            )

        if not isinstance(
            merge_allowed,
            bool,
        ):
            _error(
                f"{pair_id} expected_merge_allowed must be boolean."
            )

        if not isinstance(
            hard_conflict,
            bool,
        ):
            _error(
                f"{pair_id} expected_hard_conflict must be boolean."
            )

        if gate == "ineligible":
            if (
                relation is not None
                or decision is not None
            ):
                _error(
                    f"{pair_id} must short-circuit without "
                    "relation/decision."
                )

            if (
                merge_allowed
                or hard_conflict
            ):
                _error(
                    f"{pair_id} invalid ineligible expectations."
                )

        else:
            if relation not in RELATIONS:
                _error(
                    f"{pair_id} has invalid expected_relation."
                )

            if decision not in DECISIONS:
                _error(
                    f"{pair_id} has invalid expected_decision."
                )

        if hard_conflict:
            if not pair.get(
                "expected_hard_conflict_reason"
            ):
                _error(
                    f"{pair_id} hard conflict requires a reason."
                )

            if (
                merge_allowed
                or decision != "rejected"
            ):
                _error(
                    f"{pair_id} hard conflict must reject merge."
                )

        if (
            decision == "auto_linked"
            and not merge_allowed
        ):
            _error(
                f"{pair_id} auto_linked requires "
                "merge_allowed=true."
            )

        if (
            decision == "rejected"
            and merge_allowed
        ):
            _error(
                f"{pair_id} rejected cannot allow merge."
            )

    release = _mapping(
        manifest.get(
            "release_thresholds"
        ),
        "release_thresholds",
    )

    for key in (
        "ineligible_gate_accuracy",
        "hard_conflict_recall",
        "auto_link_precision",
        "pair_decision_accuracy",
        "relation_accuracy",
    ):
        _probability(
            release.get(key),
            f"release_thresholds.{key}",
        )

    false_links = release.get(
        "hard_conflict_false_auto_links"
    )

    if (
        isinstance(false_links, bool)
        or not isinstance(false_links, int)
    ):
        _error(
            "hard_conflict_false_auto_links must be an integer."
        )

    if false_links < 0:
        _error(
            "hard_conflict_false_auto_links cannot be negative."
        )

    if not isinstance(
        release.get("order_invariance"),
        bool,
    ):
        _error(
            "order_invariance must be boolean."
        )


def _read_json(
    path: Path,
    label: str,
) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except FileNotFoundError as exc:
        raise EventMatchingBenchmarkError(
            f"{label} not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise EventMatchingBenchmarkError(
            f"{label} is invalid JSON: {path}: {exc}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        _error(
            f"{label} must contain a JSON object."
        )

    return payload


def load_event_matching_benchmark(
    manifest_path: str | Path,
) -> EventMatchingBenchmark:
    """Load gold files, index signals and validate pair references."""

    path = Path(
        manifest_path
    ).resolve()

    manifest = _read_json(
        path,
        "event-matching manifest",
    )

    validate_event_matching_manifest(
        manifest
    )

    case_code = manifest[
        "case_code"
    ]

    gold_paths: list[Path] = []
    gold_documents: list[
        dict[str, Any]
    ] = []

    signal_index: dict[
        str,
        dict[str, Any],
    ] = {}

    signal_sources: dict[
        str,
        Path,
    ] = {}

    for relative_path in manifest[
        "source_gold_documents"
    ]:
        gold_path = (
            path.parent
            / relative_path
        ).resolve()

        gold = _read_json(
            gold_path,
            "gold document",
        )

        if gold.get(
            "case_code"
        ) != case_code:
            _error(
                f"case_code mismatch in {gold_path}."
            )

        expected = _mapping(
            gold.get("expected"),
            f"{gold_path}.expected",
        )

        signals = expected.get(
            "signals"
        )

        if not isinstance(
            signals,
            list,
        ):
            _error(
                f"{gold_path}.expected.signals "
                "must be an array."
            )

        for signal in signals:
            signal = _mapping(
                signal,
                f"{gold_path}.signal",
            )

            signal_id = signal.get(
                "local_signal_id"
            )

            if (
                not isinstance(
                    signal_id,
                    str,
                )
                or not signal_id
            ):
                _error(
                    f"{gold_path} contains a signal "
                    "without local_signal_id."
                )

            if signal_id in signal_index:
                _error(
                    f"duplicate local_signal_id: "
                    f"{signal_id}."
                )

            if not isinstance(
                signal.get("signal_role"),
                str,
            ):
                _error(
                    f"{signal_id} has invalid signal_role."
                )

            if not isinstance(
                signal.get("signal_type"),
                str,
            ):
                _error(
                    f"{signal_id} has invalid signal_type."
                )

            signal_index[
                signal_id
            ] = dict(signal)

            signal_sources[
                signal_id
            ] = gold_path

        gold_paths.append(
            gold_path
        )
        gold_documents.append(
            gold
        )

    eligibility = _mapping(
        manifest["eligibility"],
        "eligibility",
    )

    for pair in manifest[
        "adjudicated_pairs"
    ]:
        source_id = pair[
            "source_signal_id"
        ]
        target_id = pair[
            "target_signal_id"
        ]
        pair_id = pair[
            "pair_id"
        ]

        missing = [
            signal_id
            for signal_id in (
                source_id,
                target_id,
            )
            if signal_id
            not in signal_index
        ]

        if missing:
            _error(
                f"{pair_id} references unknown "
                f"signal IDs: {missing}."
            )

        source_eligible = (
            signal_matching_eligible(
                signal_index[
                    source_id
                ],
                eligibility,
            )
        )

        target_eligible = (
            signal_matching_eligible(
                signal_index[
                    target_id
                ],
                eligibility,
            )
        )

        derived_gate = (
            "eligible"
            if (
                source_eligible
                and target_eligible
            )
            else "ineligible"
        )

        if (
            pair["expected_gate"]
            != derived_gate
        ):
            _error(
                f"{pair_id} expected_gate="
                f"{pair['expected_gate']!r}, "
                f"derived={derived_gate!r}."
            )

    return EventMatchingBenchmark(
        manifest_path=path,
        manifest=manifest,
        gold_paths=tuple(
            gold_paths
        ),
        gold_documents=tuple(
            gold_documents
        ),
        signal_index=signal_index,
        signal_sources=signal_sources,
        adjudicated_pairs=tuple(
            dict(pair)
            for pair in manifest[
                "adjudicated_pairs"
            ]
        ),
    )

from datetime import date


EVENT_MATCHING_COMPONENT_WEIGHTS = {
    "etiology": 0.35,
    "geography": 0.25,
    "temporality": 0.15,
    "host": 0.10,
    "epidemiology": 0.10,
    "shared_context": 0.05,
}


_EVENT_LOCATION_ROLES = {
    "event_location",
    "possible_exposure_location",
    "sampling_location",
}


_CONTEXT_LOCATION_ROLES = {
    "travel_history",
    "laboratory_location",
    "testing_location",
    "current_location",
    "reporting_jurisdiction",
}


_HANTAVIRUS_PATHOGEN_TERMS = {
    "hantavirus",
    "andes virus",
    "virus andes",
    "cepa andes",
    "orthohantavirus andesense",
}


_ONE_HEALTH_HOST_TYPES = {
    "human",
    "wildlife",
    "domestic_animal",
    "vector",
}


_SIGNAL_TYPE_COMPATIBILITY = {
    frozenset({"outbreak", "cluster"}): 0.95,
    frozenset({"outbreak", "case_report"}): 0.90,
    frozenset({"cluster", "case_report"}): 0.90,
    frozenset(
        {
            "laboratory_investigation",
            "laboratory_result",
        }
    ): 0.95,
    frozenset(
        {
            "laboratory_result",
            "genomic_observation",
        }
    ): 0.85,
    frozenset(
        {
            "outbreak",
            "laboratory_result",
        }
    ): 0.80,
    frozenset(
        {
            "outbreak",
            "genomic_observation",
        }
    ): 0.80,
    frozenset(
        {
            "outbreak",
            "transmission_observation",
        }
    ): 0.85,
    frozenset(
        {
            "case_report",
            "laboratory_result",
        }
    ): 0.85,
    frozenset(
        {
            "case_report",
            "transmission_observation",
        }
    ): 0.80,
    frozenset(
        {
            "transmission_observation",
            "genomic_observation",
        }
    ): 0.65,
    frozenset(
        {
            "intervention",
            "wildlife_event",
        }
    ): 0.70,
    frozenset(
        {
            "intervention",
            "laboratory_result",
        }
    ): 0.70,
    frozenset(
        {
            "intervention",
            "travel_or_mobility",
        }
    ): 0.70,
    frozenset(
        {
            "travel_or_mobility",
            "outbreak",
        }
    ): 0.60,
}


def _norm_value(
    value: Any,
) -> str | None:
    if value is None:
        return None

    normalized = " ".join(
        str(value)
        .strip()
        .casefold()
        .split()
    )

    return normalized or None


def _entity_name(
    entity: Any,
) -> str | None:
    if not isinstance(
        entity,
        Mapping,
    ):
        return None

    canonical = _norm_value(
        entity.get("canonical_name")
    )

    if canonical:
        return canonical

    normalization_status = _norm_value(
        entity.get("normalization_status")
    )

    if normalization_status == "unresolved":
        # An explicitly unresolved entity is missing
        # information, not evidence of incompatibility.
        return None

    return _norm_value(
        entity.get("verbatim")
    )


def _pathogen_similarity(
    left: str,
    right: str,
) -> float:
    if left == right:
        return 1.0

    if (
        left in _HANTAVIRUS_PATHOGEN_TERMS
        and right in _HANTAVIRUS_PATHOGEN_TERMS
    ):
        return 0.85

    return 0.0


def _etiology_score(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> float | None:
    source_disease = _entity_name(
        source.get("disease")
    )
    target_disease = _entity_name(
        target.get("disease")
    )

    source_pathogen = _entity_name(
        source.get("pathogen")
    )
    target_pathogen = _entity_name(
        target.get("pathogen")
    )

    disease_score: float | None = None
    pathogen_score: float | None = None

    if (
        source_disease
        and target_disease
    ):
        disease_score = (
            1.0
            if source_disease
            == target_disease
            else 0.0
        )

    if (
        source_pathogen
        and target_pathogen
    ):
        pathogen_score = (
            _pathogen_similarity(
                source_pathogen,
                target_pathogen,
            )
        )

    if (
        pathogen_score is not None
        and disease_score is not None
    ):
        return (
            0.75 * pathogen_score
            + 0.25 * disease_score
        )

    if pathogen_score is not None:
        return pathogen_score

    if disease_score is not None:
        # Disease-only agreement is useful but less specific
        # than pathogen-level agreement.
        return (
            0.80
            if disease_score == 1.0
            else 0.0
        )

    return None


def _location_role(
    location: Mapping[str, Any],
) -> str | None:
    return _norm_value(
        location.get("role")
    )


def _locations_for_roles(
    signal: Mapping[str, Any],
    roles: set[str],
) -> list[Mapping[str, Any]]:
    locations = signal.get(
        "locations"
    )

    if not isinstance(
        locations,
        list,
    ):
        return []

    return [
        location
        for location in locations
        if (
            isinstance(
                location,
                Mapping,
            )
            and _location_role(
                location
            )
            in roles
        )
    ]


def _location_similarity(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> float:
    source_country = _norm_value(
        source.get("country_iso2")
        or source.get("country")
    )
    target_country = _norm_value(
        target.get("country_iso2")
        or target.get("country")
    )

    if (
        source_country
        and target_country
        and source_country
        != target_country
    ):
        return 0.0

    for field, score in (
        ("locality", 1.0),
        ("admin2", 0.90),
        ("admin1", 0.80),
    ):
        source_value = _norm_value(
            source.get(field)
        )
        target_value = _norm_value(
            target.get(field)
        )

        if (
            source_value
            and target_value
            and source_value
            == target_value
        ):
            return score

    if (
        source_country
        and target_country
        and source_country
        == target_country
    ):
        return 0.35

    return 0.0


def _best_location_similarity(
    source_locations: list[
        Mapping[str, Any]
    ],
    target_locations: list[
        Mapping[str, Any]
    ],
) -> float | None:
    if (
        not source_locations
        or not target_locations
    ):
        return None

    return max(
        _location_similarity(
            source,
            target,
        )
        for source in source_locations
        for target in target_locations
    )


def _geography_score(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> float | None:
    return _best_location_similarity(
        _locations_for_roles(
            source,
            _EVENT_LOCATION_ROLES,
        ),
        _locations_for_roles(
            target,
            _EVENT_LOCATION_ROLES,
        ),
    )


def _parse_date(
    value: Any,
) -> date | None:
    if not isinstance(
        value,
        str,
    ):
        return None

    try:
        return date.fromisoformat(
            value
        )
    except ValueError:
        return None


def _partial_date_bounds(
    value: Any,
) -> tuple[
    date,
    date,
] | None:
    if not isinstance(
        value,
        Mapping,
    ):
        return None

    exact = _parse_date(
        value.get("date")
    )

    if exact:
        return exact, exact

    year = value.get("year")
    month = value.get("month")

    if (
        isinstance(year, int)
        and isinstance(month, int)
        and 1 <= month <= 12
    ):
        import calendar

        last_day = calendar.monthrange(
            year,
            month,
        )[1]

        return (
            date(
                year,
                month,
                1,
            ),
            date(
                year,
                month,
                last_day,
            ),
        )

    if isinstance(year, int):
        return (
            date(
                year,
                1,
                1,
            ),
            date(
                year,
                12,
                31,
            ),
        )

    return None


def _signal_interval(
    signal: Mapping[str, Any],
) -> tuple[
    date,
    date,
] | None:
    event_date = signal.get(
        "event_date"
    )

    if isinstance(
        event_date,
        Mapping,
    ):
        start = _parse_date(
            event_date.get("start")
        )

        end = _parse_date(
            event_date.get("end")
        )

        if start:
            return (
                start,
                end or start,
            )

    reference = signal.get(
        "reference_period"
    )

    if not isinstance(
        reference,
        Mapping,
    ):
        return None

    start_bounds = (
        _partial_date_bounds(
            reference.get("start")
        )
    )

    end_bounds = (
        _partial_date_bounds(
            reference.get("end")
        )
    )

    if (
        start_bounds
        and end_bounds
    ):
        return (
            start_bounds[0],
            end_bounds[1],
        )

    if start_bounds:
        return start_bounds

    if end_bounds:
        return end_bounds

    return None


def _temporality_score(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> float | None:
    source_interval = (
        _signal_interval(source)
    )

    target_interval = (
        _signal_interval(target)
    )

    if (
        source_interval is None
        or target_interval is None
    ):
        return None

    source_start, source_end = (
        source_interval
    )

    target_start, target_end = (
        target_interval
    )

    if (
        source_start <= target_end
        and target_start <= source_end
    ):
        return 1.0

    if source_end < target_start:
        gap = (
            target_start
            - source_end
        ).days
    else:
        gap = (
            source_start
            - target_end
        ).days

    if gap <= 7:
        return 0.90

    if gap <= 30:
        return 0.75

    if gap <= 90:
        return 0.50

    if gap <= 180:
        return 0.25

    return 0.0


def _host_score(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> float | None:
    source_hosts = source.get(
        "hosts"
    )

    target_hosts = target.get(
        "hosts"
    )

    if (
        not isinstance(source_hosts, list)
        or not isinstance(target_hosts, list)
        or not source_hosts
        or not target_hosts
    ):
        return None

    source_names = {
        name
        for host in source_hosts
        if isinstance(host, Mapping)
        for name in [
            _norm_value(
                host.get(
                    "canonical_name"
                )
                or host.get(
                    "verbatim"
                )
            )
        ]
        if name
    }

    target_names = {
        name
        for host in target_hosts
        if isinstance(host, Mapping)
        for name in [
            _norm_value(
                host.get(
                    "canonical_name"
                )
                or host.get(
                    "verbatim"
                )
            )
        ]
        if name
    }

    if (
        source_names
        and target_names
        and source_names
        & target_names
    ):
        return 1.0

    source_types = {
        value
        for host in source_hosts
        if isinstance(host, Mapping)
        for value in [
            _norm_value(
                host.get("host_type")
            )
        ]
        if value
    }

    target_types = {
        value
        for host in target_hosts
        if isinstance(host, Mapping)
        for value in [
            _norm_value(
                host.get("host_type")
            )
        ]
        if value
    }

    if (
        source_types
        and target_types
        and source_types
        & target_types
    ):
        return 0.85

    if (
        source_types
        and target_types
        and source_types
        <= _ONE_HEALTH_HOST_TYPES
        and target_types
        <= _ONE_HEALTH_HOST_TYPES
    ):
        # Cross-sector host differences are compatible
        # with a One Health event and are not conflicts.
        return 0.50

    return 0.25


def _diagnostic_result(
    signal: Mapping[str, Any],
) -> str | None:
    diagnostics = signal.get(
        "diagnostics"
    )

    if not isinstance(
        diagnostics,
        Mapping,
    ):
        return None

    value = _norm_value(
        diagnostics.get("result")
    )

    if value in {
        "positive",
        "negative",
        "indeterminate",
    }:
        return value

    return None


def _epidemiology_score(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> float | None:
    source_type = _norm_value(
        source.get("signal_type")
    )

    target_type = _norm_value(
        target.get("signal_type")
    )

    if (
        not source_type
        or not target_type
    ):
        return None

    if source_type == target_type:
        score = 1.0
    else:
        score = (
            _SIGNAL_TYPE_COMPATIBILITY.get(
                frozenset(
                    {
                        source_type,
                        target_type,
                    }
                ),
                0.45,
            )
        )

    source_result = (
        _diagnostic_result(source)
    )

    target_result = (
        _diagnostic_result(target)
    )

    if (
        source_result
        and target_result
        and source_result
        != target_result
    ):
        if {
            source_result,
            target_result,
        } == {
            "positive",
            "negative",
        }:
            score = min(
                score,
                0.25,
            )

    if (
        source_type
        == "transmission_observation"
        and target_type
        == "transmission_observation"
    ):
        source_transmission = (
            source.get("transmission")
        )
        target_transmission = (
            target.get("transmission")
        )

        if (
            isinstance(
                source_transmission,
                Mapping,
            )
            and isinstance(
                target_transmission,
                Mapping,
            )
        ):
            for field in (
                "human_to_human",
                "animal_to_human",
                "vector_borne",
            ):
                left = _norm_value(
                    source_transmission.get(
                        field
                    )
                )
                right = _norm_value(
                    target_transmission.get(
                        field
                    )
                )

                if (
                    left
                    and right
                    and left != "unknown"
                    and right != "unknown"
                    and left != right
                ):
                    if (
                        "refuted"
                        in {
                            left,
                            right,
                        }
                    ):
                        score = min(
                            score,
                            0.10,
                        )
                    else:
                        score = min(
                            score,
                            0.75,
                        )

    return score


def _domain_similarity(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> float | None:
    source_domains = source.get(
        "domains"
    )

    target_domains = target.get(
        "domains"
    )

    if (
        not isinstance(source_domains, list)
        or not isinstance(target_domains, list)
    ):
        return None

    source_set = {
        _norm_value(value)
        for value in source_domains
        if _norm_value(value)
    }

    target_set = {
        _norm_value(value)
        for value in target_domains
        if _norm_value(value)
    }

    if (
        not source_set
        or not target_set
    ):
        return None

    return (
        len(
            source_set
            & target_set
        )
        /
        len(
            source_set
            | target_set
        )
    )


def _shared_context_score(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> float | None:
    parts: list[float] = []

    domain_score = (
        _domain_similarity(
            source,
            target,
        )
    )

    if domain_score is not None:
        parts.append(
            domain_score
        )

    location_score = (
        _best_location_similarity(
            _locations_for_roles(
                source,
                _CONTEXT_LOCATION_ROLES,
            ),
            _locations_for_roles(
                target,
                _CONTEXT_LOCATION_ROLES,
            ),
        )
    )

    if location_score is not None:
        parts.append(
            location_score
        )

    if not parts:
        return None

    return sum(parts) / len(parts)


def _validated_component_weights(
    weights: Mapping[
        str,
        Any,
    ] | None,
) -> dict[str, float]:
    selected = dict(
        EVENT_MATCHING_COMPONENT_WEIGHTS
        if weights is None
        else weights
    )

    if set(selected) != WEIGHT_KEYS:
        _error(
            "component scoring weights have unexpected keys."
        )

    normalized = {
        key: _probability(
            selected[key],
            f"weights.{key}",
        )
        for key in WEIGHT_KEYS
    }

    total = sum(
        normalized.values()
    )

    if not math.isclose(
        total,
        1.0,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        _error(
            "component scoring weights must sum to 1.0."
        )

    return normalized


def score_signal_pair_components(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
    eligibility: Mapping[str, Any],
    weights: Mapping[
        str,
        Any,
    ] | None = None,
) -> dict[str, Any]:
    """Score the six observable compatibility dimensions.

    Missing dimensions are represented as None and do not
    reduce the normalized compatibility score. Their absence
    is instead captured by information_coverage.

    Hard conflicts and final matching decisions are intentionally
    outside this function in v0.4.8.
    """

    selected_weights = (
        _validated_component_weights(
            weights
        )
    )

    source_eligible = (
        signal_matching_eligible(
            source,
            eligibility,
        )
    )

    target_eligible = (
        signal_matching_eligible(
            target,
            eligibility,
        )
    )

    empty_components = {
        key: None
        for key in WEIGHT_KEYS
    }

    if not (
        source_eligible
        and target_eligible
    ):
        return {
            "source_signal_id": source.get(
                "local_signal_id"
            ),
            "target_signal_id": target.get(
                "local_signal_id"
            ),
            "eligible": False,
            "source_eligible": source_eligible,
            "target_eligible": target_eligible,
            "score": None,
            "information_coverage": 0.0,
            "component_scores": empty_components,
        }

    component_scores = {
        "etiology": _etiology_score(
            source,
            target,
        ),
        "geography": _geography_score(
            source,
            target,
        ),
        "temporality": _temporality_score(
            source,
            target,
        ),
        "host": _host_score(
            source,
            target,
        ),
        "epidemiology": _epidemiology_score(
            source,
            target,
        ),
        "shared_context": _shared_context_score(
            source,
            target,
        ),
    }

    observed_weight = sum(
        selected_weights[key]
        for key, value
        in component_scores.items()
        if value is not None
    )

    weighted_sum = sum(
        selected_weights[key]
        * value
        for key, value
        in component_scores.items()
        if value is not None
    )

    score = (
        weighted_sum
        / observed_weight
        if observed_weight > 0
        else None
    )

    rounded_components = {
        key: (
            round(value, 6)
            if value is not None
            else None
        )
        for key, value
        in component_scores.items()
    }

    return {
        "source_signal_id": source.get(
            "local_signal_id"
        ),
        "target_signal_id": target.get(
            "local_signal_id"
        ),
        "eligible": True,
        "source_eligible": True,
        "target_eligible": True,
        "score": (
            round(score, 6)
            if score is not None
            else None
        ),
        "information_coverage": round(
            observed_weight,
            6,
        ),
        "component_scores": rounded_components,
    }

_NON_RELATION_TEXT_MARKERS = (
    "sin relaciÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â³n",
    "sin relacion",
    "no relacionado",
    "no relacionada",
    "no relacionados",
    "no relacionadas",
    "diferente de",
    "descartar",
    "descartÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â³",
    "descarto",
    "not related",
    "unrelated",
    "different from",
)


def _signal_text(
    signal: Mapping[str, Any],
) -> str:
    parts: list[str] = []

    summary = signal.get(
        "signal_summary"
    )

    if isinstance(summary, str):
        parts.append(summary)

    evidence = signal.get(
        "evidence"
    )

    if isinstance(evidence, list):
        for item in evidence:
            if not isinstance(
                item,
                Mapping,
            ):
                continue

            value = item.get("text")

            if isinstance(value, str):
                parts.append(value)

    return " ".join(
        parts
    ).casefold()


def _genomic_sequence_reported(
    signal: Mapping[str, Any],
) -> bool:
    genomics = signal.get(
        "genomics"
    )

    return bool(
        isinstance(genomics, Mapping)
        and genomics.get(
            "sequence_reported"
        )
        is True
    )


def _has_refuted_transmission(
    signal: Mapping[str, Any],
) -> bool:
    transmission = signal.get(
        "transmission"
    )

    if not isinstance(
        transmission,
        Mapping,
    ):
        return False

    return any(
        _norm_value(
            transmission.get(field)
        )
        == "refuted"
        for field in (
            "human_to_human",
            "animal_to_human",
            "vector_borne",
        )
    )


def _is_negative_refutation(
    signal: Mapping[str, Any],
) -> bool:
    return (
        _norm_value(
            signal.get("signal_role")
        )
        == "negative_evidence"
        and (
            _norm_value(
                signal.get(
                    "verification_status"
                )
            )
            == "refuted"
            or _has_refuted_transmission(
                signal
            )
        )
    )


def _contains_explicit_non_relation(
    signal: Mapping[str, Any],
) -> bool:
    text = _signal_text(
        signal
    )

    return any(
        marker in text
        for marker
        in _NON_RELATION_TEXT_MARKERS
    )


def detect_hard_conflict(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Detect explicit evidence that must override similarity.

    Detection is symmetric. The strongest supported reason wins.
    """

    pairs = (
        (source, target),
        (target, source),
    )

    if policy.get(
        "explicit_genomic_incompatibility"
    ) is True:
        for negative, counterpart in pairs:
            if (
                _is_negative_refutation(
                    negative
                )
                and _genomic_sequence_reported(
                    negative
                )
                and _genomic_sequence_reported(
                    counterpart
                )
                and (
                    _has_refuted_transmission(
                        negative
                    )
                    or _contains_explicit_non_relation(
                        negative
                    )
                )
            ):
                return {
                    "hard_conflict": True,
                    "reason": (
                        "explicit_genomic_incompatibility"
                    ),
                }

    if policy.get(
        "explicit_official_non_relation"
    ) is True:
        for negative, _counterpart in pairs:
            if (
                _is_negative_refutation(
                    negative
                )
                and _contains_explicit_non_relation(
                    negative
                )
            ):
                return {
                    "hard_conflict": True,
                    "reason": (
                        "explicit_official_non_relation"
                    ),
                }

    if policy.get(
        "explicit_source_refutation"
    ) is True:
        for negative, _counterpart in pairs:
            if (
                _is_negative_refutation(
                    negative
                )
                and _has_refuted_transmission(
                    negative
                )
            ):
                return {
                    "hard_conflict": True,
                    "reason": (
                        "explicit_source_refutation"
                    ),
                }

    return {
        "hard_conflict": False,
        "reason": None,
    }


def _known_transmission_values(
    signal: Mapping[str, Any],
) -> set[tuple[str, str]]:
    transmission = signal.get(
        "transmission"
    )

    if not isinstance(
        transmission,
        Mapping,
    ):
        return set()

    values: set[
        tuple[str, str]
    ] = set()

    for field in (
        "human_to_human",
        "animal_to_human",
        "vector_borne",
    ):
        value = _norm_value(
            transmission.get(field)
        )

        if (
            value
            and value != "unknown"
        ):
            values.add(
                (field, value)
            )

    return values


def _is_transmission_refinement(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> bool:
    if (
        _norm_value(
            source.get("signal_type")
        )
        != "transmission_observation"
        or _norm_value(
            target.get("signal_type")
        )
        != "transmission_observation"
    ):
        return False

    source_known = (
        _known_transmission_values(
            source
        )
    )

    target_known = (
        _known_transmission_values(
            target
        )
    )

    return (
        bool(source_known)
        != bool(target_known)
    )


def classify_pair_relation(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
    component_result: Mapping[str, Any],
    hard_conflict: Mapping[str, Any],
) -> str:
    """Classify the epidemiological relationship deterministically."""

    if hard_conflict.get(
        "hard_conflict"
    ):
        return "contradicts"

    source_type = _norm_value(
        source.get("signal_type")
    )

    target_type = _norm_value(
        target.get("signal_type")
    )

    if (
        source_type
        == "genomic_observation"
        and target_type
        == "genomic_observation"
    ):
        return "duplicates"

    if (
        source_type == target_type
        == "outbreak"
    ):
        return "refines"

    if (
        source_type == target_type
        == "transmission_observation"
    ):
        if _is_transmission_refinement(
            source,
            target,
        ):
            return "refines"

        return "supports"

    if (
        source_type == target_type
        == "travel_or_mobility"
    ):
        return "possibly_related"

    type_pair = frozenset(
        {
            source_type,
            target_type,
        }
    )

    if type_pair in {
        frozenset(
            {
                "case_report",
                "outbreak",
            }
        ),
        frozenset(
            {
                "cluster",
                "outbreak",
            }
        ),
        frozenset(
            {
                "laboratory_investigation",
                "laboratory_result",
            }
        ),
    }:
        return "refines"

    if type_pair == frozenset(
        {
            "travel_or_mobility",
            "intervention",
        }
    ):
        return "supports"

    if type_pair in {
        frozenset(
            {
                "intervention",
                "laboratory_result",
            }
        ),
        frozenset(
            {
                "intervention",
                "genomic_observation",
            }
        ),
        frozenset(
            {
                "intervention",
                "wildlife_event",
            }
        ),
    }:
        return "possibly_related"

    score = component_result.get(
        "score"
    )

    if (
        isinstance(score, (int, float))
        and score >= 0.60
    ):
        return "supports"

    return "unknown"


def _pair_decision(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
    relation: str,
    component_result: Mapping[str, Any],
    hard_conflict: Mapping[str, Any],
    thresholds: Mapping[str, Any],
) -> tuple[str, bool]:
    """Return decision and whether event fusion is allowed."""

    if hard_conflict.get(
        "hard_conflict"
    ):
        return (
            "rejected",
            False,
        )

    score = component_result.get(
        "score"
    )

    auto_link_min = float(
        thresholds[
            "auto_link_min"
        ]
    )

    if relation == "duplicates":
        if (
            isinstance(
                score,
                (int, float),
            )
            and score
            >= auto_link_min
        ):
            return (
                "auto_linked",
                True,
            )

        return (
            "review_required",
            True,
        )

    if relation == "refines":
        # A transition from unknown to a specific
        # transmission hypothesis is epistemically
        # important and remains human-reviewed.
        if _is_transmission_refinement(
            source,
            target,
        ):
            return (
                "review_required",
                True,
            )

        if (
            isinstance(
                score,
                (int, float),
            )
            and score
            >= auto_link_min
        ):
            return (
                "auto_linked",
                True,
            )

        return (
            "review_required",
            True,
        )

    if relation in {
        "supports",
        "possibly_related",
    }:
        return (
            "review_required",
            False,
        )

    return (
        "rejected",
        False,
    )


def evaluate_signal_pair_v048(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluate one pair through the full deterministic v0.4.8 policy."""

    eligibility = _mapping(
        manifest.get("eligibility"),
        "eligibility",
    )

    scoring = _mapping(
        manifest.get("scoring"),
        "scoring",
    )

    component_result = (
        score_signal_pair_components(
            source,
            target,
            eligibility,
            _mapping(
                scoring.get("weights"),
                "scoring.weights",
            ),
        )
    )

    if not component_result[
        "eligible"
    ]:
        return {
            **component_result,
            "gate": "ineligible",
            "relation": None,
            "hard_conflict": False,
            "hard_conflict_reason": None,
            "decision": None,
            "merge_allowed": False,
        }

    hard_conflict = (
        detect_hard_conflict(
            source,
            target,
            _mapping(
                manifest.get(
                    "hard_conflict_policy"
                ),
                "hard_conflict_policy",
            ),
        )
    )

    relation = classify_pair_relation(
        source,
        target,
        component_result,
        hard_conflict,
    )

    decision, merge_allowed = (
        _pair_decision(
            source,
            target,
            relation,
            component_result,
            hard_conflict,
            _mapping(
                scoring.get(
                    "thresholds"
                ),
                "scoring.thresholds",
            ),
        )
    )

    return {
        **component_result,
        "gate": "eligible",
        "relation": relation,
        "hard_conflict": hard_conflict[
            "hard_conflict"
        ],
        "hard_conflict_reason": hard_conflict[
            "reason"
        ],
        "decision": decision,
        "merge_allowed": merge_allowed,
    }

_ORDER_INVARIANT_FIELDS = (
    "eligible",
    "score",
    "information_coverage",
    "component_scores",
    "gate",
    "relation",
    "hard_conflict",
    "hard_conflict_reason",
    "decision",
    "merge_allowed",
)


def _ratio(
    numerator: int,
    denominator: int,
    *,
    empty_value: float = 1.0,
) -> float:
    if denominator == 0:
        return empty_value

    return round(
        numerator / denominator,
        6,
    )

def _pair_order_invariant(
    forward: Mapping[str, Any],
    reverse: Mapping[str, Any],
) -> bool:
    symmetric_fields_match = all(
        forward.get(field)
        == reverse.get(field)
        for field
        in _ORDER_INVARIANT_FIELDS
    )

    endpoint_eligibility_swaps_correctly = (
        forward.get("source_eligible")
        == reverse.get("target_eligible")
        and forward.get("target_eligible")
        == reverse.get("source_eligible")
    )

    return (
        symmetric_fields_match
        and endpoint_eligibility_swaps_correctly
    )

def evaluate_event_matching_benchmark(
    benchmark_or_path: EventMatchingBenchmark | str | Path,
) -> dict[str, Any]:
    """Evaluate all adjudicated v0.4.8 pairs and apply the release gate."""

    if isinstance(
        benchmark_or_path,
        EventMatchingBenchmark,
    ):
        benchmark = benchmark_or_path
    else:
        benchmark = (
            load_event_matching_benchmark(
                benchmark_or_path
            )
        )

    manifest = benchmark.manifest
    thresholds = _mapping(
        manifest.get(
            "release_thresholds"
        ),
        "release_thresholds",
    )

    pair_results: list[
        dict[str, Any]
    ] = []

    expected_ineligible = 0
    correct_ineligible = 0

    expected_hard_conflicts = 0
    detected_hard_conflicts = 0
    expected_hard_conflict_reasons = 0
    correct_hard_conflict_reasons = 0
    hard_conflict_false_auto_links = 0

    predicted_auto_links = 0
    correct_auto_links = 0

    decision_total = 0
    decision_correct = 0

    relation_total = 0
    relation_correct = 0

    invariant_pairs = 0

    for pair in benchmark.adjudicated_pairs:
        source = benchmark.signal_index[
            pair["source_signal_id"]
        ]

        target = benchmark.signal_index[
            pair["target_signal_id"]
        ]

        result = evaluate_signal_pair_v048(
            source,
            target,
            manifest,
        )

        reverse = evaluate_signal_pair_v048(
            target,
            source,
            manifest,
        )

        order_invariant = (
            _pair_order_invariant(
                result,
                reverse,
            )
        )

        if order_invariant:
            invariant_pairs += 1

        expected_gate = pair[
            "expected_gate"
        ]

        expected_relation = pair[
            "expected_relation"
        ]

        expected_decision = pair[
            "expected_decision"
        ]

        expected_hard_conflict = pair[
            "expected_hard_conflict"
        ]

        if expected_gate == "ineligible":
            expected_ineligible += 1

            if result["gate"] == "ineligible":
                correct_ineligible += 1

        if expected_hard_conflict:
            expected_hard_conflicts += 1

            if result["hard_conflict"]:
                detected_hard_conflicts += 1

            expected_reason = pair.get(
                "expected_hard_conflict_reason"
            )

            if expected_reason is not None:
                expected_hard_conflict_reasons += 1

                if (
                    result["hard_conflict_reason"]
                    == expected_reason
                ):
                    correct_hard_conflict_reasons += 1

            if result["decision"] == "auto_linked":
                hard_conflict_false_auto_links += 1

        if result["decision"] == "auto_linked":
            predicted_auto_links += 1

            if expected_decision == "auto_linked":
                correct_auto_links += 1

        decision_total += 1

        if result["decision"] == expected_decision:
            decision_correct += 1

        if expected_gate == "eligible":
            relation_total += 1

            if result["relation"] == expected_relation:
                relation_correct += 1

        pair_results.append(
            {
                "pair_id": pair[
                    "pair_id"
                ],
                "family": pair.get(
                    "family"
                ),
                "source_signal_id": pair[
                    "source_signal_id"
                ],
                "target_signal_id": pair[
                    "target_signal_id"
                ],
                "expected": {
                    "gate": expected_gate,
                    "relation": expected_relation,
                    "decision": expected_decision,
                    "merge_allowed": pair[
                        "expected_merge_allowed"
                    ],
                    "hard_conflict": (
                        expected_hard_conflict
                    ),
                    "hard_conflict_reason": (
                        pair.get(
                            "expected_hard_conflict_reason"
                        )
                    ),
                },
                "actual": result,
                "order_invariant": (
                    order_invariant
                ),
            }
        )

    ineligible_gate_accuracy = _ratio(
        correct_ineligible,
        expected_ineligible,
    )

    hard_conflict_recall = _ratio(
        detected_hard_conflicts,
        expected_hard_conflicts,
    )

    hard_conflict_reason_accuracy = _ratio(
        correct_hard_conflict_reasons,
        expected_hard_conflict_reasons,
    )

    auto_link_precision = _ratio(
        correct_auto_links,
        predicted_auto_links,
    )

    pair_decision_accuracy = _ratio(
        decision_correct,
        decision_total,
    )

    relation_accuracy = _ratio(
        relation_correct,
        relation_total,
    )

    order_invariance = (
        invariant_pairs
        == len(
            benchmark.adjudicated_pairs
        )
    )

    metrics = {
        "ineligible_gate_accuracy": (
            ineligible_gate_accuracy
        ),
        "hard_conflict_recall": (
            hard_conflict_recall
        ),
        "hard_conflict_reason_accuracy": (
            hard_conflict_reason_accuracy
        ),
        "hard_conflict_false_auto_links": (
            hard_conflict_false_auto_links
        ),
        "auto_link_precision": (
            auto_link_precision
        ),
        "pair_decision_accuracy": (
            pair_decision_accuracy
        ),
        "relation_accuracy": (
            relation_accuracy
        ),
        "order_invariance": (
            order_invariance
        ),
    }

    metrics_pass = (
        ineligible_gate_accuracy
        >= float(
            thresholds[
                "ineligible_gate_accuracy"
            ]
        )
        and hard_conflict_recall
        >= float(
            thresholds[
                "hard_conflict_recall"
            ]
        )
        and hard_conflict_false_auto_links
        <= int(
            thresholds[
                "hard_conflict_false_auto_links"
            ]
        )
        and auto_link_precision
        >= float(
            thresholds[
                "auto_link_precision"
            ]
        )
        and pair_decision_accuracy
        >= float(
            thresholds[
                "pair_decision_accuracy"
            ]
        )
        and relation_accuracy
        >= float(
            thresholds[
                "relation_accuracy"
            ]
        )
        and (
            thresholds[
                "order_invariance"
            ]
            is False
            or order_invariance
        )
    )

    return {
        "evaluation_schema_version": "0.1",
        "benchmark_kind": "event_matching",
        "benchmark_version": manifest[
            "benchmark_version"
        ],
        "case_code": manifest[
            "case_code"
        ],
        "evaluated_pairs": len(
            benchmark.adjudicated_pairs
        ),
        "eligible_pairs": relation_total,
        "ineligible_pairs": (
            expected_ineligible
        ),
        "expected_hard_conflicts": (
            expected_hard_conflicts
        ),
        "predicted_auto_links": (
            predicted_auto_links
        ),
        "aggregate": metrics,
        "release_gate": {
            "metrics_pass": metrics_pass,
            "event_matcher_validated": (
                bool(metrics_pass)
            ),
            "thresholds": dict(
                thresholds
            ),
        },
        "pairs": pair_results,
    }
