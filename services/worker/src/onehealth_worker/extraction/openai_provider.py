from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

import httpx


class LLMProviderError(RuntimeError):
    pass


@dataclass(slots=True)
class ProviderResponse:
    payload: dict[str, Any]
    response_id: str | None


OPENAI_UNSUPPORTED_SCHEMA_KEYWORDS = frozenset({
    # Validation-only constraints kept in OETI's canonical schema but not sent
    # to Structured Outputs. The API enforces the structural contract; OETI
    # re-validates the returned payload locally against the richer schema.
    "$schema",
    "$id",
    "title",
    "uniqueItems",
    "minItems",
    "maxItems",
    "minLength",
    "maxLength",
    "pattern",
    "format",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
    "minProperties",
    "maxProperties",
})


def _infer_json_type(value: Any) -> str | None:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return None


def _to_openai_structured_output_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Build the provider schema accepted by OpenAI Structured Outputs.

    OETI deliberately keeps a richer canonical Draft 2020-12 JSON Schema for
    local validation. OpenAI strict Structured Outputs accepts a smaller,
    structural subset, so this adapter:

    * removes validation-only keywords from the provider copy;
    * converts ``const`` to a one-value ``enum``;
    * adds an explicit ``type`` to enum/const schemas when it can be inferred;
    * never mutates the canonical OETI schema.

    The model response is still validated locally against the full canonical
    schema after it is returned by the API.
    """

    def clean(value: Any) -> Any:
        if isinstance(value, list):
            return [clean(child) for child in value]
        if not isinstance(value, dict):
            return value

        out: dict[str, Any] = {}
        for key, child in value.items():
            if key in OPENAI_UNSUPPORTED_SCHEMA_KEYWORDS:
                continue
            if key == "const":
                # ``enum`` is part of the supported Structured Outputs subset.
                out["enum"] = [clean(child)]
                continue
            out[key] = clean(child)

        # OpenAI requires explicit types for property schemas. JSON Schema
        # itself allows enum/const to imply a type, but Structured Outputs does
        # not. Infer the type when all enum values share one JSON type.
        if "type" not in out and "enum" in out and isinstance(out["enum"], list) and out["enum"]:
            inferred = {_infer_json_type(item) for item in out["enum"]}
            inferred.discard(None)
            if len(inferred) == 1:
                out["type"] = inferred.pop()

        return out

    return clean(schema)


class OpenAIResponsesProvider:
    """OpenAI Responses API adapter using Structured Outputs (JSON Schema)."""

    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1"):
        if not api_key:
            raise ValueError("LLM_API_KEY es obligatorio para provider=openai")
        if not model:
            raise ValueError("LLM_MODEL es obligatorio para provider=openai")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def extract(self, *, instructions: str, document_input: str, schema: dict[str, Any]) -> ProviderResponse:
        body = {
            "model": self.model,
            "instructions": instructions,
            "input": document_input,
            "store": False,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "oeti_signal_extractor_v0_3",
                    "schema": _to_openai_structured_output_schema(schema),
                    "strict": True,
                },
                "verbosity": "low",
            },
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_network_error: Exception | None = None
        for attempt in range(3):
            try:
                with httpx.Client(timeout=httpx.Timeout(120.0, connect=20.0)) as client:
                    response = client.post(f"{self.base_url}/responses", headers=headers, json=body)
                break
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_network_error = exc
                if attempt == 2:
                    raise LLMProviderError(f"Error de red al consultar OpenAI: {exc}") from exc
                time.sleep(2 ** attempt)
        else:  # pragma: no cover
            raise LLMProviderError(f"Error de red al consultar OpenAI: {last_network_error}")

        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text[:2000]
            raise LLMProviderError(f"OpenAI API HTTP {response.status_code}: {detail}")

        data = response.json()
        if data.get("status") not in {"completed", None}:
            raise LLMProviderError(
                f"OpenAI Responses API no completó la extracción: status={data.get('status')!r}, "
                f"error={data.get('error')!r}, incomplete={data.get('incomplete_details')!r}"
            )

        output_text = _extract_output_text(data)
        if not output_text:
            raise LLMProviderError("La respuesta no contiene output_text utilizable.")
        try:
            payload = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise LLMProviderError(f"Structured Output no pudo parsearse como JSON: {exc}") from exc

        return ProviderResponse(payload=payload, response_id=data.get("id"))


def _extract_output_text(data: dict[str, Any]) -> str | None:
    # Raw HTTP Responses payload exposes output[]; SDK convenience property output_text
    # is not guaranteed to be serialized in the JSON.
    if isinstance(data.get("output_text"), str):
        return data["output_text"]
    for item in data.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return content["text"]
    return None
