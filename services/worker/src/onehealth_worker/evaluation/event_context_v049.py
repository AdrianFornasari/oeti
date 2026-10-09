from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


CONTEXT_RESOLVER_VERSION = "0.4.9"


_VESSEL_NAME_RE = re.compile(
    r"\b(?i:buque|crucero|embarcaci[o?]n)\s+"
    r"(?P<name>"
    r"(?:(?:MV|M/V|M\.V\.)\s+)?"
    r"[A-Z??????][\w.-]*"
    r"(?:\s+[A-Z??????][\w.-]*){0,3}"
    r")"
)

_MV_NAME_RE = re.compile(
    r"\b(?P<name>"
    r"(?:MV|M/V|M\.V\.)\s+"
    r"[A-Z??????][\w.-]*"
    r"(?:\s+[A-Z??????][\w.-]*){0,3}"
    r")"
)

_CONTEXT_RESET_PREFIXES = (
    "a nivel nacional",
    "por otro lado",
)

_ANAPHORIC_EVENT_MARKERS = (
    "el brote",
    "del brote",
    "este brote",
    "los casos",
    "estos casos",
    "del crucero",
    "a bordo del crucero",
    "del buque",
    "a bordo del buque",
    "la embarcacion",
    "la embarcaci?n",
    "investigacion epidemiologica",
    "investigaci?n epidemiol?gica",
)


def _normalize_anchor_name(
    value: str,
) -> str:
    value = re.sub(
        r"\s+",
        " ",
        value.strip(),
    )

    value = value.rstrip(
        ".,;:!?)]}"
    )

    value = value.replace(
        "M/V ",
        "MV ",
    ).replace(
        "M.V. ",
        "MV ",
    )

    return value.casefold()


def extract_event_context_anchors(
    text: str,
) -> tuple[str, ...]:
    """Extract explicit event anchors from text.

    v0.4.9 initially supports named vessels because this is the
    first production context demonstrated by longitudinal data.
    """

    anchors: set[str] = set()

    for regex in (
        _VESSEL_NAME_RE,
        _MV_NAME_RE,
    ):
        for match in regex.finditer(
            text
        ):
            name = _normalize_anchor_name(
                match.group("name")
            )

            anchors.add(
                f"vessel:{name}"
            )

    return tuple(
        sorted(anchors)
    )


def _signal_text(
    signal: Mapping[str, Any],
) -> str:
    parts: list[str] = []

    summary = signal.get(
        "signal_summary"
    )

    if isinstance(
        summary,
        str,
    ):
        parts.append(summary)

    evidence = signal.get(
        "evidence"
    )

    if isinstance(
        evidence,
        list,
    ):
        for item in evidence:
            if not isinstance(
                item,
                Mapping,
            ):
                continue

            text = item.get("text")

            if isinstance(
                text,
                str,
            ):
                parts.append(text)

    return "\n".join(parts)


def _paragraph_bounds(
    raw_text: str,
    position: int,
) -> tuple[int, int]:
    start = raw_text.rfind(
        "\n\n",
        0,
        position,
    )

    start = (
        0
        if start < 0
        else start + 2
    )

    end = raw_text.find(
        "\n\n",
        position,
    )

    if end < 0:
        end = len(raw_text)

    return start, end


def _previous_paragraph(
    raw_text: str,
    paragraph_start: int,
) -> str:
    prefix = raw_text[
        :paragraph_start
    ].rstrip()

    if not prefix:
        return ""

    previous_start = prefix.rfind(
        "\n\n"
    )

    if previous_start < 0:
        previous_start = 0
    else:
        previous_start += 2

    return prefix[
        previous_start:
    ].strip()


def _is_context_reset(
    paragraph: str,
) -> bool:
    normalized = (
        paragraph
        .strip()
        .casefold()
    )

    return any(
        normalized.startswith(prefix)
        for prefix
        in _CONTEXT_RESET_PREFIXES
    )


def _has_event_anaphora(
    paragraph: str,
) -> bool:
    normalized = (
        paragraph
        .casefold()
    )

    return any(
        marker in normalized
        for marker
        in _ANAPHORIC_EVENT_MARKERS
    )


def resolve_signal_event_context_anchors(
    signal: Mapping[str, Any],
    raw_text: str,
) -> tuple[str, ...]:
    """Resolve explicit or locally inherited event anchors.

    Resolution order:
    1. explicit anchor in the signal itself;
    2. explicit anchor in the paragraph containing its evidence;
    3. anchor from the immediately preceding paragraph only when
       the current paragraph contains event anaphora and does not
       start a new reporting context.

    This intentionally avoids broad character windows, which can
    leak an anchor across surveillance-section boundaries.
    """

    direct = extract_event_context_anchors(
        _signal_text(signal)
    )

    if direct:
        return direct

    evidence = signal.get(
        "evidence"
    )

    if not isinstance(
        evidence,
        list,
    ):
        return ()

    resolved: set[str] = set()

    for item in evidence:
        if not isinstance(
            item,
            Mapping,
        ):
            continue

        phrase = item.get("text")

        if (
            not isinstance(
                phrase,
                str,
            )
            or not phrase.strip()
        ):
            continue

        position = raw_text.find(
            phrase
        )

        if position < 0:
            continue

        start, end = (
            _paragraph_bounds(
                raw_text,
                position,
            )
        )

        paragraph = raw_text[
            start:end
        ].strip()

        paragraph_anchors = (
            extract_event_context_anchors(
                paragraph
            )
        )

        if paragraph_anchors:
            resolved.update(
                paragraph_anchors
            )
            continue

        if _is_context_reset(
            paragraph
        ):
            continue

        if not _has_event_anaphora(
            paragraph
        ):
            continue

        previous = (
            _previous_paragraph(
                raw_text,
                start,
            )
        )

        resolved.update(
            extract_event_context_anchors(
                previous
            )
        )

    return tuple(
        sorted(resolved)
    )
