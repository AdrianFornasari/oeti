"""Shared contract for provider-reported token counts."""
from collections.abc import Mapping

TOKEN_USAGE_KEYS = (
    "input_tokens", "cached_input_tokens", "output_tokens",
    "reasoning_tokens", "total_tokens",
)


def normalize_token_usage(usage: Mapping | None) -> dict[str, int] | None:
    if usage is None:
        return None
    if not isinstance(usage, Mapping):
        raise ValueError("Token usage must be a mapping or None")
    result = {}
    for key in TOKEN_USAGE_KEYS:
        value = usage.get(key)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"Token usage must be an integer: {key}")
        if value < 0:
            raise ValueError(f"Token usage cannot be negative: {key}={value}")
        result[key] = value
    return result or None
