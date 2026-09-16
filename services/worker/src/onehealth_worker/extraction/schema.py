from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


class ExtractionSchemaError(ValueError):
    pass


def default_schema_path() -> Path:
    # services/worker/src/onehealth_worker/extraction/schema.py -> repository root
    return Path(__file__).resolve().parents[5] / "shared" / "schemas" / "signal-extractor-v0.4.schema.json"


def load_schema(path: Path | None = None) -> dict[str, Any]:
    schema_path = path or default_schema_path()
    return json.loads(schema_path.read_text(encoding="utf-8"))




def default_atomic_claims_schema_path() -> Path:
    return Path(__file__).resolve().parents[5] / "shared" / "schemas" / "atomic-claims-v0.1.schema.json"


def load_atomic_claims_schema(path: Path | None = None) -> dict[str, Any]:
    schema_path = path or default_atomic_claims_schema_path()
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_atomic_claims(payload: dict[str, Any], schema: dict[str, Any] | None = None) -> None:
    validator = Draft202012Validator(schema or load_atomic_claims_schema(), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(payload), key=lambda err: list(err.absolute_path))
    if not errors:
        return
    details: list[str] = []
    for error in errors[:10]:
        path = ".".join(str(part) for part in error.absolute_path) or "$"
        details.append(f"{path}: {error.message}")
    if len(errors) > 10:
        details.append(f"... y {len(errors) - 10} errores adicionales")
    raise ExtractionSchemaError("Salida de claims atómicos inválida:\n" + "\n".join(details))

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


def _normalize_evidence_text(value: str) -> str:
    """Normalize whitespace only; do not alter words or punctuation."""
    return " ".join(value.split())


def validate_literal_evidence(payload: dict[str, Any], raw_text: str) -> None:
    """Require every evidence excerpt to be a contiguous literal source span.

    Whitespace differences caused by HTML/PDF extraction are ignored, but ellipses,
    paraphrases and reconstructed quotes are rejected.
    """
    normalized_source = _normalize_evidence_text(raw_text)
    failures: list[str] = []
    for signal in payload.get("signals", []):
        local_id = signal.get("local_signal_id", "?")
        for index, evidence in enumerate(signal.get("evidence", [])):
            excerpt = evidence.get("text")
            if not isinstance(excerpt, str) or not excerpt.strip():
                failures.append(f"{local_id}.evidence[{index}]: evidencia vacía")
                continue
            normalized_excerpt = _normalize_evidence_text(excerpt)
            if normalized_excerpt not in normalized_source:
                failures.append(
                    f"{local_id}.evidence[{index}]: el fragmento no existe literalmente en raw_text: {excerpt!r}"
                )
    if failures:
        raise ExtractionSchemaError(
            "Evidencia no literal o no trazable:\n" + "\n".join(failures[:10])
            + (f"\n... y {len(failures)-10} errores adicionales" if len(failures) > 10 else "")
        )


def validate_literal_claim_evidence(payload: dict[str, Any], raw_text: str) -> None:
    normalized_source = _normalize_evidence_text(raw_text)
    failures: list[str] = []
    for claim in payload.get("claims", []):
        claim_id = claim.get("claim_id", "?")
        for index, evidence in enumerate(claim.get("evidence", [])):
            excerpt = evidence.get("text")
            if not isinstance(excerpt, str) or not excerpt.strip():
                failures.append(f"{claim_id}.evidence[{index}]: evidencia vacía")
                continue
            normalized_excerpt = _normalize_evidence_text(excerpt)
            if normalized_excerpt not in normalized_source:
                failures.append(
                    f"{claim_id}.evidence[{index}]: el fragmento no existe literalmente en raw_text: {excerpt!r}"
                )
    if failures:
        raise ExtractionSchemaError(
            "Evidencia de claims no literal o no trazable:\n" + "\n".join(failures[:10])
            + (f"\n... y {len(failures)-10} errores adicionales" if len(failures) > 10 else "")
        )
