from contextlib import contextmanager
from decimal import Decimal
from uuid import UUID

import pytest

from onehealth_worker.evaluation.event_matching_repository_v049 import (
    EventMatchingRepository,
)


EVENT_A = (
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"
)

EVENT_B = (
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2"
)

SIGNAL_A = (
    "11111111-1111-1111-1111-111111111111"
)

SIGNAL_B = (
    "22222222-2222-2222-2222-222222222222"
)

OTHER_A = (
    "33333333-3333-3333-3333-333333333333"
)

OTHER_B = (
    "44444444-4444-4444-4444-444444444444"
)

REL_A = (
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1"
)

REL_B = (
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2"
)


def _item(
    *,
    event_id,
    signal_id,
    relation_id,
):
    return {
        "signal_relation_id":
            relation_id,
        "assignment_plan": {
            "action":
                "attach_target_to_event",
            "reason":
                "source_already_has_event",
            "event_id":
                event_id,
            "signal_ids": [
                signal_id,
            ],
            "write_allowed":
                True,
            "requires_review":
                False,
        },
    }


def _relation_row(
    relation_id,
    signal_id,
    other_id,
):
    return {
        "id": UUID(
            relation_id
        ),
        "source_signal_id": UUID(
            other_id
        ),
        "target_signal_id": UUID(
            signal_id
        ),
        "relation": "refines",
        "score": Decimal("0.950"),
        "hard_conflict": False,
        "rationale": {
            "producer":
                "oeti_event_matcher",
            "matcher_version":
                "0.4.8",
            "decision":
                "auto_linked",
            "merge_allowed":
                True,
            "raw_score":
                0.951234,
        },
    }


def test_batch_empty_is_noop():
    repository = EventMatchingRepository(
        "postgresql://unused"
    )

    assert (
        repository
        .persist_event_signal_attachments_batch(
            []
        )
        == []
    )


def test_batch_rejects_duplicate_membership_before_database():
    repository = EventMatchingRepository(
        "postgresql://unused"
    )

    items = [
        _item(
            event_id=EVENT_A,
            signal_id=SIGNAL_A,
            relation_id=REL_A,
        ),
        _item(
            event_id=EVENT_A,
            signal_id=SIGNAL_A,
            relation_id=REL_B,
        ),
    ]

    with pytest.raises(
        ValueError,
        match="duplicate event/signal",
    ):
        repository.persist_event_signal_attachments_batch(
            items
        )


def test_batch_inserts_two_attachments_with_one_commit():
    relation_rows = {
        REL_A: _relation_row(
            REL_A,
            SIGNAL_A,
            OTHER_A,
        ),
        REL_B: _relation_row(
            REL_B,
            SIGNAL_B,
            OTHER_B,
        ),
    }

    class FakeCursor:
        def __init__(self):
            self.last_query = ""
            self.last_params = None
            self.calls = []

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
            self.last_query = " ".join(
                str(query).split()
            )
            self.last_params = params
            self.calls.append(
                (
                    self.last_query,
                    params,
                )
            )

        def fetchone(self):
            query = self.last_query
            params = self.last_params

            if query.startswith(
                "select id, lifecycle_status::text"
            ):
                return {
                    "id": UUID(
                        params[0]
                    ),
                    "lifecycle_status":
                        "active",
                }

            if query.startswith(
                "select id from public.signals"
            ):
                return {
                    "id": UUID(
                        params[0]
                    ),
                }

            if query.startswith(
                "select id, source_signal_id"
            ):
                return relation_rows[
                    str(params[0])
                ]

            if query.startswith(
                "select relation_to_event::text"
            ):
                return None

            if query.startswith(
                "insert into public.event_signals"
            ):
                return {
                    "linked_at": None,
                }

            raise AssertionError(
                query
            )

    cursor = FakeCursor()

    class FakeConnection:
        def __init__(self):
            self.commit_count = 0

        def cursor(self):
            return cursor

        def commit(self):
            self.commit_count += 1

    connection = FakeConnection()

    @contextmanager
    def fake_connection():
        yield connection

    repository = EventMatchingRepository(
        "postgresql://unused"
    )
    repository.connection = (
        fake_connection
    )

    result = (
        repository
        .persist_event_signal_attachments_batch(
            [
                _item(
                    event_id=EVENT_B,
                    signal_id=SIGNAL_B,
                    relation_id=REL_B,
                ),
                _item(
                    event_id=EVENT_A,
                    signal_id=SIGNAL_A,
                    relation_id=REL_A,
                ),
            ]
        )
    )

    assert len(result) == 2

    assert [
        item["action"]
        for item in result
    ] == [
        "inserted",
        "inserted",
    ]

    assert (
        connection.commit_count
        == 1
    )

    inserts = [
        query
        for query, _params
        in cursor.calls
        if query.startswith(
            "insert into public.event_signals"
        )
    ]

    assert len(inserts) == 2


