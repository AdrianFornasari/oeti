import pytest


@pytest.mark.parametrize("changed_field", [
    None, "event_code", "title", "priority", "source_relation",
    "event_creation_version", "event_start_date", "first_signal_at",
    "pathogen_id", "disease_id", "domains_present", "lifecycle_status",
    "review_status", "evidence_confidence", "cross_sector_convergence",
    "contradictions_present", "source_relations", "matcher_version",
    "strong_event_context_anchors", "missing_title", "missing_signal",
    "conflicting_pathogens",
    "context_direct", "context_inherited", "context_target_missing",
    "context_source_missing", "context_raw_missing", "context_reset",
    "context_fabricated_excerpt", "context_summary_only", "context_extra_anchor",
    "context_without_override",
    "membership_manual_linked", "membership_manual_unlinked",
    "membership_linked_by", "membership_other_event",
    "membership_resolved", "membership_closed", "membership_unknown",
    "membership_same_active", "membership_same_monitoring",
    "membership_other_without_target", "membership_other_closed",
    "membership_closed_empty", "membership_resolved_empty",
    "existing_identical", "existing_title_changed", "existing_missing_member",
    "existing_extra_member", "existing_audit_changed", "existing_score_changed",
    "existing_review_changed", "existing_date_changed", "existing_relation_changed",
    "existing_producer_changed", "existing_missing_audit", "existing_timezone_equivalent",
    "audit_missing_policy", "audit_old_matcher", "audit_old_resolver",
    "policy_missing_coverage", "policy_low_coverage_no_override",
])
def test_cohort_reconstructs_seed_from_persisted_data(changed_field):
    from contextlib import contextmanager
    from onehealth_worker.evaluation.event_creation_v049 import build_event_creation_cohort_seed

    a, b, relation_id = [f"00000000-0000-0000-0000-{number:012d}" for number in (1, 2, 3)]
    signals = [
        {"signal_id": a, "pathogen_canonical_name": "Andes virus", "domains": ["human"], "occurred_start": "2026-05-02"},
        {"signal_id": b, "pathogen_canonical_name": "Andes virus", "domains": ["human"], "observed_at": "2026-05-04T18:06:44+00:00"},
    ]
    rationale = {"gate": "eligible", "decision": "auto_linked", "merge_allowed": True,
        "matcher_version": "0.4.8", "policy_version": "0.4.9", "context_resolver_version": "0.4.9", "information_coverage": 0.8}
    policy_case = changed_field and changed_field.startswith("policy_")
    if changed_field == "policy_missing_coverage": del rationale["information_coverage"]
    elif changed_field == "policy_low_coverage_no_override": rationale["information_coverage"] = 0.15
    audit_case = changed_field and changed_field.startswith("audit_")
    if changed_field == "audit_missing_policy": del rationale["policy_version"]
    elif changed_field == "audit_old_matcher": rationale["matcher_version"] = "0.4.7"
    elif changed_field == "audit_old_resolver": rationale["context_resolver_version"] = "0.4.8"
    context_case = changed_field and changed_field.startswith("context_")
    if context_case:
        rationale.update({
            "information_coverage": 0.15,
            "matcher_version": "0.4.8", "policy_version": "0.4.9",
            "context_resolver_version": "0.4.9",
            "auto_link_guard_override_reason": "shared_strong_event_context_anchor",
            "shared_event_context_anchors": ["vessel:mv hondius"],
        })
        for signal in signals:
            signal["raw_text"] = "Se investiga el brote en el buque MV Hondius."
            signal["evidence"] = [{"text": signal["raw_text"]}]
        if changed_field == "context_inherited":
            signals[1]["raw_text"] += "\n\nLos casos siguen en estudio."
            signals[1]["evidence"] = [{"text": "Los casos siguen en estudio."}]
        elif changed_field in {"context_target_missing", "context_source_missing"}:
            signal = signals[0 if changed_field == "context_source_missing" else 1]
            signal["raw_text"] = "Otro episodio independiente."
            signal["evidence"] = [{"text": signal["raw_text"]}]
        elif changed_field == "context_raw_missing":
            signals[1]["raw_text"] = None
        elif changed_field == "context_reset":
            signals[1]["raw_text"] += "\n\nA nivel nacional, los casos siguen en estudio."
            signals[1]["evidence"] = [{"text": "A nivel nacional, los casos siguen en estudio."}]
        elif changed_field == "context_fabricated_excerpt":
            signals[1]["raw_text"] = "Otro episodio independiente."
        elif changed_field == "context_summary_only":
            signals[1]["signal_summary"] = signals[1]["raw_text"]
            signals[1]["evidence"] = []
        elif changed_field == "context_extra_anchor":
            rationale["shared_event_context_anchors"].append("vessel:otro barco")
        elif changed_field == "context_without_override":
            del rationale["auto_link_guard_override_reason"]
            signals[1]["raw_text"] = None
    relation = {"id": relation_id, "source_signal_id": a, "target_signal_id": b, "relation": "refines", "hard_conflict": False, "rationale": rationale}
    seed = build_event_creation_cohort_seed(
        signals=signals,
        relations=[{"signal_relation_id": relation_id, "source_signal_id": a, "target_signal_id": b, "matcher_result": {**rationale, "relation": "refines", "hard_conflict": False}}],
        strong_event_context_anchors=rationale.get("shared_event_context_anchors", []),
    )
    if changed_field == "missing_title":
        del seed["title"]
    elif changed_field == "conflicting_pathogens":
        signals[0]["pathogen_id"] = a
        signals[1]["pathogen_id"] = b
    elif changed_field and changed_field != "missing_signal" and not context_case and not audit_case and not policy_case and not changed_field.startswith(("membership_", "existing_")):
        seed[changed_field] = "tampered"
    # Input and database ordering must not affect reconstruction.
    seed["source_signal_ids"].reverse()

    membership_case = changed_field and changed_field.startswith("membership_")
    target_event = None
    memberships = []
    existing_case = changed_field and changed_field.startswith("existing_")
    if existing_case:
        from copy import deepcopy
        target_event = {**seed, "id": relation_id, "summary": None, "reviewed_by": None, "reviewed_at": None}
        audit = {
            "producer": "oeti_event_creation", "event_code": seed["event_code"],
            "source_signal_ids": sorted([a, b]), "source_relation_ids": [relation_id],
            "strong_event_context_anchors": [], "matcher_version": "0.4.8",
            "event_creation_version": "0.4.9",
            "source_relation_audit": [{"signal_relation_id": relation_id,
                "matcher_version": "0.4.8", "policy_version": "0.4.9", "context_resolver_version": "0.4.9"}],
        }
        memberships = [{"event_id": relation_id, "signal_id": identifier,
            "relation_to_event": "supports", "match_score": None,
            "match_decision": "auto_linked", "linked_by": None,
            "rationale": deepcopy(audit)} for identifier in (b, a)]
        if changed_field == "existing_title_changed": target_event["title"] = "changed"
        elif changed_field == "existing_missing_member": memberships.pop()
        elif changed_field == "existing_extra_member": memberships.append({**memberships[0], "signal_id": relation_id})
        elif changed_field == "existing_audit_changed": memberships[0]["rationale"]["event_creation_version"] = "0.4.8"
        elif changed_field == "existing_score_changed": memberships[0]["match_score"] = 0.9
        elif changed_field == "existing_review_changed": target_event["reviewed_by"] = b
        elif changed_field == "existing_date_changed": target_event["event_start_date"] = "2026-05-03"
        elif changed_field == "existing_relation_changed": memberships[0]["relation_to_event"] = "refines"
        elif changed_field == "existing_producer_changed": memberships[0]["rationale"]["producer"] = "another"
        elif changed_field == "existing_missing_audit": memberships[0]["rationale"] = {}
        elif changed_field == "existing_timezone_equivalent": target_event["first_signal_at"] = "2026-05-04T15:06:44-03:00"
    if membership_case:
        target_event = {"id": relation_id, "lifecycle_status": "active"}
        membership = {
            "event_id": relation_id, "signal_id": a,
            "lifecycle_status": "active", "match_decision": "auto_linked",
            "linked_by": None,
        }
        if changed_field in {"membership_manual_linked", "membership_manual_unlinked"}:
            membership["match_decision"] = changed_field.removeprefix("membership_")
        elif changed_field == "membership_linked_by":
            membership["linked_by"] = b
        elif changed_field == "membership_other_event":
            membership["event_id"] = b
        elif changed_field in {"membership_resolved", "membership_closed", "membership_unknown", "membership_same_monitoring"}:
            lifecycle = changed_field.removeprefix("membership_").removeprefix("same_")
            target_event["lifecycle_status"] = None if lifecycle == "unknown" else lifecycle
            membership["lifecycle_status"] = target_event["lifecycle_status"]
        memberships = [membership]
        if changed_field == "membership_other_without_target":
            target_event = None
        elif changed_field == "membership_other_closed":
            membership["event_id"] = b
            membership["lifecycle_status"] = "closed"
        elif changed_field in {"membership_closed_empty", "membership_resolved_empty"}:
            target_event["lifecycle_status"] = changed_field.split("_")[1]
            memberships = []

    class Cursor:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def execute(self, query, params=None):
            self.sql = " ".join(query.lower().split())
            assert self.sql.startswith("select ")
        def fetchall(self):
            if "from public.event_signals" in self.sql: return memberships
            if "from public.signal_relations" in self.sql: return [relation]
            if "as signal_id" in self.sql:
                return signals[:1] if changed_field == "missing_signal" else list(reversed(signals))
            return [{"id": a}, {"id": b}]
        def fetchone(self):
            assert "from public.events" in self.sql
            return target_event

    class Connection:
        def cursor(self): return Cursor()

    @contextmanager
    def connection(): yield Connection()

    repository = EventMatchingRepository("postgresql://unused")
    repository.connection = connection
    if changed_field and changed_field not in {"context_direct", "context_inherited", "existing_identical", "existing_timezone_equivalent"}:
        result = repository.persist_event_creation_cohort(event_seed=seed)
        assert result["status"] == "blocked"
        if policy_case:
            assert result["reason"] == "invalid_matcher_policy"
        elif audit_case:
            assert result["reason"] == ("invalid_context_versions" if changed_field == "audit_missing_policy" else "incompatible_context_versions")
        elif existing_case:
            assert result["reason"] == ("existing_event_mismatch" if changed_field in {"existing_title_changed", "existing_review_changed", "existing_date_changed"} else "existing_membership_mismatch")
        elif membership_case:
            if changed_field in {"membership_manual_linked", "membership_manual_unlinked", "membership_linked_by"}:
                assert result["reason"] == "manual_membership_conflict"
            elif changed_field in {"membership_other_event", "membership_other_without_target", "membership_other_closed"}:
                assert result["reason"] == "other_event_membership_conflict"
            elif changed_field in {"membership_same_active", "membership_same_monitoring"}:
                assert result["reason"] == "existing_event_mismatch"
            else:
                assert result["reason"] == "event_lifecycle_blocked"
        elif context_case:
            assert result["reason"] == "unsupported_context_anchors"
            assert result["invalid_relation_ids"] == [relation_id]
        elif changed_field == "missing_signal":
            assert result["reason"] == "incomplete_seed_signals"
        elif changed_field == "conflicting_pathogens":
            assert result["reason"] == "invalid_persisted_event_seed"
        else:
            assert result["reason"] == "event_seed_mismatch"
            assert result["mismatched_fields"] == ["title" if changed_field == "missing_title" else changed_field]
    else:
        result = repository.persist_event_creation_cohort(event_seed=seed)
        assert result["status"] == ("already_exists" if existing_case else "ready_to_create")
        assert result["dry_run"] is True
        assert result["event_seed"]["event_code"] == seed["event_code"]
        assert len(result["memberships"]) == 2

