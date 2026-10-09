from __future__ import annotations

from typing import Any


def _has_resolved_event_identity(
    signal: dict[str, Any],
) -> bool:
    """Return whether the signal has an etiological anchor for auto-matching.

    A signal may still be persisted when disease/pathogen are unresolved.
    It is withheld from automatic Event Matching until at least one of those
    entities is normalized to a canonical identity.
    """

    for field in (
        "disease",
        "pathogen",
    ):
        entity = signal.get(field)

        if not isinstance(
            entity,
            dict,
        ):
            continue

        canonical_name = (
            entity.get(
                "canonical_name"
            )
        )

        if (
            entity.get(
                "normalization_status"
            )
            == "resolved"
            and isinstance(
                canonical_name,
                str,
            )
            and canonical_name.strip()
        ):
            return True

    return False


def event_matching_eligible(
    signal: dict[str, Any],
) -> bool:
    """Deterministic production pre-gate for automatic event matching.

    Administrative alerts and contextual/baseline signals are excluded because
    they can duplicate epidemiological facts represented elsewhere.

    Signals without a resolved disease or pathogen identity are retained by
    OETI but withheld from automatic Event Matching. The current schema has no
    explicit syndromic identity capable of safely replacing that etiological
    anchor.

    Negative evidence remains eligible when it has a resolved disease/pathogen
    identity because it can refine or contradict an event hypothesis.
    """

    if (
        signal.get(
            "signal_type"
        )
        == "official_alert"
    ):
        return False

    if signal.get(
        "signal_role"
    ) in {
        "background_context",
        "surveillance_baseline",
    }:
        return False

    if not _has_resolved_event_identity(
        signal
    ):
        return False

    return True
