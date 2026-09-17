import json
from pathlib import Path

from onehealth_worker.evaluation.scoring_v046 import _evidence_support_f1, evidence_support_similarity
from onehealth_worker.extraction.assembly_v046 import assemble_claims_payload
from onehealth_worker.extraction.normalization import normalize_extraction_payload
from onehealth_worker.extraction.schema import validate_extraction


ROOT = Path(__file__).resolve().parents[3]
PRED = ROOT / "evaluation/predictions/mv-hondius"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _assemble(claims_name: str):
    payload = normalize_extraction_payload(assemble_claims_payload(_load(PRED / claims_name)))
    validate_extraction(payload)
    return payload


def test_v046_evidence_excerpt_is_textual_alias():
    gold = {"type": "text", "text": "se identificaron ocho casos a bordo del buque", "page_number": None}
    pred = {"type": "excerpt", "text": "se identificaron ocho casos a bordo del buque", "page_number": None}
    assert evidence_support_similarity(gold, pred) == 1.0


def test_v046_evidence_document_text_is_textual_alias():
    gold = {"type": "text", "text": "durante la SE 17 se identificaron tres casos nuevos", "page_number": None}
    pred = {"type": "document_text", "text": "durante la SE 17 se identificaron tres casos nuevos", "page_number": None}
    assert evidence_support_similarity(gold, pred) == 1.0


def test_v046_evidence_aliases_keep_negation_guard():
    gold = {"type": "text", "text": "no se notificaron casos de hantavirus", "page_number": None}
    pred = {"type": "document_text", "text": "se notificaron casos de hantavirus", "page_number": None}
    assert evidence_support_similarity(gold, pred) == 0.0


def test_v046_evidence_support_uses_many_to_many_coverage():
    gold = [
        {
            "type": "text",
            "text": "se identificaron ocho casos a bordo del buque, seis confirmados y dos probables",
            "page_number": None,
        }
    ]
    pred = [
        {"type": "text", "text": "se identificaron ocho casos a bordo del buque", "page_number": None},
        {"type": "text", "text": "seis confirmados y dos probables", "page_number": None},
    ]
    score, matches = _evidence_support_f1(gold, pred)
    assert score == 1.0
    assert {(m.gold_index, m.prediction_index) for m in matches} == {(0, 0), (0, 1)}


def test_v046_evidence_coverage_penalizes_unsupported_prediction_fragment():
    gold = [{"type": "text", "text": "se identificaron ocho casos a bordo del buque", "page_number": None}]
    pred = [
        {"type": "text", "text": "se identificaron ocho casos a bordo del buque", "page_number": None},
        {"type": "text", "text": "la temperatura máxima fue 31 grados", "page_number": None},
    ]
    score, _ = _evidence_support_f1(gold, pred)
    assert score < 1.0


def test_v046_initial_notification_keeps_individual_positive_diagnostic_as_case_report():
    prediction = _assemble("2026-05-04-v044-atomic-automatic.claims.json")
    case_signals = [s for s in prediction["signals"] if s["signal_type"] == "case_report"]
    assert any(
        any(m["name"] == "confirmed_cases" and m["value_numeric"] == 1 for m in signal["metrics"])
        for signal in case_signals
    )


def test_v046_se17_collective_lab_characterization_is_not_case_report():
    prediction = _assemble("2026-05-12-ben-se17-v044-atomic-automatic.claims.json")

    assert len(prediction["signals"]) == 6
    assert not any(
        signal["signal_type"] == "case_report" and "pcr" in signal.get("signal_summary", "").casefold()
        for signal in prediction["signals"]
    )

    lab = [s for s in prediction["signals"] if s["signal_type"] == "laboratory_result"]
    assert len(lab) == 1
    assert lab[0]["pathogen"]["canonical_name"] == "Andes virus"
    assert lab[0]["genomics"]["sequence_reported"] is True
    assert "genomic" in lab[0]["domains"]


def test_v046_se18_merges_operational_mobility_into_intervention_and_surveillance_snapshot():
    prediction = _assemble("2026-05-19-ben-se18-v044-atomic-automatic.claims.json")

    assert len(prediction["signals"]) == 5
    assert not any(
        signal["signal_type"] == "laboratory_investigation"
        and "investigando el origen del brote" in signal.get("signal_summary", "").casefold()
        for signal in prediction["signals"]
    )
    assert not any(
        signal["signal_type"] == "travel_or_mobility"
        and "inei-anlis" in signal.get("signal_summary", "").casefold()
        for signal in prediction["signals"]
    )

    interventions = [s for s in prediction["signals"] if s["signal_type"] == "intervention"]
    assert len(interventions) == 1
    assert "tierra del fuego" in interventions[0]["signal_summary"].casefold()

    baselines = [s for s in prediction["signals"] if s["signal_role"] == "surveillance_baseline"]
    assert len(baselines) == 1
    values = {m["value_numeric"] for m in baselines[0]["metrics"]}
    assert {3, 105}.issubset(values)


def test_v046_se19_merges_weekly_zero_and_season_total_into_one_surveillance_snapshot():
    prediction = _assemble("2026-05-26-ben-se19-v044-atomic-automatic.claims.json")

    assert len(prediction["signals"]) == 4
    assert not any(
        signal["signal_type"] == "laboratory_investigation"
        and "investigaci" in signal.get("signal_summary", "").casefold()
        for signal in prediction["signals"]
    )

    baselines = [s for s in prediction["signals"] if s["signal_role"] == "surveillance_baseline"]
    assert len(baselines) == 1
    values = {m["value_numeric"] for m in baselines[0]["metrics"]}
    assert {0, 106}.issubset(values)