from onehealth_worker.evaluation.event_matching_repository_v049 import (
    EventMatchingRepository,
)


def test_cohort_persistence_exposes_dry_run_contract():
    import inspect

    repository = EventMatchingRepository(
        "postgresql://unused"
    )

    method = getattr(
        repository,
        "persist_event_creation_cohort",
        None,
    )

    assert callable(method)

    signature = inspect.signature(method)

    assert "event_seed" in signature.parameters
    assert "dry_run" in signature.parameters

    assert (
        signature.parameters["dry_run"].default
        is True
    )



def test_persisted_relation_preserves_context_audit():
    from contextlib import contextmanager
    from uuid import UUID

    signal_a = UUID("00000000-0000-0000-0000-000000000001")
    signal_b = UUID("00000000-0000-0000-0000-000000000002")
    relation_id = UUID("00000000-0000-0000-0000-000000000003")

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params):
            assert "public.signal_relations" in str(query)
            assert str(params[0]) == str(relation_id)

        def fetchone(self):
            return {
                "id": relation_id,
                "source_signal_id": signal_a,
                "target_signal_id": signal_b,
                "relation": "refines",
                "score": 0.85,
                "hard_conflict": False,
                "rationale": {
                    "producer": "oeti_event_matcher",
                    "matcher_version": "0.4.8",
                    "gate": "eligible",
                    "decision": "auto_linked",
                    "merge_allowed": True,
                    "base_decision": "review_required",
                    "policy_version": "0.4.9",
                    "context_resolver_version": "0.4.9",
                    "auto_link_guard_override_reason":
                        "shared_strong_event_context_anchor",
                    "shared_event_context_anchors": [
                        "vessel:mv hondius"
                    ],
                },
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
    repository.connection = fake_connection

    result = (
        repository.load_persisted_matcher_relation_by_id(
            str(relation_id)
        )
    )

    assert result["matcher_result"]["base_decision"] == (
        "review_required"
    )
    assert result["matcher_result"]["policy_version"] == (
        "0.4.9"
    )
    assert result["matcher_result"][
        "context_resolver_version"
    ] == "0.4.9"
    assert result["matcher_result"][
        "auto_link_guard_override_reason"
    ] == "shared_strong_event_context_anchor"
    assert result["matcher_result"][
        "shared_event_context_anchors"
    ] == ["vessel:mv hondius"]



def test_cohort_dry_run_queries_db_without_writes():
    from contextlib import contextmanager

    signal_a = "00000000-0000-0000-0000-000000000001"
    signal_b = "00000000-0000-0000-0000-000000000002"
    relation_id = "00000000-0000-0000-0000-000000000003"

    seed = {
        "event_code": "OETI-EVT-TEST",
        "source_signal_ids": [signal_a, signal_b],
        "source_relation_ids": [relation_id],
    }

    class FakeCursor:
        def __init__(self):
            self.queries = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params=None):
            sql = " ".join(str(query).lower().split())
            self.queries.append(sql)

            if sql.startswith(
                ("insert ", "update ", "delete ", "truncate ")
            ):
                raise AssertionError(
                    "Dry-run attempted a database write."
                )

        def fetchone(self):
            return None

        def fetchall(self):
            return []

    cursor = FakeCursor()

    class FakeConnection:
        def cursor(self):
            return cursor

        def commit(self):
            raise AssertionError(
                "Dry-run must not explicitly commit."
            )

    @contextmanager
    def fake_connection():
        yield FakeConnection()

    repository = EventMatchingRepository(
        "postgresql://unused"
    )
    repository.connection = fake_connection

    result = repository.persist_event_creation_cohort(
        event_seed=seed,
        dry_run=True,
    )

    assert isinstance(result, dict)
    assert result["status"] == "blocked"
    assert result["dry_run"] is True
    assert cursor.queries
    assert all(
        query.startswith("select ")
        for query in cursor.queries
    )



