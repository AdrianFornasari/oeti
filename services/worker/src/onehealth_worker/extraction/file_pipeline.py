from __future__ import annotations

import json
from math import isfinite
from pathlib import Path
from typing import Any

from .repository import ExtractionRepository
from .schema import load_schema, validate_extraction, validate_literal_evidence


def _unique_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("El JSON contiene claves duplicadas.")
        result[key] = value
    return result


def _finite_json_number(value: str) -> float:
    number = float(value)
    if not isfinite(number):
        raise ValueError("El JSON contiene un número no finito.")
    return number


def validate_file(path: Path, schema_path: Path | None = None) -> dict[str, Any]:
    payload = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_json_keys,
        parse_float=_finite_json_number,
        parse_constant=_finite_json_number,
    )
    validate_extraction(payload, load_schema(schema_path))
    return payload


def persist_file(
    *,
    database_url: str,
    path: Path,
    provider: str = "manual_json",
    model_name: str = "manual_or_fixture",
    schema_path: Path | None = None,
) -> tuple[str, list[str]]:
    payload = validate_file(path, schema_path)
    raw_item_id = payload["document"]["raw_item_id"]
    repo = ExtractionRepository(database_url)
    # Force existence and payload binding before any write and verify evidence
    # against the exact stored source text.
    document = repo.load_raw_document(raw_item_id)
    validate_literal_evidence(payload, document.raw_text)
    return repo.persist_extraction(
        raw_item_id=raw_item_id,
        payload=payload,
        provider=provider,
        model_name=model_name,
        response_id=None,
        input_char_count=0,
    )
