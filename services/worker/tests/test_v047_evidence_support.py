from onehealth_worker.evaluation.scoring_v047 import (
    _evidence_support_f1,
    evaluate_payloads,
    evidence_support_similarity,
    signal_pair_components,
)


def _evidence(text: str) -> dict:
    return {
        "type": "text",
        "text": text,
        "page_number": None,
    }


def test_v047_compound_count_can_be_supported_by_atomic_fragments():
    """
    A single adjudicated compound statement may legitimately be represented
    by several literal atomic excerpts.

    BEN SE18 pattern:
      11 cases = 8 confirmed + 2 probable + 1 inconclusive.

    The fragment set as a whole supports the gold proposition even though
    not every fragment independently exceeds the evidence threshold.
    """
    gold = [
        _evidence(
            "se identificaron 11 casos: "
            "8 confirmados, 2 probables y 1 inconcluso"
        )
    ]

    prediction = [
        _evidence("se identificaron 11 casos"),
        _evidence("8 confirmados"),
        _evidence("2 probables"),
        _evidence("1 inconcluso"),
    ]

    score, matches = _evidence_support_f1(gold, prediction)

    assert score == 1.0
    assert {match.prediction_index for match in matches} == {0, 1, 2, 3}


def test_v047_mixed_positive_negative_statement_can_be_supported_by_fragments():
    """
    Tierra del Fuego pattern.

    One gold excerpt contains both:
      - a positive sampling count; and
      - an explicit negative wildlife observation.

    Splitting the source sentence into literal atomic excerpts must not make
    the positive clause fail merely because the combined gold sentence also
    contains a negation.
    """
    gold = [
        _evidence(
            "durante esos operativos se capturaron 144 roedores "
            "y no se identificaron ejemplares de Oligoryzomys longicaudatus"
        )
    ]

    prediction = [
        _evidence(
            "durante esos operativos se capturaron 144 roedores"
        ),
        _evidence(
            "no se identificaron ejemplares de Oligoryzomys longicaudatus"
        ),
    ]

    score, matches = _evidence_support_f1(gold, prediction)

    assert score == 1.0
    assert {match.prediction_index for match in matches} == {0, 1}


def test_v047_fragment_support_must_preserve_negation_and_number_guards():
    """
    Fragment-set support must not weaken the v0.4.6 contradiction guards.

    Opposite polarity and incompatible epidemiologic counts must remain
    non-equivalent.
    """
    positive = _evidence(
        "se identificaron ejemplares de Oligoryzomys longicaudatus"
    )
    negative = _evidence(
        "no se identificaron ejemplares de Oligoryzomys longicaudatus"
    )

    assert evidence_support_similarity(positive, negative) == 0.0

    three_probable = _evidence("se identificaron 3 casos probables")
    two_probable = _evidence("se identificaron 2 casos probables")

    assert evidence_support_similarity(
        three_probable,
        two_probable,
    ) == 0.0


def _surveillance_signal(metrics: list[dict]) -> dict:
    return {
        "signal_role": "surveillance_baseline",
        "signal_type": "case_report",
        "domains": ["human"],
        "disease": {
            "verbatim": "hantavirus",
            "canonical_name": "Hantavirus disease",
        },
        "pathogen": {
            "verbatim": "hantavirus",
            "canonical_name": "Hantavirus",
        },
        "metrics": metrics,
        "locations": [],
        "event_date": {
            "start": None,
            "end": None,
            "precision": "unknown",
        },
        "reference_period": {
            "start": {
                "date": None,
                "year": None,
                "month": None,
                "precision": "unknown",
            },
            "end": {
                "date": None,
                "year": None,
                "month": None,
                "precision": "unknown",
            },
            "period_type": "unknown",
        },
        "diagnostics": {
            "test_reported": False,
            "test_type": None,
            "method": None,
            "target": None,
            "specimen": None,
            "result": "unknown",
        },
    }


