from __future__ import annotations

from typing import Any
import re

from . import scoring as _base
from .scoring_v046 import evidence_support_similarity


DEFAULT_MATCH_THRESHOLD = _base.DEFAULT_MATCH_THRESHOLD
EVIDENCE_SUPPORT_THRESHOLD = _base.EVIDENCE_SUPPORT_THRESHOLD
EvidencePairMatch = _base.EvidencePairMatch

# Keep an immutable reference to the historical component scorer.
# evaluate_payloads temporarily monkey-patches _base.signal_pair_components,
# so v0.4.7 must not call that mutable global reference recursively.
_BASE_SIGNAL_PAIR_COMPONENTS = _base.signal_pair_components

_TEXTUAL_EVIDENCE_TYPES = {
    "text",
    "quote",
    "excerpt",
    "document_text",
}


# ---------------------------------------------------------------------------
# Metric normalization
# ---------------------------------------------------------------------------

_METRIC_NAME_ALIASES = {
    "new_cases": "new_cases",
    "cases_new": "new_cases",
    "confirmed_cases": "confirmed_cases",
    "cases_confirmed_total": "confirmed_cases",
}


_COUNT_UNIT_ALIASES = {
    "case": "count",
    "cases": "count",
    "person": "count",
    "persons": "count",
    "people": "count",
}


def _canonical_evidence_type(value: Any) -> str | None:
    normalized = _base._norm_text(value)

    if normalized in _TEXTUAL_EVIDENCE_TYPES:
        return "text"

    return normalized


def _canonical_metric_name(value: Any) -> str | None:
    normalized = _base._norm_text(value)

    if normalized is None:
        return None

    return _METRIC_NAME_ALIASES.get(
        normalized,
        normalized,
    )


def _canonical_metric_unit(value: Any) -> str | None:
    normalized = _base._norm_text(value)

    if normalized is None:
        return None

    return _COUNT_UNIT_ALIASES.get(
        normalized,
        normalized,
    )


def _normalized_numeric(value: Any) -> float | int | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return round(value, 8)

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    if numeric.is_integer():
        return int(numeric)

    return round(numeric, 8)


def _optional_values_compatible(
    gold_value: Any,
    pred_value: Any,
) -> bool:
    """Missing metadata is compatible; contradictory explicit metadata is not."""
    if gold_value is None or pred_value is None:
        return True

    return gold_value == pred_value


def _metric_temporally_compatible(
    gold: dict[str, Any],
    pred: dict[str, Any],
) -> bool:
    """Reject explicit temporal contradictions while allowing sparse metadata."""
    if not _optional_values_compatible(
        gold.get("as_of_date"),
        pred.get("as_of_date"),
    ):
        return False

    if not _optional_values_compatible(
        gold.get("as_of_year"),
        pred.get("as_of_year"),
    ):
        return False

    if not _optional_values_compatible(
        gold.get("as_of_month"),
        pred.get("as_of_month"),
    ):
        return False

    return True


def _metric_equivalent(
    gold: dict[str, Any],
    pred: dict[str, Any],
) -> bool:
    """Conservative semantic equivalence for known metric representations."""
    gold_name = _canonical_metric_name(
        gold.get("name")
    )
    pred_name = _canonical_metric_name(
        pred.get("name")
    )

    if gold_name != pred_name:
        return False

    gold_numeric = _normalized_numeric(
        gold.get("value_numeric")
    )
    pred_numeric = _normalized_numeric(
        pred.get("value_numeric")
    )

    if (
        gold_numeric is not None
        and pred_numeric is not None
    ):
        if gold_numeric != pred_numeric:
            return False
    else:
        gold_text = _base._norm_text(
            gold.get("value_text")
        )
        pred_text = _base._norm_text(
            pred.get("value_text")
        )

        if (
            gold_text is not None
            and pred_text is not None
            and gold_text != pred_text
        ):
            return False

        # If neither side provides comparable numeric or textual value,
        # equivalence cannot be established safely.
        if (
            gold_numeric is None
            and pred_numeric is None
            and (
                gold_text is None
                or pred_text is None
            )
        ):
            return False

    gold_unit = _canonical_metric_unit(
        gold.get("unit")
    )
    pred_unit = _canonical_metric_unit(
        pred.get("unit")
    )

    if (
        gold_unit is not None
        and pred_unit is not None
        and gold_unit != pred_unit
    ):
        return False

    if not _metric_temporally_compatible(
        gold,
        pred,
    ):
        return False

    return True


