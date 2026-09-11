from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .normalization import normalize_extraction_payload
from .openai_provider import OpenAIResponsesProvider
from .prompt import SYSTEM_INSTRUCTIONS, build_document_input
from .repository import ExtractionRepository
from .schema import load_schema, validate_extraction


@dataclass(slots=True)
class ExtractionResult:
    raw_item_id: str
    extraction_run_id: str | None
    signal_count: int
    persisted: bool
    provider: str
    model_name: str
    response_id: str | None
    warnings: list[str]
    payload: dict[str, Any]


def extract_raw_item(
    *,
    database_url: str,
    raw_item_id: str,
    provider_name: str,
    model_name: str,
    api_key: str,
    schema_path: Path | None = None,
    persist: bool = True,
) -> ExtractionResult:
    repo = ExtractionRepository(database_url)
    document = repo.load_raw_document(raw_item_id)
    schema = load_schema(schema_path)
    document_input = build_document_input(
        raw_item_id=document.raw_item_id,
        title=document.title,
        url=document.url,
        published_at=document.published_at,
        language=document.language,
        raw_text=document.raw_text,
    )

    if provider_name.lower() != "openai":
        raise ValueError(f"Provider no soportado en Sprint 1C: {provider_name!r}")

    provider = OpenAIResponsesProvider(api_key=api_key, model=model_name)
    provider_response = None
    try:
        provider_response = provider.extract(
            instructions=SYSTEM_INSTRUCTIONS,
            document_input=document_input,
            schema=schema,
        )
        payload = normalize_extraction_payload(provider_response.payload)
        validate_extraction(payload, schema)
        _validate_document_binding(payload, document.raw_item_id)
    except Exception as exc:
        if persist:
            repo.record_failed_run(
                raw_item_id=document.raw_item_id,
                schema_version=_schema_version(schema),
                provider=provider_name,
                model_name=model_name,
                input_char_count=len(document_input),
                error_text=str(exc),
                response_id=provider_response.response_id if provider_response else None,
            )
        raise

    run_id: str | None = None
    warnings = list(payload.get("warnings", []))
    if persist:
        run_id, warnings = repo.persist_extraction(
            raw_item_id=document.raw_item_id,
            payload=payload,
            provider=provider_name,
            model_name=model_name,
            response_id=provider_response.response_id,
            input_char_count=len(document_input),
        )

    return ExtractionResult(
        raw_item_id=document.raw_item_id,
        extraction_run_id=run_id,
        signal_count=len(payload.get("signals", [])),
        persisted=persist,
        provider=provider_name,
        model_name=model_name,
        response_id=provider_response.response_id,
        warnings=warnings,
        payload=payload,
    )


def _validate_document_binding(payload: dict[str, Any], expected_raw_item_id: str) -> None:
    returned = payload.get("document", {}).get("raw_item_id")
    if returned != expected_raw_item_id:
        raise ValueError(
            f"El extractor devolvió raw_item_id={returned!r}, pero se esperaba {expected_raw_item_id!r}."
        )


def _schema_version(schema: dict[str, Any]) -> str:
    version_schema = schema.get("properties", {}).get("schema_version", {})
    if "const" in version_schema:
        return str(version_schema["const"])
    enum = version_schema.get("enum")
    if isinstance(enum, list) and len(enum) == 1:
        return str(enum[0])
    return "unknown"
