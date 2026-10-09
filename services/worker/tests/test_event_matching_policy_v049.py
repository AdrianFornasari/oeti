from onehealth_worker.evaluation.event_matching_policy_v049 import (
    MIN_AUTO_LINK_INFORMATION_COVERAGE,
    apply_v049_auto_link_guard,
)


def _auto_link(
    *,
    coverage: float,
) -> dict:
    return {
        "decision": "auto_linked",
        "relation": "refines",
        "score": 0.96,
        "information_coverage": coverage,
        "merge_allowed": True,
    }


def test_low_coverage_auto_link_requires_review():
    result = apply_v049_auto_link_guard(
        _auto_link(
            coverage=0.25,
        )
    )

    assert (
        result["decision"]
        == "review_required"
    )

    assert (
        result["base_decision"]
        == "auto_linked"
    )

    assert (
        result[
            "auto_link_guard_reason"
        ]
        == "insufficient_information_coverage"
    )


def test_sufficient_coverage_auto_link_is_preserved():
    result = apply_v049_auto_link_guard(
        _auto_link(
            coverage=0.60,
        )
    )

    assert (
        MIN_AUTO_LINK_INFORMATION_COVERAGE
        == 0.50
    )

    assert (
        result["decision"]
        == "auto_linked"
    )

    assert (
        result[
            "auto_link_guard_reason"
        ]
        is None
    )


def test_existing_review_decision_is_unchanged():
    result = apply_v049_auto_link_guard(
        {
            "decision": "review_required",
            "relation": "supports",
            "score": 0.95,
            "information_coverage": 0.10,
            "merge_allowed": False,
        }
    )

    assert (
        result["decision"]
        == "review_required"
    )

    assert (
        result["base_decision"]
        == "review_required"
    )


def test_shared_strong_vessel_anchor_preserves_low_coverage_auto_link():
    result = apply_v049_auto_link_guard(
        _auto_link(
            coverage=0.25,
        ),
        source_context_anchors=(
            "vessel:mv hondius",
        ),
        target_context_anchors=(
            "vessel:mv hondius",
        ),
    )

    assert (
        result["decision"]
        == "auto_linked"
    )

    assert (
        result[
            "auto_link_guard_reason"
        ]
        is None
    )

    assert (
        result[
            "auto_link_guard_override_reason"
        ]
        == "shared_strong_event_context_anchor"
    )

    assert (
        result[
            "shared_event_context_anchors"
        ]
        == ["vessel:mv hondius"]
    )


def test_different_vessels_do_not_override_low_coverage_guard():
    result = apply_v049_auto_link_guard(
        _auto_link(
            coverage=0.25,
        ),
        source_context_anchors=(
            "vessel:mv hondius",
        ),
        target_context_anchors=(
            "vessel:mv ortelius",
        ),
    )

    assert (
        result["decision"]
        == "review_required"
    )

    assert (
        result[
            "auto_link_guard_reason"
        ]
        == "insufficient_information_coverage"
    )


def test_non_strong_shared_context_does_not_override_guard():
    result = apply_v049_auto_link_guard(
        _auto_link(
            coverage=0.25,
        ),
        source_context_anchors=(
            "country:argentina",
        ),
        target_context_anchors=(
            "country:argentina",
        ),
    )

    assert (
        result["decision"]
        == "review_required"
    )

    assert (
        result[
            "auto_link_guard_reason"
        ]
        == "insufficient_information_coverage"
    )
