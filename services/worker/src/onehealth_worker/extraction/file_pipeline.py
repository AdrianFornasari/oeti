from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .repository import ExtractionRepository
from .schema import load_schema, validate_extraction


def validate_file(path: Path, schema_path: Path | None = None) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
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
    # Force existence and payload binding before any write.
    repo.load_raw_document(raw_item_id)
    return repo.persist_extraction(
        raw_item_id=raw_item_id,
        payload=payload,
        provider=provider,
        model_name=model_name,
        response_id=None,
        input_char_count=0,
    )
