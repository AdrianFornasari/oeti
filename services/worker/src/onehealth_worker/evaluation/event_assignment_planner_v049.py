from __future__ import annotations

from typing import Any

from .event_assignment_v049 import (
    apply_event_lifecycle_guard,
    plan_event_assignment,
)
from .event_matching_repository_v049 import (
    EventMatchingRepository,
)


class EventAssignmentPlanner:
    """Build event-assignment plans from persisted matcher relations.

    This component is read-only. It never creates or modifies events.
    """

    def __init__(
        self,
        repository: EventMatchingRepository,
    ):
        self.repository = repository

    def plan_persisted_anchor(
        self,
        anchor_signal_id: str,
    ) -> dict[str, Any]:
        relations = (
            self.repository
            .load_persisted_matcher_relations_for_signal(
                anchor_signal_id
            )
        )

        membership_cache: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        def memberships(
            signal_id: str,
        ) -> list[dict[str, Any]]:
            if (
                signal_id
                not in membership_cache
            ):
                membership_cache[
                    signal_id
                ] = (
                    self.repository
                    .load_event_memberships_for_signal(
                        signal_id
                    )
                )

            return membership_cache[
                signal_id
            ]

        plans: list[
            dict[str, Any]
        ] = []

        action_counts = {
            "no_event_change": 0,
            "create_event": 0,
            "attach_target_to_event": 0,
            "attach_source_to_event": 0,
            "already_same_event": 0,
            "manual_review": 0,
        }

        write_allowed = 0
        requires_review = 0

        for relation in relations:
            source_signal_id = relation[
                "source_signal_id"
            ]

            target_signal_id = relation[
                "target_signal_id"
            ]

            source_memberships = memberships(
                source_signal_id
            )

            target_memberships = memberships(
                target_signal_id
            )

            assignment = (
                plan_event_assignment(
                    source_signal_id=(
                        source_signal_id
                    ),
                    target_signal_id=(
                        target_signal_id
                    ),
                    matcher_result=(
                        relation[
                            "matcher_result"
                        ]
                    ),
                    source_event_ids=[
                        item["event_id"]
                        for item
                        in source_memberships
                    ],
                    target_event_ids=[
                        item["event_id"]
                        for item
                        in target_memberships
                    ],
                )
            )

            lifecycle_by_event_id: dict[
                str,
                str | None,
            ] = {}

            for membership in (
                *source_memberships,
                *target_memberships,
            ):
                event_id = str(
                    membership[
                        "event_id"
                    ]
                )

                lifecycle_status = (
                    membership.get(
                        "lifecycle_status"
                    )
                )

                if (
                    event_id
                    in lifecycle_by_event_id
                    and lifecycle_by_event_id[
                        event_id
                    ]
                    != lifecycle_status
                ):
                    raise ValueError(
                        "Conflicting lifecycle "
                        "status for event "
                        f"{event_id}."
                    )

                lifecycle_by_event_id[
                    event_id
                ] = lifecycle_status

            assignment = (
                apply_event_lifecycle_guard(
                    assignment,
                    lifecycle_by_event_id=(
                        lifecycle_by_event_id
                    ),
                )
            )

            action_counts[
                assignment.action
            ] += 1

            if assignment.write_allowed:
                write_allowed += 1

            if assignment.requires_review:
                requires_review += 1

            plans.append(
                {
                    **relation,
                    "source_memberships": (
                        source_memberships
                    ),
                    "target_memberships": (
                        target_memberships
                    ),
                    "assignment_plan": (
                        assignment.to_dict()
                    ),
                }
            )

        return {
            "mode": "plan_only",
            "anchor_signal_id": (
                anchor_signal_id
            ),
            "persisted_relations": len(
                relations
            ),
            "signals_with_membership_lookup": (
                len(
                    membership_cache
                )
            ),
            "summary": {
                **action_counts,
                "write_allowed": (
                    write_allowed
                ),
                "requires_review": (
                    requires_review
                ),
            },
            "plans": plans,
        }
