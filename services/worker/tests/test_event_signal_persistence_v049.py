from contextlib import contextmanager
from decimal import Decimal
from uuid import UUID

import pytest

from onehealth_worker.evaluation.event_matching_repository_v049 import (
    EventMatchingRepository,
)


EVENT = (
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)

SIGNAL = (
    "11111111-1111-1111-1111-111111111111"
)

OTHER_SIGNAL = (
    "22222222-2222-2222-2222-222222222222"
)

RELATION_ID = (
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
)


def _plan():
    return {
        "action": "attach_target_to_event",
        "reason": "source_already_has_event",
        "event_id": EVENT,
        "signal_ids": [
            SIGNAL,
        ],
        "write_allowed": True,
        "requires_review": False,
    }


def _relation_row():
    return {
        "id": UUID(
            RELATION_ID
        ),
        "source_signal_id": UUID(
            OTHER_SIGNAL
        ),
        "target_signal_id": UUID(
            SIGNAL
        ),
        "relation": "refines",
        "score": Decimal("0.950"),
        "hard_conflict": False,
        "rationale": {
            "producer": "oeti_event_matcher",
            "matcher_version": "0.4.8",
            "decision": "auto_linked",
            "merge_allowed": True,
            "raw_score": 0.951234,
        },
    }


def test_event_signal_persistence_rejects_create_event_plan_before_db():
    repository = EventMatchingRepository(
        "postgresql://unused"
    )

    plan = {
        **_plan(),
        "action": "create_event",
        "event_id": None,
        "signal_ids": [
            SIGNAL,
            OTHER_SIGNAL,
        ],
    }

    with pytest.raises(
        ValueError,
        match="existing-event attachment",
    ):
        repository.persist_event_signal_attachment(
            assignment_plan=plan,
            signal_relation_id=RELATION_ID,
        )


def test_event_signal_persistence_inserts_into_active_event():
    class FakeCursor:
        def __init__(self):
            self.phase = 0
            self.last_query = ""
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
            self.calls.append(
                (
                    self.last_query,
                    params,
                )
            )

        def fetchone(self):
            query = self.last_query

            if query.startswith(
                "select id, lifecycle_status::text"
            ):
                return {
                    "id": UUID(EVENT),
                    "lifecycle_status": "active",
                }

            if query.startswith(
                "select id from public.signals"
            ):
                return {
                    "id": UUID(SIGNAL),
                }

            if query.startswith(
                "select id, source_signal_id"
            ):
                return _relation_row()

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

            raise AssertionError(query)

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
        repository.persist_event_signal_attachment(
            assignment_plan=_plan(),
            signal_relation_id=RELATION_ID,
        )
    )

    assert result["action"] == "inserted"
    assert result["event_id"] == EVENT
    assert result["signal_id"] == SIGNAL
    assert (
        result["relation_to_event"]
        == "refines"
    )
    assert result["match_score"] == 0.95
    assert (
        result["match_decision"]
        == "auto_linked"
    )
    assert (
        result["lifecycle_status"]
        == "active"
    )

    assert connection.commit_count == 1

    inserts = [
        call
        for call in cursor.calls
        if call[0].startswith(
            "insert into public.event_signals"
        )
    ]

    assert len(inserts) == 1


def test_event_signal_persistence_updates_matcher_owned_membership():
    class FakeCursor:
        def __init__(self):
            self.last_query = ""

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

        def fetchone(self):
            query = self.last_query

            if query.startswith(
                "select id, lifecycle_status::text"
            ):
                return {
                    "id": UUID(EVENT),
                    "lifecycle_status": "monitoring",
                }

            if query.startswith(
                "select id from public.signals"
            ):
                return {
                    "id": UUID(SIGNAL),
                }

            if query.startswith(
                "select id, source_signal_id"
            ):
                return _relation_row()

            if query.startswith(
                "select relation_to_event::text"
            ):
                return {
                    "relation_to_event":
                        "refines",
                    "match_decision":
                        "auto_linked",
                    "rationale": {
                        "producer":
                            "oeti_event_matcher",
                    },
                    "linked_at": None,
                }

            if query.startswith(
                "update public.event_signals"
            ):
                return {
                    "linked_at": None,
                }

            raise AssertionError(query)

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
        repository.persist_event_signal_attachment(
            assignment_plan=_plan(),
            signal_relation_id=RELATION_ID,
        )
    )

    assert result["action"] == "updated"
    assert (
        result["lifecycle_status"]
        == "monitoring"
    )
    assert connection.commit_count == 1


def test_event_signal_persistence_blocks_terminal_event_inside_transaction():
    class FakeCursor:
        def __init__(self):
            self.last_query = ""

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

        def fetchone(self):
            return {
                "id": UUID(EVENT),
                "lifecycle_status": "resolved",
            }

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
        repository.persist_event_signal_attachment(
            assignment_plan=_plan(),
            signal_relation_id=RELATION_ID,
        )

    assert connection.commit_count == 0


def test_event_signal_persistence_blocks_stale_signal():
    class FakeCursor:
        def __init__(self):
            self.last_query = ""

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

        def fetchone(self):
            if self.last_query.startswith(
                "select id, lifecycle_status::text"
            ):
                return {
                    "id": UUID(EVENT),
                    "lifecycle_status": "active",
                }

            if self.last_query.startswith(
                "select id from public.signals"
            ):
                return None

            raise AssertionError(
                self.last_query
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
        match="no longer current",
    ):
        repository.persist_event_signal_attachment(
            assignment_plan=_plan(),
            signal_relation_id=RELATION_ID,
        )

    assert connection.commit_count == 0


def test_event_signal_persistence_protects_manual_membership():
    class FakeCursor:
        def __init__(self):
            self.last_query = ""

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

        def fetchone(self):
            query = self.last_query

            if query.startswith(
                "select id, lifecycle_status::text"
            ):
                return {
                    "id": UUID(EVENT),
                    "lifecycle_status": "active",
                }

            if query.startswith(
                "select id from public.signals"
            ):
                return {
                    "id": UUID(SIGNAL),
                }

            if query.startswith(
                "select id, source_signal_id"
            ):
                return _relation_row()

            if query.startswith(
                "select relation_to_event::text"
            ):
                return {
                    "relation_to_event":
                        "refines",
                    "match_decision":
                        "manual_linked",
                    "rationale": {},
                    "linked_at": None,
                }

            raise AssertionError(query)

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
        repository.persist_event_signal_attachment(
            assignment_plan=_plan(),
            signal_relation_id=RELATION_ID,
        )

    assert connection.commit_count == 0
