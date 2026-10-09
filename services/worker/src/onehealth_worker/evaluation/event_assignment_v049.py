from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class EventAssignmentPlan:
    action: str
    reason: str
    event_id: str | None
    signal_ids: tuple[str, ...]
    write_allowed: bool
    requires_review: bool

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["signal_ids"] = list(
            self.signal_ids
        )
        return payload


def _normalize_event_ids(
    values: Iterable[str] | None,
) -> tuple[str, ...]:
    if values is None:
        return ()

    normalized = {
        str(value)
        for value in values
        if value is not None
    }

    return tuple(
        sorted(normalized)
    )


def plan_event_assignment(
    *,
    source_signal_id: str,
    target_signal_id: str,
    matcher_result: Mapping[str, Any],
    source_event_ids: Iterable[str] | None = None,
    target_event_ids: Iterable[str] | None = None,
) -> EventAssignmentPlan:
    """Plan event membership without performing database writes.

    Automatic event mutation is permitted only when the deterministic
    matcher explicitly returned auto_linked + merge_allowed=true.

    Existing distinct events are never merged automatically.
    """

    source_signal_id = str(
        source_signal_id
    )
    target_signal_id = str(
        target_signal_id
    )

    if (
        source_signal_id
        == target_signal_id
    ):
        raise ValueError(
            "Una señal no puede planificarse "
            "contra sí misma."
        )

    source_events = (
        _normalize_event_ids(
            source_event_ids
        )
    )
    target_events = (
        _normalize_event_ids(
            target_event_ids
        )
    )

    gate = matcher_result.get(
        "gate"
    )
    relation = matcher_result.get(
        "relation"
    )
    decision = matcher_result.get(
        "decision"
    )
    merge_allowed = (
        matcher_result.get(
            "merge_allowed"
        )
        is True
    )
    hard_conflict = bool(
        matcher_result.get(
            "hard_conflict"
        )
    )

    pair = tuple(
        sorted(
            (
                source_signal_id,
                target_signal_id,
            )
        )
    )

    if gate != "eligible":
        return EventAssignmentPlan(
            action="no_event_change",
            reason="matcher_pair_ineligible",
            event_id=None,
            signal_ids=pair,
            write_allowed=False,
            requires_review=False,
        )

    if hard_conflict:
        return EventAssignmentPlan(
            action="no_event_change",
            reason="hard_conflict",
            event_id=None,
            signal_ids=pair,
            write_allowed=False,
            requires_review=False,
        )

    if decision != "auto_linked":
        return EventAssignmentPlan(
            action="no_event_change",
            reason=(
                "matcher_requires_review"
                if decision
                == "review_required"
                else "matcher_rejected"
            ),
            event_id=None,
            signal_ids=pair,
            write_allowed=False,
            requires_review=(
                decision
                == "review_required"
            ),
        )

    if not merge_allowed:
        raise ValueError(
            "Contrato inválido: auto_linked "
            "requiere merge_allowed=true."
        )

    if relation not in {
        "duplicates",
        "refines",
    }:
        raise ValueError(
            "Contrato inválido: una relación "
            f"{relation!r} no puede producir "
            "auto_linked en v0.4.9."
        )

    # Defensive rule: ambiguous existing membership is never mutated
    # automatically.
    if (
        len(source_events) > 1
        or len(target_events) > 1
    ):
        return EventAssignmentPlan(
            action="manual_review",
            reason=(
                "signal_has_multiple_existing_events"
            ),
            event_id=None,
            signal_ids=pair,
            write_allowed=False,
            requires_review=True,
        )

    source_event = (
        source_events[0]
        if source_events
        else None
    )
    target_event = (
        target_events[0]
        if target_events
        else None
    )

    if (
        source_event is not None
        and target_event is not None
    ):
        if source_event == target_event:
            return EventAssignmentPlan(
                action="already_same_event",
                reason=(
                    "both_signals_already_linked"
                ),
                event_id=source_event,
                signal_ids=(),
                write_allowed=False,
                requires_review=False,
            )

        return EventAssignmentPlan(
            action="manual_review",
            reason=(
                "signals_belong_to_distinct_events"
            ),
            event_id=None,
            signal_ids=pair,
            write_allowed=False,
            requires_review=True,
        )

    if source_event is not None:
        return EventAssignmentPlan(
            action="attach_target_to_event",
            reason=(
                "source_already_has_event"
            ),
            event_id=source_event,
            signal_ids=(
                target_signal_id,
            ),
            write_allowed=True,
            requires_review=False,
        )

    if target_event is not None:
        return EventAssignmentPlan(
            action="attach_source_to_event",
            reason=(
                "target_already_has_event"
            ),
            event_id=target_event,
            signal_ids=(
                source_signal_id,
            ),
            write_allowed=True,
            requires_review=False,
        )

    return EventAssignmentPlan(
        action="create_event",
        reason=(
            "auto_linked_pair_without_event"
        ),
        event_id=None,
        signal_ids=pair,
        write_allowed=True,
        requires_review=False,
    )

OPEN_EVENT_LIFECYCLE_STATUSES = frozenset(
    {
        "active",
        "monitoring",
    }
)

TERMINAL_EVENT_LIFECYCLE_STATUSES = frozenset(
    {
        "resolved",
        "closed",
    }
)


def apply_event_lifecycle_guard(
    plan: EventAssignmentPlan,
    *,
    lifecycle_by_event_id: Mapping[str, str | None],
) -> EventAssignmentPlan:
    """Block automatic attachment to non-open events.

    Automatic writes to an existing event are allowed only while the
    event is active or monitoring. Resolved, closed, or unknown lifecycle
    states require human review.

    Plans that do not mutate an existing event are returned unchanged.
    """

    if (
        not plan.write_allowed
        or plan.event_id is None
    ):
        return plan

    event_id = str(
        plan.event_id
    )

    lifecycle_status = (
        lifecycle_by_event_id.get(
            event_id
        )
    )

    if (
        lifecycle_status
        in OPEN_EVENT_LIFECYCLE_STATUSES
    ):
        return plan

    if (
        lifecycle_status
        in TERMINAL_EVENT_LIFECYCLE_STATUSES
    ):
        reason = (
            "target_event_"
            f"{lifecycle_status}"
        )
    else:
        reason = (
            "target_event_lifecycle_unknown"
        )

    return EventAssignmentPlan(
        action="manual_review",
        reason=reason,
        event_id=event_id,
        signal_ids=plan.signal_ids,
        write_allowed=False,
        requires_review=True,
    )

