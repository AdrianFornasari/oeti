from __future__ import annotations

from typing import Any


def event_matching_eligible(signal: dict[str, Any]) -> bool:
    """Deterministic pre-gate for future automatic event matching.

    Administrative alerts and contextual baselines must not be candidates for
    automatic matching because they can duplicate epidemiological facts already
    represented by primary signals. Negative evidence remains eligible because
    it can refine or contradict an event hypothesis.
    """
    if signal.get("signal_type") == "official_alert":
        return False
    if signal.get("signal_role") in {"background_context", "surveillance_baseline"}:
        return False
    return True