def _metric_support_f1(
    gold: list[dict[str, Any]],
    pred: list[dict[str, Any]],
) -> float:
    """One-to-one matching using conservative metric equivalence."""
    if not gold and not pred:
        return 1.0

    if not gold or not pred:
        return 0.0

    matched_pred: set[int] = set()
    matched_gold = 0

    for gold_metric in gold:
        match_index: int | None = None

        for pred_index, pred_metric in enumerate(pred):
            if pred_index in matched_pred:
                continue

            if _metric_equivalent(
                gold_metric,
                pred_metric,
            ):
                match_index = pred_index
                break

        if match_index is not None:
            matched_gold += 1
            matched_pred.add(match_index)

    precision = matched_gold / len(pred)
    recall = matched_gold / len(gold)

    if precision + recall == 0:
        return 0.0

    return round(
        2 * precision * recall / (precision + recall),
        6,
    )


def signal_pair_components(
    gold: dict[str, Any],
    pred: dict[str, Any],
) -> dict[str, float]:
    """Historical signal components with v0.4.7 metric semantics."""
    components = _BASE_SIGNAL_PAIR_COMPONENTS(
        gold,
        pred,
    )

    components["metrics"] = _metric_support_f1(
        gold.get("metrics", []),
        pred.get("metrics", []),
    )

    return components


# ---------------------------------------------------------------------------
# Evidence composition
# ---------------------------------------------------------------------------

def _split_evidence_clauses(
    text: str | None,
) -> list[str]:
    """Split only structurally strong compound evidence boundaries.

    v0.4.7 recognizes:
    - semicolon and colon boundaries;
    - sentence boundaries;
    - commas immediately before numeric clauses;
    - Spanish conjunctions ``y`` / ``e`` only when followed by
      a numeric or explicit negative clause.

    This deliberately avoids splitting ordinary prose such as:
        "A nivel nacional, no se notificó..."
    or:
        "...otro a Jujuy y otro a Chubut."

    The splitter is used only for evidence composition.
    """
    if not text:
        return []

    parts = re.split(
        r"(?:"
        r"\s*;\s*"
        r"|\s*:\s*"
        r"|(?<=[.!?])\s+"
        r"|,\s*(?=\d)"
        r"|\s+(?:y|e)\s+(?=(?:\d|no\b|sin\b))"
        r")",
        str(text).strip(),
        flags=re.IGNORECASE,
    )

    return [
        part.strip(" \t\r\n,;:.")
        for part in parts
        if part
        and part.strip(" \t\r\n,;:.")
    ]

def _clause_evidence(
    evidence: dict[str, Any],
    clause: str,
) -> dict[str, Any]:
    """Create an evidence object for one literal clause."""
    result = dict(evidence)
    result["text"] = clause
    return result


