import json
from pathlib import Path

import pytest

from onehealth_worker.extraction.prompt import SYSTEM_INSTRUCTIONS
from onehealth_worker.extraction.matching import event_matching_eligible
from onehealth_worker.extraction.schema import (
    ExtractionSchemaError,
    load_schema,
    validate_extraction,
    validate_literal_evidence,
)


def test_v04_fixture_validates():
    root = Path(__file__).resolve().parents[3]
    payload = json.loads((root / "services/worker/tests/fixtures/extraction_valid_v04.json").read_text(encoding="utf-8"))
    schema = json.loads((root / "shared/schemas/signal-extractor-v0.4.schema.json").read_text(encoding="utf-8"))
    validate_extraction(payload, schema)


def test_default_schema_is_v04_with_diagnostics():
    schema = load_schema()
    assert schema["properties"]["schema_version"]["const"] == "0.4"
    signal = schema["$defs"]["signal"]
    assert "diagnostics" in signal["required"]
    assert "laboratory_investigation" in signal["properties"]["signal_type"]["enum"]
    roles = schema["$defs"]["location"]["properties"]["role"]["enum"]
    assert "laboratory_location" in roles


def test_prompt_separates_diagnostics_genomics_and_requires_literal_evidence():
    assert "DIAGNÓSTICO VS GENÓMICA" in SYSTEM_INSTRUCTIONS
    assert "PRUEBAS EN CURSO" in SYSTEM_INSTRUCTIONS
    assert "EVIDENCIA LITERAL" in SYSTEM_INSTRUCTIONS
    assert "ITINERARIOS" in SYSTEM_INSTRUCTIONS


def test_literal_evidence_accepts_whitespace_only_differences():
    payload = {"signals": [{"local_signal_id":"S1","evidence":[{"text":"un pasajero con confirmación laboratorial de hantavirus"}]}]}
    raw = "Texto previo. un pasajero   con confirmación laboratorial de hantavirus. Texto posterior."
    validate_literal_evidence(payload, raw)


def test_literal_evidence_rejects_ellipsis_or_paraphrase():
    payload = {"signals": [{"local_signal_id":"S1","evidence":[{"text":"Tierra del Fuego ... no ha registrado casos"}]}]}
    raw = "Tierra del Fuego no tiene presencia de hantavirus y no ha registrado casos desde 1996."
    with pytest.raises(ExtractionSchemaError):
        validate_literal_evidence(payload, raw)


def test_event_matching_gate_is_deterministic():
    assert event_matching_eligible({"signal_type":"official_alert","signal_role":"primary_event"}) is False
    assert event_matching_eligible({"signal_type":"case_report","signal_role":"surveillance_baseline"}) is False
    assert event_matching_eligible({"signal_type":"laboratory_result","signal_role":"primary_event"}) is True
    assert event_matching_eligible({"signal_type":"pathogen_detection","signal_role":"negative_evidence"}) is True
