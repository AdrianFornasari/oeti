from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from onehealth_worker.evaluation.event_creation_planner_v049 import (
    EventCreationPlanner,
)
from onehealth_worker.evaluation.event_matching_repository_v049 import (
    EventMatchingRepository,
)


REL = (
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)

A = (
    "11111111-1111-1111-1111-111111111111"
)

B = (
    "22222222-2222-2222-2222-222222222222"
)

DISEASE = (
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
)

PATHOGEN = (
    "cccccccc-cccc-cccc-cccc-cccccccccccc"
)


def _relation(
    **overrides,
):
    matcher = {
        "gate": "eligible",
        "relation": "refines",
        "decision": "auto_linked",
        "merge_allowed": True,
        "hard_conflict": False,
        "hard_conflict_reason": None,
        "score": 0.95,
        "information_coverage": 1.0,
        "component_scores": {},
    }

    matcher.update(
        overrides
    )

    return {
        "signal_relation_id": REL,
        "source_signal_id": A,
        "target_signal_id": B,
        "matcher_version": "0.4.8",
        "matcher_result": matcher,
    }


def _signal(
    signal_id,
    *,
    occurred_start,
):
    return {
        "signal_id": signal_id,
        "disease_id": DISEASE,
        "disease_canonical_name":
            "Hantavirus disease",
        "pathogen_id": PATHOGEN,
        "pathogen_canonical_name":
            "Andes virus",
        "domains": [
            "human",
        ],
        "occurred_start":
            occurred_start,
        "observed_at":
            "2026-05-12T12:00:00+00:00",
    }


def test_repository_loads_event_creation_signal_projection():
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

        def fetchone(self):
            return {
                "signal_id": UUID(A),
                "disease_id":
                    UUID(DISEASE),
                "disease_canonical_name":
                    "Hantavirus disease",
                "pathogen_id":
                    UUID(PATHOGEN),
                "pathogen_canonical_name":
                    "Andes virus",
                "domains": [
                    "human",
                    "genomic",
                ],
                "occurred_start":
                    datetime(
                        2026,
                        5,
                        4,
                        tzinfo=timezone.utc,
                    ).date(),
                "observed_at":
                    datetime(
                        2026,
                        5,
                        4,
                        18,
                        6,
                        tzinfo=timezone.utc,
                    ),
            }

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

    @contextmanager
    def fake_connection():
        yield FakeConnection()

    repository = EventMatchingRepository(
        "postgresql://unused"
    )
    repository.connection = (
        fake_connection
    )

    row = (
        repository
        .load_event_creation_signal(
            A
        )
    )

    assert row[
        "signal_id"
    ] == A

    assert row[
        "disease_id"
    ] == DISEASE

    assert row[
        "pathogen_id"
    ] == PATHOGEN

    assert row[
        "domains"
    ] == [
        "human",
        "genomic",
    ]

    assert row[
        "occurred_start"
    ] == "2026-05-04"

    assert row[
        "observed_at"
    ].startswith(
        "2026-05-04T18:06"
    )


def test_planner_blocks_review_required_without_loading_signals():
    class FakeRepository:
        def load_persisted_matcher_relation_by_id(
            self,
            signal_relation_id,
        ):
            return _relation(
                relation="supports",
                decision="review_required",
                merge_allowed=False,
            )

        def load_event_creation_signal(
            self,
            signal_id,
        ):
            raise AssertionError(
                "Signals must not be loaded."
            )

    report = EventCreationPlanner(
        FakeRepository()
    ).plan_relation(
        REL
    )

    assert (
        report["status"]
        == "blocked"
    )
    assert (
        report["reason"]
        == "matcher_requires_review"
    )
    assert (
        report["event_seed"]
        is None
    )


def test_planner_blocks_rejected_relation():
    class FakeRepository:
        def load_persisted_matcher_relation_by_id(
            self,
            signal_relation_id,
        ):
            return _relation(
                relation="unknown",
                decision="rejected",
                merge_allowed=False,
            )

    report = EventCreationPlanner(
        FakeRepository()
    ).plan_relation(
        REL
    )

    assert (
        report["status"]
        == "blocked"
    )
    assert (
        report["reason"]
        == "matcher_rejected"
    )


def test_planner_blocks_existing_event_membership():
    class FakeRepository:
        def load_persisted_matcher_relation_by_id(
            self,
            signal_relation_id,
        ):
            return _relation()

        def load_event_memberships_for_signal(
            self,
            signal_id,
        ):
            if signal_id == A:
                return [
                    {
                        "event_id":
                            "event-a",
                    }
                ]

            return []

        def load_event_creation_signal(
            self,
            signal_id,
        ):
            raise AssertionError(
                "Seed signals must not be loaded."
            )

    report = EventCreationPlanner(
        FakeRepository()
    ).plan_relation(
        REL
    )

    assert (
        report["status"]
        == "blocked"
    )
    assert (
        report["reason"]
        == "existing_event_membership"
    )
    assert (
        report["write_allowed"]
        is False
    )


def test_planner_builds_seed_for_valid_auto_link():
    class FakeRepository:
        def load_persisted_matcher_relation_by_id(
            self,
            signal_relation_id,
        ):
            return _relation()

        def load_event_memberships_for_signal(
            self,
            signal_id,
        ):
            return []

        def load_event_creation_signal(
            self,
            signal_id,
        ):
            return _signal(
                signal_id,
                occurred_start=(
                    "2026-05-04"
                    if signal_id == A
                    else "2026-05-12"
                ),
            )

    report = EventCreationPlanner(
        FakeRepository()
    ).plan_relation(
        REL
    )

    assert (
        report["status"]
        == "ready"
    )

    assert (
        report["write_allowed"]
        is True
    )

    seed = report[
        "event_seed"
    ]

    assert (
        seed["event_start_date"]
        == "2026-05-04"
    )

    assert (
        seed["disease_id"]
        == DISEASE
    )

    assert (
        seed["pathogen_id"]
        == PATHOGEN
    )

    assert (
        seed["source_signal_ids"]
        == [
            A,
            B,
        ]
    )


def test_planner_blocks_hard_conflict_before_membership_lookup():
    class FakeRepository:
        def load_persisted_matcher_relation_by_id(
            self,
            signal_relation_id,
        ):
            return _relation(
                relation="contradicts",
                decision="rejected",
                merge_allowed=False,
                hard_conflict=True,
            )

        def load_event_memberships_for_signal(
            self,
            signal_id,
        ):
            raise AssertionError(
                "Memberships must not be loaded."
            )

    report = EventCreationPlanner(
        FakeRepository()
    ).plan_relation(
        REL
    )

    assert (
        report["status"]
        == "blocked"
    )

    assert (
        report["reason"]
        == "hard_conflict"
    )