def _short_literal_fragment_similarity(
    gold: dict[str, Any],
    pred: dict[str, Any],
) -> float:
    """Conservative support for very short atomic numeric fragments.

    Examples:
      "8 confirmados (todos cepa Andes)" <- "8 confirmados"
      "2 probables"                      <- "2 probables"

    This is deliberately not a general semantic-similarity rule.
    """
    if (
        _canonical_evidence_type(
            gold.get("type")
        )
        != _canonical_evidence_type(
            pred.get("type")
        )
    ):
        return 0.0

    gold_page = gold.get("page_number")
    pred_page = pred.get("page_number")

    if (
        gold_page is not None
        and pred_page is not None
        and gold_page != pred_page
    ):
        return 0.0

    g_text = (
        _base._norm_text(
            gold.get("text")
        )
        or ""
    )

    p_text = (
        _base._norm_text(
            pred.get("text")
        )
        or ""
    )

    if not g_text or not p_text:
        return 0.0

    g_tokens_all = set(
        _base._evidence_tokens(
            g_text,
            remove_stopwords=False,
        )
    )

    p_tokens_all = set(
        _base._evidence_tokens(
            p_text,
            remove_stopwords=False,
        )
    )

    g_neg = bool(
        g_tokens_all
        & _base._NEGATION_TOKENS
    )

    p_neg = bool(
        p_tokens_all
        & _base._NEGATION_TOKENS
    )

    if g_neg != p_neg:
        return 0.0

    g_numbers = {
        token
        for token in g_tokens_all
        if token.isdigit()
    }

    p_numbers = {
        token
        for token in p_tokens_all
        if token.isdigit()
    }

    # For short numeric fragments the proposition must agree numerically.
    if g_numbers or p_numbers:
        if g_numbers != p_numbers:
            return 0.0

    g_content = set(
        _base._evidence_tokens(
            g_text,
            remove_stopwords=True,
        )
    )

    p_content = set(
        _base._evidence_tokens(
            p_text,
            remove_stopwords=True,
        )
    )

    if not g_content or not p_content:
        return 0.0

    if len(g_content) <= len(p_content):
        shorter = g_content
        longer = p_content
    else:
        shorter = p_content
        longer = g_content

    # Restrict this fallback to genuinely short atomic fragments.
    if len(shorter) > 2:
        return 0.0

    if not shorter.issubset(longer):
        return 0.0

    return 1.0


def _compound_fragment_matches(
    gold: list[dict[str, Any]],
    pred: list[dict[str, Any]],
    threshold: float = EVIDENCE_SUPPORT_THRESHOLD,
) -> list[EvidencePairMatch]:
    """Find prediction fragments that jointly cover compound gold evidence.

    Every clause in a compound gold excerpt must be supported.
    """
    compound_matches: list[
        EvidencePairMatch
    ] = []

    for gi, gold_evidence in enumerate(gold):
        clauses = _split_evidence_clauses(
            gold_evidence.get("text")
        )

        if len(clauses) < 2:
            continue

        clause_matches: list[
            EvidencePairMatch
        ] = []

        complete = True

        for clause in clauses:
            clause_evidence = _clause_evidence(
                gold_evidence,
                clause,
            )

            best_match: (
                EvidencePairMatch | None
            ) = None

            for pi, pred_evidence in enumerate(pred):
                score = evidence_support_similarity(
                    clause_evidence,
                    pred_evidence,
                )

                if score < threshold:
                    score = (
                        _short_literal_fragment_similarity(
                            clause_evidence,
                            pred_evidence,
                        )
                    )

                if score < threshold:
                    continue

                candidate = EvidencePairMatch(
                    gi,
                    pi,
                    score,
                )

                if (
                    best_match is None
                    or candidate.score
                    > best_match.score
                    or (
                        candidate.score
                        == best_match.score
                        and candidate.prediction_index
                        < best_match.prediction_index
                    )
                ):
                    best_match = candidate

            if best_match is None:
                complete = False
                break

            clause_matches.append(
                best_match
            )

        if complete:
            compound_matches.extend(
                clause_matches
            )

    # Deduplicate clauses that selected the same prediction evidence.
    best_by_pair: dict[
        tuple[int, int],
        EvidencePairMatch,
    ] = {}

    for match in compound_matches:
        key = (
            match.gold_index,
            match.prediction_index,
        )

        previous = best_by_pair.get(
            key
        )

        if (
            previous is None
            or match.score > previous.score
        ):
            best_by_pair[key] = match

    matches = list(
        best_by_pair.values()
    )

    matches.sort(
        key=lambda item: (
            -item.score,
            item.gold_index,
            item.prediction_index,
        )
    )

    return matches


