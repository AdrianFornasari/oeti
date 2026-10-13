from __future__ import annotations

import json
import math
import time
import re
from dataclasses import dataclass
from typing import Any

import httpx

from .token_usage import normalize_token_usage


class LLMProviderError(RuntimeError):
    pass


@dataclass(slots=True)
class ProviderResponse:
    payload: dict[str, Any]
    response_id: str | None
    usage: dict[str, int] | None


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


def _structured_output_name(schema: dict[str, Any]) -> str:
    version_schema = schema.get("properties", {}).get("schema_version", {})
    version = version_schema.get("const")
    if version is None:
        enum = version_schema.get("enum")
        if isinstance(enum, list) and len(enum) == 1:
            version = enum[0]
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", str(version or "unknown"))
    return f"oeti_signal_extractor_v{safe}"




def _extract_usage(
    data: dict[str, Any],
) -> dict[str, int] | None:
    usage_raw = data.get("usage")
    if usage_raw is None:
        return None
    if not isinstance(usage_raw, dict):
        raise ValueError("Provider usage must be a mapping")
    input_details = usage_raw.get("input_tokens_details")
    output_details = usage_raw.get("output_tokens_details")
    for details in (input_details, output_details):
        if details is not None and not isinstance(details, dict):
            raise ValueError("Provider token details must be a mapping")
    return normalize_token_usage({
        "input_tokens": usage_raw.get("input_tokens"),
        "cached_input_tokens": (input_details or {}).get("cached_tokens"),
        "output_tokens": usage_raw.get("output_tokens"),
        "reasoning_tokens": (output_details or {}).get("reasoning_tokens"),
        "total_tokens": usage_raw.get("total_tokens"),
    })


class OpenAIResponsesProvider:
    """OpenAI Responses API adapter using Structured Outputs (JSON Schema)."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        read_timeout_seconds: float = 600.0,
    ):
        if not api_key:
            raise ValueError("LLM_API_KEY es obligatorio para provider=openai")
        if not model:
            raise ValueError("LLM_MODEL es obligatorio para provider=openai")
        if (
            type(read_timeout_seconds) not in (int, float)
            or not math.isfinite(read_timeout_seconds)
            or read_timeout_seconds <= 0
        ):
            raise ValueError("read_timeout_seconds debe ser un número finito mayor que cero")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.read_timeout_seconds = float(read_timeout_seconds)

    def extract(self, *, instructions: str, document_input: str, schema: dict[str, Any]) -> ProviderResponse:
        body = {
            "model": self.model,
            "instructions": instructions,
            "input": document_input,
            "store": False,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": _structured_output_name(schema),
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

        for attempt in range(3):
            try:
                timeout = httpx.Timeout(
                    connect=20.0,
                    read=self.read_timeout_seconds,
                    write=20.0,
                    pool=20.0,
                )

                with httpx.Client(
                    timeout=timeout
                ) as client:
                    response = client.post(
                        f"{self.base_url}/responses",
                        headers=headers,
                        json=body,
                    )

                break

            except (
                httpx.ConnectTimeout,
                httpx.ConnectError,
            ) as exc:
                if attempt == 2:
                    raise LLMProviderError(
                        "No se pudo conectar con OpenAI después de tres intentos."
                    ) from exc

                time.sleep(
                    2 ** attempt
                )
            except httpx.RequestError as exc:
                raise LLMProviderError(
                    f"Error de transporte al consultar OpenAI ({type(exc).__name__}). "
                    "La solicitud no se reintenta automáticamente. "
                    "No se puede confirmar su procesamiento desde este cliente."
                ) from exc

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

        usage = _extract_usage(
            data
        )

        return ProviderResponse(
            payload=payload,
            response_id=data.get("id"),
            usage=usage,
        )


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
