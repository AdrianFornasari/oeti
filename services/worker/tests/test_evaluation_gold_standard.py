import copy
import json
from pathlib import Path

from onehealth_worker.evaluation.scoring import evaluate_payloads, signal_pair_score
from onehealth_worker.evaluation.corpus import evaluate_corpus


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "services/worker/tests/fixtures/evaluation"


def _gold():
    return json.loads((FIXTURES / "mv_hondius_20260504_gold.json").read_text(encoding="utf-8"))


def _prediction():
    return json.loads((FIXTURES / "mv_hondius_v035_reviewed_prediction.json").read_text(encoding="utf-8"))


def test_perfect_gold_copy_scores_one_even_with_different_signal_ids():
    gold = _gold()
    prediction = copy.deepcopy(gold["expected"])
    for idx, signal in enumerate(prediction["signals"], 1):
        signal["local_signal_id"] = f"MODEL-{idx}"
    report = evaluate_payloads(prediction, gold)
    assert report["signal_detection"]["precision"] == 1.0
    assert report["signal_detection"]["recall"] == 1.0
    assert report["field_metrics"]["signal_role_accuracy"] == 1.0
    assert report["field_metrics"]["evidence_f1"] == 1.0
    assert report["composite_score"] == 1.0


def test_reviewed_v035_is_detected_as_near_gold_not_perfect():
    report = evaluate_payloads(_prediction(), _gold())
    assert report["signal_detection"]["f1"] == 1.0
    assert report["field_metrics"]["signal_role_accuracy"] == 1.0
    assert report["field_metrics"]["evidence_f1"] == 1.0
    assert report["field_metrics"]["reference_period_accuracy"] < 1.0
    assert report["field_metrics"]["diagnostics_accuracy"] < 1.0
    assert report["release_gate"]["event_matcher_ready"] is False


def test_missing_signal_reduces_recall_without_creating_false_positive():
    prediction = _prediction()
    prediction["signals"] = prediction["signals"][:-1]
    report = evaluate_payloads(prediction, _gold())
    assert report["signal_detection"]["tp"] == 6
    assert report["signal_detection"]["fn"] == 1
    assert report["signal_detection"]["fp"] == 0
    assert report["signal_detection"]["recall"] < 1.0


def test_extra_signal_reduces_precision():
    prediction = _prediction()
    extra = copy.deepcopy(prediction["signals"][0])
    extra["local_signal_id"] = "EXTRA"
    extra["signal_type"] = "intervention"
    extra["signal_role"] = "negative_evidence"
    extra["disease"] = {"verbatim": "x", "canonical_name": "x", "normalization_status": "resolved", "confidence": 0.9}
    extra["pathogen"] = {"verbatim": "y", "canonical_name": "y", "normalization_status": "resolved", "confidence": 0.9}
    extra["metrics"] = [{"name":"vaccinated","value_numeric":999,"value_text":None,"unit":"persons","as_of_date":None,"as_of_year":None,"as_of_month":None,"as_of_precision":"unknown","as_of_verbatim":None}]
    extra["locations"] = []
    extra["evidence"] = [{"type":"text","text":"invented","location_in_document":None,"page_number":None}]
    prediction["signals"].append(extra)
    report = evaluate_payloads(prediction, _gold())
    assert report["signal_detection"]["tp"] == 7
    assert report["signal_detection"]["fp"] == 1
    assert report["signal_detection"]["precision"] < 1.0


def test_signal_pair_score_uses_semantics_not_local_id():
    gold_signal = _gold()["expected"]["signals"][0]
    pred_signal = copy.deepcopy(gold_signal)
    pred_signal["local_signal_id"] = "completely-different-id"
    assert signal_pair_score(gold_signal, pred_signal) == 1.0


def test_corpus_gate_requires_multiple_documents(tmp_path):
    gold_path = tmp_path / "gold.json"
    pred_path = tmp_path / "prediction.json"
    manifest_path = tmp_path / "manifest.json"
    gold_path.write_text(json.dumps(_gold(), ensure_ascii=False), encoding="utf-8")
    pred_path.write_text(json.dumps(_prediction(), ensure_ascii=False), encoding="utf-8")
    manifest = {
        "case_code": "ARG-HANTA-MV-HONDIUS-2026",
        "documents": [
            {"label":"doc1","status":"adjudicated","prediction":"prediction.json","gold":"gold.json"},
            {"label":"doc2","status":"pending_adjudication"},
        ],
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    report = evaluate_corpus(manifest_path)
    assert report["evaluated_documents"] == 1
    assert report["release_gate"]["corpus_complete"] is False
    assert report["release_gate"]["event_matcher_ready"] is False
