from onehealth_worker.evaluation.event_creation_cohort_v049 import (
    build_event_creation_cohorts,
)


def _relation(
    relation_id,
    source,
    target,
    *,
    score=0.9,
    anchors=(),
    decision="auto_linked",
    merge_allowed=True,
    hard_conflict=False,
):
    return {
        "signal_relation_id": relation_id,
        "source_signal_id": source,
        "target_signal_id": target,
        "matcher_result": {
            "decision": decision,
            "merge_allowed": merge_allowed,
            "hard_conflict": hard_conflict,
            "score": score,
            "shared_event_context_anchors": list(
                anchors
            ),
        },
    }


def test_shared_signal_builds_one_cohort():
    cohorts = build_event_creation_cohorts(
        [
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
    )

    assert len(cohorts) == 1
    assert cohorts[0]["signal_ids"] == [
        "a",
        "b",
        "c",
    ]


def test_disconnected_pairs_join_through_strong_anchor():
    cohorts = build_event_creation_cohorts(
        [
            _relation(
                "r1",
                "a",
                "b",
                anchors=(
                    "vessel:mv hondius",
                ),
            ),
            _relation(
                "r2",
                "c",
                "d",
                anchors=(
                    "vessel:mv hondius",
                ),
            ),
        ]
    )

    assert len(cohorts) == 1
    assert cohorts[0]["signal_count"] == 4

    assert cohorts[0][
        "strong_event_context_anchors"
    ] == [
        "vessel:mv hondius"
    ]


def test_different_strong_anchors_remain_separate():
    cohorts = build_event_creation_cohorts(
        [
            _relation(
                "r1",
                "a",
                "b",
                anchors=(
                    "vessel:mv hondius",
                ),
            ),
            _relation(
                "r2",
                "c",
                "d",
                anchors=(
                    "vessel:mv ortelius",
                ),
            ),
        ]
    )

    assert len(cohorts) == 2


def test_non_auto_linked_relations_do_not_create_cohort():
    cohorts = build_event_creation_cohorts(
        [
            _relation(
                "r1",
                "a",
                "b",
                decision=(
                    "review_required"
                ),
            )
        ]
    )

    assert cohorts == []


def test_highest_score_relation_is_deterministic_seed():
    cohorts = build_event_creation_cohorts(
        [
            _relation(
                "r-low",
                "a",
                "b",
                score=0.83,
                anchors=(
                    "vessel:mv hondius",
                ),
            ),
            _relation(
                "r-high",
                "c",
                "d",
                score=0.967,
                anchors=(
                    "vessel:mv hondius",
                ),
            ),
        ]
    )

    assert len(cohorts) == 1

    assert (
        cohorts[0][
            "seed_relation_id"
        ]
        == "r-high"
    )
