from __future__ import annotations

import re
from copy import deepcopy
from datetime import date
from typing import Any

_YEAR_RE = re.compile(r"^(?P<year>\d{4})$")
_MONTH_RE = re.compile(r"^(?P<year>\d{4})-(?P<month>\d{2})$")


def normalize_extraction_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize provider output before canonical JSON Schema validation.

    Structured Outputs guarantees structure, not OETI's richer semantic/date rules.
    In particular, a source may state only a year (e.g. ``2004``) while the canonical
    ``as_of_date`` field requires a full calendar date. OETI must not fabricate
    ``2004-01-01``. Instead we preserve the partial temporal information explicitly
    and set ``as_of_date`` to null.
    """

    result = deepcopy(payload)
    warnings = list(result.get("warnings") or [])

    for signal in result.get("signals") or []:
        local_id = signal.get("local_signal_id") or "?"
        for metric in signal.get("metrics") or []:
            _normalize_metric_date(metric, local_id=local_id, warnings=warnings)
        reference_period = signal.get("reference_period") or {}
        for endpoint_name in ("start", "end"):
            endpoint = reference_period.get(endpoint_name)
            if isinstance(endpoint, dict):
                _normalize_temporal_point(endpoint, local_id=local_id, field_name=f"reference_period.{endpoint_name}", warnings=warnings)

    result["warnings"] = warnings
    return result


def _normalize_metric_date(metric: dict[str, Any], *, local_id: str, warnings: list[str]) -> None:
    raw = metric.get("as_of_date")

    # Ensure the v0.2 temporal fields always exist, even if a provider omitted them.
    metric.setdefault("as_of_year", None)
    metric.setdefault("as_of_month", None)
    metric.setdefault("as_of_precision", "unknown")
    metric.setdefault("as_of_verbatim", None)

    if raw is None:
        return
    if not isinstance(raw, str):
        metric["as_of_verbatim"] = metric.get("as_of_verbatim") or str(raw)
        metric["as_of_date"] = None
        metric["as_of_precision"] = "unknown"
        warnings.append(
            f"Signal {local_id}, metric {metric.get('name')!r}: as_of_date no textual descartado; valor original={raw!r}."
        )
        return

    value = raw.strip()
    if _is_full_iso_date(value):
        metric["as_of_precision"] = "day"
        if metric.get("as_of_year") is None:
            metric["as_of_year"] = int(value[0:4])
        if metric.get("as_of_month") is None:
            metric["as_of_month"] = int(value[5:7])
        return

    year_match = _YEAR_RE.fullmatch(value)
    if year_match:
        year = int(year_match.group("year"))
        metric["as_of_date"] = None
        metric["as_of_year"] = year
        metric["as_of_month"] = None
        metric["as_of_precision"] = "year"
        metric["as_of_verbatim"] = metric.get("as_of_verbatim") or value
        warnings.append(
            f"Signal {local_id}, metric {metric.get('name')!r}: fecha parcial {value!r} preservada con precisión anual; no se inventó día/mes."
        )
        return

    month_match = _MONTH_RE.fullmatch(value)
    if month_match:
        year = int(month_match.group("year"))
        month = int(month_match.group("month"))
        if 1 <= month <= 12:
            metric["as_of_date"] = None
            metric["as_of_year"] = year
            metric["as_of_month"] = month
            metric["as_of_precision"] = "month"
            metric["as_of_verbatim"] = metric.get("as_of_verbatim") or value
            warnings.append(
                f"Signal {local_id}, metric {metric.get('name')!r}: fecha parcial {value!r} preservada con precisión mensual; no se inventó día."
            )
            return

    metric["as_of_date"] = None
    metric["as_of_precision"] = "unknown"
    metric["as_of_verbatim"] = metric.get("as_of_verbatim") or value
    warnings.append(
        f"Signal {local_id}, metric {metric.get('name')!r}: as_of_date {value!r} no es una fecha ISO completa; se preservó como valor temporal verbatim."
    )


def _normalize_temporal_point(point: dict[str, Any], *, local_id: str, field_name: str, warnings: list[str]) -> None:
    """Preserve year/month temporal precision without fabricating a calendar date."""
    point.setdefault("date", None)
    point.setdefault("year", None)
    point.setdefault("month", None)
    point.setdefault("precision", "unknown")
    point.setdefault("verbatim", None)

    raw = point.get("date")
    if raw is None:
        return
    if not isinstance(raw, str):
        point["verbatim"] = point.get("verbatim") or str(raw)
        point["date"] = None
        point["precision"] = "unknown"
        warnings.append(f"Signal {local_id}, {field_name}: fecha no textual descartada; valor original={raw!r}.")
        return

    value = raw.strip()
    if _is_full_iso_date(value):
        point["precision"] = "day"
        point["year"] = point.get("year") or int(value[0:4])
        point["month"] = point.get("month") or int(value[5:7])
        return

    year_match = _YEAR_RE.fullmatch(value)
    if year_match:
        point["date"] = None
        point["year"] = int(year_match.group("year"))
        point["month"] = None
        point["precision"] = "year"
        point["verbatim"] = point.get("verbatim") or value
        warnings.append(f"Signal {local_id}, {field_name}: {value!r} preservado con precisión anual; no se inventó fecha completa.")
        return

    month_match = _MONTH_RE.fullmatch(value)
    if month_match and 1 <= int(month_match.group("month")) <= 12:
        point["date"] = None
        point["year"] = int(month_match.group("year"))
        point["month"] = int(month_match.group("month"))
        point["precision"] = "month"
        point["verbatim"] = point.get("verbatim") or value
        warnings.append(f"Signal {local_id}, {field_name}: {value!r} preservado con precisión mensual; no se inventó día.")
        return

    point["date"] = None
    point["precision"] = "unknown"
    point["verbatim"] = point.get("verbatim") or value
    warnings.append(f"Signal {local_id}, {field_name}: fecha {value!r} no normalizable; se preservó verbatim.")


def _is_full_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))
