from __future__ import annotations

from datetime import date
from decimal import Decimal

from onehealth_worker.evaluation.event_matching_repository_v049 import (
    build_matcher_signal_payload,
)
from onehealth_worker.evaluation.event_matching_v048 import (
    detect_hard_conflict,
)


def _base_row(**overrides):
    row = {
        "signal_id":
            "11111111-1111-1111-1111-111111111111",
        "local_signal_key":
            "signal-01",
        "schema_version":
            "0.2",
        "signal_role":
            "primary_event",
        "signal_type":
            "outbreak",
        "signal_summary":
            "Brote de hantavirus.",
        "verification_status":
            "confirmed",
        "event_matching_eligible":
            True,
        "is_current":
            True,
        "domains":
            ["human", "genomic"],
        "extraction_confidence":
            Decimal("0.910"),
        "disease_verbatim":
            "hantavirus",
        "disease_canonical_name":
            "Hantavirus disease",
        "disease_normalization_status":
            "resolved",
        "disease_confidence":
            Decimal("0.820"),
        "pathogen_verbatim":
            "virus Andes",
        "pathogen_canonical_name":
            "Andes virus",
        "pathogen_normalization_status":
            "resolved",
        "pathogen_confidence":
            Decimal("0.900"),
        "occurred_start":
            date(2026, 5, 12),
        "occurred_end":
            date(2026, 5, 13),
        "date_precision":
            "day",
        "reference_period": {
            "start": {
                "date": "2026-05-12"
            },
            "end": {
                "date": "2026-05-13"
            },
        },
        "transmission": {
            "human_to_human":
                "unknown",
            "animal_to_human":
                "unknown",
            "vector_borne":
                "unknown",
        },
        "locations": [
            {
                "country_iso2": "AR",
                "country": "Argentina",
                "admin1": "NeuquÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©n",
                "admin2": None,
                "locality": None,
                "region": None,
                "precision": "admin1",
                "role": "event_location",
                "confidence": 0.9,
            }
        ],
        "hosts": [
            {
                "verbatim": "Humano",
                "canonical_name":
                    "Homo sapiens",
                "host_type": "human",
                "confidence": 1.0,
            }
        ],
        "metrics": [
            {
                "name": "confirmed_cases",
                "value_numeric": 8,
                "value_text": None,
                "unit": "cases",
            }
        ],
        "evidence": [
            {
                "type": "text",
                "text":
                    "Se confirmaron ocho casos.",
                "location_in_document":
                    None,
                "page_number": None,
            }
        ],
        "diagnostics": {
            "test_reported": True,
            "test_type": "PCR",
            "method": "RT-PCR",
            "target": "hantavirus",
            "specimen": None,
            "result": "positive",
        },
        "genomics": {
            "sequence_reported": True,
            "accession": None,
            "lineage": None,
            "clade": None,
            "test_result": "positive",
        },
    }

    row.update(overrides)

    return row


def test_v049_db_adapter_reconstructs_matcher_payload():
    payload = build_matcher_signal_payload(
        _base_row()
    )

    assert (
        payload["database_signal_id"]
        == "11111111-1111-1111-1111-111111111111"
    )

    assert (
        payload["local_signal_id"]
        == "signal-01"
    )

    assert (
        payload["event_date"]["start"]
        == "2026-05-12"
    )

    assert (
        payload["event_date"]["end"]
        == "2026-05-13"
    )

    assert (
        payload[
            "pathogen"
        ][
            "canonical_name"
        ]
        == "Andes virus"
    )

    assert (
        payload["locations"][0]["role"]
        == "event_location"
    )

    assert (
        payload["hosts"][0]["host_type"]
        == "human"
    )

    assert (
        payload["diagnostics"]["result"]
        == "positive"
    )

    assert (
        payload["genomics"][
            "sequence_reported"
        ]
        is True
    )

    assert (
        payload["extraction_confidence"]
        == 0.91
    )


def test_v049_db_adapter_uses_safe_defaults_for_optional_children():
    payload = build_matcher_signal_payload(
        _base_row(
            locations=None,
            hosts=None,
            metrics=None,
            evidence=None,
            diagnostics=None,
            genomics=None,
            reference_period=None,
            transmission=None,
        )
    )

    assert payload["locations"] == []
    assert payload["hosts"] == []
    assert payload["metrics"] == []
    assert payload["evidence"] == []

    assert (
        payload["diagnostics"]["result"]
        == "unknown"
    )

    assert (
        payload["diagnostics"][
            "test_reported"
        ]
        is False
    )

    assert (
        payload["genomics"][
            "sequence_reported"
        ]
        is False
    )

    assert (
        payload["transmission"]
        == {}
    )

    assert (
        payload["reference_period"]
        == {}
    )


