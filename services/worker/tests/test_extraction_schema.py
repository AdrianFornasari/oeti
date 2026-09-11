import copy
import json
from pathlib import Path

import pytest

from onehealth_worker.extraction.schema import ExtractionSchemaError, validate_extraction


FIXTURE = Path(__file__).parent / "fixtures" / "extraction_valid.json"


def _payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_valid_extraction_matches_contract():
    validate_extraction(_payload())


def test_unknown_property_is_rejected():
    payload = copy.deepcopy(_payload())
    payload["signals"][0]["invented_field"] = "no"
    with pytest.raises(ExtractionSchemaError):
        validate_extraction(payload)
