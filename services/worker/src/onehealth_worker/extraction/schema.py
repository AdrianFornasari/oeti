from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


class ExtractionSchemaError(ValueError):
    pass


def default_schema_path() -> Path:
    # services/worker/src/onehealth_worker/extraction/schema.py -> repository root
    return Path(__file__).resolve().parents[5] / "shared" / "schemas" / "signal-extractor-v0.3.schema.json"


def load_schema(path: Path | None = None) -> dict[str, Any]:
    schema_path = path or default_schema_path()
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_extraction(payload: dict[str, Any], schema: dict[str, Any] | None = None) -> None:
    validator = Draft202012Validator(schema or load_schema(), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(payload), key=lambda err: list(err.absolute_path))
    if not errors:
        return

    details: list[str] = []
    for error in errors[:10]:
        path = ".".join(str(part) for part in error.absolute_path) or "$"
        details.append(f"{path}: {error.message}")
    if len(errors) > 10:
        details.append(f"... y {len(errors) - 10} errores adicionales")
    raise ExtractionSchemaError("Salida de extracción inválida:\n" + "\n".join(details))
