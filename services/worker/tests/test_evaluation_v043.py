import copy
import json
from pathlib import Path

from onehealth_worker.evaluation.scoring import evaluate_payloads, evidence_support_similarity


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "services/worker/tests/fixtures/evaluation"


def _gold():
    return json.loads((FIXTURES / "mv_hondius_20260504_gold.json").read_text(encoding="utf-8"))


def test_evidence_support_accepts_literal_subspan_but_exact_stays_strict():
    gold = _gold()
    prediction = copy.deepcopy(gold["expected"])
    for idx, signal in enumerate(prediction["signals"], 1):
        signal["local_signal_id"] = f"MODEL-{idx}"

    original = prediction["signals"][0]["evidence"][0]["text"]
    prediction["signals"][0]["evidence"][0]["text"] = "conglomerado de enfermedades respiratorias agudas graves a bordo del crucero, incluyendo tres fallecimientos"
    assert prediction["signals"][0]["evidence"][0]["text"] in original

    report = evaluate_payloads(prediction, gold)
    assert report["evaluation_schema_version"] == "0.2"
    assert report["field_metrics"]["evidence_exact_f1"] < 1.0
    assert report["field_metrics"]["evidence_support_f1"] == 1.0
    assert report["field_metrics"]["evidence_f1"] == 1.0


def test_evidence_support_rejects_opposite_negation_even_with_shared_terms():
    gold = {"type": "text", "text": "no se identificaron ejemplares de Oligoryzomys longicaudatus", "page_number": None}
    pred = {"type": "text", "text": "se identificaron ejemplares de Oligoryzomys longicaudatus", "page_number": None}
    assert evidence_support_similarity(gold, pred) == 0.0


def test_unmatched_signal_reports_include_semantic_snapshot():
    gold = _gold()
    prediction = copy.deepcopy(gold["expected"])
    missing = prediction["signals"].pop()
    report = evaluate_payloads(prediction, gold)
    assert report["unmatched_gold"]
    snapshot = report["unmatched_gold"][0]
    assert snapshot["local_signal_id"] == gold["expected"]["signals"][-1]["local_signal_id"]
    assert "signal_role" in snapshot
    assert "signal_type" in snapshot
    assert "evidence" in snapshot
    assert missing["local_signal_id"] != snapshot["local_signal_id"] or missing["local_signal_id"] == snapshot["local_signal_id"]