def test_cohort_dry_run_blocks_missing_relations():
    from contextlib import contextmanager
    from uuid import UUID

    signal_a = "00000000-0000-0000-0000-000000000001"
    signal_b = "00000000-0000-0000-0000-000000000002"
    relation_id = "00000000-0000-0000-0000-000000000003"

    class FakeCursor:
        def __init__(self):
            self.query = ""
            self.queries = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params=None):
            self.query = " ".join(
                str(query).lower().split()
            )
            self.queries.append(self.query)

            assert self.query.startswith("select ")

        def fetchall(self):
            if "from public.signals" in self.query:
                return [
                    {"id": UUID(signal_a)},
                    {"id": UUID(signal_b)},
                ]

            if "from public.signal_relations" in self.query:
                return []

            return []

        def fetchone(self):
            return None

    cursor = FakeCursor()

    class FakeConnection:
        def cursor(self):
            return cursor

        def commit(self):
            raise AssertionError(
                "Dry-run must not explicitly commit."
            )

    @contextmanager
    def fake_connection():
        yield FakeConnection()

    repository = EventMatchingRepository(
        "postgresql://unused"
    )
    repository.connection = fake_connection

    seed = {
        "event_code": "OETI-EVT-TEST",
        "source_signal_ids": [signal_a, signal_b],
        "source_relation_ids": [relation_id],
    }

    result = repository.persist_event_creation_cohort(
        event_seed=seed,
        dry_run=True,
    )

    assert result["status"] == "blocked"
    assert result["dry_run"] is True
    assert relation_id in result["missing_relation_ids"]

    assert any(
        "from public.signal_relations" in query
        for query in cursor.queries
    )



