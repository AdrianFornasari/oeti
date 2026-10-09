from contextlib import contextmanager

import pytest

from onehealth_worker.evaluation.event_matching_repository_v049 import EventMatchingRepository


def test_creation_writes_disabled_by_default():
    repository = EventMatchingRepository("postgresql://unused")
    repository.connection = lambda: pytest.fail("Disabled writes must not connect")
    with pytest.raises(RuntimeError, match="not enabled"):
        repository.persist_event_creation_cohort(event_seed={
            "event_code": "test", "source_signal_ids": [
                "00000000-0000-0000-0000-000000000001",
                "00000000-0000-0000-0000-000000000002"],
            "source_relation_ids": ["00000000-0000-0000-0000-000000000003"],
        }, dry_run=False)


@pytest.mark.parametrize("failure", [False, True])
def test_creation_insert_is_inside_single_transaction(failure):
    from onehealth_worker.evaluation.event_creation_v049 import build_event_creation_cohort_seed

    ids = [f"00000000-0000-0000-0000-{n:012d}" for n in (1, 2, 3)]
    seed = build_event_creation_cohort_seed(signals=[{"signal_id": ids[0]}, {"signal_id": ids[1]}],
        relations=[{"signal_relation_id": ids[2], "source_signal_id": ids[0], "target_signal_id": ids[1],
            "matcher_result": {"gate": "eligible", "decision": "auto_linked", "merge_allowed": True, "relation": "refines"}}])
    state = {"transaction": False, "commits": 0, "rollbacks": 0, "insertions": 0}

    class Cursor:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def execute(self, query, params=None):
            assert state["transaction"]
            if "insert into" in query.lower():
                state["insertions"] += 1
                if failure and state["insertions"] == 3: raise RuntimeError("membership failure")
        def fetchone(self): return {"id": ids[2]}

    class Connection:
        @contextmanager
        def transaction(self):
            state["transaction"] = True
            try:
                yield
            except Exception:
                state["rollbacks"] += 1
                raise
            else:
                state["commits"] += 1
            finally:
                state["transaction"] = False
        def cursor(self): return Cursor()

    @contextmanager
    def connection(): yield Connection()

    repository = EventMatchingRepository("postgresql://unused", event_creation_writes_enabled=True)
    repository.connection = connection
    def validate(cur, **kwargs):
        assert state["transaction"]
        return {"status": "ready_to_create", "event_seed": seed, "event_code": seed["event_code"],
            "memberships": [{"signal_id": identifier, "relation_to_event": "supports",
                "match_score": None, "match_decision": "auto_linked", "rationale": {}} for identifier in ids[:2]]}
    repository._validate_event_creation_cohort = validate
    if failure:
        with pytest.raises(RuntimeError, match="membership failure"):
            repository.persist_event_creation_cohort(event_seed=seed, dry_run=False)
        assert state["rollbacks"] == 1
        assert state["commits"] == 0
    else:
        result = repository.persist_event_creation_cohort(event_seed=seed, dry_run=False)
        assert result["status"] == "created"
        assert result["dry_run"] is False
        assert state["commits"] == 1
    assert state["insertions"] == 3
