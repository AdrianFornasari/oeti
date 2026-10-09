import pytest

from onehealth_worker.evaluation.event_creation_v049 import (
    build_event_creation_seed,
    deterministic_event_code,
)


A = (
    "11111111-1111-1111-1111-111111111111"
)

B = (
    "22222222-2222-2222-2222-222222222222"
)

DISEASE = (
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)

PATHOGEN = (
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
)


def _signal(
    signal_id,
    **overrides,
):
    result = {
        "signal_id":
            signal_id,
        "disease_id":
            DISEASE,
        "disease_canonical_name":
            "Hantavirus disease",
        "pathogen_id":
            PATHOGEN,
        "pathogen_canonical_name":
            "Andes virus",
        "domains": [
            "human",
        ],
        "occurred_start":
            "2026-05-12",
        "observed_at":
            "2026-05-12T12:00:00+00:00",
    }

    result.update(
        overrides
    )

    return result


def _matcher(
    **overrides,
):
    result = {
        "gate": "eligible",
        "relation": "refines",
        "decision": "auto_linked",
        "merge_allowed": True,
        "hard_conflict": False,
    }

    result.update(
        overrides
    )

    return result


def test_event_code_is_order_invariant():
    assert (
        deterministic_event_code(
            A,
            B,
        )
        == deterministic_event_code(
            B,
            A,
        )
    )


def test_event_seed_is_order_invariant():
    first = build_event_creation_seed(
        source_signal=_signal(
            A,
            domains=[
                "human",
            ],
            occurred_start=
                "2026-05-12",
        ),
        target_signal=_signal(
            B,
            domains=[
                "genomic",
                "human",
            ],
            occurred_start=
                "2026-05-04",
        ),
        matcher_result=_matcher(),
    )

    second = build_event_creation_seed(
        source_signal=_signal(
            B,
            domains=[
                "genomic",
                "human",
            ],
            occurred_start=
                "2026-05-04",
        ),
        target_signal=_signal(
            A,
            domains=[
                "human",
            ],
            occurred_start=
                "2026-05-12",
        ),
        matcher_result=_matcher(),
    )

    assert first == second

    assert (
        first["event_start_date"]
        == "2026-05-04"
    )

    assert first[
        "domains_present"
    ] == [
        "genomic",
        "human",
    ]


def test_event_seed_uses_known_catalog_id_when_other_is_missing():
    seed = build_event_creation_seed(
        source_signal=_signal(
            A,
        ),
        target_signal=_signal(
            B,
            disease_id=None,
            pathogen_id=None,
        ),
        matcher_result=_matcher(),
    )

    assert (
        seed["disease_id"]
        == DISEASE
    )

    assert (
        seed["pathogen_id"]
        == PATHOGEN
    )


def test_event_seed_rejects_conflicting_disease_ids():
    with pytest.raises(
        ValueError,
        match="disease_id",
    ):
        build_event_creation_seed(
            source_signal=_signal(
                A,
            ),
            target_signal=_signal(
                B,
                disease_id=(
                    "cccccccc-cccc-cccc-cccc-cccccccccccc"
                ),
            ),
            matcher_result=_matcher(),
        )


def test_event_seed_rejects_conflicting_pathogen_ids():
    with pytest.raises(
        ValueError,
        match="pathogen_id",
    ):
        build_event_creation_seed(
            source_signal=_signal(
                A,
            ),
            target_signal=_signal(
                B,
                pathogen_id=(
                    "cccccccc-cccc-cccc-cccc-cccccccccccc"
                ),
            ),
            matcher_result=_matcher(),
        )


def test_event_seed_requires_auto_link():
    with pytest.raises(
        ValueError,
        match="auto_linked",
    ):
        build_event_creation_seed(
            source_signal=_signal(
                A,
            ),
            target_signal=_signal(
                B,
            ),
            matcher_result=_matcher(
                relation="supports",
                decision="review_required",
                merge_allowed=False,
            ),
        )


def test_event_seed_blocks_hard_conflict():
    with pytest.raises(
        ValueError,
        match="Hard conflict",
    ):
        build_event_creation_seed(
            source_signal=_signal(
                A,
            ),
            target_signal=_signal(
                B,
            ),
            matcher_result=_matcher(
                relation="contradicts",
                decision="rejected",
                merge_allowed=False,
                hard_conflict=True,
            ),
        )


def test_event_seed_has_conservative_initial_state():
    seed = build_event_creation_seed(
        source_signal=_signal(
            A,
        ),
        target_signal=_signal(
            B,
        ),
        matcher_result=_matcher(),
    )

    assert (
        seed["title"]
        == "Hantavirus disease - emerging event"
    )

    assert (
        seed["lifecycle_status"]
        == "active"
    )

    assert (
        seed["priority"]
        == "P3"
    )

    assert (
        seed["evidence_confidence"]
        == "low"
    )

    assert (
        seed[
            "cross_sector_convergence"
        ]
        == "none"
    )

    assert (
        seed[
            "contradictions_present"
        ]
        is False
    )

    assert (
        seed["review_status"]
        == "pending"
    )
