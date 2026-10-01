import json
from pathlib import Path

from onehealth_worker.evaluation.scoring import evaluate_payloads, evidence_support_similarity
from onehealth_worker.extraction.assembly_v045 import (
    _merge_genomic_nonrelation_signals,
    assemble_claims_payload,
)
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


def test_v045_merges_genomic_nonrelation_into_negative_transmission_signal():
    payload = {
        "signals": [
            {
                "local_signal_id": "g-discovery",
                "signal_role": "primary_event",
                "signal_type": "genomic_observation",
                "domains": ["wildlife", "genomic"],
                "pathogen": {
                    "verbatim": "Orthohantavirus andesense",
                    "canonical_name": "Orthohantavirus andesense",
                    "normalization_status": "resolved",
                    "confidence": 0.95,
                },
                "hosts": [],
                "genomics": {
                    "sequence_reported": True,
                    "lineage": "variante viral no descripta previamente",
                    "clade": None,
                    "accession": None,
                    "test_result": "positive",
                },
                "verification_status": "confirmed",
                "signal_summary": "Se identificó una variante viral no descripta previamente clasificada como Orthohantavirus andesense.",
                "evidence": [
                    {"type": "text", "text": "se clasifica dentro de la especie Orthohantavirus andesense", "page_number": None}
                ],
            },
            {
                "local_signal_id": "g-relation",
                "signal_role": "primary_event",
                "signal_type": "genomic_observation",
                "domains": ["wildlife", "human", "genomic"],
                "pathogen": {
                    "verbatim": "Orthohantavirus andesense",
                    "canonical_name": "Orthohantavirus andesense",
                    "normalization_status": "resolved",
                    "confidence": 0.95,
                },
                "hosts": [],
                "genomics": {
                    "sequence_reported": True,
                    "lineage": "variante viral no descripta previamente",
                    "clade": None,
                    "accession": None,
                    "test_result": "positive",
                },
                "verification_status": "reported",
                "signal_summary": "La variante en roedores es diferente de la observada en casos humanos asociados al brote investigado.",
                "evidence": [
                    {"type": "text", "text": "la variante viral hallada en los roedores es diferente de la observada en los casos humanos", "page_number": None}
                ],
            },
            {
                "local_signal_id": "tx-negative",
                "signal_role": "negative_evidence",
                "signal_type": "transmission_observation",
                "domains": ["wildlife", "human"],
                "pathogen": {
                    "verbatim": "hantavirus",
                    "canonical_name": "Hantavirus",
                    "normalization_status": "resolved",
                    "confidence": 0.8,
                },
                "hosts": [],
                "genomics": {
                    "sequence_reported": False,
                    "lineage": None,
                    "clade": None,
                    "accession": None,
                    "test_result": "unknown",
                },
                "transmission": {
                    "human_to_human": "unknown",
                    "animal_to_human": "refuted",
                    "vector_borne": "unknown",
                },
                "verification_status": "reported",
                "signal_summary": "Se descartó que los roedores analizados fueran la fuente de infección del brote.",
                "evidence": [
                    {"type": "text", "text": "se descartó que los roedores analizados hayan sido la fuente de infección", "page_number": None}
                ],
            },
        ]
    }

    _merge_genomic_nonrelation_signals(payload)

    assert len(payload["signals"]) == 2
    assert {s["local_signal_id"] for s in payload["signals"]} == {"g-discovery", "tx-negative"}
    transmission = next(s for s in payload["signals"] if s["local_signal_id"] == "tx-negative")
    assert transmission["signal_role"] == "negative_evidence"
    assert transmission["verification_status"] == "refuted"
    assert "genomic" in transmission["domains"]
    assert transmission["pathogen"]["canonical_name"] == "Orthohantavirus andesense"
    assert transmission["genomics"]["sequence_reported"] is True
    assert len(transmission["evidence"]) == 2


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
