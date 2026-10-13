"""Execute one explicitly selected, previously reviewed cohort proposal."""
from collections.abc import Mapping
from copy import deepcopy
from typing import Any
from uuid import UUID

from .event_matching_repository_v049 import EventMatchingRepository


def _identifiers(value: Any, *, minimum: int) -> set[UUID]:
    if not isinstance(value, list) or len(value) < minimum:
        raise ValueError("Cohort identifiers must be a nonempty list of UUID strings.")
    try:
        if any(not isinstance(item, str) for item in value):
            raise ValueError
        identifiers = {UUID(item) for item in value}
    except (ValueError, AttributeError):
        raise ValueError("Invalid cohort UUID.") from None
    if len(identifiers) != len(value):
        raise ValueError("Duplicate cohort identifiers.")
    return identifiers


class EventCreationExecutor:
    """Delegate revalidation and atomic persistence; never enable writes."""

    def __init__(self, repository: EventMatchingRepository):
        self.repository = repository

    def execute_planned_cohort(
        self, *, report: Mapping[str, Any], expected_event_code: str,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        if not isinstance(dry_run, bool):
            raise ValueError("dry_run must be a boolean.")
        if not isinstance(expected_event_code, str) or not expected_event_code.strip():
            raise ValueError("An expected event code is required.")
        if not isinstance(report, Mapping) or report.get("mode") != "plan_only":
            raise ValueError("Expected a plan_only cohort report.")
        cohorts = report.get("cohorts")
        if not isinstance(cohorts, list) or any(not isinstance(item, Mapping) for item in cohorts):
            raise ValueError("Invalid cohort entries.")
        selected = [item for item in cohorts if isinstance(item.get("event_seed"), Mapping)
                    and item["event_seed"].get("event_code") == expected_event_code]
        if len(selected) != 1:
            raise ValueError("Expected exactly one cohort for the selected event code.")
        item = selected[0]
        validation = item.get("validation")
        if (not isinstance(validation, Mapping) or validation.get("dry_run") is not True
                or validation.get("status") not in {"ready_to_create", "already_exists"}):
            raise ValueError("Selected cohort must have a successful dry-run proposal.")
        cohort = item.get("cohort")
        if not isinstance(cohort, Mapping):
            raise ValueError("Selected cohort metadata is missing.")
        seed = item["event_seed"]
        for seed_key, cohort_key, minimum in (
            ("source_signal_ids", "signal_ids", 2),
            ("source_relation_ids", "signal_relation_ids", 1),
        ):
            if _identifiers(seed.get(seed_key), minimum=minimum) != _identifiers(cohort.get(cohort_key), minimum=minimum):
                raise ValueError("Seed identifiers differ from the reviewed cohort.")
        result = self.repository.persist_event_creation_cohort(
            event_seed=deepcopy(dict(seed)), dry_run=dry_run,
        )
        expected_statuses = {"ready_to_create", "already_exists", "blocked"} if dry_run else {"created", "already_exists", "blocked"}
        if not isinstance(result, Mapping) or result.get("status") not in expected_statuses:
            raise RuntimeError("Unexpected cohort repository status.")
        return result
