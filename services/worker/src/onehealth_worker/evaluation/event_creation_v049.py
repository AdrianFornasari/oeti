from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from .event_matching_repository_v049 import (
    canonical_signal_pair,
)


def _normalized_text(
    value: Any,
) -> str | None:
    if not isinstance(
        value,
        str,
    ):
        return None

    value = value.strip()

    return value or None


def _normalized_string_list(
    value: Any,
) -> tuple[str, ...]:
    if not isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):
        return ()

    normalized = {
        str(item).strip()
        for item in value
        if item is not None
        and str(item).strip()
    }

    return tuple(
        sorted(normalized)
    )


def _minimum_date(
    *values: Any,
) -> str | None:
    parsed: list[
        date
    ] = []

    for value in values:
        if value is None:
            continue

        if isinstance(
            value,
            datetime,
        ):
            parsed.append(
                value.date()
            )
            continue

        if isinstance(
            value,
            date,
        ):
            parsed.append(
                value
            )
            continue

        if isinstance(
            value,
            str,
        ):
            try:
                parsed.append(
                    date.fromisoformat(
                        value[:10]
                    )
                )
            except ValueError:
                continue

    if not parsed:
        return None

    return min(
        parsed
    ).isoformat()


def _minimum_datetime(
    *values: Any,
) -> str | None:
    parsed: list[
        datetime
    ] = []

    for value in values:
        if value is None:
            continue

        if isinstance(
            value,
            datetime,
        ):
            parsed.append(
                value
            )
            continue

        if isinstance(
            value,
            str,
        ):
            candidate = (
                value.replace(
                    "Z",
                    "+00:00",
                )
            )

            try:
                parsed.append(
                    datetime.fromisoformat(
                        candidate
                    )
                )
            except ValueError:
                continue

    if not parsed:
        return None

    result = min(
        parsed
    )

    return result.isoformat()


def _compatible_catalog_id(
    source_value: Any,
    target_value: Any,
    *,
    field: str,
) -> str | None:
    source = (
        str(source_value)
        if source_value
        else None
    )

    target = (
        str(target_value)
        if target_value
        else None
    )

    if (
        source is not None
        and target is not None
        and source != target
    ):
        raise ValueError(
            "Conflicting catalog IDs prevent "
            "automatic event creation: "
            f"{field}."
        )

    return (
        source
        or target
    )


