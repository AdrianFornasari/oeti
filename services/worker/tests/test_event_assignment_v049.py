import pytest

from onehealth_worker.evaluation.event_assignment_v049 import (
    plan_event_assignment,
)


SOURCE = (
    "11111111-1111-1111-1111-111111111111"
)

TARGET = (
    "22222222-2222-2222-2222-222222222222"
)

EVENT_A = (
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)

EVENT_B = (
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
)


def auto_result(
    **overrides,
):
    result = {
        "gate": "eligible",
        "relation": "refines",
        "decision": "auto_linked",
        "merge_allowed": True,
        "hard_conflict": False,
        "score": 0.95,
    }

    result.update(
        overrides
    )

    return result


def test_review_required_never_mutates_event_membership():
    plan = plan_event_assignment(
        source_signal_id=SOURCE,
        target_signal_id=TARGET,
        matcher_result=auto_result(
            relation="supports",
            decision="review_required",
            merge_allowed=False,
        ),
    )

    assert (
        plan.action
        == "no_event_change"
    )
    assert (
        plan.reason
        == "matcher_requires_review"
    )
    assert plan.write_allowed is False
    assert plan.requires_review is True


def test_hard_conflict_never_mutates_event_membership():
    plan = plan_event_assignment(
        source_signal_id=SOURCE,
        target_signal_id=TARGET,
        matcher_result=auto_result(
            relation="contradicts",
            decision="rejected",
            merge_allowed=False,
            hard_conflict=True,
        ),
    )

    assert (
        plan.action
        == "no_event_change"
    )
    assert (
        plan.reason
        == "hard_conflict"
    )
    assert plan.write_allowed is False


def test_auto_link_without_existing_event_creates_event_plan():
    plan = plan_event_assignment(
        source_signal_id=SOURCE,
        target_signal_id=TARGET,
        matcher_result=auto_result(),
    )

    assert (
        plan.action
        == "create_event"
    )
    assert plan.event_id is None
    assert (
        set(plan.signal_ids)
        == {
            SOURCE,
            TARGET,
        }
    )
    assert plan.write_allowed is True
    assert plan.requires_review is False


def test_auto_link_attaches_target_to_source_event():
    plan = plan_event_assignment(
        source_signal_id=SOURCE,
        target_signal_id=TARGET,
        matcher_result=auto_result(),
        source_event_ids=[
            EVENT_A,
        ],
    )

    assert (
        plan.action
        == "attach_target_to_event"
    )
    assert (
        plan.event_id
        == EVENT_A
    )
    assert plan.signal_ids == (
        TARGET,
    )
    assert plan.write_allowed is True


def test_auto_link_attaches_source_to_target_event():
    plan = plan_event_assignment(
        source_signal_id=SOURCE,
        target_signal_id=TARGET,
        matcher_result=auto_result(),
        target_event_ids=[
            EVENT_A,
        ],
    )

    assert (
        plan.action
        == "attach_source_to_event"
    )
    assert (
        plan.event_id
        == EVENT_A
    )
    assert plan.signal_ids == (
        SOURCE,
    )
    assert plan.write_allowed is True


def test_pair_already_in_same_event_is_noop():
    plan = plan_event_assignment(
        source_signal_id=SOURCE,
        target_signal_id=TARGET,
        matcher_result=auto_result(),
        source_event_ids=[
            EVENT_A,
        ],
        target_event_ids=[
            EVENT_A,
        ],
    )

    assert (
        plan.action
        == "already_same_event"
    )
    assert (
        plan.event_id
        == EVENT_A
    )
    assert plan.signal_ids == ()
    assert plan.write_allowed is False
    assert plan.requires_review is False


def test_distinct_existing_events_are_never_auto_merged():
    plan = plan_event_assignment(
        source_signal_id=SOURCE,
        target_signal_id=TARGET,
        matcher_result=auto_result(),
        source_event_ids=[
            EVENT_A,
        ],
        target_event_ids=[
            EVENT_B,
        ],
    )

    assert (
        plan.action
        == "manual_review"
    )
    assert (
        plan.reason
        == "signals_belong_to_distinct_events"
    )
    assert plan.write_allowed is False
    assert plan.requires_review is True


def test_multiple_existing_events_force_manual_review():
    plan = plan_event_assignment(
        source_signal_id=SOURCE,
        target_signal_id=TARGET,
        matcher_result=auto_result(),
        source_event_ids=[
            EVENT_A,
            EVENT_B,
        ],
    )

    assert (
        plan.action
        == "manual_review"
    )
    assert (
        plan.reason
        == "signal_has_multiple_existing_events"
    )
    assert plan.write_allowed is False
    assert plan.requires_review is True


def test_invalid_auto_link_contract_is_rejected():
    with pytest.raises(
        ValueError,
        match="no puede producir",
    ):
        plan_event_assignment(
            source_signal_id=SOURCE,
            target_signal_id=TARGET,
            matcher_result=auto_result(
                relation="supports",
            ),
        )


def _attachment_plan():
    from onehealth_worker.evaluation.event_assignment_v049 import (
        EventAssignmentPlan,
    )

    return EventAssignmentPlan(
        action="attach_target_to_event",
        reason="source_already_has_event",
        event_id=EVENT_A,
        signal_ids=(TARGET,),
        write_allowed=True,
        requires_review=False,
    )


def test_lifecycle_guard_allows_active_event():
    from onehealth_worker.evaluation.event_assignment_v049 import (
        apply_event_lifecycle_guard,
    )

    original = _attachment_plan()

    guarded = apply_event_lifecycle_guard(
        original,
        lifecycle_by_event_id={
            EVENT_A: "active",
        },
    )

    assert guarded == original
    assert guarded.write_allowed is True


def test_lifecycle_guard_allows_monitoring_event():
    from onehealth_worker.evaluation.event_assignment_v049 import (
        apply_event_lifecycle_guard,
    )

    original = _attachment_plan()

    guarded = apply_event_lifecycle_guard(
        original,
        lifecycle_by_event_id={
            EVENT_A: "monitoring",
        },
    )

    assert guarded == original
    assert guarded.write_allowed is True


def test_lifecycle_guard_blocks_resolved_event():
    from onehealth_worker.evaluation.event_assignment_v049 import (
        apply_event_lifecycle_guard,
    )

    guarded = apply_event_lifecycle_guard(
        _attachment_plan(),
        lifecycle_by_event_id={
            EVENT_A: "resolved",
        },
    )

    assert guarded.action == "manual_review"
    assert (
        guarded.reason
        == "target_event_resolved"
    )
    assert guarded.event_id == EVENT_A
    assert guarded.write_allowed is False
    assert guarded.requires_review is True


def test_lifecycle_guard_blocks_closed_event():
    from onehealth_worker.evaluation.event_assignment_v049 import (
        apply_event_lifecycle_guard,
    )

    guarded = apply_event_lifecycle_guard(
        _attachment_plan(),
        lifecycle_by_event_id={
            EVENT_A: "closed",
        },
    )

    assert guarded.action == "manual_review"
    assert (
        guarded.reason
        == "target_event_closed"
    )
    assert guarded.write_allowed is False
    assert guarded.requires_review is True


def test_lifecycle_guard_blocks_unknown_status():
    from onehealth_worker.evaluation.event_assignment_v049 import (
        apply_event_lifecycle_guard,
    )

    guarded = apply_event_lifecycle_guard(
        _attachment_plan(),
        lifecycle_by_event_id={},
    )

    assert guarded.action == "manual_review"
    assert (
        guarded.reason
        == "target_event_lifecycle_unknown"
    )
    assert guarded.write_allowed is False
    assert guarded.requires_review is True

