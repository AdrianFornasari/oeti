from __future__ import annotations

from typing import Any

from .event_creation_v049 import (
    build_event_creation_seed,
    build_event_creation_cohort_seed,
)
from .event_creation_cohort_v049 import build_event_creation_cohorts
from .event_matching_repository_v049 import (
    EventMatchingRepository,
)


class EventCreationPlanner:
    """Plan event creation from persisted pairs or cohorts without writing."""

    def __init__(
        self,
        repository: EventMatchingRepository,
    ):
        self.repository = repository

    def plan_cohorts(self, signal_relation_ids: list[str]) -> dict[str, Any]:
        """Group selected persisted relations and validate each cohort read-only.

        Readiness is advisory. Execution must revalidate in its transaction.
        This entry point never enables or invokes the write path.
        """
        relations = [
            self.repository.load_persisted_matcher_relation_by_id(identifier)
            for identifier in sorted(set(signal_relation_ids))
        ]
        eligible = []
        excluded_ids = []
        for row in relations:
            matcher = row["matcher_result"]
            if (
                matcher.get("gate") == "eligible"
                and matcher.get("decision") == "auto_linked"
                and matcher.get("merge_allowed") is True
                and matcher.get("hard_conflict") is False
                and matcher.get("relation") in {"duplicates", "refines"}
            ):
                eligible.append(row)
            else:
                excluded_ids.append(row["signal_relation_id"])

        relation_by_id = {row["signal_relation_id"]: row for row in eligible}
        plans = []
        summary = {"ready_to_create": 0, "already_exists": 0, "blocked": 0}
        for cohort in build_event_creation_cohorts(eligible):
            seed = None
            try:
                signals = [
                    self.repository.load_event_creation_signal(identifier)
                    for identifier in cohort["signal_ids"]
                ]
                seed = build_event_creation_cohort_seed(
                    signals=signals,
                    relations=[relation_by_id[identifier] for identifier in cohort["signal_relation_ids"]],
                    strong_event_context_anchors=cohort["strong_event_context_anchors"],
                )
            except ValueError as exc:
                validation = {
                    "status": "blocked", "dry_run": True,
                    "reason": "invalid_cohort_seed", "detail": str(exc),
                }
            else:
                validation = self.repository.persist_event_creation_cohort(
                    event_seed=seed, dry_run=True,
                )
            if validation.get("status") not in summary:
                raise RuntimeError("Unexpected cohort dry-run status.")
            summary[validation["status"]] += 1
            plans.append({"cohort": cohort, "event_seed": seed, "validation": validation})
        return {
            "mode": "plan_only", "cohorts": plans, "summary": summary,
            "excluded_relation_ids": sorted(excluded_ids),
        }

    def plan_relation(
        self,
        signal_relation_id: str,
    ) -> dict[str, Any]:
        relation = (
            self.repository
            .load_persisted_matcher_relation_by_id(
                signal_relation_id
            )
        )

        matcher = relation[
            "matcher_result"
        ]

        if matcher.get(
            "gate"
        ) != "eligible":
            return self._blocked(
                relation,
                "matcher_pair_ineligible",
            )

        if matcher.get(
            "hard_conflict"
        ):
            return self._blocked(
                relation,
                "hard_conflict",
            )

        if (
            matcher.get(
                "decision"
            )
            != "auto_linked"
        ):
            reason = (
                "matcher_requires_review"
                if matcher.get(
                    "decision"
                )
                == "review_required"
                else "matcher_rejected"
            )

            return self._blocked(
                relation,
                reason,
            )

        if (
            matcher.get(
                "merge_allowed"
            )
            is not True
        ):
            return self._blocked(
                relation,
                "merge_not_allowed",
            )

        if matcher.get(
            "relation"
        ) not in {
            "duplicates",
            "refines",
        }:
            return self._blocked(
                relation,
                "relation_not_auto_creatable",
            )

        source_id = relation[
            "source_signal_id"
        ]

        target_id = relation[
            "target_signal_id"
        ]

        source_memberships = (
            self.repository
            .load_event_memberships_for_signal(
                source_id
            )
        )

        target_memberships = (
            self.repository
            .load_event_memberships_for_signal(
                target_id
            )
        )

        if (
            source_memberships
            or target_memberships
        ):
            return {
                **self._blocked(
                    relation,
                    "existing_event_membership",
                ),
                "source_memberships": (
                    source_memberships
                ),
                "target_memberships": (
                    target_memberships
                ),
            }

        source_signal = (
            self.repository
            .load_event_creation_signal(
                source_id
            )
        )

        target_signal = (
            self.repository
            .load_event_creation_signal(
                target_id
            )
        )

        seed = (
            build_event_creation_seed(
                source_signal=source_signal,
                target_signal=target_signal,
                matcher_result=matcher,
            )
        )

        return {
            "mode": "plan_only",
            "status": "ready",
            "reason": (
                "auto_linked_pair_without_event"
            ),
            "signal_relation_id": (
                relation[
                    "signal_relation_id"
                ]
            ),
            "source_signal_id": (
                source_id
            ),
            "target_signal_id": (
                target_id
            ),
            "matcher_version": (
                relation[
                    "matcher_version"
                ]
            ),
            "matcher_result": matcher,
            "source_memberships": [],
            "target_memberships": [],
            "event_seed": seed,
            "write_allowed": True,
        }

    @staticmethod
    def _blocked(
        relation: dict[str, Any],
        reason: str,
    ) -> dict[str, Any]:
        return {
            "mode": "plan_only",
            "status": "blocked",
            "reason": reason,
            "signal_relation_id": (
                relation[
                    "signal_relation_id"
                ]
            ),
            "source_signal_id": (
                relation[
                    "source_signal_id"
                ]
            ),
            "target_signal_id": (
                relation[
                    "target_signal_id"
                ]
            ),
            "matcher_version": (
                relation[
                    "matcher_version"
                ]
            ),
            "matcher_result": (
                relation[
                    "matcher_result"
                ]
            ),
            "event_seed": None,
            "write_allowed": False,
        }
