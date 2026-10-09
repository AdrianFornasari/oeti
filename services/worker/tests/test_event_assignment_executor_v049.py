from onehealth_worker.evaluation.event_assignment_executor_v049 import (
    EventAssignmentExecutor,
)


ANCHOR = (
    "11111111-1111-1111-1111-111111111111"
)


def _report(
    plans,
):
    summary = {
        "no_event_change": 0,
        "create_event": 0,
        "attach_target_to_event": 0,
        "attach_source_to_event": 0,
        "already_same_event": 0,
        "manual_review": 0,
        "write_allowed": 0,
        "requires_review": 0,
    }

    for item in plans:
        plan = item[
            "assignment_plan"
        ]

        summary[
            plan["action"]
        ] += 1

        if plan[
            "write_allowed"
        ]:
            summary[
                "write_allowed"
            ] += 1

        if plan[
            "requires_review"
        ]:
            summary[
                "requires_review"
            ] += 1

    return {
        "mode": "plan_only",
        "anchor_signal_id": ANCHOR,
        "persisted_relations": len(
            plans
        ),
        "signals_with_membership_lookup": 0,
        "summary": summary,
        "plans": plans,
    }


def _item(
    *,
    relation_id,
    action,
    reason,
    write_allowed,
    requires_review=False,
):
    return {
        "signal_relation_id":
            relation_id,
        "source_signal_id":
            "11111111-1111-1111-1111-111111111111",
        "target_signal_id":
            "22222222-2222-2222-2222-222222222222",
        "matcher_result": {},
        "candidate_prefilter": {},
        "matcher_version": "0.4.8",
        "source_memberships": [],
        "target_memberships": [],
        "assignment_plan": {
            "action": action,
            "reason": reason,
            "event_id": (
                "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
                if action.startswith(
                    "attach_"
                )
                else None
            ),
            "signal_ids": [
                "22222222-2222-2222-2222-222222222222"
            ],
            "write_allowed":
                write_allowed,
            "requires_review":
                requires_review,
        },
    }


def test_executor_dry_run_with_only_review_and_rejected_pairs_writes_nothing():
    class FakePlanner:
        def plan_persisted_anchor(
            self,
            anchor_signal_id,
        ):
            return _report(
                [
                    _item(
                        relation_id="r1",
                        action="no_event_change",
                        reason="matcher_requires_review",
                        write_allowed=False,
                        requires_review=True,
                    ),
                    _item(
                        relation_id="r2",
                        action="no_event_change",
                        reason="matcher_rejected",
                        write_allowed=False,
                    ),
                ]
            )

    report = (
        EventAssignmentExecutor(
            FakePlanner()
        ).evaluate_anchor(
            ANCHOR
        )
    )

    assert (
        report["mode"]
        == "dry_run"
    )
    assert (
        report[
            "executable_attachments"
        ]
        == 0
    )
    assert (
        report[
            "would_write_event_signals"
        ]
        == 0
    )
    assert (
        report[
            "would_create_events"
        ]
        == 0
    )
    assert (
        report[
            "blocked_or_noop"
        ]
        == 2
    )


def test_executor_identifies_existing_event_attachment():
    class FakePlanner:
        def plan_persisted_anchor(
            self,
            anchor_signal_id,
        ):
            return _report(
                [
                    _item(
                        relation_id="r1",
                        action="attach_target_to_event",
                        reason="source_already_has_event",
                        write_allowed=True,
                    )
                ]
            )

    report = (
        EventAssignmentExecutor(
            FakePlanner()
        ).evaluate_anchor(
            ANCHOR
        )
    )

    assert (
        report[
            "executable_attachments"
        ]
        == 1
    )
    assert (
        report[
            "would_write_event_signals"
        ]
        == 1
    )
    assert (
        report[
            "executable"
        ][0][
            "signal_relation_id"
        ]
        == "r1"
    )


def test_executor_defers_new_event_creation():
    class FakePlanner:
        def plan_persisted_anchor(
            self,
            anchor_signal_id,
        ):
            return _report(
                [
                    _item(
                        relation_id="r1",
                        action="create_event",
                        reason="auto_linked_pair_without_event",
                        write_allowed=True,
                    )
                ]
            )

    report = (
        EventAssignmentExecutor(
            FakePlanner()
        ).evaluate_anchor(
            ANCHOR
        )
    )

    assert (
        report[
            "executable_attachments"
        ]
        == 0
    )
    assert (
        report[
            "deferred_create_events"
        ]
        == 1
    )
    assert (
        report[
            "would_create_events"
        ]
        == 1
    )


