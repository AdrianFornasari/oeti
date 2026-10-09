from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping


POLICY_VERSION = "0.4.9"

MIN_AUTO_LINK_INFORMATION_COVERAGE = 0.50

_STRONG_EVENT_CONTEXT_PREFIXES = (
    "vessel:",
)


def _normalize_context_anchors(
    anchors: Iterable[str] | None,
) -> set[str]:
    if anchors is None:
        return set()

    return {
        value.strip().casefold()
        for value in anchors
        if (
            isinstance(value, str)
            and value.strip()
        )
    }


def _shared_strong_context_anchors(
    source_context_anchors: Iterable[str] | None,
    target_context_anchors: Iterable[str] | None,
) -> tuple[str, ...]:
    source = _normalize_context_anchors(
        source_context_anchors
    )

    target = _normalize_context_anchors(
        target_context_anchors
    )

    shared = source & target

    strong = {
        anchor
        for anchor in shared
        if anchor.startswith(
            _STRONG_EVENT_CONTEXT_PREFIXES
        )
    }

    return tuple(
        sorted(strong)
    )


def apply_v049_auto_link_guard(
    matcher_result: Mapping[str, Any],
    *,
    source_context_anchors: Iterable[str] | None = None,
    target_context_anchors: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Apply the production v0.4.9 auto-link safety guard.

    Score and information coverage describe different properties.

    A high normalized compatibility score based on insufficient
    observed information cannot normally authorize an automatic
    event link.

    Exception:
    a low-coverage auto-link may remain automatic when both signals
    resolve to the same strong event-context anchor.

    Strong anchors are intentionally conservative. v0.4.9 initially
    supports named vessels because this behavior has been demonstrated
    against real longitudinal production data.
    """

    result = deepcopy(
        dict(matcher_result)
    )

    result[
        "base_decision"
    ] = result.get(
        "decision"
    )

    result[
        "policy_version"
    ] = POLICY_VERSION

    result[
        "auto_link_guard_reason"
    ] = None

    result[
        "auto_link_guard_override_reason"
    ] = None

    if (
        result.get("decision")
        != "auto_linked"
    ):
        return result

    coverage = result.get(
        "information_coverage"
    )

    if not isinstance(
        coverage,
        (int, float),
    ):
        result[
            "decision"
        ] = "review_required"

        result[
            "auto_link_guard_reason"
        ] = (
            "information_coverage_unavailable"
        )

        return result

    if (
        float(coverage)
        >= MIN_AUTO_LINK_INFORMATION_COVERAGE
    ):
        return result

    shared_anchors = (
        _shared_strong_context_anchors(
            source_context_anchors,
            target_context_anchors,
        )
    )

    if shared_anchors:
        result[
            "auto_link_guard_override_reason"
        ] = (
            "shared_strong_event_context_anchor"
        )

        result[
            "shared_event_context_anchors"
        ] = list(
            shared_anchors
        )

        return result

    result[
        "decision"
    ] = "review_required"

    result[
        "auto_link_guard_reason"
    ] = (
        "insufficient_information_coverage"
    )

    return result