def test_cohort_dry_run_blocks_non_autolinked_relation():
    from contextlib import contextmanager
    from uuid import UUID

    signal_a = "00000000-0000-0000-0000-000000000001"
    signal_b = "00000000-0000-0000-0000-000000000002"
    relation_id = "00000000-0000-0000-0000-000000000003"

    class FakeCursor:
        def __init__(self):
            self.query = ""
            self.queries = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params=None):
            self.query = " ".join(str(query).lower().split())
            self.queries.append(self.query)
            assert self.query.startswith("select ")

        def fetchall(self):
            if "from public.signals" in self.query:
                return [
                    {"id": UUID(signal_a)},
                    {"id": UUID(signal_b)},
                ]

            if "from public.signal_relations" in self.query:
                return [{
                    "id": UUID(relation_id),
                    "source_signal_id": UUID(signal_a),
                    "target_signal_id": UUID(signal_b),
                    "relation": "refines",
                    "hard_conflict": False,
                    "rationale": {
                        "producer": "oeti_event_matcher",
                        "gate": "eligible",
                        "decision": "review_required",
                        "merge_allowed": False,
                    },
                }]

            return []

        def fetchone(self):
            return None

    cursor = FakeCursor()

    class FakeConnection:
        def cursor(self):
            return cursor

        def commit(self):
            raise AssertionError("Dry-run must not commit.")

    @contextmanager
    def fake_connection():
        yield FakeConnection()

    repository = EventMatchingRepository("postgresql://unused")
    repository.connection = fake_connection

    result = repository.persist_event_creation_cohort(
        event_seed={
            "event_code": "OETI-EVT-TEST",
            "source_signal_ids": [signal_a, signal_b],
            "source_relation_ids": [relation_id],
        },
        dry_run=True,
    )

    assert result["status"] == "blocked"
    assert result["reason"] == "invalid_matcher_relations"
    assert relation_id in result["invalid_relation_ids"]
    assert any(
        "from public.signal_relations" in query
        for query in cursor.queries
    )