def test_v049_db_adapter_preserves_genomic_hard_conflict_semantics():
    human = build_matcher_signal_payload(
        _base_row(
            signal_id=
                "22222222-2222-2222-2222-222222222222",
            local_signal_key=
                "human-genomic",
            signal_role=
                "primary_event",
            signal_type=
                "genomic_observation",
            signal_summary=
                "Secuencia del brote humano.",
            transmission={
                "human_to_human":
                    "unknown",
                "animal_to_human":
                    "unknown",
                "vector_borne":
                    "unknown",
            },
            genomics={
                "sequence_reported": True,
                "test_result": "positive",
            },
        )
    )

    wildlife = build_matcher_signal_payload(
        _base_row(
            signal_id=
                "33333333-3333-3333-3333-333333333333",
            local_signal_key=
                "wildlife-negative",
            signal_role=
                "negative_evidence",
            signal_type=
                "transmission_observation",
            signal_summary=(
                "La variante detectada en "
                "roedores es diferente de la "
                "del brote humano."
            ),
            verification_status=
                "refuted",
            transmission={
                "human_to_human":
                    "unknown",
                "animal_to_human":
                    "refuted",
                "vector_borne":
                    "unknown",
            },
            evidence=[
                {
                    "type": "text",
                    "text": (
                        "La secuencia es "
                        "diferente de la "
                        "observada en el brote."
                    ),
                }
            ],
            genomics={
                "sequence_reported": True,
                "test_result": "positive",
            },
        )
    )

    result = detect_hard_conflict(
        human,
        wildlife,
        {
            "explicit_genomic_incompatibility":
                True,
            "explicit_official_non_relation":
                True,
            "explicit_source_refutation":
                True,
        },
    )

    assert result["hard_conflict"] is True

    assert (
        result["reason"]
        == "explicit_genomic_incompatibility"
    )

def test_v049_canonical_pair_is_order_independent():
    from onehealth_worker.evaluation.event_matching_repository_v049 import (
        canonical_signal_pair,
    )

    a = "11111111-1111-1111-1111-111111111111"
    b = "22222222-2222-2222-2222-222222222222"

    assert (
        canonical_signal_pair(
            a,
            b,
        )
        == canonical_signal_pair(
            b,
            a,
        )
    )

    assert (
        canonical_signal_pair(
            b,
            a,
        )
        == (
            a,
            b,
        )
    )


def test_v049_canonical_pair_rejects_self_pair():
    import pytest

    from onehealth_worker.evaluation.event_matching_repository_v049 import (
        canonical_signal_pair,
    )

    signal_id = (
        "11111111-1111-1111-1111-111111111111"
    )

    with pytest.raises(
        ValueError,
        match="consigo misma",
    ):
        canonical_signal_pair(
            signal_id,
            signal_id,
        )


def test_v049_candidate_limit_is_validated_before_database_access():
    import pytest

    from onehealth_worker.evaluation.event_matching_repository_v049 import (
        EventMatchingRepository,
    )

    repository = EventMatchingRepository(
        "postgresql://unused"
    )

    with pytest.raises(
        ValueError,
        match="max_candidates",
    ):
        repository.load_candidate_signal_refs(
            "11111111-1111-1111-1111-111111111111",
            max_candidates=0,
        )

    with pytest.raises(
        ValueError,
        match="max_candidates",
    ):
        repository.load_candidate_signal_refs(
            "11111111-1111-1111-1111-111111111111",
            max_candidates=5001,
        )


