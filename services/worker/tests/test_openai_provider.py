from onehealth_worker.extraction.openai_provider import (
    _extract_output_text,
    _to_openai_structured_output_schema,
)


def test_extract_output_text_from_responses_payload():
    payload = {
        "id": "resp_test",
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": '{"schema_version":"0.1"}'}
                ],
            }
        ],
    }
    assert _extract_output_text(payload) == '{"schema_version":"0.1"}'


def test_openai_schema_sanitizes_provider_incompatible_constraints_without_mutation():
    canonical = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Canonical",
        "type": "object",
        "properties": {
            "schema_version": {"const": "0.1"},
            "status": {"enum": ["confirmed", "unknown"]},
            "domains": {
                "type": "array",
                "items": {"enum": ["human", "animal"]},
                "uniqueItems": True,
                "minItems": 1,
            },
            "country_iso2": {
                "type": ["string", "null"],
                "pattern": "^[A-Z]{2}$",
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
            },
        },
        "required": ["schema_version", "status", "domains", "country_iso2", "confidence"],
        "additionalProperties": False,
    }

    api_schema = _to_openai_structured_output_schema(canonical)

    assert "$schema" not in api_schema
    assert "title" not in api_schema
    assert api_schema["properties"]["schema_version"] == {
        "enum": ["0.1"],
        "type": "string",
    }
    assert api_schema["properties"]["status"]["type"] == "string"
    assert api_schema["properties"]["domains"]["items"]["type"] == "string"
    assert "uniqueItems" not in api_schema["properties"]["domains"]
    assert "minItems" not in api_schema["properties"]["domains"]
    assert "pattern" not in api_schema["properties"]["country_iso2"]
    assert "minimum" not in api_schema["properties"]["confidence"]
    assert "maximum" not in api_schema["properties"]["confidence"]

    # Canonical schema remains untouched for OETI local validation.
    assert canonical["properties"]["schema_version"]["const"] == "0.1"
    assert canonical["properties"]["domains"]["uniqueItems"] is True
    assert canonical["properties"]["confidence"]["maximum"] == 1