@pytest.mark.parametrize(
    (
        "persisted_anchors, matcher_version, "
        "policy_version, context_resolver_version, "
        "expected_reason"
    ),
    [
        (
            [], "0.4.8", "0.4.9", "0.4.9",
            "invalid_context_override",
        ),
        (
            ["vessel:otro barco"], "0.4.8", "0.4.9",
            "0.4.9", "context_anchor_mismatch",
        ),
        (
            ["vessel:mv hondius"], "0.4.8", None,
            "0.4.9", "invalid_context_versions",
        ),
        (
            ["vessel:mv hondius"], None, "0.4.9",
            "0.4.9", "invalid_context_versions",
        ),
        (
            ["vessel:mv hondius"], "0.4.8", "0.4.9",
            None, "invalid_context_versions",
        ),
        (
            ["vessel:mv hondius"], "0.4.7", "0.4.9",
            "0.4.9", "incompatible_context_versions",
        ),
        (
            ["vessel:mv hondius"], "0.4.8", "0.4.8",
            "0.4.9", "incompatible_context_versions",
        ),
        (
            ["vessel:mv hondius"], "0.4.8", "0.4.9",
            "0.4.8", "incompatible_context_versions",
        ),
    ],
)
def test_cohort_dry_run_blocks_missing_context_override(
    persisted_anchors,
    matcher_version,
    policy_version,
    context_resolver_version,
    expected_reason,
):
    from contextlib import contextmanager
    from uuid import UUID

    signal_a = "00000000-0000-0000-0000-000000000001"
    signal_b = "00000000-0000-0000-0000-000000000002"
    relation_id = "00000000-0000-0000-0000-000000000003"

    class FakeCursor:
        def __init__(self):
            self.query = ""

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params=None):
            self.query = " ".join(
                str(query).lower().split()
            )
            assert self.query.startswith("select ")

        def fetchall(self):
            if "from public.signals" in self.query:
                return [
                    {"id": UUID(signal_a)},
                    {"id": UUID(signal_b)},
                ]

            if "from public.signal_relations" in self.query:
                return [{
                    "id": UUID(relation_id),
                    "source_signal_id": UUID(signal_a),
                    "target_signal_id": UUID(signal_b),
                    "relation": "refines",
                    "hard_conflict": False,
                    "rationale": {
                        "producer": "oeti_event_matcher",
                        "matcher_version": matcher_version,
                        "gate": "eligible",
                        "decision": "auto_linked",
                        "merge_allowed": True,
                        "policy_version": policy_version,
                        "context_resolver_version": context_resolver_version,
                        "auto_link_guard_override_reason":
                            "shared_strong_event_context_anchor",
                        "shared_event_context_anchors": persisted_anchors,
                    },
                }]

            return []

        def fetchone(self):
            return None

    cursor = FakeCursor()

    class FakeConnection:
        def cursor(self):
            return cursor

        def commit(self):
            raise AssertionError(
                "Dry-run must not commit."
            )

    @contextmanager
    def fake_connection():
        yield FakeConnection()

    repository = EventMatchingRepository(
        "postgresql://unused"
    )
    repository.connection = fake_connection

    result = repository.persist_event_creation_cohort(
        event_seed={
            "event_code": "OETI-EVT-TEST",
            "source_signal_ids": [signal_a, signal_b],
            "source_relation_ids": [relation_id],
            "strong_event_context_anchors": [
                "vessel:mv hondius"
            ],
        },
        dry_run=True,
    )

    assert result["status"] == "blocked"
    assert result["reason"] == expected_reason
    assert relation_id in result["invalid_relation_ids"]