def test_v049_candidate_selection_is_high_recall_and_deterministic():
    from contextlib import contextmanager
    from datetime import date
    from uuid import UUID

    from onehealth_worker.evaluation.event_matching_repository_v049 import (
        EventMatchingRepository,
    )

    anchor_id = UUID(
        "11111111-1111-1111-1111-111111111111"
    )

    candidate_a = UUID(
        "22222222-2222-2222-2222-222222222222"
    )

    candidate_b = UUID(
        "33333333-3333-3333-3333-333333333333"
    )

    disease_id = UUID(
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    )

    pathogen_id = UUID(
        "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    )

    class FakeCursor:
        def __init__(self):
            self.execute_calls = []
            self._phase = 0

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
            self.execute_calls.append(
                (
                    str(query),
                    params,
                )
            )
            self._phase += 1

        def fetchone(self):
            assert self._phase == 1

            return {
                "id": anchor_id,
                "disease_id": disease_id,
                "pathogen_id": pathogen_id,
                "occurred_start":
                    date(2026, 5, 12),
                "occurred_end":
                    date(2026, 5, 13),
            }

        def fetchall(self):
            assert self._phase == 2

            return [
                {
                    "signal_id":
                        candidate_a,
                    "same_disease":
                        True,
                    "same_pathogen":
                        True,
                    "temporal_distance_days":
                        7,
                },
                {
                    "signal_id":
                        candidate_b,
                    "same_disease":
                        False,
                    "same_pathogen":
                        False,
                    "temporal_distance_days":
                        48,
                },
            ]

    fake_cursor = FakeCursor()

    class FakeConnection:
        def cursor(self):
            return fake_cursor

    @contextmanager
    def fake_connection():
        yield FakeConnection()

    repository = EventMatchingRepository(
        "postgresql://unused"
    )

    repository.connection = (
        fake_connection
    )

    candidates = (
        repository.load_candidate_signal_refs(
            str(anchor_id),
            max_candidates=25,
        )
    )

    assert [
        item.signal_id
        for item in candidates
    ] == [
        str(candidate_a),
        str(candidate_b),
    ]

    assert (
        candidates[0].same_pathogen
        is True
    )

    assert (
        candidates[0].same_disease
        is True
    )

    assert (
        candidates[0].temporal_distance_days
        == 7
    )

    assert (
        candidates[1].same_pathogen
        is False
    )

    assert (
        candidates[1].same_disease
        is False
    )

    assert len(
        fake_cursor.execute_calls
    ) == 2

    candidate_query, candidate_params = (
        fake_cursor.execute_calls[1]
    )

    normalized_query = (
        " ".join(
            candidate_query.split()
        )
    )

    assert (
        "candidate.event_matching_eligible = true"
        in normalized_query
    )

    assert (
        "candidate.is_current = true"
        in normalized_query
    )

    assert (
        "candidate.id <> anchor.signal_id"
        in normalized_query
    )

    # No disease/pathogen/time predicate is permitted
    # in WHERE: those dimensions only rank candidates.
    where_clause = (
        normalized_query
        .split(" where ", 1)[1]
        .split(" order by ", 1)[0]
    )

    assert (
        "candidate.disease_id ="
        not in where_clause
    )

    assert (
        "candidate.pathogen_id ="
        not in where_clause
    )

    assert (
        "occurred_start >"
        not in where_clause
    )

    assert (
        candidate_params[-1]
        == 25
    )

def _v049_matcher_manifest():
    return {
        "benchmark_version": "0.4.8",
        "eligibility": {
            "eligible_signal_roles": [
                "primary_event",
                "negative_evidence",
            ],
            "ineligible_signal_roles": [
                "background_context",
                "surveillance_baseline",
            ],
            "ineligible_signal_types": [
                "official_alert",
            ],
            "short_circuit_ineligible": True,
        },
        "scoring": {
            "weights": {
                "etiology": 0.35,
                "geography": 0.25,
                "temporality": 0.15,
                "host": 0.10,
                "epidemiology": 0.10,
                "shared_context": 0.05,
            },
            "thresholds": {
                "auto_link_min": 0.80,
                "review_min": 0.60,
            },
        },
        "hard_conflict_policy": {
            "explicit_genomic_incompatibility":
                True,
            "explicit_official_non_relation":
                True,
            "explicit_source_refutation":
                True,
            "host_difference_alone":
                False,
            "domain_difference_alone":
                False,
            "geographic_difference_alone":
                False,
        },
    }


def test_v049_orchestrator_returns_empty_result_without_candidates():
    from onehealth_worker.evaluation.event_matching_orchestrator_v049 import (
        EventMatchingOrchestrator,
    )
    from onehealth_worker.evaluation.event_matching_repository_v049 import (
        PersistedMatcherSignal,
    )

    anchor_id = (
        "11111111-1111-1111-1111-111111111111"
    )

    class FakeRepository:
        def load_signal_for_matching(
            self,
            signal_id,
        ):
            assert signal_id == anchor_id

            return PersistedMatcherSignal(
                signal_id=anchor_id,
                payload=(
                    build_matcher_signal_payload(
                        _base_row()
                    )
                ),
            )

        def load_candidate_signal_refs(
            self,
            signal_id,
            *,
            max_candidates,
        ):
            assert signal_id == anchor_id
            assert max_candidates == 50
            return []

    orchestrator = (
        EventMatchingOrchestrator(
            FakeRepository(),
            _v049_matcher_manifest(),
        )
    )

    report = orchestrator.evaluate_anchor(
        anchor_id,
        max_candidates=50,
    )

    assert report["mode"] == "read_only"
    assert report["candidate_count"] == 0
    assert report["evaluated_pairs"] == 0
    assert report["results"] == []

    assert report["summary"] == {
        "auto_linked": 0,
        "review_required": 0,
        "rejected": 0,
        "ineligible": 0,
        "hard_conflicts": 0,
    }


def test_v049_orchestrator_uses_canonical_pair_orientation(
    monkeypatch,
):
    import onehealth_worker.evaluation.event_matching_orchestrator_v049 as module

    from onehealth_worker.evaluation.event_matching_repository_v049 import (
        CandidateSignalRef,
        PersistedMatcherSignal,
    )

    high_id = (
        "ffffffff-ffff-ffff-ffff-ffffffffffff"
    )

    low_id = (
        "11111111-1111-1111-1111-111111111111"
    )

    high_payload = (
        build_matcher_signal_payload(
            _base_row(
                signal_id=high_id,
                local_signal_key="high",
            )
        )
    )

    low_payload = (
        build_matcher_signal_payload(
            _base_row(
                signal_id=low_id,
                local_signal_key="low",
            )
        )
    )

    class FakeRepository:
        def load_signal_for_matching(
            self,
            signal_id,
        ):
            if signal_id == high_id:
                return PersistedMatcherSignal(
                    signal_id=high_id,
                    payload=high_payload,
                )

            if signal_id == low_id:
                return PersistedMatcherSignal(
                    signal_id=low_id,
                    payload=low_payload,
                )

            raise AssertionError(signal_id)

        def load_candidate_signal_refs(
            self,
            signal_id,
            *,
            max_candidates,
        ):
            assert signal_id == high_id

            return [
                CandidateSignalRef(
                    signal_id=low_id,
                    same_disease=True,
                    same_pathogen=True,
                    temporal_distance_days=0,
                )
            ]

    seen = {}

    def fake_evaluate(
        source,
        target,
        manifest,
    ):
        seen["source"] = source[
            "database_signal_id"
        ]
        seen["target"] = target[
            "database_signal_id"
        ]

        return {
            "gate": "eligible",
            "relation": "refines",
            "decision": "auto_linked",
            "merge_allowed": True,
            "hard_conflict": False,
            "hard_conflict_reason": None,
            "score": 1.0,
        }

    monkeypatch.setattr(
        module,
        "evaluate_signal_pair_v048",
        fake_evaluate,
    )

    orchestrator = (
        module.EventMatchingOrchestrator(
            FakeRepository(),
            _v049_matcher_manifest(),
        )
    )

    report = orchestrator.evaluate_anchor(
        high_id
    )

    assert seen == {
        "source": low_id,
        "target": high_id,
    }

    pair = report["results"][0]

    assert (
        pair["source_signal_id"]
        == low_id
    )

    assert (
        pair["target_signal_id"]
        == high_id
    )

    assert (
        pair["anchor_signal_id"]
        == high_id
    )

    assert (
        pair["candidate_signal_id"]
        == low_id
    )


def test_v049_orchestrator_preserves_candidate_ranking_metadata(
    monkeypatch,
):
    import onehealth_worker.evaluation.event_matching_orchestrator_v049 as module

    from onehealth_worker.evaluation.event_matching_repository_v049 import (
        CandidateSignalRef,
        PersistedMatcherSignal,
    )

    anchor_id = (
        "11111111-1111-1111-1111-111111111111"
    )

    candidate_id = (
        "22222222-2222-2222-2222-222222222222"
    )

    class FakeRepository:
        def load_signal_for_matching(
            self,
            signal_id,
        ):
            return PersistedMatcherSignal(
                signal_id=signal_id,
                payload=(
                    build_matcher_signal_payload(
                        _base_row(
                            signal_id=signal_id
                        )
                    )
                ),
            )

        def load_candidate_signal_refs(
            self,
            signal_id,
            *,
            max_candidates,
        ):
            return [
                CandidateSignalRef(
                    signal_id=candidate_id,
                    same_disease=False,
                    same_pathogen=True,
                    temporal_distance_days=42,
                )
            ]

    monkeypatch.setattr(
        module,
        "evaluate_signal_pair_v048",
        lambda source, target, manifest: {
            "gate": "eligible",
            "relation": "supports",
            "decision":
                "review_required",
            "merge_allowed": False,
            "hard_conflict": False,
            "hard_conflict_reason": None,
            "score": 0.7,
        },
    )

    report = (
        module.EventMatchingOrchestrator(
            FakeRepository(),
            _v049_matcher_manifest(),
        ).evaluate_anchor(
            anchor_id
        )
    )

    item = report["results"][0]

    assert (
        item["candidate_rank"]
        == 1
    )

    assert item[
        "candidate_prefilter"
    ] == {
        "same_disease": False,
        "same_pathogen": True,
        "temporal_distance_days": 42,
    }

    assert (
        report["summary"][
            "review_required"
        ]
        == 1
    )


def test_v049_orchestrator_integrates_with_real_v048_matcher():
    from onehealth_worker.evaluation.event_matching_orchestrator_v049 import (
        EventMatchingOrchestrator,
    )
    from onehealth_worker.evaluation.event_matching_repository_v049 import (
        CandidateSignalRef,
        PersistedMatcherSignal,
    )

    anchor_id = (
        "11111111-1111-1111-1111-111111111111"
    )

    candidate_id = (
        "22222222-2222-2222-2222-222222222222"
    )

    anchor_payload = (
        build_matcher_signal_payload(
            _base_row(
                signal_id=anchor_id,
                local_signal_key=
                    "outbreak-week-1",
                signal_type="outbreak",
                occurred_start=
                    date(2026, 5, 12),
                occurred_end=
                    date(2026, 5, 12),
            )
        )
    )

    candidate_payload = (
        build_matcher_signal_payload(
            _base_row(
                signal_id=candidate_id,
                local_signal_key=
                    "outbreak-week-2",
                signal_type="outbreak",
                occurred_start=
                    date(2026, 5, 19),
                occurred_end=
                    date(2026, 5, 19),
            )
        )
    )

    class FakeRepository:
        def load_signal_for_matching(
            self,
            signal_id,
        ):
            if signal_id == anchor_id:
                return PersistedMatcherSignal(
                    signal_id=anchor_id,
                    payload=anchor_payload,
                )

            return PersistedMatcherSignal(
                signal_id=candidate_id,
                payload=candidate_payload,
            )

        def load_candidate_signal_refs(
            self,
            signal_id,
            *,
            max_candidates,
        ):
            return [
                CandidateSignalRef(
                    signal_id=candidate_id,
                    same_disease=True,
                    same_pathogen=True,
                    temporal_distance_days=7,
                )
            ]

    report = (
        EventMatchingOrchestrator(
            FakeRepository(),
            _v049_matcher_manifest(),
        ).evaluate_anchor(
            anchor_id
        )
    )

    result = report[
        "results"
    ][0][
        "matcher_result"
    ]

    assert (
        result["gate"]
        == "eligible"
    )

    assert (
        result["relation"]
        == "refines"
    )

    assert (
        result["decision"]
        == "auto_linked"
    )

    assert (
        result["merge_allowed"]
        is True
    )

    assert (
        report["summary"][
            "auto_linked"
        ]
        == 1
    )

def _v049_persistable_result(
    **overrides,
):
    result = {
        "eligible": True,
        "gate": "eligible",
        "relation": "refines",
        "decision": "auto_linked",
        "merge_allowed": True,
        "hard_conflict": False,
        "hard_conflict_reason": None,
        "score": 0.912345,
        "information_coverage": 0.85,
        "component_scores": {
            "etiology": 1.0,
            "geography": 0.8,
            "temporality": 0.9,
        },
    }

    result.update(overrides)

    return result


def test_v049_relation_persistence_rejects_ineligible_result():
    import pytest

    from onehealth_worker.evaluation.event_matching_repository_v049 import (
        EventMatchingRepository,
    )

    repository = EventMatchingRepository(
        "postgresql://unused"
    )

    with pytest.raises(
        ValueError,
        match="elegibles",
    ):
        repository.persist_matcher_relation(
            source_signal_id=(
                "11111111-1111-1111-1111-111111111111"
            ),
            target_signal_id=(
                "22222222-2222-2222-2222-222222222222"
            ),
            matcher_result=(
                _v049_persistable_result(
                    gate="ineligible",
                    relation=None,
                    decision=None,
                )
            ),
        )


def test_v049_relation_persistence_inserts_new_matcher_pair():
    from contextlib import contextmanager
    from uuid import UUID

    from onehealth_worker.evaluation.event_matching_repository_v049 import (
        EventMatchingRepository,
    )

    source_id = (
        "11111111-1111-1111-1111-111111111111"
    )

    target_id = (
        "22222222-2222-2222-2222-222222222222"
    )

    relation_id = UUID(
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    )

    class FakeCursor:
        def __init__(self):
            self.calls = []
            self.fetchone_results = [
                None,
                {
                    "id": relation_id,
                },
            ]
            self.fetchall_results = [
                [],
            ]

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
            self.calls.append(
                (
                    " ".join(
                        str(query).split()
                    ),
                    params,
                )
            )

        def fetchone(self):
            return self.fetchone_results.pop(0)

        def fetchall(self):
            return self.fetchall_results.pop(0)

    cursor = FakeCursor()

    class FakeConnection:
        def __init__(self):
            self.committed = False

        def cursor(self):
            return cursor

        def commit(self):
            self.committed = True

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
        repository.persist_matcher_relation(
            source_signal_id=target_id,
            target_signal_id=source_id,
            matcher_result=(
                _v049_persistable_result()
            ),
            candidate_prefilter={
                "same_disease": True,
                "same_pathogen": True,
                "temporal_distance_days": 7,
            },
        )
    )

    assert result["action"] == "inserted"

    assert (
        result["source_signal_id"]
        == source_id
    )

    assert (
        result["target_signal_id"]
        == target_id
    )

    assert (
        result["score"]
        == 0.912345
    )

    assert connection.committed is True

    insert_calls = [
        call
        for call in cursor.calls
        if call[0].startswith(
            "insert into public.signal_relations"
        )
    ]

    assert len(insert_calls) == 1

    insert_params = insert_calls[0][1]

    assert insert_params[0] == source_id
    assert insert_params[1] == target_id
    assert insert_params[2] == "refines"

    import json

    rationale = json.loads(
        insert_params[5]
    )

    assert (
        rationale["producer"]
        == "oeti_event_matcher"
    )

    assert (
        rationale["matcher_version"]
        == "0.4.8"
    )

    assert (
        rationale["raw_score"]
        == 0.912345
    )

    assert (
        rationale[
            "candidate_prefilter"
        ][
            "temporal_distance_days"
        ]
        == 7
    )


