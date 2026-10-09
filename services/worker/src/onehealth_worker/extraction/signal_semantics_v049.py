from __future__ import annotations

from copy import deepcopy
from typing import Any


_SURVEILLANCE_PERIOD_TYPES = {
    "surveillance_period",
    "season",
}


def harden_signal_semantics_v049(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Apply conservative deterministic semantic corrections.

    The LLM output remains auditable upstream. This layer corrects only patterns
    that are structurally strong enough to classify deterministically.
    """

    hardened = deepcopy(payload)

    warnings = list(
        hardened.get("warnings") or []
    )

    for signal in (
        hardened.get("signals")
        or []
    ):
        if _is_aggregate_surveillance_snapshot(
            signal
        ):
            signal[
                "signal_role"
            ] = "surveillance_baseline"

            signal[
                "signal_type"
            ] = "case_report"

            warning = (
                "SEM-049-01 "
                f"{signal.get('local_signal_id')}: "
                "aggregate surveillance snapshot "
                "reclassified as surveillance_baseline."
            )

            if warning not in warnings:
                warnings.append(
                    warning
                )

    hardened["warnings"] = warnings

    return hardened


def _is_aggregate_surveillance_snapshot(
    signal: dict[str, Any],
) -> bool:
    if (
        signal.get("signal_role")
        != "primary_event"
    ):
        return False

    if signal.get(
        "signal_type"
    ) not in {
        "outbreak",
        "case_report",
    }:
        return False

    if not signal.get(
        "metrics"
    ):
        return False

    event_date = (
        signal.get("event_date")
        or {}
    )

    if (
        event_date.get("start")
        or event_date.get("end")
    ):
        return False

    reference_period = (
        signal.get(
            "reference_period"
        )
        or {}
    )

    if reference_period.get(
        "period_type"
    ) not in _SURVEILLANCE_PERIOD_TYPES:
        return False

    locations = (
        signal.get("locations")
        or []
    )

    if not locations:
        return False

    roles = {
        str(
            location.get(
                "role"
            )
            or ""
        )
        for location in locations
    }

    # Require an explicit surveillance jurisdiction.
    if (
        "reporting_jurisdiction"
        not in roles
    ):
        return False

    # An event/exposure/current location means that the signal may represent
    # an actual incident rather than a population surveillance snapshot.
    if roles - {
        "reporting_jurisdiction"
    }:
        return False

    return True
