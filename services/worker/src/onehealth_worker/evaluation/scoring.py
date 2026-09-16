from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterable
import json
import re


DEFAULT_MATCH_THRESHOLD = 0.55
EVIDENCE_SUPPORT_THRESHOLD = 0.70

# Small Spanish/English stop-word set used only for evidence-overlap scoring.
# Evidence remains required to be literal source text by the extractor validator.
_EVIDENCE_STOPWORDS = {
    "a", "al", "ante", "bajo", "con", "contra", "de", "del", "desde", "durante",
    "e", "el", "ella", "ellas", "ellos", "en", "entre", "era", "es", "esa", "ese",
    "esta", "este", "fue", "ha", "hasta", "la", "las", "lo", "los", "o", "para",
    "pero", "por", "que", "se", "sin", "su", "sus", "un", "una", "uno", "unos",
    "unas", "y", "ya", "the", "of", "and", "in", "to", "for", "with", "was", "were",
}
_NEGATION_TOKENS = {"no", "sin", "ningun", "ninguna", "ninguno", "negativo", "negativa", "negativos", "negativas"}


@dataclass(frozen=True)
class PairMatch:
    gold_index: int
    prediction_index: int
    score: float


@dataclass(frozen=True)
class EvidencePairMatch:
    gold_index: int
    prediction_index: int
    score: float