def test_v049_relation_persistence_updates_existing_matcher_pair():
    from contextlib import contextmanager
    from uuid import UUID

    from onehealth_worker.evaluation.event_matching_repository_v049 import (
        EventMatchingRepository,
    )

    source_id = (
        "11111111-1111-1111-1111-111111111111"
    )

    target_id = (
        "22222222-2222-2222-2222-222222222222"
    )

    relation_id = UUID(
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    )

    class FakeCursor:
        def __init__(self):
            self.calls = []
            self.fetchone_results = [
                None,
                {
                    "id": relation_id,
                },
            ]
            self.fetchall_results = [
                [
                    {
                        "id": relation_id,
                        "relation": "supports",
                    }
                ]
            ]

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
            self.calls.append(
                (
                    " ".join(
                        str(query).split()
                    ),
                    params,
                )
            )

        def fetchone(self):
            return self.fetchone_results.pop(0)

        def fetchall(self):
            return self.fetchall_results.pop(0)

    cursor = FakeCursor()

    class FakeConnection:
        def __init__(self):
            self.committed = False

        def cursor(self):
            return cursor

        def commit(self):
            self.committed = True

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
        repository.persist_matcher_relation(
            source_signal_id=source_id,
            target_signal_id=target_id,
            matcher_result=(
                _v049_persistable_result(
                    relation="contradicts",
                    decision="rejected",
                    merge_allowed=False,
                    hard_conflict=True,
                    hard_conflict_reason=(
                        "explicit_source_refutation"
                    ),
                    score=0.41,
                )
            ),
        )
    )

    assert result["action"] == "updated"

    assert (
        result["relation"]
        == "contradicts"
    )

    assert (
        result["hard_conflict"]
        is True
    )

    assert connection.committed is True

    update_calls = [
        call
        for call in cursor.calls
        if call[0].startswith(
            "update public.signal_relations"
        )
    ]

    assert len(update_calls) == 1

    assert (
        update_calls[0][1][0]
        == "contradicts"
    )


