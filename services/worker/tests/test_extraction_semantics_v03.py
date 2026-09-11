import json
from pathlib import Path

from onehealth_worker.extraction.prompt import SYSTEM_INSTRUCTIONS
from onehealth_worker.extraction.schema import load_schema, validate_extraction


def test_v03_fixture_validates():
    root = Path(__file__).resolve().parents[3]
    payload = json.loads((root / "services/worker/tests/fixtures/extraction_valid_v03.json").read_text(encoding="utf-8"))
    schema = json.loads((root / "shared/schemas/signal-extractor-v0.3.schema.json").read_text(encoding="utf-8"))
    validate_extraction(payload, schema)


def test_prompt_contains_non_attribution_and_context_rules():
    assert "ATRIBUCIÓN DE MÉTRICAS" in SYSTEM_INSTRUCTIONS
    assert "SEPARACIÓN SÍNDROME-ETIOLOGÍA" in SYSTEM_INSTRUCTIONS
    assert "surveillance_baseline" in SYSTEM_INSTRUCTIONS
    assert "location.role" in SYSTEM_INSTRUCTIONS
    assert "reference_period" in SYSTEM_INSTRUCTIONS
    assert "hantavirus" in SYSTEM_INSTRUCTIONS


def test_default_schema_is_v03():
    schema = load_schema()
    assert schema["properties"]["schema_version"]["const"] == "0.3"
    signal = schema["$defs"]["signal"]
    assert "signal_role" in signal["required"]
    assert "reference_period" in signal["required"]
    location = schema["$defs"]["location"]
    assert "role" in location["required"]
