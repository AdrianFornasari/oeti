from onehealth_worker.extraction.signal_semantics_v049 import (
    harden_signal_semantics_v049,
)


def _signal(
    *,
    role="primary_event",
    signal_type="outbreak",
    period_type="surveillance_period",
    locations=None,
    event_start=None,
):
    return {
        "local_signal_id": "S1",
        "signal_role": role,
        "signal_type": signal_type,
        "metrics": [
            {
                "name": "cases_confirmed",
                "value_numeric": 102,
            }
        ],
        "event_date": {
            "start": event_start,
            "end": None,
            "precision": "unknown",
        },
        "reference_period": {
            "period_type": period_type,
        },
        "locations": (
            locations
            if locations is not None
            else [
                {
                    "role":
                        "reporting_jurisdiction",
                    "country":
                        "Argentina",
                }
            ]
        ),
    }


def test_aggregate_surveillance_snapshot_becomes_baseline():
    payload = {
        "signals": [
            _signal()
        ],
        "warnings": [],
    }

    result = (
        harden_signal_semantics_v049(
            payload
        )
    )

    signal = result[
        "signals"
    ][0]

    assert (
        signal["signal_role"]
        == "surveillance_baseline"
    )

    assert (
        signal["signal_type"]
        == "case_report"
    )

    assert any(
        "SEM-049-01"
        in warning
        for warning
        in result["warnings"]
    )


def test_concrete_case_with_current_location_stays_primary():
    payload = {
        "signals": [
            _signal(
                period_type=
                    "observation_window",
                locations=[
                    {
                        "role":
                            "reporting_jurisdiction",
                        "country":
                            "Argentina",
                    },
                    {
                        "role":
                            "current_location",
                        "admin1":
                            "Buenos Aires",
                    },
                ],
            )
        ]
    }

    result = (
        harden_signal_semantics_v049(
            payload
        )
    )

    signal = result[
        "signals"
    ][0]

    assert (
        signal["signal_role"]
        == "primary_event"
    )

    assert (
        signal["signal_type"]
        == "outbreak"
    )


def test_event_with_real_event_date_stays_primary():
    payload = {
        "signals": [
            _signal(
                event_start=
                    "2026-05-12"
            )
        ]
    }

    result = (
        harden_signal_semantics_v049(
            payload
        )
    )

    assert (
        result["signals"][0][
            "signal_role"
        ]
        == "primary_event"
    )


def test_rule_is_idempotent():
    payload = {
        "signals": [
            _signal()
        ],
        "warnings": [],
    }

    first = (
        harden_signal_semantics_v049(
            payload
        )
    )

    second = (
        harden_signal_semantics_v049(
            first
        )
    )

    assert first == second