def test_v049_relation_persistence_protects_foreign_relation():
    from contextlib import contextmanager
    from uuid import UUID

    import pytest

    from onehealth_worker.evaluation.event_matching_repository_v049 import (
        EventMatchingRepository,
    )

    class FakeCursor:
        def __init__(self):
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
            self.calls.append(
                (
                    str(query),
                    params,
                )
            )

        def fetchone(self):
            return {
                "id": UUID(
                    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
                )
            }

    cursor = FakeCursor()

    class FakeConnection:
        def cursor(self):
            return cursor

        def commit(self):
            raise AssertionError(
                "No debe hacer commit."
            )

    @contextmanager
    def fake_connection():
        yield FakeConnection()

    repository = EventMatchingRepository(
        "postgresql://unused"
    )

    repository.connection = (
        fake_connection
    )

    with pytest.raises(
        ValueError,
        match="otro productor",
    ):
        repository.persist_matcher_relation(
            source_signal_id=(
                "11111111-1111-1111-1111-111111111111"
            ),
            target_signal_id=(
                "22222222-2222-2222-2222-222222222222"
            ),
            matcher_result=(
                _v049_persistable_result()
            ),
        )

    assert not any(
        "insert into public.signal_relations"
        in query.lower()
        for query, _params
        in cursor.calls
    )