def _evidence_support_f1(
    gold: list[dict[str, Any]],
    pred: list[dict[str, Any]],
    threshold: float = EVIDENCE_SUPPORT_THRESHOLD,
) -> tuple[
    float,
    list[EvidencePairMatch],
]:
    """Measure coverage of adjudicated evidence.

    v0.4.7 treats evidence_support as coverage of gold propositions.

    Additional literal prediction evidence does not automatically reduce
    support when the adjudicated gold proposition is already supported.

    For structurally compound gold evidence, a shorter prediction fragment
    must not support the whole gold excerpt by containment alone. In that
    case all component clauses must be covered by the compound matcher.

    Exact evidence-set agreement remains independently measurable through
    evidence_exact_f1.
    """
    if not gold and not pred:
        return 1.0, []

    if not gold or not pred:
        return 0.0, []

    matches: list[
        EvidencePairMatch
    ] = []

    # Historical pairwise support.
    #
    # Important v0.4.7 guard:
    # If gold contains multiple structurally meaningful clauses, do not let
    # one shorter prediction subspan mark the entire compound proposition
    # as supported. Exact/full gold containment in the prediction is still
    # accepted directly.
    for gi, gold_evidence in enumerate(gold):
        gold_text = (
            _base._norm_text(
                gold_evidence.get("text")
            )
            or ""
        )

        gold_clauses = _split_evidence_clauses(
            gold_evidence.get("text")
        )

        gold_is_compound = (
            len(gold_clauses) >= 2
        )

        for pi, pred_evidence in enumerate(pred):
            pred_text = (
                _base._norm_text(
                    pred_evidence.get("text")
                )
                or ""
            )

            if gold_is_compound:
                # Direct support is valid only when the complete gold
                # excerpt is literally preserved in the prediction.
                #
                # A shorter fragment must instead pass through compound
                # clause coverage below.
                complete_gold_is_present = (
                    bool(gold_text)
                    and bool(pred_text)
                    and gold_text in pred_text
                )

                if not complete_gold_is_present:
                    continue

            score = evidence_support_similarity(
                gold_evidence,
                pred_evidence,
            )

            if score >= threshold:
                matches.append(
                    EvidencePairMatch(
                        gi,
                        pi,
                        score,
                    )
                )

    # v0.4.7 compound evidence composition.
    #
    # A compound gold excerpt becomes supported only when every clause
    # finds qualifying literal prediction evidence.
    matches.extend(
        _compound_fragment_matches(
            gold,
            pred,
            threshold=threshold,
        )
    )

    # Deduplicate direct and compound matches.
    best_by_pair: dict[
        tuple[int, int],
        EvidencePairMatch,
    ] = {}

    for match in matches:
        key = (
            match.gold_index,
            match.prediction_index,
        )

        previous = best_by_pair.get(
            key
        )

        if (
            previous is None
            or match.score > previous.score
        ):
            best_by_pair[key] = match

    matches = list(
        best_by_pair.values()
    )

    matches.sort(
        key=lambda item: (
            -item.score,
            item.gold_index,
            item.prediction_index,
        )
    )

    supported_gold = {
        match.gold_index
        for match in matches
    }

    support = (
        len(supported_gold)
        / len(gold)
    )

    return round(
        support,
        6,
    ), matches

# ---------------------------------------------------------------------------
# Public evaluator
# ---------------------------------------------------------------------------

def evaluate_payloads(
    prediction: dict[str, Any],
    gold_standard: dict[str, Any],
    threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> dict[str, Any]:
    """Run stable evaluation with v0.4.7 metric and evidence semantics.

    The historical base scorer remains unchanged. v0.4.7 behavior is
    injected only for the duration of this evaluation call.
    """
    old_types = (
        _base._TEXTUAL_EVIDENCE_TYPES
    )

    old_support = (
        _base._evidence_support_f1
    )

    old_signal_pair_components = (
        _base.signal_pair_components
    )

    try:
        _base._TEXTUAL_EVIDENCE_TYPES = set(
            _TEXTUAL_EVIDENCE_TYPES
        )

        _base._evidence_support_f1 = (
            _evidence_support_f1
        )

        _base.signal_pair_components = (
            signal_pair_components
        )

        return _base.evaluate_payloads(
            prediction,
            gold_standard,
            threshold=threshold,
        )

    finally:
        _base._TEXTUAL_EVIDENCE_TYPES = (
            old_types
        )

        _base._evidence_support_f1 = (
            old_support
        )

        _base.signal_pair_components = (
            old_signal_pair_components
        )