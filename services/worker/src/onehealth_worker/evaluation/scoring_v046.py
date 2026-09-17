from __future__ import annotations

from typing import Any

from . import scoring as _base


DEFAULT_MATCH_THRESHOLD = _base.DEFAULT_MATCH_THRESHOLD
EVIDENCE_SUPPORT_THRESHOLD = _base.EVIDENCE_SUPPORT_THRESHOLD
EvidencePairMatch = _base.EvidencePairMatch

_TEXTUAL_EVIDENCE_TYPES = {"text", "quote", "excerpt", "document_text"}


def _canonical_evidence_type(value: Any) -> str | None:
    normalized = _base._norm_text(value)
    if normalized in _TEXTUAL_EVIDENCE_TYPES:
        return "text"
    return normalized


def evidence_support_similarity(gold: dict[str, Any], pred: dict[str, Any]) -> float:
    """v0.4.6 evidence-support similarity.

    All observed literal textual evidence labels are canonicalized to one textual
    class. Negation, page and incompatible-number guards remain unchanged.
    """
    if _canonical_evidence_type(gold.get("type")) != _canonical_evidence_type(pred.get("type")):
        return 0.0

    gold_page = gold.get("page_number")
    pred_page = pred.get("page_number")
    if gold_page is not None and pred_page is not None and gold_page != pred_page:
        return 0.0

    g_text = _base._norm_text(gold.get("text")) or ""
    p_text = _base._norm_text(pred.get("text")) or ""
    if not g_text or not p_text:
        return 0.0
    if g_text == p_text:
        return 1.0

    g_tokens_all = set(_base._evidence_tokens(g_text, remove_stopwords=False))
    p_tokens_all = set(_base._evidence_tokens(p_text, remove_stopwords=False))
    g_content = set(_base._evidence_tokens(g_text, remove_stopwords=True))
    p_content = set(_base._evidence_tokens(p_text, remove_stopwords=True))

    g_neg = bool(g_tokens_all & _base._NEGATION_TOKENS)
    p_neg = bool(p_tokens_all & _base._NEGATION_TOKENS)
    if g_neg != p_neg:
        return 0.0

    gold_is_shorter = len(g_text) <= len(p_text)
    shorter = g_text if gold_is_shorter else p_text
    container = p_text if gold_is_shorter else g_text
    shorter_content = g_content if gold_is_shorter else p_content
    if shorter in container and (len(shorter_content) >= 3 or len(shorter) >= 24):
        return 1.0

    g_numbers = {token for token in g_tokens_all if token.isdigit()}
    p_numbers = {token for token in p_tokens_all if token.isdigit()}
    if g_numbers and p_numbers and not (g_numbers & p_numbers):
        return 0.0

    if not g_content or not p_content:
        return 0.0
    overlap = g_content & p_content
    if len(overlap) < 3:
        return 0.0
    return round(_base._token_f1(g_content, p_content), 6)


def _evidence_support_f1(
    gold: list[dict[str, Any]],
    pred: list[dict[str, Any]],
    threshold: float = EVIDENCE_SUPPORT_THRESHOLD,
) -> tuple[float, list[EvidencePairMatch]]:
    """Measure evidence support as many-to-many coverage rather than 1:1 identity.

    A canonical signal can legitimately contain several literal atomic-claim excerpts
    that jointly support one gold excerpt. Extra unsupported prediction excerpts still
    reduce precision, and unsupported gold excerpts still reduce recall.
    """
    if not gold and not pred:
        return 1.0, []
    if not gold or not pred:
        return 0.0, []

    matches: list[EvidencePairMatch] = []
    for gi, gold_evidence in enumerate(gold):
        for pi, pred_evidence in enumerate(pred):
            score = evidence_support_similarity(gold_evidence, pred_evidence)
            if score >= threshold:
                matches.append(EvidencePairMatch(gi, pi, score))

    matches.sort(key=lambda item: (-item.score, item.gold_index, item.prediction_index))
    supported_gold = {match.gold_index for match in matches}
    supported_pred = {match.prediction_index for match in matches}

    precision = len(supported_pred) / len(pred)
    recall = len(supported_gold) / len(gold)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return round(f1, 6), matches


def evaluate_payloads(
    prediction: dict[str, Any],
    gold_standard: dict[str, Any],
    threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> dict[str, Any]:
    """Run the stable evaluator with v0.4.6 evidence semantics.

    The base scorer remains untouched so historical v0.4.5 tests stay reproducible.
    During this call only, exact evidence keys recognize the expanded textual aliases
    and support scoring uses many-to-many coverage.
    """
    old_types = _base._TEXTUAL_EVIDENCE_TYPES
    old_support = _base._evidence_support_f1
    try:
        _base._TEXTUAL_EVIDENCE_TYPES = set(_TEXTUAL_EVIDENCE_TYPES)
        _base._evidence_support_f1 = _evidence_support_f1
        return _base.evaluate_payloads(prediction, gold_standard, threshold=threshold)
    finally:
        _base._TEXTUAL_EVIDENCE_TYPES = old_types
        _base._evidence_support_f1 = old_support