def test_batch_terminal_second_event_prevents_commit():
    class FakeCursor:
        def __init__(self):
            self.last_query = ""
            self.last_params = None

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
            self.last_query = " ".join(
                str(query).split()
            )
            self.last_params = params

        def fetchone(self):
            query = self.last_query
            params = self.last_params

            if query.startswith(
                "select id, lifecycle_status::text"
            ):
                status = (
                    "resolved"
                    if str(
                        params[0]
                    )
                    == EVENT_B
                    else "active"
                )

                return {
                    "id": UUID(
                        params[0]
                    ),
                    "lifecycle_status":
                        status,
                }

            if query.startswith(
                "select id from public.signals"
            ):
                return {
                    "id": UUID(
                        params[0]
                    ),
                }

            if query.startswith(
                "select id, source_signal_id"
            ):
                relation_id = str(
                    params[0]
                )

                if relation_id == REL_A:
                    return _relation_row(
                        REL_A,
                        SIGNAL_A,
                        OTHER_A,
                    )

                return _relation_row(
                    REL_B,
                    SIGNAL_B,
                    OTHER_B,
                )

            if query.startswith(
                "select relation_to_event::text"
            ):
                return None

            if query.startswith(
                "insert into public.event_signals"
            ):
                return {
                    "linked_at": None,
                }

            raise AssertionError(
                query
            )

    cursor = FakeCursor()

    class FakeConnection:
        def __init__(self):
            self.commit_count = 0

        def cursor(self):
            return cursor

        def commit(self):
            self.commit_count += 1

    connection = FakeConnection()

    @contextmanager
    def fake_connection():
        yield connection

    repository = EventMatchingRepository(
        "postgresql://unused"
    )
    repository.connection = (
        fake_connection
    )

    with pytest.raises(
        ValueError,
        match="not open",
    ):
        repository.persist_event_signal_attachments_batch(
            [
                _item(
                    event_id=EVENT_A,
                    signal_id=SIGNAL_A,
                    relation_id=REL_A,
                ),
                _item(
                    event_id=EVENT_B,
                    signal_id=SIGNAL_B,
                    relation_id=REL_B,
                ),
            ]
        )

    assert (
        connection.commit_count
        == 0
    )


def test_batch_manual_membership_prevents_commit():
    class FakeCursor:
        def __init__(self):
            self.last_query = ""
            self.last_params = None

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
            self.last_query = " ".join(
                str(query).split()
            )
            self.last_params = params

        def fetchone(self):
            query = self.last_query
            params = self.last_params

            if query.startswith(
                "select id, lifecycle_status::text"
            ):
                return {
                    "id": UUID(
                        params[0]
                    ),
                    "lifecycle_status":
                        "monitoring",
                }

            if query.startswith(
                "select id from public.signals"
            ):
                return {
                    "id": UUID(
                        params[0]
                    ),
                }

            if query.startswith(
                "select id, source_signal_id"
            ):
                return _relation_row(
                    REL_A,
                    SIGNAL_A,
                    OTHER_A,
                )

            if query.startswith(
                "select relation_to_event::text"
            ):
                return {
                    "relation_to_event":
                        "refines",
                    "match_decision":
                        "manual_linked",
                    "rationale": {},
                    "linked_at":
                        None,
                }

            raise AssertionError(
                query
            )

    cursor = FakeCursor()

    class FakeConnection:
        def __init__(self):
            self.commit_count = 0

        def cursor(self):
            return cursor

        def commit(self):
            self.commit_count += 1

    connection = FakeConnection()

    @contextmanager
    def fake_connection():
        yield connection

    repository = EventMatchingRepository(
        "postgresql://unused"
    )
    repository.connection = (
        fake_connection
    )

    with pytest.raises(
        ValueError,
        match="Manual event membership",
    ):
        repository.persist_event_signal_attachments_batch(
            [
                _item(
                    event_id=EVENT_A,
                    signal_id=SIGNAL_A,
                    relation_id=REL_A,
                )
            ]
        )

    assert (
        connection.commit_count
        == 0
    )