def test_executor_keeps_manual_review_blocked():
    class FakePlanner:
        def plan_persisted_anchor(
            self,
            anchor_signal_id,
        ):
            return _report(
                [
                    _item(
                        relation_id="r1",
                        action="manual_review",
                        reason="target_event_closed",
                        write_allowed=False,
                        requires_review=True,
                    )
                ]
            )

    report = (
        EventAssignmentExecutor(
            FakePlanner()
        ).evaluate_anchor(
            ANCHOR
        )
    )

    assert (
        report[
            "executable_attachments"
        ]
        == 0
    )

    assert report[
        "blocked"
    ] == [
        {
            "signal_relation_id":
                "r1",
            "action":
                "manual_review",
            "reason":
                "target_event_closed",
            "requires_review":
                True,
        }
    ]


def test_executor_persist_mode_calls_one_atomic_batch():
    class FakePlanner:
        def plan_persisted_anchor(
            self,
            anchor_signal_id,
        ):
            return _report(
                [
                    _item(
                        relation_id="r1",
                        action="attach_target_to_event",
                        reason="source_already_has_event",
                        write_allowed=True,
                    ),
                    _item(
                        relation_id="r2",
                        action="attach_source_to_event",
                        reason="target_already_has_event",
                        write_allowed=True,
                    ),
                ]
            )

    class FakeRepository:
        def __init__(self):
            self.calls = []

        def persist_event_signal_attachments_batch(
            self,
            items,
        ):
            self.calls.append(
                items
            )

            return [
                {
                    "signal_relation_id":
                        "r1",
                    "action":
                        "inserted",
                },
                {
                    "signal_relation_id":
                        "r2",
                    "action":
                        "updated",
                },
            ]

    repository = FakeRepository()

    report = (
        EventAssignmentExecutor(
            FakePlanner(),
            repository=repository,
        ).evaluate_anchor(
            ANCHOR,
            persist=True,
        )
    )

    assert (
        report["mode"]
        == "persist"
    )

    assert len(
        repository.calls
    ) == 1

    assert len(
        repository.calls[0]
    ) == 2

    assert report[
        "persistence"
    ] == {
        "requested": True,
        "requested_attachments": 2,
        "persisted_attachments": 2,
        "inserted": 1,
        "updated": 1,
        "deferred_create_events": 0,
    }


def test_executor_persist_mode_with_zero_attachments_does_not_write():
    class FakePlanner:
        def plan_persisted_anchor(
            self,
            anchor_signal_id,
        ):
            return _report(
                [
                    _item(
                        relation_id="r1",
                        action="no_event_change",
                        reason="matcher_requires_review",
                        write_allowed=False,
                        requires_review=True,
                    )
                ]
            )

    class FakeRepository:
        def persist_event_signal_attachments_batch(
            self,
            items,
        ):
            raise AssertionError(
                "Batch persistence must not be called."
            )

    report = (
        EventAssignmentExecutor(
            FakePlanner(),
            repository=FakeRepository(),
        ).evaluate_anchor(
            ANCHOR,
            persist=True,
        )
    )

    assert (
        report["mode"]
        == "persist"
    )

    assert (
        report[
            "executable_attachments"
        ]
        == 0
    )

    assert report[
        "persistence"
    ] == {
        "requested": True,
        "requested_attachments": 0,
        "persisted_attachments": 0,
        "inserted": 0,
        "updated": 0,
        "deferred_create_events": 0,
    }


def test_executor_persist_mode_still_defers_event_creation():
    class FakePlanner:
        def plan_persisted_anchor(
            self,
            anchor_signal_id,
        ):
            return _report(
                [
                    _item(
                        relation_id="r1",
                        action="create_event",
                        reason="auto_linked_pair_without_event",
                        write_allowed=True,
                    )
                ]
            )

    class FakeRepository:
        def persist_event_signal_attachments_batch(
            self,
            items,
        ):
            raise AssertionError(
                "Create-event plans must not enter "
                "attachment persistence."
            )

    report = (
        EventAssignmentExecutor(
            FakePlanner(),
            repository=FakeRepository(),
        ).evaluate_anchor(
            ANCHOR,
            persist=True,
        )
    )

    assert (
        report[
            "deferred_create_events"
        ]
        == 1
    )

    assert (
        report[
            "would_create_events"
        ]
        == 1
    )

    assert (
        report[
            "persistence"
        ][
            "persisted_attachments"
        ]
        == 0
    )

    assert (
        report[
            "persistence"
        ][
            "deferred_create_events"
        ]
        == 1
    )


def test_executor_requires_repository_only_when_real_attachment_exists():
    import pytest

    class FakePlanner:
        def plan_persisted_anchor(
            self,
            anchor_signal_id,
        ):
            return _report(
                [
                    _item(
                        relation_id="r1",
                        action="attach_target_to_event",
                        reason="source_already_has_event",
                        write_allowed=True,
                    )
                ]
            )

    executor = EventAssignmentExecutor(
        FakePlanner(),
        repository=None,
    )

    with pytest.raises(
        ValueError,
        match="no repository",
    ):
        executor.evaluate_anchor(
            ANCHOR,
            persist=True,
        )

