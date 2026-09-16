from __future__ import annotations

from pathlib import Path
from typing import Any
import copy
import json

from .scoring import DEFAULT_MATCH_THRESHOLD, evaluate_payloads
from ..extraction.schema import load_schema, validate_extraction


DEFAULT_RELEASE_THRESHOLDS = {
    "mean_signal_f1": 0.90,
    "mean_evidence_support_f1": 0.90,
    "mean_signal_role_accuracy": 0.90,
    "mean_signal_type_accuracy": 0.85,
}


def evaluate_file(prediction_path: Path, gold_path: Path, threshold: float = DEFAULT_MATCH_THRESHOLD) -> dict[str, Any]:
    prediction = json.loads(prediction_path.read_text(encoding="utf-8-sig"))
    gold = json.loads(gold_path.read_text(encoding="utf-8-sig"))
    expected = copy.deepcopy(gold.get("expected", gold))
    prediction_raw_item_id = prediction.get("document", {}).get("raw_item_id")
    binding = gold.get("adjudication", {}).get("raw_item_binding")
    if binding == "prediction":
        expected.setdefault("document", {})["raw_item_id"] = prediction_raw_item_id
        gold = copy.deepcopy(gold)
        gold["expected"] = expected

    schema = load_schema()
    validate_extraction(prediction, schema)
    validate_extraction(expected, schema)
    if prediction_raw_item_id != expected.get("document", {}).get("raw_item_id"):
        raise ValueError("Prediction y gold standard corresponden a raw_item_id diferentes.")
    return evaluate_payloads(prediction, gold, threshold=threshold)


def _mean(documents: list[dict[str, Any]], getter) -> float:
    if not documents:
        return 0.0
    return round(sum(getter(d["report"]) for d in documents) / len(documents), 6)


def evaluate_corpus(manifest_path: Path, threshold: float = DEFAULT_MATCH_THRESHOLD) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    base = manifest_path.parent
    documents = []
    skipped = []

    for item in manifest.get("documents", []):
        if item.get("status") != "adjudicated":
            skipped.append({"label": item.get("label"), "reason": "gold_not_adjudicated"})
            continue
        prediction = item.get("prediction")
        gold = item.get("gold")
        if not prediction or not gold:
            skipped.append({"label": item.get("label"), "reason": "missing_paths"})
            continue
        prediction_path = (base / prediction).resolve()
        gold_path = (base / gold).resolve()
        if not prediction_path.exists():
            skipped.append({"label": item.get("label"), "reason": "prediction_not_found", "path": str(prediction_path)})
            continue
        if not gold_path.exists():
            skipped.append({"label": item.get("label"), "reason": "gold_not_found", "path": str(gold_path)})
            continue
        report = evaluate_file(prediction_path, gold_path, threshold)
        documents.append({"label": item.get("label"), "report": report})

    avg_signal_f1 = _mean(documents, lambda r: r["signal_detection"]["f1"])
    avg_evidence_exact = _mean(documents, lambda r: r["field_metrics"]["evidence_exact_f1"])
    avg_evidence_support = _mean(documents, lambda r: r["field_metrics"]["evidence_support_f1"])
    avg_role = _mean(documents, lambda r: r["field_metrics"]["signal_role_accuracy"])
    avg_type = _mean(documents, lambda r: r["field_metrics"]["signal_type_accuracy"])

    micro_tp = sum(d["report"]["signal_detection"]["tp"] for d in documents)
    micro_fp = sum(d["report"]["signal_detection"]["fp"] for d in documents)
    micro_fn = sum(d["report"]["signal_detection"]["fn"] for d in documents)
    micro_precision = micro_tp / (micro_tp + micro_fp) if micro_tp + micro_fp else 1.0
    micro_recall = micro_tp / (micro_tp + micro_fn) if micro_tp + micro_fn else 1.0
    micro_f1 = (
        2 * micro_precision * micro_recall / (micro_precision + micro_recall)
        if micro_precision + micro_recall else 0.0
    )

    adjudicated_total = sum(1 for x in manifest.get("documents", []) if x.get("status") == "adjudicated")
    minimum_documents = int(manifest.get("minimum_documents_for_event_matcher_gate", 6))
    corpus_ready = len(documents) >= minimum_documents and len(documents) == adjudicated_total

    thresholds = {**DEFAULT_RELEASE_THRESHOLDS, **(manifest.get("release_thresholds") or {})}
    metrics_pass = (
        avg_signal_f1 >= thresholds["mean_signal_f1"]
        and avg_evidence_support >= thresholds["mean_evidence_support_f1"]
        and avg_role >= thresholds["mean_signal_role_accuracy"]
        and avg_type >= thresholds["mean_signal_type_accuracy"]
    )

    return {
        "evaluation_schema_version": "0.2",
        "case_code": manifest.get("case_code"),
        "benchmark_version": manifest.get("benchmark_version"),
        "evaluated_documents": len(documents),
        "skipped_documents": skipped,
        "aggregate": {
            "mean_signal_f1": avg_signal_f1,
            "mean_evidence_exact_f1": avg_evidence_exact,
            "mean_evidence_support_f1": avg_evidence_support,
            # Backward-compatible alias: from schema 0.2 evidence_f1 means support equivalence.
            "mean_evidence_f1": avg_evidence_support,
            "mean_signal_role_accuracy": avg_role,
            "mean_signal_type_accuracy": avg_type,
            "micro_signal_detection": {
                "tp": micro_tp,
                "fp": micro_fp,
                "fn": micro_fn,
                "precision": round(micro_precision, 6),
                "recall": round(micro_recall, 6),
                "f1": round(micro_f1, 6),
            },
        },
        "release_gate": {
            "corpus_complete": corpus_ready,
            "metrics_pass": metrics_pass,
            "event_matcher_ready": bool(corpus_ready and metrics_pass),
            "minimum_documents": minimum_documents,
            "thresholds": thresholds,
        },
        "documents": documents,
    }
