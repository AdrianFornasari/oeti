from __future__ import annotations

from typing import Any

from .event_assignment_planner_v049 import (
    EventAssignmentPlanner,
)


_EXECUTABLE_ATTACHMENT_ACTIONS = {
    "attach_source_to_event",
    "attach_target_to_event",
}


class EventAssignmentExecutor:
    """Execute validated event-assignment plans.

    Existing-event attachments may be persisted atomically. Event creation
    remains deliberately deferred in v0.4.9.
    """

    def __init__(
        self,
        planner: EventAssignmentPlanner,
        repository: Any | None = None,
    ):
        self.planner = planner

        if repository is None:
            repository = getattr(
                planner,
                "repository",
                None,
            )

        self.repository = repository

    def evaluate_anchor(
        self,
        anchor_signal_id: str,
        *,
        persist: bool = False,
    ) -> dict[str, Any]:
        planner_report = (
            self.planner
            .plan_persisted_anchor(
                anchor_signal_id
            )
        )

        executable: list[
            dict[str, Any]
        ] = []

        blocked: list[
            dict[str, Any]
        ] = []

        deferred_create_event: list[
            dict[str, Any]
        ] = []

        for item in planner_report[
            "plans"
        ]:
            plan = item[
                "assignment_plan"
            ]

            action = plan[
                "action"
            ]

            if (
                action
                in _EXECUTABLE_ATTACHMENT_ACTIONS
                and plan[
                    "write_allowed"
                ]
                is True
            ):
                executable.append(
                    {
                        "signal_relation_id": (
                            item[
                                "signal_relation_id"
                            ]
                        ),
                        "source_signal_id": (
                            item[
                                "source_signal_id"
                            ]
                        ),
                        "target_signal_id": (
                            item[
                                "target_signal_id"
                            ]
                        ),
                        "assignment_plan": (
                            plan
                        ),
                    }
                )

                continue

            if (
                action == "create_event"
                and plan[
                    "write_allowed"
                ]
                is True
            ):
                deferred_create_event.append(
                    {
                        "signal_relation_id": (
                            item[
                                "signal_relation_id"
                            ]
                        ),
                        "source_signal_id": (
                            item[
                                "source_signal_id"
                            ]
                        ),
                        "target_signal_id": (
                            item[
                                "target_signal_id"
                            ]
                        ),
                        "assignment_plan": (
                            plan
                        ),
                    }
                )

                continue

            blocked.append(
                {
                    "signal_relation_id": (
                        item[
                            "signal_relation_id"
                        ]
                    ),
                    "action": action,
                    "reason": (
                        plan[
                            "reason"
                        ]
                    ),
                    "requires_review": (
                        plan[
                            "requires_review"
                        ]
                    ),
                }
            )

        persisted: list[
            dict[str, Any]
        ] = []

        if persist and executable:
            if self.repository is None:
                raise ValueError(
                    "Persistence requested but no "
                    "repository is available."
                )

            persisted = (
                self.repository
                .persist_event_signal_attachments_batch(
                    executable
                )
            )

            if len(persisted) != len(
                executable
            ):
                raise RuntimeError(
                    "Event-signal batch persistence "
                    "returned an unexpected row count."
                )

        inserted = sum(
            1
            for item in persisted
            if item.get("action")
            == "inserted"
        )

        updated = sum(
            1
            for item in persisted
            if item.get("action")
            == "updated"
        )

        return {
            "mode": (
                "persist"
                if persist
                else "dry_run"
            ),
            "anchor_signal_id": (
                anchor_signal_id
            ),
            "planner_summary": (
                planner_report[
                    "summary"
                ]
            ),
            "persisted_relations": (
                planner_report[
                    "persisted_relations"
                ]
            ),
            "executable_attachments": len(
                executable
            ),
            "deferred_create_events": len(
                deferred_create_event
            ),
            "blocked_or_noop": len(
                blocked
            ),
            "would_write_event_signals": len(
                executable
            ),
            "would_create_events": len(
                deferred_create_event
            ),
            "persistence": {
                "requested": persist,
                "requested_attachments": len(
                    executable
                ),
                "persisted_attachments": len(
                    persisted
                ),
                "inserted": inserted,
                "updated": updated,
                "deferred_create_events": len(
                    deferred_create_event
                ),
            },
            "executable": executable,
            "persisted": persisted,
            "deferred_create_event": (
                deferred_create_event
            ),
            "blocked": blocked,
        }
