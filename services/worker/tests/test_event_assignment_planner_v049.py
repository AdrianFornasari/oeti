from contextlib import contextmanager
from decimal import Decimal
from uuid import UUID

from onehealth_worker.evaluation.event_assignment_planner_v049 import (
    EventAssignmentPlanner,
)
from onehealth_worker.evaluation.event_matching_repository_v049 import (
    EventMatchingRepository,
)


ANCHOR = (
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


def _persisted_relation(
    *,
    relation="supports",
    decision="review_required",
    merge_allowed=False,
    score=0.78,
    hard_conflict=False,
):
    return {
        "signal_relation_id": "relation-1",
        "source_signal_id": ANCHOR,
        "target_signal_id": TARGET,
        "candidate_prefilter": {},
        "matcher_version": "0.4.8",
        "matcher_result": {
            "gate": "eligible",
            "relation": relation,
            "decision": decision,
            "merge_allowed": merge_allowed,
            "hard_conflict": hard_conflict,
            "hard_conflict_reason": None,
            "score": score,
            "information_coverage": 1.0,
            "component_scores": {},
        },
    }


def test_repository_reconstructs_persisted_matcher_relation():
    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(
            self,
            exc_type,
            exc,
            tb,
        ):
            return False

        def execute(
            self,
            query,
            params,
        ):
            self.params = params

        def fetchall(self):
            return [
                {
                    "id": UUID(
                        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
                    ),
                    "source_signal_id": UUID(
                        ANCHOR
                    ),
                    "target_signal_id": UUID(
                        TARGET
                    ),
                    "relation": "supports",
                    "score": Decimal(
                        "0.780"
                    ),
                    "hard_conflict": False,
                    "rationale": {
                        "producer":
                            "oeti_event_matcher",
                        "matcher_version":
                            "0.4.8",
                        "gate": "eligible",
                        "decision":
                            "review_required",
                        "merge_allowed":
                            False,
                        "hard_conflict_reason":
                            None,
                        "information_coverage":
                            0.9,
                        "component_scores": {
                            "etiology": 1.0,
                        },
                        "candidate_prefilter": {
                            "same_disease": True,
                        },
                    },
                }
            ]

    cursor = FakeCursor()

    class FakeConnection:
        def cursor(self):
            return cursor

    @contextmanager
    def fake_connection():
        yield FakeConnection()

    repository = EventMatchingRepository(
        "postgresql://unused"
    )
    repository.connection = (
        fake_connection
    )

    rows = (
        repository
        .load_persisted_matcher_relations_for_signal(
            ANCHOR
        )
    )

    assert len(rows) == 1
    assert (
        rows[0]["matcher_result"][
            "decision"
        ]
        == "review_required"
    )
    assert (
        rows[0]["matcher_result"][
            "score"
        ]
        == 0.78
    )
    assert (
        rows[0]["candidate_prefilter"][
            "same_disease"
        ]
        is True
    )


def test_repository_reads_event_membership_and_lifecycle():
    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(
            self,
            exc_type,
            exc,
            tb,
        ):
            return False

        def execute(
            self,
            query,
            params,
        ):
            self.params = params

        def fetchall(self):
            return [
                {
                    "event_id":
                        UUID(EVENT_A),
                    "event_code":
                        "OETI-TEST-001",
                    "lifecycle_status":
                        "monitoring",
                    "relation_to_event":
                        "refines",
                    "match_score":
                        Decimal("0.950"),
                    "match_decision":
                        "auto_linked",
                    "linked_at":
                        None,
                }
            ]

    cursor = FakeCursor()

    class FakeConnection:
        def cursor(self):
            return cursor

    @contextmanager
    def fake_connection():
        yield FakeConnection()

    repository = EventMatchingRepository(
        "postgresql://unused"
    )
    repository.connection = (
        fake_connection
    )

    rows = (
        repository
        .load_event_memberships_for_signal(
            ANCHOR
        )
    )

    assert rows == [
        {
            "event_id": EVENT_A,
            "event_code":
                "OETI-TEST-001",
            "lifecycle_status":
                "monitoring",
            "relation_to_event":
                "refines",
            "match_score": 0.95,
            "match_decision":
                "auto_linked",
            "linked_at": None,
        }
    ]


def test_planner_review_relation_never_writes_and_caches_memberships():
    class FakeRepository:
        def __init__(self):
            self.membership_calls = []

        def load_persisted_matcher_relations_for_signal(
            self,
            signal_id,
        ):
            return [
                _persisted_relation(),
                {
                    **_persisted_relation(
                        relation="unknown",
                        decision="rejected",
                        score=0.44,
                    ),
                    "signal_relation_id":
                        "relation-2",
                    "target_signal_id":
                        "33333333-3333-3333-3333-333333333333",
                },
            ]

        def load_event_memberships_for_signal(
            self,
            signal_id,
        ):
            self.membership_calls.append(
                signal_id
            )
            return []

    repository = FakeRepository()

    report = EventAssignmentPlanner(
        repository
    ).plan_persisted_anchor(
        ANCHOR
    )

    assert (
        report["mode"]
        == "plan_only"
    )
    assert (
        report["persisted_relations"]
        == 2
    )
    assert (
        report["summary"][
            "no_event_change"
        ]
        == 2
    )
    assert (
        report["summary"][
            "write_allowed"
        ]
        == 0
    )
    assert (
        report["summary"][
            "requires_review"
        ]
        == 1
    )

    assert (
        repository.membership_calls.count(
            ANCHOR
        )
        == 1
    )


def test_planner_auto_link_without_membership_creates_event_plan():
    class FakeRepository:
        def load_persisted_matcher_relations_for_signal(
            self,
            signal_id,
        ):
            return [
                _persisted_relation(
                    relation="refines",
                    decision="auto_linked",
                    merge_allowed=True,
                    score=0.95,
                )
            ]

        def load_event_memberships_for_signal(
            self,
            signal_id,
        ):
            return []

    report = EventAssignmentPlanner(
        FakeRepository()
    ).plan_persisted_anchor(
        ANCHOR
    )

    plan = report[
        "plans"
    ][0][
        "assignment_plan"
    ]

    assert (
        plan["action"]
        == "create_event"
    )
    assert (
        plan["write_allowed"]
        is True
    )
    assert (
        report["summary"][
            "create_event"
        ]
        == 1
    )


def test_planner_distinct_existing_events_forces_manual_review():
    class FakeRepository:
        def load_persisted_matcher_relations_for_signal(
            self,
            signal_id,
        ):
            return [
                _persisted_relation(
                    relation="refines",
                    decision="auto_linked",
                    merge_allowed=True,
                    score=0.95,
                )
            ]

        def load_event_memberships_for_signal(
            self,
            signal_id,
        ):
            event_id = (
                EVENT_A
                if signal_id == ANCHOR
                else EVENT_B
            )

            return [
                {
                    "event_id":
                        event_id,
                    "event_code":
                        "TEST",
                    "lifecycle_status":
                        "active",
                    "relation_to_event":
                        "refines",
                    "match_score":
                        0.95,
                    "match_decision":
                        "auto_linked",
                    "linked_at":
                        None,
                }
            ]

    report = EventAssignmentPlanner(
        FakeRepository()
    ).plan_persisted_anchor(
        ANCHOR
    )

    plan = report[
        "plans"
    ][0][
        "assignment_plan"
    ]

    assert (
        plan["action"]
        == "manual_review"
    )
    assert (
        plan["reason"]
        == "signals_belong_to_distinct_events"
    )
    assert (
        report["summary"][
            "write_allowed"
        ]
        == 0
    )
    assert (
        report["summary"][
            "requires_review"
        ]
        == 1
    )


def test_planner_active_event_allows_auto_attachment():
    class FakeRepository:
        def load_persisted_matcher_relations_for_signal(
            self,
            signal_id,
        ):
            return [
                _persisted_relation(
                    relation="refines",
                    decision="auto_linked",
                    merge_allowed=True,
                    score=0.95,
                )
            ]

        def load_event_memberships_for_signal(
            self,
            signal_id,
        ):
            if signal_id != ANCHOR:
                return []

            return [
                {
                    "event_id": EVENT_A,
                    "event_code": "TEST-ACTIVE",
                    "lifecycle_status": "active",
                    "relation_to_event": "refines",
                    "match_score": 0.95,
                    "match_decision": "auto_linked",
                    "linked_at": None,
                }
            ]

    report = EventAssignmentPlanner(
        FakeRepository()
    ).plan_persisted_anchor(
        ANCHOR
    )

    plan = report[
        "plans"
    ][0][
        "assignment_plan"
    ]

    assert (
        plan["action"]
        == "attach_target_to_event"
    )
    assert (
        plan["event_id"]
        == EVENT_A
    )
    assert (
        plan["signal_ids"]
        == [TARGET]
    )
    assert (
        plan["write_allowed"]
        is True
    )
    assert (
        report["summary"][
            "write_allowed"
        ]
        == 1
    )


def test_planner_resolved_event_blocks_auto_attachment():
    class FakeRepository:
        def load_persisted_matcher_relations_for_signal(
            self,
            signal_id,
        ):
            return [
                _persisted_relation(
                    relation="refines",
                    decision="auto_linked",
                    merge_allowed=True,
                    score=0.95,
                )
            ]

        def load_event_memberships_for_signal(
            self,
            signal_id,
        ):
            if signal_id != ANCHOR:
                return []

            return [
                {
                    "event_id": EVENT_A,
                    "event_code": "TEST-RESOLVED",
                    "lifecycle_status": "resolved",
                    "relation_to_event": "refines",
                    "match_score": 0.95,
                    "match_decision": "auto_linked",
                    "linked_at": None,
                }
            ]

    report = EventAssignmentPlanner(
        FakeRepository()
    ).plan_persisted_anchor(
        ANCHOR
    )

    plan = report[
        "plans"
    ][0][
        "assignment_plan"
    ]

    assert (
        plan["action"]
        == "manual_review"
    )
    assert (
        plan["reason"]
        == "target_event_resolved"
    )
    assert (
        plan["write_allowed"]
        is False
    )
    assert (
        plan["requires_review"]
        is True
    )
    assert (
        report["summary"][
            "write_allowed"
        ]
        == 0
    )
    assert (
        report["summary"][
            "requires_review"
        ]
        == 1
    )