def test_v049_batch_persistence_commits_once():
    from contextlib import contextmanager
    from uuid import UUID

    from onehealth_worker.evaluation.event_matching_repository_v049 import (
        EventMatchingRepository,
    )

    ids = iter(
        [
            UUID(
                "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"
            ),
            UUID(
                "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2"
            ),
        ]
    )

    class FakeCursor:
        def __init__(self):
            self.last_query = ""
            self.inserted_ids = []

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
            self.last_query = (
                " ".join(
                    str(query).split()
                )
            )

        def fetchone(self):
            if self.last_query.startswith(
                "select id from public.signal_relations"
            ):
                return None

            if self.last_query.startswith(
                "insert into public.signal_relations"
            ):
                value = next(ids)
                self.inserted_ids.append(
                    value
                )
                return {
                    "id": value,
                }

            raise AssertionError(
                self.last_query
            )

        def fetchall(self):
            assert self.last_query.startswith(
                "select id, relation::text as relation"
            )
            return []

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

    items = [
        {
            "source_signal_id":
                "11111111-1111-1111-1111-111111111111",
            "target_signal_id":
                "22222222-2222-2222-2222-222222222222",
            "matcher_result":
                _v049_persistable_result(),
            "candidate_prefilter": {},
        },
        {
            "source_signal_id":
                "11111111-1111-1111-1111-111111111111",
            "target_signal_id":
                "33333333-3333-3333-3333-333333333333",
            "matcher_result":
                _v049_persistable_result(
                    relation="supports",
                    decision="review_required",
                    merge_allowed=False,
                    score=0.72,
                ),
            "candidate_prefilter": {},
        },
    ]

    persisted = (
        repository.persist_matcher_relations_batch(
            items
        )
    )

    assert len(persisted) == 2

    assert [
        item["action"]
        for item in persisted
    ] == [
        "inserted",
        "inserted",
    ]

    assert (
        connection.commit_count
        == 1
    )


