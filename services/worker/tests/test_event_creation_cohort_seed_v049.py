import pytest

from onehealth_worker.evaluation.event_creation_v049 import (
    build_event_creation_cohort_seed,
    deterministic_cohort_event_code,
)


def _signal(
    signal_id,
    *,
    disease_id=None,
    disease_name=None,
    pathogen_id=None,
    pathogen_name=None,
    occurred_start=None,
    observed_at=None,
):
    return {
        "signal_id": signal_id,
        "disease_id": disease_id,
        "disease_canonical_name": disease_name,
        "pathogen_id": pathogen_id,
        "pathogen_canonical_name": pathogen_name,
        "domains": [],
        "occurred_start": occurred_start,
        "observed_at": observed_at,
    }


def _relation(
    relation_id,
    source,
    target,
    *,
    relation="refines",
    decision="auto_linked",
    merge_allowed=True,
    hard_conflict=False,
):
    return {
        "signal_relation_id": relation_id,
        "source_signal_id": source,
        "target_signal_id": target,
        "matcher_result": {
            "gate": "eligible",
            "relation": relation,
            "decision": decision,
            "merge_allowed": merge_allowed,
            "hard_conflict": hard_conflict,
        },
    }


def test_cohort_event_code_is_order_invariant():
    first = deterministic_cohort_event_code(
        ["c", "a", "b"]
    )

    second = deterministic_cohort_event_code(
        ["b", "c", "a"]
    )

    assert first == second


def test_cohort_seed_consolidates_dates_and_pathogen():
    signals = [
        _signal(
            "a",
            occurred_start="2026-05-02",
            observed_at="2026-05-04T18:06:44+00:00",
        ),
        _signal(
            "b",
            observed_at="2026-05-12T20:30:05+00:00",
        ),
        _signal(
            "c",
            occurred_start="2026-05-02",
            observed_at="2026-05-04T18:06:44+00:00",
        ),
        _signal(
            "d",
            observed_at="2026-05-04T18:06:44+00:00",
        ),
        _signal(
            "e",
            pathogen_id="pathogen-andes",
            pathogen_name="Andes virus",
            observed_at="2026-05-12T20:30:05+00:00",
        ),
    ]

    relations = [
        _relation(
            "r1",
            "a",
            "b",
        ),
        _relation(
            "r2",
            "b",
            "c",
        ),
        _relation(
            "r3",
            "d",
            "e",
        ),
    ]

    seed = build_event_creation_cohort_seed(
        signals=signals,
        relations=relations,
        strong_event_context_anchors=[
            "vessel:mv hondius"
        ],
    )

    assert seed["event_start_date"] == (
        "2026-05-02"
    )

    assert seed["first_signal_at"] == (
        "2026-05-04T18:06:44+00:00"
    )

    assert seed["disease_id"] is None

    assert seed["pathogen_id"] == (
        "pathogen-andes"
    )

    assert seed["title"] == (
        "Andes virus - emerging event"
    )

    assert len(
        seed["source_signal_ids"]
    ) == 5

    assert len(
        seed["source_relation_ids"]
    ) == 3

    assert seed[
        "strong_event_context_anchors"
    ] == [
        "vessel:mv hondius"
    ]


def test_cohort_seed_rejects_conflicting_pathogen_ids():
    signals = [
        _signal(
            "a",
            pathogen_id="p1",
        ),
        _signal(
            "b",
            pathogen_id="p2",
        ),
    ]

    relations = [
        _relation(
            "r1",
            "a",
            "b",
        )
    ]

    with pytest.raises(
        ValueError,
        match="pathogen_id",
    ):
        build_event_creation_cohort_seed(
            signals=signals,
            relations=relations,
        )


def test_cohort_seed_rejects_review_required_relation():
    signals = [
        _signal("a"),
        _signal("b"),
    ]

    relations = [
        _relation(
            "r1",
            "a",
            "b",
            decision="review_required",
        )
    ]

    with pytest.raises(
        ValueError,
        match="auto_linked",
    ):
        build_event_creation_cohort_seed(
            signals=signals,
            relations=relations,
        )


def test_cohort_seed_rejects_uncovered_signal():
    signals = [
        _signal("a"),
        _signal("b"),
        _signal("c"),
    ]

    relations = [
        _relation(
            "r1",
            "a",
            "b",
        )
    ]

    with pytest.raises(
        ValueError,
        match="Every signal",
    ):
        build_event_creation_cohort_seed(
            signals=signals,
            relations=relations,
        )


def test_cohort_seed_is_order_invariant():
    signals = [
        _signal(
            "a",
            occurred_start="2026-05-02",
            observed_at="2026-05-04T18:06:44+00:00",
        ),
        _signal(
            "b",
            pathogen_id="p-andes",
            pathogen_name="Andes virus",
            observed_at="2026-05-12T20:30:05+00:00",
        ),
        _signal(
            "c",
            observed_at="2026-05-04T18:06:44+00:00",
        ),
    ]

    relations = [
        _relation(
            "r1",
            "a",
            "b",
        ),
        _relation(
            "r2",
            "b",
            "c",
        ),
    ]

    first = build_event_creation_cohort_seed(
        signals=signals,
        relations=relations,
        strong_event_context_anchors=[
            "vessel:mv hondius"
        ],
    )

    second = build_event_creation_cohort_seed(
        signals=list(
            reversed(signals)
        ),
        relations=list(
            reversed(relations)
        ),
        strong_event_context_anchors=[
            "vessel:mv hondius"
        ],
    )

    assert first == second
