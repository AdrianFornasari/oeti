import json
from pathlib import Path

from onehealth_worker.evaluation.scoring import evaluate_payloads, evidence_support_similarity
from onehealth_worker.extraction.assembly_v045 import assemble_claims_payload
from onehealth_worker.extraction.normalization import normalize_extraction_payload
from onehealth_worker.extraction.schema import validate_extraction


ROOT = Path(__file__).resolve().parents[3]
PRED = ROOT / "evaluation/predictions/mv-hondius"
GOLD = ROOT / "evaluation/gold/mv-hondius"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _assemble(claims_name: str):
    payload = normalize_extraction_payload(assemble_claims_payload(_load(PRED / claims_name)))
    validate_extraction(payload)
    return payload


def test_evidence_quote_and_text_are_same_textual_class():
    gold = {"type": "text", "text": "no se identificaron ejemplares de Oligoryzomys longicaudatus", "page_number": None}
    pred = {"type": "quote", "text": "no se identificaron ejemplares de Oligoryzomys longicaudatus", "page_number": None}
    assert evidence_support_similarity(gold, pred) == 1.0


def test_evidence_type_alias_does_not_disable_negation_guard():
    gold = {"type": "text", "text": "no se identificaron ejemplares de Oligoryzomys longicaudatus", "page_number": None}
    pred = {"type": "quote", "text": "se identificaron ejemplares de Oligoryzomys longicaudatus", "page_number": None}
    assert evidence_support_similarity(gold, pred) == 0.0


def test_v045_reassembles_initial_notification_into_seven_canonical_signals():
    prediction = _assemble("2026-05-04-v044-atomic-automatic.claims.json")
    assert len(prediction["signals"]) == 7
    assert [s["signal_type"] for s in prediction["signals"]] == [
        "cluster",
        "case_report",
        "transmission_observation",
        "laboratory_investigation",
        "travel_or_mobility",
        "case_report",
        "case_report",
    ]
    assert prediction["signals"][5]["signal_role"] == "background_context"
    assert prediction["signals"][6]["signal_role"] == "surveillance_baseline"
    cluster = prediction["signals"][0]
    assert any(m["name"] == "deaths" and m["value_numeric"] == 3 for m in cluster["metrics"])
    case = prediction["signals"][1]
    assert any(m["name"] == "confirmed_cases" and m["value_numeric"] == 1 for m in case["metrics"])
    assert not any(l.get("role") == "current_location" for l in case["locations"])
    mobility = prediction["signals"][4]
    assert mobility["event_date"]["start"] == "2025-11-16"
    assert mobility["event_date"]["end"] == "2026-04-01"
    assert mobility["reference_period"]["period_type"] == "observation_window"


def test_v045_reassembles_tierra_del_fuego_into_four_canonical_signals():
    prediction = _assemble("2026-06-29-tierra-del-fuego-rodents-v044-atomic-automatic.claims.json")
    assert len(prediction["signals"]) == 4
    assert {s["signal_type"] for s in prediction["signals"]} == {
        "laboratory_result",
        "genomic_observation",
        "wildlife_event",
        "transmission_observation",
    }
    assert not any(s["signal_type"] == "intervention" for s in prediction["signals"])
    genomic = next(s for s in prediction["signals"] if s["signal_type"] == "genomic_observation")
    assert genomic["pathogen"]["canonical_name"] == "Orthohantavirus andesense"
    assert genomic["genomics"]["lineage"] == "variante viral no descripta previamente"
    wildlife = next(s for s in prediction["signals"] if s["signal_type"] == "wildlife_event")
    assert wildlife["signal_role"] == "negative_evidence"
    assert {m["value_numeric"] for m in wildlife["metrics"]} == {144, 0}


def test_mendoza_keeps_perfect_signal_detection_and_recovers_evidence_support():
    prediction = _assemble("2026-07-08-mendoza-rodents-v044-atomic-automatic.claims.json")
    gold = _load(GOLD / "2026-07-08-mendoza-rodents.gold.json")
    report = evaluate_payloads(prediction, gold)
    assert report["signal_detection"]["f1"] == 1.0
    assert report["field_metrics"]["evidence_support_f1"] >= 0.90


def test_initial_notification_signal_detection_improves_over_v044():
    prediction = _assemble("2026-05-04-v044-atomic-automatic.claims.json")
    gold = _load(GOLD / "2026-05-04-initial-notification.gold.json")
    report = evaluate_payloads(prediction, gold)
    assert report["signal_detection"]["f1"] >= 0.85
    assert report["field_metrics"]["signal_role_accuracy"] == 1.0
    assert report["field_metrics"]["signal_type_accuracy"] == 1.0
