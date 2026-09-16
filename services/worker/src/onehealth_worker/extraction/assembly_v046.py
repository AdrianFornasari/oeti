from __future__ import annotations

from copy import deepcopy
from typing import Any

from .assembly_v045 import assemble_claims_payload as assemble_claims_payload_v045


def assemble_claims_payload(claim_payload: dict[str, Any]) -> dict[str, Any]:
    """v0.4.6 TDD baseline.

    The first commit intentionally delegates to the v0.4.5 assembler unchanged.
    Regression tests in test_v046_benchmark_hardening.py define the required
    benchmark-hardening behavior before the deterministic rules are implemented.
    """
    return assemble_claims_payload_v045(deepcopy(claim_payload))