def test_v047_surveillance_metric_aliases_and_sparse_metadata_are_equivalent():
    """
    SE18 pattern.

    Provider-facing atomic claims and adjudicated gold can use different
    metric labels and different amounts of descriptive metadata while
    representing the same epidemiologic quantity.

    Equivalence requires:
      - an explicit canonical metric alias;
      - the same numeric value;
      - no contradictory temporal metadata.

    Missing optional metadata must not create a false mismatch.
    """
    gold = _surveillance_signal(
        [
            {
                "name": "new_cases",
                "value_numeric": 3,
                "value_text": "tres casos nuevos",
                "unit": "persons",
                "as_of_date": None,
                "as_of_year": 2026,
                "as_of_month": None,
                "as_of_precision": "year",
            },
            {
                "name": "confirmed_cases",
                "value_numeric": 105,
                "value_text": "105 confirmados",
                "unit": "persons",
                "as_of_date": None,
                "as_of_year": 2026,
                "as_of_month": None,
                "as_of_precision": "year",
            },
        ]
    )

    prediction = _surveillance_signal(
        [
            {
                "name": "cases_new",
                "value_numeric": 3,
                "value_text": None,
                "unit": "cases",
                "as_of_date": None,
                "as_of_year": None,
                "as_of_month": None,
                "as_of_precision": "unknown",
            },
            {
                "name": "cases_confirmed_total",
                "value_numeric": 105,
                "value_text": None,
                "unit": "cases",
                "as_of_date": None,
                "as_of_year": None,
                "as_of_month": None,
                "as_of_precision": "unknown",
            },
        ]
    )

    components = signal_pair_components(gold, prediction)

    assert components["metrics"] == 1.0

def test_v047_evaluate_payloads_uses_metric_aliases_without_recursion():
    gold_signal = _surveillance_signal(
        [
            {
                "name": "new_cases",
                "value_numeric": 3,
                "value_text": "tres casos nuevos",
                "unit": "persons",
                "as_of_date": None,
                "as_of_year": 2026,
                "as_of_month": None,
                "as_of_precision": "year",
            }
        ]
    )

    prediction_signal = _surveillance_signal(
        [
            {
                "name": "cases_new",
                "value_numeric": 3,
                "value_text": None,
                "unit": "cases",
                "as_of_date": None,
                "as_of_year": None,
                "as_of_month": None,
                "as_of_precision": "unknown",
            }
        ]
    )

    gold_signal["local_signal_id"] = "GOLD-1"
    prediction_signal["local_signal_id"] = "PRED-1"

    gold = {
        "expected": {
            "signals": [gold_signal],
        }
    }

    prediction = {
        "signals": [prediction_signal],
    }

    report = evaluate_payloads(prediction, gold)

    assert report["signal_detection"]["f1"] == 1.0
    assert report["field_metrics"]["metrics_f1"] == 1.0

def test_v047_corpus_router_selects_v047_evaluator():
    from onehealth_worker.evaluation import corpus
    from onehealth_worker.evaluation.scoring_v046 import (
        evaluate_payloads as evaluate_payloads_v046,
    )
    from onehealth_worker.evaluation.scoring_v047 import (
        evaluate_payloads as evaluate_payloads_v047,
    )

    assert corpus._select_evaluator("0.4.7") is evaluate_payloads_v047
    assert corpus._select_evaluator("0.4.6") is evaluate_payloads_v046