def test_v049_batch_rejects_duplicate_canonical_pair_before_db():
    import pytest

    from onehealth_worker.evaluation.event_matching_repository_v049 import (
        EventMatchingRepository,
    )

    repository = EventMatchingRepository(
        "postgresql://unused"
    )

    a = (
        "11111111-1111-1111-1111-111111111111"
    )

    b = (
        "22222222-2222-2222-2222-222222222222"
    )

    items = [
        {
            "source_signal_id": a,
            "target_signal_id": b,
            "matcher_result":
                _v049_persistable_result(),
        },
        {
            "source_signal_id": b,
            "target_signal_id": a,
            "matcher_result":
                _v049_persistable_result(),
        },
    ]

    with pytest.raises(
        ValueError,
        match="par canónico",
    ):
        repository.persist_matcher_relations_batch(
            items
        )


def test_v049_batch_foreign_conflict_aborts_without_commit():
    from contextlib import contextmanager
    from uuid import UUID

    import pytest

    from onehealth_worker.evaluation.event_matching_repository_v049 import (
        EventMatchingRepository,
    )

    class FakeCursor:
        def __init__(self):
            self.last_query = ""
            self.foreign_checks = 0

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
            self.last_query = (
                " ".join(
                    str(query).split()
                )
            )

        def fetchone(self):
            if self.last_query.startswith(
                "select id from public.signal_relations"
            ):
                self.foreign_checks += 1

                if self.foreign_checks == 2:
                    return {
                        "id": UUID(
                            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
                        )
                    }

                return None

            if self.last_query.startswith(
                "insert into public.signal_relations"
            ):
                return {
                    "id": UUID(
                        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
                    )
                }

            raise AssertionError(
                self.last_query
            )

        def fetchall(self):
            return []

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

    items = [
        {
            "source_signal_id":
                "11111111-1111-1111-1111-111111111111",
            "target_signal_id":
                "22222222-2222-2222-2222-222222222222",
            "matcher_result":
                _v049_persistable_result(),
        },
        {
            "source_signal_id":
                "11111111-1111-1111-1111-111111111111",
            "target_signal_id":
                "33333333-3333-3333-3333-333333333333",
            "matcher_result":
                _v049_persistable_result(),
        },
    ]

    with pytest.raises(
        ValueError,
        match="batch fue abortado",
    ):
        repository.persist_matcher_relations_batch(
            items
        )

    assert (
        connection.commit_count
        == 0
    )


