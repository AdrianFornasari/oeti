from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from ..extraction.prompt import build_document_input


def scoped_document_input(document, scope: str | None) -> str:
    base = build_document_input(
        raw_item_id=document.raw_item_id,
        title=document.title,
        url=document.url,
        published_at=document.published_at,
        language=document.language,
        raw_text=document.raw_text,
    )
    if not scope:
        return base
    return (
        base
        + "\n\nEVALUATION_SCOPE_BEGIN\n"
        + scope.strip()
        + "\nExtraé únicamente claims dentro de este alcance para este benchmark. "
          "No extraigas señales de otros temas; en esta arquitectura eso significa no extraer claims de otros temas del documento.\n"
        + "EVALUATION_SCOPE_END"
    )


def extract_evaluation_corpus(
    *,
    manifest_path: Path,
    database_url: str,
    provider_name: str,
    model_name: str,
    api_key: str,
    force: bool = False,
) -> dict[str, Any]:
    if provider_name.lower() != "openai":
        raise ValueError(f"Provider no soportado para benchmark: {provider_name!r}")

    # Lazy imports keep offline evaluation/tests independent from DB/provider packages.
    from ..extraction.atomic_claims import assemble_claims_payload
    from ..extraction.normalization import normalize_extraction_payload
    from ..extraction.openai_provider import OpenAIResponsesProvider
    from ..extraction.prompt import SYSTEM_INSTRUCTIONS
    from ..extraction.repository import ExtractionRepository
    from ..extraction.schema import (
        load_schema,
        load_atomic_claims_schema,
        validate_atomic_claims,
        validate_extraction,
        validate_literal_claim_evidence,
        validate_literal_evidence,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    base = manifest_path.parent
    repo = ExtractionRepository(database_url)
    signal_schema = load_schema()
    claims_schema = load_atomic_claims_schema()
    provider = OpenAIResponsesProvider(api_key=api_key, model=model_name)
    default_scope = manifest.get("evaluation_scope")
    results: list[dict[str, Any]] = []

    for item in manifest.get("documents", []):
        if item.get("status") != "adjudicated":
            results.append({"label": item.get("label"), "status": "skipped_not_adjudicated"})
            continue
        prediction_rel = item.get("prediction")
        source_url = item.get("source_url")
        if not prediction_rel or not source_url:
            results.append({"label": item.get("label"), "status": "skipped_missing_config"})
            continue
        prediction_path = (base / prediction_rel).resolve()
        claims_path = prediction_path.with_name(prediction_path.stem + ".claims.json")
        if prediction_path.exists() and not force:
            results.append({
                "label": item.get("label"),
                "status": "existing",
                "path": str(prediction_path),
                "claims_path": str(claims_path) if claims_path.exists() else None,
            })
            continue

        document = repo.load_raw_document_by_url(source_url)
        document_input = scoped_document_input(document, item.get("evaluation_scope") or default_scope)
        response = provider.extract(
            instructions=SYSTEM_INSTRUCTIONS,
            document_input=document_input,
            schema=claims_schema,
        )
        claims_payload = response.payload
        validate_atomic_claims(claims_payload, claims_schema)
        returned = claims_payload.get("document", {}).get("raw_item_id")
        if returned != document.raw_item_id:
            raise ValueError(
                f"{item.get('label')}: raw_item_id devuelto {returned!r}; esperado {document.raw_item_id!r}."
            )
        validate_literal_claim_evidence(claims_payload, document.raw_text)

        payload = normalize_extraction_payload(assemble_claims_payload(claims_payload))
        validate_extraction(payload, signal_schema)
        validate_literal_evidence(payload, document.raw_text)

        prediction_path.parent.mkdir(parents=True, exist_ok=True)
        claims_path.write_text(json.dumps(claims_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        prediction_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        results.append({
            "label": item.get("label"),
            "status": "generated",
            "raw_item_id": document.raw_item_id,
            "claims": len(claims_payload.get("claims", [])),
            "signals": len(payload.get("signals", [])),
            "path": str(prediction_path),
            "claims_path": str(claims_path),
            "response_id": response.response_id,
        })

    return {
        "case_code": manifest.get("case_code"),
        "provider": provider_name,
        "model": model_name,
        "architecture": "atomic_claims_v0.1+deterministic_signal_assembly_v0.4.4",
        "results": results,
    }
