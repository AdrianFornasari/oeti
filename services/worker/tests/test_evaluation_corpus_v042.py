import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from onehealth_worker.evaluation.corpus import evaluate_file
from onehealth_worker.evaluation.extraction import scoped_document_input
from onehealth_worker.extraction.schema import load_schema, validate_extraction

ROOT = Path(__file__).resolve().parents[3]


def test_all_six_mv_hondius_gold_files_validate_against_schema():
    schema = load_schema()
    gold_dir = ROOT / "evaluation/gold/mv-hondius"
    files = sorted(gold_dir.glob("*.gold.json"))
    assert len(files) == 6
    for path in files:
        gold = json.loads(path.read_text(encoding="utf-8"))
        validate_extraction(gold["expected"], schema)
        assert gold["adjudication"]["status"] == "adjudicated"


def test_manifest_has_six_adjudicated_documents():
    manifest = json.loads((ROOT / "config/evaluation/mv-hondius-gold-standard.json").read_text(encoding="utf-8"))
    assert len(manifest["documents"]) == 6
    assert all(x["status"] == "adjudicated" for x in manifest["documents"])
    assert all(x.get("prediction") and x.get("gold") for x in manifest["documents"])


def test_scoped_document_input_marks_benchmark_scope():
    @dataclass
    class Doc:
        raw_item_id: str = "11111111-1111-4111-8111-111111111111"
        title: str = "BEN"
        url: str = "https://example.test/ben"
        published_at: datetime = datetime(2026, 5, 12)
        language: str = "es"
        raw_text: str = "Hantavirus. Influenza."
    text = scoped_document_input(Doc(), "Solo hantavirus")
    assert "EVALUATION_SCOPE_BEGIN" in text
    assert "Solo hantavirus" in text
    assert "No extraigas señales de otros temas" in text


def test_portable_gold_binds_to_prediction_raw_item_id(tmp_path):
    gold_src = ROOT / "evaluation/gold/mv-hondius/2026-05-12-ben-se17.gold.json"
    gold = json.loads(gold_src.read_text(encoding="utf-8"))
    prediction = json.loads(json.dumps(gold["expected"]))
    prediction["document"]["raw_item_id"] = "11111111-1111-4111-8111-111111111111"
    for idx, sig in enumerate(prediction["signals"], 1):
        sig["local_signal_id"] = f"MODEL-{idx}"
    gp = tmp_path / "gold.json"
    pp = tmp_path / "pred.json"
    gp.write_text(json.dumps(gold, ensure_ascii=False), encoding="utf-8")
    pp.write_text(json.dumps(prediction, ensure_ascii=False), encoding="utf-8")
    report = evaluate_file(pp, gp)
    assert report["signal_detection"]["f1"] == 1.0


def test_v044_manifest_uses_atomic_prediction_paths_and_release_thresholds():
    manifest = json.loads((ROOT / "config/evaluation/mv-hondius-gold-standard.json").read_text(encoding="utf-8"))
    assert manifest["benchmark_version"] == "0.4"
    assert manifest["release_thresholds"]["mean_evidence_support_f1"] == 0.90
    assert all("v044-atomic-automatic.json" in x["prediction"] for x in manifest["documents"])
    assert manifest["prediction_architecture"] == "atomic_claims_v0.1+deterministic_signal_assembly_v0.4.4"
    assert all(x.get("source_url") for x in manifest["documents"])


def test_release_gate_passes_for_six_perfect_predictions(tmp_path):
    source_manifest = json.loads((ROOT / "config/evaluation/mv-hondius-gold-standard.json").read_text(encoding="utf-8"))
    documents = []
    for idx, source_item in enumerate(source_manifest["documents"], 1):
        gold_source = (ROOT / "config/evaluation" / source_item["gold"]).resolve()
        gold = json.loads(gold_source.read_text(encoding="utf-8"))
        prediction = json.loads(json.dumps(gold["expected"]))
        prediction["document"]["raw_item_id"] = f"00000000-0000-4000-8000-{idx:012d}"
        for sidx, signal in enumerate(prediction["signals"], 1):
            signal["local_signal_id"] = f"MODEL-{idx}-{sidx}"
        gp = tmp_path / f"gold-{idx}.json"
        pp = tmp_path / f"pred-{idx}.json"
        gp.write_text(json.dumps(gold, ensure_ascii=False), encoding="utf-8")
        pp.write_text(json.dumps(prediction, ensure_ascii=False), encoding="utf-8")
        documents.append({
            "label": source_item["label"],
            "status": "adjudicated",
            "prediction": pp.name,
            "gold": gp.name,
        })
    manifest = {
        "case_code": source_manifest["case_code"],
        "benchmark_version": "test",
        "minimum_documents_for_event_matcher_gate": 6,
        "release_thresholds": source_manifest["release_thresholds"],
        "documents": documents,
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    from onehealth_worker.evaluation.corpus import evaluate_corpus
    report = evaluate_corpus(manifest_path)
    assert report["evaluated_documents"] == 6
    assert report["aggregate"]["mean_signal_f1"] == 1.0
    assert report["aggregate"]["mean_evidence_exact_f1"] == 1.0
    assert report["aggregate"]["mean_evidence_support_f1"] == 1.0
    assert report["release_gate"]["metrics_pass"] is True
    assert report["release_gate"]["event_matcher_ready"] is True