def test_v047_short_numeric_fragments_can_cover_compound_count_evidence():
    """
    V047-05.

    Short atomic numeric fragments may jointly support a compound
    epidemiologic statement when their numbers and concepts agree.

    SE18 pattern:
      11 total
      8 confirmed
      2 probable
      1 inconclusive

    The rule must remain numerically strict: 7 confirmed must not be
    accepted as support for 8 confirmed.
    """
    gold = [
        _evidence(
            "al 13 de mayo, se identificaron 11 casos: "
            "8 confirmados (todos cepa Andes), "
            "2 probables y 1 inconcluso."
        )
    ]

    correct_prediction = [
        _evidence(
            "al 13 de mayo, se identificaron 11 casos:"
        ),
        _evidence("8 confirmados"),
        _evidence("2 probables"),
        _evidence("1 inconcluso"),
    ]

    correct_score, correct_matches = _evidence_support_f1(
        gold,
        correct_prediction,
    )

    assert correct_score == 1.0
    assert {
        match.prediction_index
        for match in correct_matches
    } == {0, 1, 2, 3}

    wrong_prediction = [
        _evidence(
            "al 13 de mayo, se identificaron 11 casos:"
        ),
        _evidence("7 confirmados"),
        _evidence("2 probables"),
        _evidence("1 inconcluso"),
    ]

    wrong_score, _ = _evidence_support_f1(
        gold,
        wrong_prediction,
    )

    assert wrong_score < 1.0


def test_v047_compound_evidence_can_split_at_sentence_boundary():
    """
    V047-06.

    A gold excerpt may contain two consecutive sentences while the atomic
    prediction preserves each proposition as a separate literal excerpt.

    SE19 pattern:
      no new cases.
      cumulative total remains 106 confirmed.
    """
    gold = [
        _evidence(
            "A nivel nacional, no se notificó ningún caso de hantavirus "
            "durante la SE 19. "
            "El total de casos de toda la temporada 2025-2026 "
            "se mantiene en 106 confirmados."
        )
    ]

    prediction = [
        _evidence(
            "A nivel nacional, no se notificó ningún caso de hantavirus "
            "durante la SE 19."
        ),
        _evidence(
            "El total de casos de toda la temporada 2025-2026 "
            "se mantiene en 106 confirmados."
        ),
    ]

    score, matches = _evidence_support_f1(
        gold,
        prediction,
    )

    assert score == 1.0
    assert {
        match.prediction_index
        for match in matches
    } == {0, 1}


def test_v047_additional_literal_evidence_does_not_reduce_gold_support():
    """
    V047-07.

    evidence_support measures whether the adjudicated proposition is
    sufficiently supported. Additional literal evidence belonging to the
    same canonical signal must not automatically reduce gold coverage.

    Exact evidence-set agreement remains independently visible through
    evidence_exact_f1.
    """
    gold = [
        _evidence(
            "Durante la SE 17 se identificaron tres casos nuevos"
        )
    ]

    prediction = [
        _evidence(
            "Durante la SE 17 se identificaron tres casos nuevos"
        ),
        _evidence(
            "el total de casos de la temporada 2025-2026 "
            "asciende a 105 confirmados."
        ),
    ]

    score, matches = _evidence_support_f1(
        gold,
        prediction,
    )

    assert score == 1.0

    assert any(
        match.prediction_index == 0
        for match in matches
    )


def test_v047_related_causal_inference_is_not_automatic_evidence_equivalence():
    """
    V047-08.

    Semantic relatedness is not sufficient for evidence equivalence.

    Tierra del Fuego pattern:
      genomic non-relatedness
    versus
      epidemiologic source refutation.

    The latter may be an inference supported by the former in context,
    but the evaluator must not manufacture that equivalence from lexical
    or conceptual similarity alone.
    """
    genomic_difference = _evidence(
        "la variante viral hallada en los roedores de Tierra del Fuego "
        "es diferente de la observada en los casos humanos asociados "
        "al brote investigado."
    )

    source_refutation = _evidence(
        "la investigación permitió descartar que los roedores analizados "
        "hayan sido la fuente de infección vinculada a ese evento."
    )

    similarity = evidence_support_similarity(
        genomic_difference,
        source_refutation,
    )

    assert similarity < 0.70

    score, matches = _evidence_support_f1(
        [genomic_difference],
        [source_refutation],
    )

    assert score == 0.0
    assert matches == []