def test_v049_orchestrator_persist_mode_writes_one_atomic_batch(
    monkeypatch,
):
    import onehealth_worker.evaluation.event_matching_orchestrator_v049 as module

    from onehealth_worker.evaluation.event_matching_repository_v049 import (
        CandidateSignalRef,
        PersistedMatcherSignal,
    )

    anchor_id = (
        "11111111-1111-1111-1111-111111111111"
    )

    candidate_ids = [
        "22222222-2222-2222-2222-222222222222",
        "33333333-3333-3333-3333-333333333333",
    ]

    class FakeRepository:
        def __init__(self):
            self.batch_calls = []

        def load_signal_for_matching(
            self,
            signal_id,
        ):
            return PersistedMatcherSignal(
                signal_id=signal_id,
                payload=(
                    build_matcher_signal_payload(
                        _base_row(
                            signal_id=signal_id,
                            local_signal_key=
                                signal_id,
                        )
                    )
                ),
            )

        def load_candidate_signal_refs(
            self,
            signal_id,
            *,
            max_candidates,
        ):
            return [
                CandidateSignalRef(
                    signal_id=candidate_ids[0],
                    same_disease=True,
                    same_pathogen=True,
                    temporal_distance_days=7,
                ),
                CandidateSignalRef(
                    signal_id=candidate_ids[1],
                    same_disease=True,
                    same_pathogen=False,
                    temporal_distance_days=14,
                ),
            ]

        def persist_matcher_relations_batch(
            self,
            items,
            *,
            matcher_version,
        ):
            self.batch_calls.append(
                (
                    items,
                    matcher_version,
                )
            )

            return [
                {
                    "action": "inserted",
                    "signal_relation_id": "r1",
                },
                {
                    "action": "updated",
                    "signal_relation_id": "r2",
                },
            ]

    repository = FakeRepository()

    monkeypatch.setattr(
        module,
        "evaluate_signal_pair_v048",
        lambda source, target, manifest: (
            _v049_persistable_result()
        ),
    )

    report = (
        module.EventMatchingOrchestrator(
            repository,
            _v049_matcher_manifest(),
        ).evaluate_anchor(
            anchor_id,
            persist=True,
        )
    )

    assert (
        report["mode"]
        == "persist"
    )

    assert len(
        repository.batch_calls
    ) == 1

    batch, matcher_version = (
        repository.batch_calls[0]
    )

    assert len(batch) == 2

    assert (
        matcher_version
        == "0.4.8"
    )

    assert report[
        "persistence"
    ] == {
        "requested": True,
        "persistable_pairs": 2,
        "persisted_pairs": 2,
        "inserted": 1,
        "updated": 1,
        "skipped_ineligible": 0,
    }