def _shared_label(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> str | None:
    source_disease = (
        _normalized_text(
            source.get(
                "disease_canonical_name"
            )
        )
    )

    target_disease = (
        _normalized_text(
            target.get(
                "disease_canonical_name"
            )
        )
    )

    if (
        source_disease
        and target_disease
        and source_disease.casefold()
        == target_disease.casefold()
    ):
        return source_disease

    source_pathogen = (
        _normalized_text(
            source.get(
                "pathogen_canonical_name"
            )
        )
    )

    target_pathogen = (
        _normalized_text(
            target.get(
                "pathogen_canonical_name"
            )
        )
    )

    if (
        source_pathogen
        and target_pathogen
        and source_pathogen.casefold()
        == target_pathogen.casefold()
    ):
        return source_pathogen

    # If only one endpoint has a normalized identity, retain it.
    disease_candidates = {
        value
        for value in (
            source_disease,
            target_disease,
        )
        if value
    }

    if len(
        disease_candidates
    ) == 1:
        return next(
            iter(
                disease_candidates
            )
        )

    pathogen_candidates = {
        value
        for value in (
            source_pathogen,
            target_pathogen,
        )
        if value
    }

    if len(
        pathogen_candidates
    ) == 1:
        return next(
            iter(
                pathogen_candidates
            )
        )

    return None


def deterministic_event_code(
    source_signal_id: str,
    target_signal_id: str,
) -> str:
    source, target = (
        canonical_signal_pair(
            source_signal_id,
            target_signal_id,
        )
    )

    event_uuid = uuid5(
        NAMESPACE_URL,
        (
            "oeti:event:v0.4.9:"
            f"{source}:{target}"
        ),
    )

    return (
        "OETI-EVT-"
        + str(
            event_uuid
        )
    )


def build_event_creation_seed(
    *,
    source_signal: Mapping[str, Any],
    target_signal: Mapping[str, Any],
    matcher_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one deterministic initial event without database writes."""

    source_signal_id = str(
        source_signal[
            "signal_id"
        ]
    )

    target_signal_id = str(
        target_signal[
            "signal_id"
        ]
    )

    source_signal_id, target_signal_id = (
        canonical_signal_pair(
            source_signal_id,
            target_signal_id,
        )
    )

    if (
        matcher_result.get(
            "gate"
        )
        != "eligible"
    ):
        raise ValueError(
            "Event creation requires an "
            "eligible matcher result."
        )

    if matcher_result.get(
        "hard_conflict"
    ):
        raise ValueError(
            "Hard conflict blocks "
            "automatic event creation."
        )

    if (
        matcher_result.get(
            "decision"
        )
        != "auto_linked"
        or matcher_result.get(
            "merge_allowed"
        )
        is not True
    ):
        raise ValueError(
            "Event creation requires "
            "auto_linked + merge_allowed."
        )

    relation = matcher_result.get(
        "relation"
    )

    if relation not in {
        "duplicates",
        "refines",
    }:
        raise ValueError(
            "Automatic event creation only "
            "accepts duplicates or refines."
        )

    disease_id = (
        _compatible_catalog_id(
            source_signal.get(
                "disease_id"
            ),
            target_signal.get(
                "disease_id"
            ),
            field="disease_id",
        )
    )

    pathogen_id = (
        _compatible_catalog_id(
            source_signal.get(
                "pathogen_id"
            ),
            target_signal.get(
                "pathogen_id"
            ),
            field="pathogen_id",
        )
    )

    domains = tuple(
        sorted(
            set(
                _normalized_string_list(
                    source_signal.get(
                        "domains"
                    )
                )
            )
            | set(
                _normalized_string_list(
                    target_signal.get(
                        "domains"
                    )
                )
            )
        )
    )

    event_start_date = (
        _minimum_date(
            source_signal.get(
                "occurred_start"
            ),
            target_signal.get(
                "occurred_start"
            ),
        )
    )

    first_signal_at = (
        _minimum_datetime(
            source_signal.get(
                "observed_at"
            ),
            target_signal.get(
                "observed_at"
            ),
        )
    )

    label = _shared_label(
        source_signal,
        target_signal,
    )

    title = (
        f"{label} - emerging event"
        if label
        else "One Health emerging event"
    )

    event_code = (
        deterministic_event_code(
            source_signal_id,
            target_signal_id,
        )
    )

    return {
        "event_code": event_code,
        "title": title,
        "disease_id": disease_id,
        "pathogen_id": pathogen_id,
        "domains_present": list(
            domains
        ),
        "event_start_date": (
            event_start_date
        ),
        "first_signal_at": (
            first_signal_at
        ),
        "lifecycle_status": "active",
        "priority": "P3",
        "evidence_confidence": "low",
        "cross_sector_convergence": "none",
        "contradictions_present": False,
        "review_status": "pending",
        "source_signal_ids": [
            source_signal_id,
            target_signal_id,
        ],
        "source_relation": relation,
        "matcher_version": "0.4.8",
    }

def _compatible_cohort_catalog_id(
    signals: list[Mapping[str, Any]],
    *,
    field: str,
) -> str | None:
    values = {
        str(
            signal.get(field)
        ).strip()
        for signal in signals
        if signal.get(field)
        and str(
            signal.get(field)
        ).strip()
    }

    if len(values) > 1:
        raise ValueError(
            "Conflicting catalog IDs prevent "
            "automatic cohort event creation: "
            f"{field}."
        )

    if not values:
        return None

    return next(
        iter(values)
    )


def _cohort_label(
    signals: list[Mapping[str, Any]],
) -> str | None:
    def unique_label(
        field: str,
    ) -> str | None:
        grouped: dict[
            str,
            list[str],
        ] = {}

        for signal in signals:
            value = _normalized_text(
                signal.get(field)
            )

            if not value:
                continue

            grouped.setdefault(
                value.casefold(),
                [],
            ).append(value)

        if len(grouped) != 1:
            return None

        values = next(
            iter(
                grouped.values()
            )
        )

        return sorted(
            values,
            key=lambda item: (
                item.casefold(),
                item,
            ),
        )[0]

    disease = unique_label(
        "disease_canonical_name"
    )

    if disease:
        return disease

    return unique_label(
        "pathogen_canonical_name"
    )


def deterministic_cohort_event_code(
    signal_ids: list[str] | tuple[str, ...] | set[str],
) -> str:
    normalized_ids = tuple(
        sorted(
            {
                str(signal_id).strip()
                for signal_id in signal_ids
                if str(signal_id).strip()
            }
        )
    )

    if len(normalized_ids) < 2:
        raise ValueError(
            "Cohort event creation requires "
            "at least two distinct signals."
        )

    event_uuid = uuid5(
        NAMESPACE_URL,
        (
            "oeti:event:v0.4.9:cohort:"
            + ":".join(
                normalized_ids
            )
        ),
    )

    return (
        "OETI-EVT-"
        + str(event_uuid)
    )


def build_event_creation_cohort_seed(
    *,
    signals: list[Mapping[str, Any]],
    relations: list[Mapping[str, Any]],
    strong_event_context_anchors: (
        list[str]
        | tuple[str, ...]
        | set[str]
    ) = (),
) -> dict[str, Any]:
    """Build one deterministic event seed from an auto-linked cohort.

    This function is pure and performs no database writes.
    """

    if len(signals) < 2:
        raise ValueError(
            "Cohort event creation requires "
            "at least two signals."
        )

    signal_by_id: dict[
        str,
        Mapping[str, Any],
    ] = {}

    for signal in signals:
        signal_id = str(
            signal[
                "signal_id"
            ]
        )

        if signal_id in signal_by_id:
            raise ValueError(
                "Duplicate signal in event "
                f"creation cohort: {signal_id}."
            )

        signal_by_id[
            signal_id
        ] = signal

    if not relations:
        raise ValueError(
            "Cohort event creation requires "
            "at least one persisted relation."
        )

    relation_ids: set[str] = set()
    relation_types: set[str] = set()
    covered_signal_ids: set[str] = set()

    for relation_row in relations:
        relation_id = str(
            relation_row[
                "signal_relation_id"
            ]
        )

        if relation_id in relation_ids:
            raise ValueError(
                "Duplicate relation in event "
                f"creation cohort: {relation_id}."
            )

        relation_ids.add(
            relation_id
        )

        source_signal_id = str(
            relation_row[
                "source_signal_id"
            ]
        )

        target_signal_id = str(
            relation_row[
                "target_signal_id"
            ]
        )

        if (
            source_signal_id
            not in signal_by_id
            or target_signal_id
            not in signal_by_id
        ):
            raise ValueError(
                "Relation endpoint is outside "
                "the event creation cohort."
            )

        matcher_result = relation_row.get(
            "matcher_result"
        )

        if not isinstance(
            matcher_result,
            Mapping,
        ):
            raise ValueError(
                "Cohort relation lacks "
                "matcher_result."
            )

        if (
            matcher_result.get(
                "gate"
            )
            != "eligible"
        ):
            raise ValueError(
                "Event creation requires an "
                "eligible matcher result."
            )

        if matcher_result.get(
            "hard_conflict"
        ):
            raise ValueError(
                "Hard conflict blocks "
                "automatic event creation."
            )

        if (
            matcher_result.get(
                "decision"
            )
            != "auto_linked"
            or matcher_result.get(
                "merge_allowed"
            )
            is not True
        ):
            raise ValueError(
                "Event creation requires "
                "auto_linked + merge_allowed."
            )

        relation_type = matcher_result.get(
            "relation"
        )

        if relation_type not in {
            "duplicates",
            "refines",
        }:
            raise ValueError(
                "Automatic event creation only "
                "accepts duplicates or refines."
            )

        relation_types.add(
            str(relation_type)
        )

        covered_signal_ids.update(
            (
                source_signal_id,
                target_signal_id,
            )
        )

    if (
        covered_signal_ids
        != set(signal_by_id)
    ):
        raise ValueError(
            "Every signal in the cohort must "
            "participate in an approved "
            "auto-linked relation."
        )

    ordered_signals = [
        signal_by_id[
            signal_id
        ]
        for signal_id in sorted(
            signal_by_id
        )
    ]

    disease_id = (
        _compatible_cohort_catalog_id(
            ordered_signals,
            field="disease_id",
        )
    )

    pathogen_id = (
        _compatible_cohort_catalog_id(
            ordered_signals,
            field="pathogen_id",
        )
    )

    domains = tuple(
        sorted(
            {
                domain
                for signal in ordered_signals
                for domain in (
                    _normalized_string_list(
                        signal.get(
                            "domains"
                        )
                    )
                )
            }
        )
    )

    event_start_date = _minimum_date(
        *[
            signal.get(
                "occurred_start"
            )
            for signal in ordered_signals
        ]
    )

    first_signal_at = _minimum_datetime(
        *[
            signal.get(
                "observed_at"
            )
            for signal in ordered_signals
        ]
    )

    label = _cohort_label(
        ordered_signals
    )

    title = (
        f"{label} - emerging event"
        if label
        else "One Health emerging event"
    )

    signal_ids = sorted(
        signal_by_id
    )

    event_code = (
        deterministic_cohort_event_code(
            signal_ids
        )
    )

    normalized_anchors = list(
        _normalized_string_list(
            strong_event_context_anchors
        )
    )

    ordered_relation_types = sorted(
        relation_types
    )

    return {
        "event_code": event_code,
        "title": title,
        "disease_id": disease_id,
        "pathogen_id": pathogen_id,
        "domains_present": list(
            domains
        ),
        "event_start_date": (
            event_start_date
        ),
        "first_signal_at": (
            first_signal_at
        ),
        "lifecycle_status": "active",
        "priority": "P3",
        "evidence_confidence": "low",
        "cross_sector_convergence": "none",
        "contradictions_present": False,
        "review_status": "pending",
        "source_signal_ids": (
            signal_ids
        ),
        "source_relation_ids": sorted(
            relation_ids
        ),
        "source_relation": (
            ordered_relation_types[0]
            if len(
                ordered_relation_types
            )
            == 1
            else None
        ),
        "source_relations": (
            ordered_relation_types
        ),
        "strong_event_context_anchors": (
            normalized_anchors
        ),
        "matcher_version": "0.4.8",
        "event_creation_version": "0.4.9",
    }