def _norm_text(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip().casefold()
    return text or None


def _set_f1(gold: Iterable[Any], pred: Iterable[Any]) -> float:
    g = set(gold)
    p = set(pred)
    if not g and not p:
        return 1.0
    if not g or not p:
        return 0.0
    tp = len(g & p)
    precision = tp / len(p)
    recall = tp / len(g)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _entity_key(entity: dict[str, Any] | None) -> tuple[Any, ...]:
    entity = entity or {}
    return (
        _norm_text(entity.get("canonical_name")),
        _norm_text(entity.get("verbatim")),
    )


def _entity_exact(gold: dict[str, Any] | None, pred: dict[str, Any] | None) -> float:
    g = _entity_key(gold)
    p = _entity_key(pred)
    # Prefer canonical identity if both sides have it; otherwise compare verbatim.
    if g[0] is not None and p[0] is not None:
        return float(g[0] == p[0])
    return float(g[1] == p[1])


def _domains(signal: dict[str, Any]) -> list[str]:
    return [_norm_text(x) for x in signal.get("domains", []) if _norm_text(x)]


def _metric_key(metric: dict[str, Any]) -> tuple[Any, ...]:
    numeric = metric.get("value_numeric")
    if isinstance(numeric, float):
        numeric = round(numeric, 8)
    return (
        _norm_text(metric.get("name")),
        numeric,
        _norm_text(metric.get("value_text")),
        _norm_text(metric.get("unit")),
        metric.get("as_of_date"),
        metric.get("as_of_year"),
        metric.get("as_of_month"),
        _norm_text(metric.get("as_of_precision")),
    )


def _location_key(location: dict[str, Any]) -> tuple[Any, ...]:
    return (
        _norm_text(location.get("country_iso2") or location.get("country")),
        _norm_text(location.get("admin1")),
        _norm_text(location.get("admin2")),
        _norm_text(location.get("locality")),
        _norm_text(location.get("region")),
        _norm_text(location.get("role")),
    )


def _host_key(host: dict[str, Any]) -> tuple[Any, ...]:
    return (
        _norm_text(host.get("canonical_name") or host.get("verbatim")),
        _norm_text(host.get("host_type")),
    )


def _evidence_key(evidence: dict[str, Any]) -> tuple[Any, ...]:
    return (
        _norm_text(evidence.get("type")),
        _norm_text(evidence.get("text")),
        evidence.get("page_number"),
    )


def _evidence_tokens(text: Any, *, remove_stopwords: bool = True) -> list[str]:
    normalized = _norm_text(text) or ""
    tokens = re.findall(r"[0-9a-záéíóúüñ]+", normalized, flags=re.IGNORECASE)
    if remove_stopwords:
        tokens = [token for token in tokens if token not in _EVIDENCE_STOPWORDS and len(token) > 1]
    return tokens


def _token_f1(gold_tokens: set[str], pred_tokens: set[str]) -> float:
    if not gold_tokens and not pred_tokens:
        return 1.0
    if not gold_tokens or not pred_tokens:
        return 0.0
    tp = len(gold_tokens & pred_tokens)
    precision = tp / len(pred_tokens)
    recall = tp / len(gold_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def evidence_support_similarity(gold: dict[str, Any], pred: dict[str, Any]) -> float:
    """Score whether two literal excerpts support the same proposition.

    This intentionally does *not* replace literal-evidence validation. It only avoids
    penalising two different contiguous quotations from the same source when one is a
    sufficient subspan of the other or when they have strong content-token overlap.
    """
    if _norm_text(gold.get("type")) != _norm_text(pred.get("type")):
        return 0.0
    gold_page = gold.get("page_number")
    pred_page = pred.get("page_number")
    if gold_page is not None and pred_page is not None and gold_page != pred_page:
        return 0.0

    g_text = _norm_text(gold.get("text")) or ""
    p_text = _norm_text(pred.get("text")) or ""
    if not g_text or not p_text:
        return 0.0
    if g_text == p_text:
        return 1.0

    g_tokens_all = set(_evidence_tokens(g_text, remove_stopwords=False))
    p_tokens_all = set(_evidence_tokens(p_text, remove_stopwords=False))
    g_content = set(_evidence_tokens(g_text, remove_stopwords=True))
    p_content = set(_evidence_tokens(p_text, remove_stopwords=True))

    # Guard against matching opposite claims that share most disease/context words.
    # This must run before containment: the positive clause may be a literal subspan
    # of the negative clause (e.g. "no se identificaron" vs "se identificaron").
    g_neg = bool(g_tokens_all & _NEGATION_TOKENS)
    p_neg = bool(p_tokens_all & _NEGATION_TOKENS)
    if g_neg != p_neg:
        return 0.0

    # A literal subspan is strong support if it contains enough substantive content.
    gold_is_shorter = len(g_text) <= len(p_text)
    shorter = g_text if gold_is_shorter else p_text
    container = p_text if gold_is_shorter else g_text
    shorter_content = g_content if gold_is_shorter else p_content
    if shorter in container and (len(shorter_content) >= 3 or len(shorter) >= 24):
        return 1.0

    # Numbers often carry the epidemiologic proposition. If both excerpts contain
    # numeric tokens but none agree, they should not be treated as equivalent support.
    g_numbers = {t for t in g_tokens_all if t.isdigit()}
    p_numbers = {t for t in p_tokens_all if t.isdigit()}
    if g_numbers and p_numbers and not (g_numbers & p_numbers):
        return 0.0

    if not g_content or not p_content:
        return 0.0
    overlap = g_content & p_content
    if len(overlap) < 3:
        return 0.0
    return round(_token_f1(g_content, p_content), 6)


def _evidence_support_f1(
    gold: list[dict[str, Any]],
    pred: list[dict[str, Any]],
    threshold: float = EVIDENCE_SUPPORT_THRESHOLD,
) -> tuple[float, list[EvidencePairMatch]]:
    if not gold and not pred:
        return 1.0, []
    if not gold or not pred:
        return 0.0, []

    candidates: list[EvidencePairMatch] = []
    for gi, g in enumerate(gold):
        for pi, p in enumerate(pred):
            score = evidence_support_similarity(g, p)
            if score >= threshold:
                candidates.append(EvidencePairMatch(gi, pi, score))
    candidates.sort(key=lambda item: (-item.score, item.gold_index, item.prediction_index))

    used_g: set[int] = set()
    used_p: set[int] = set()
    matches: list[EvidencePairMatch] = []
    for match in candidates:
        if match.gold_index in used_g or match.prediction_index in used_p:
            continue
        used_g.add(match.gold_index)
        used_p.add(match.prediction_index)
        matches.append(match)

    tp = len(matches)
    precision = tp / len(pred)
    recall = tp / len(gold)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return round(f1, 6), matches


def _event_date_key(signal: dict[str, Any]) -> tuple[Any, ...]:
    value = signal.get("event_date") or {}
    return (value.get("start"), value.get("end"), _norm_text(value.get("precision")))


def _temporal_point_key(point: dict[str, Any] | None) -> tuple[Any, ...]:
    point = point or {}
    return (
        point.get("date"),
        point.get("year"),
        point.get("month"),
        _norm_text(point.get("precision")),
    )


def _reference_period_key(signal: dict[str, Any]) -> tuple[Any, ...]:
    value = signal.get("reference_period") or {}
    return (
        _temporal_point_key(value.get("start")),
        _temporal_point_key(value.get("end")),
        _norm_text(value.get("period_type")),
    )


def _diagnostics_key(signal: dict[str, Any]) -> tuple[Any, ...]:
    value = signal.get("diagnostics") or {}
    return (
        bool(value.get("test_reported", False)),
        _norm_text(value.get("test_type")),
        _norm_text(value.get("method")),
        _norm_text(value.get("target")),
        _norm_text(value.get("specimen")),
        _norm_text(value.get("result")),
    )


def _normalization_status_key(signal: dict[str, Any]) -> tuple[Any, ...]:
    disease = signal.get("disease") or {}
    pathogen = signal.get("pathogen") or {}
    return (
        _norm_text(disease.get("normalization_status")),
        _norm_text(pathogen.get("normalization_status")),
    )


def signal_pair_components(gold: dict[str, Any], pred: dict[str, Any]) -> dict[str, float]:
    return {
        "signal_role": float(gold.get("signal_role") == pred.get("signal_role")),
        "signal_type": float(gold.get("signal_type") == pred.get("signal_type")),
        "disease": _entity_exact(gold.get("disease"), pred.get("disease")),
        "pathogen": _entity_exact(gold.get("pathogen"), pred.get("pathogen")),
        "metrics": _set_f1((_metric_key(x) for x in gold.get("metrics", [])), (_metric_key(x) for x in pred.get("metrics", []))),
        "locations": _set_f1((_location_key(x) for x in gold.get("locations", [])), (_location_key(x) for x in pred.get("locations", []))),
        "event_date": float(_event_date_key(gold) == _event_date_key(pred)),
        "reference_period": float(_reference_period_key(gold) == _reference_period_key(pred)),
        "diagnostics": float(_diagnostics_key(gold) == _diagnostics_key(pred)),
        "domains": _set_f1(_domains(gold), _domains(pred)),
    }


def signal_pair_score(gold: dict[str, Any], pred: dict[str, Any]) -> float:
    c = signal_pair_components(gold, pred)
    weights = {
        "signal_role": 0.18,
        "signal_type": 0.22,
        "disease": 0.12,
        "pathogen": 0.10,
        "metrics": 0.12,
        "locations": 0.10,
        "event_date": 0.06,
        "reference_period": 0.04,
        "diagnostics": 0.04,
        "domains": 0.02,
    }
    return round(sum(c[k] * weights[k] for k in weights), 6)


def _best_assignment_exact(
    gold: list[dict[str, Any]],
    pred: list[dict[str, Any]],
    threshold: float,
) -> list[PairMatch]:
    matrix = [[signal_pair_score(g, p) for p in pred] for g in gold]
    n_pred = len(pred)

    @lru_cache(maxsize=None)
    def dp(g_idx: int, used_mask: int) -> tuple[float, tuple[tuple[int, int, float], ...]]:
        if g_idx >= len(gold):
            return 0.0, ()

        best_score, best_pairs = dp(g_idx + 1, used_mask)  # allow gold signal to be unmatched
        for p_idx in range(n_pred):
            if used_mask & (1 << p_idx):
                continue
            score = matrix[g_idx][p_idx]
            if score < threshold:
                continue
            rest_score, rest_pairs = dp(g_idx + 1, used_mask | (1 << p_idx))
            total = score + rest_score
            candidate = ((g_idx, p_idx, score),) + rest_pairs
            if total > best_score + 1e-12 or (abs(total - best_score) <= 1e-12 and candidate < best_pairs):
                best_score, best_pairs = total, candidate
        return best_score, best_pairs

    _, pairs = dp(0, 0)
    return [PairMatch(g, p, s) for g, p, s in pairs]


def _best_assignment_greedy(
    gold: list[dict[str, Any]],
    pred: list[dict[str, Any]],
    threshold: float,
) -> list[PairMatch]:
    candidates: list[PairMatch] = []
    for gi, g in enumerate(gold):
        for pi, p in enumerate(pred):
            score = signal_pair_score(g, p)
            if score >= threshold:
                candidates.append(PairMatch(gi, pi, score))
    candidates.sort(key=lambda x: (-x.score, x.gold_index, x.prediction_index))
    used_g: set[int] = set()
    used_p: set[int] = set()
    result: list[PairMatch] = []
    for match in candidates:
        if match.gold_index in used_g or match.prediction_index in used_p:
            continue
        used_g.add(match.gold_index)
        used_p.add(match.prediction_index)
        result.append(match)
    return result


def match_signals(
    gold: list[dict[str, Any]],
    pred: list[dict[str, Any]],
    threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> list[PairMatch]:
    if len(pred) <= 15:
        return _best_assignment_exact(gold, pred, threshold)
    return _best_assignment_greedy(gold, pred, threshold)


def _prf(tp: int, fp: int, fn: int) -> dict[str, float | int]:
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
    }


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 1.0


def _signal_snapshot(signal: dict[str, Any]) -> dict[str, Any]:
    disease = signal.get("disease") or {}
    pathogen = signal.get("pathogen") or {}
    return {
        "local_signal_id": signal.get("local_signal_id"),
        "signal_role": signal.get("signal_role"),
        "signal_type": signal.get("signal_type"),
        "signal_summary": signal.get("signal_summary"),
        "disease": {
            "verbatim": disease.get("verbatim"),
            "canonical_name": disease.get("canonical_name"),
            "normalization_status": disease.get("normalization_status"),
        },
        "pathogen": {
            "verbatim": pathogen.get("verbatim"),
            "canonical_name": pathogen.get("canonical_name"),
            "normalization_status": pathogen.get("normalization_status"),
        },
        "domains": signal.get("domains", []),
        "metrics": [
            {"name": m.get("name"), "value_numeric": m.get("value_numeric"), "value_text": m.get("value_text")}
            for m in signal.get("metrics", [])
        ],
        "locations": [
            {
                "country": l.get("country"), "admin1": l.get("admin1"), "locality": l.get("locality"),
                "region": l.get("region"), "role": l.get("role"),
            }
            for l in signal.get("locations", [])
        ],
        "hosts": [
            {"verbatim": h.get("verbatim"), "canonical_name": h.get("canonical_name"), "host_type": h.get("host_type")}
            for h in signal.get("hosts", [])
        ],
        "diagnostics": signal.get("diagnostics"),
        "evidence": [e.get("text") for e in signal.get("evidence", [])],
    }


def evaluate_payloads(
    prediction: dict[str, Any],
    gold_standard: dict[str, Any],
    threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> dict[str, Any]:
    expected = gold_standard.get("expected", gold_standard)
    gold_signals = expected.get("signals", [])
    pred_signals = prediction.get("signals", [])

    matches = match_signals(gold_signals, pred_signals, threshold)
    matched_gold = {m.gold_index for m in matches}
    matched_pred = {m.prediction_index for m in matches}

    detection = _prf(
        tp=len(matches),
        fp=len(pred_signals) - len(matches),
        fn=len(gold_signals) - len(matches),
    )
    detection.update({
        "gold_signals": len(gold_signals),
        "predicted_signals": len(pred_signals),
        "matched_signals": len(matches),
    })

    field_values: dict[str, list[float]] = {
        "signal_role_accuracy": [],
        "signal_type_accuracy": [],
        "disease_accuracy": [],
        "pathogen_accuracy": [],
        "normalization_status_accuracy": [],
        "event_date_accuracy": [],
        "reference_period_accuracy": [],
        "diagnostics_accuracy": [],
        "domains_f1": [],
        "metrics_f1": [],
        "locations_f1": [],
        "hosts_f1": [],
        "evidence_exact_f1": [],
        "evidence_support_f1": [],
    }

    matched_details = []
    for match in matches:
        g = gold_signals[match.gold_index]
        p = pred_signals[match.prediction_index]
        components = signal_pair_components(g, p)
        field_values["signal_role_accuracy"].append(components["signal_role"])
        field_values["signal_type_accuracy"].append(components["signal_type"])
        field_values["disease_accuracy"].append(components["disease"])
        field_values["pathogen_accuracy"].append(components["pathogen"])
        field_values["normalization_status_accuracy"].append(float(_normalization_status_key(g) == _normalization_status_key(p)))
        field_values["event_date_accuracy"].append(components["event_date"])
        field_values["reference_period_accuracy"].append(components["reference_period"])
        field_values["diagnostics_accuracy"].append(components["diagnostics"])
        field_values["domains_f1"].append(components["domains"])
        field_values["metrics_f1"].append(components["metrics"])
        field_values["locations_f1"].append(components["locations"])
        field_values["hosts_f1"].append(_set_f1((_host_key(x) for x in g.get("hosts", [])), (_host_key(x) for x in p.get("hosts", []))))
        exact_evidence = _set_f1((_evidence_key(x) for x in g.get("evidence", [])), (_evidence_key(x) for x in p.get("evidence", [])))
        support_evidence, evidence_pairs = _evidence_support_f1(g.get("evidence", []), p.get("evidence", []))
        field_values["evidence_exact_f1"].append(exact_evidence)
        field_values["evidence_support_f1"].append(support_evidence)

        matched_details.append({
            "gold_signal_id": g.get("local_signal_id"),
            "predicted_signal_id": p.get("local_signal_id"),
            "match_score": match.score,
            "components": components,
            "evidence": {
                "exact_f1": exact_evidence,
                "support_f1": support_evidence,
                "support_pairs": [
                    {
                        "gold_index": pair.gold_index,
                        "prediction_index": pair.prediction_index,
                        "similarity": pair.score,
                    }
                    for pair in evidence_pairs
                ],
            },
        })

    field_metrics = {name: _mean(values) for name, values in field_values.items()}
    # Backward-compatible alias. From evaluation schema 0.2 onward, release gating
    # uses support equivalence; exact citation identity remains separately visible.
    field_metrics["evidence_f1"] = field_metrics["evidence_support_f1"]

    # Descriptive macro score. Avoid double-counting exact/support aliases: the
    # support metric is the evidence component used for release decisions.
    composite_fields = [
        "signal_role_accuracy", "signal_type_accuracy", "disease_accuracy", "pathogen_accuracy",
        "normalization_status_accuracy", "event_date_accuracy", "reference_period_accuracy",
        "diagnostics_accuracy", "domains_f1", "metrics_f1", "locations_f1", "hosts_f1",
        "evidence_support_f1",
    ]
    composite_inputs = [detection["f1"], *(field_metrics[name] for name in composite_fields)]
    composite = round(sum(composite_inputs) / len(composite_inputs), 6)

    report = {
        "evaluation_schema_version": "0.2",
        "gold_standard_version": gold_standard.get("gold_standard_version"),
        "case_code": gold_standard.get("case_code"),
        "document": expected.get("document", prediction.get("document")),
        "matching_threshold": threshold,
        "evidence_support_threshold": EVIDENCE_SUPPORT_THRESHOLD,
        "signal_detection": detection,
        "field_metrics": field_metrics,
        "composite_score": composite,
        "matched_signals": matched_details,
        "unmatched_gold": [
            _signal_snapshot(gold_signals[i]) for i in range(len(gold_signals)) if i not in matched_gold
        ],
        "unmatched_prediction": [
            _signal_snapshot(pred_signals[i]) for i in range(len(pred_signals)) if i not in matched_pred
        ],
    }

    # A single document is a calibration result, not enough evidence to unlock automated event matching.
    report["release_gate"] = {
        "single_document_pass": bool(
            detection["precision"] >= 0.90
            and detection["recall"] >= 0.90
            and field_metrics["signal_role_accuracy"] >= 0.90
            and field_metrics["signal_type_accuracy"] >= 0.85
            and field_metrics["evidence_support_f1"] >= 0.90
        ),
        "event_matcher_ready": False,
        "reason": "Se requiere un corpus adjudicado de múltiples documentos antes de habilitar event matching automático.",
    }
    return report


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)
