import copy
import json
from pathlib import Path

from onehealth_worker.evaluation.scoring import evaluate_payloads
from onehealth_worker.extraction.atomic_claims import assemble_claims_payload
from onehealth_worker.extraction.schema import load_atomic_claims_schema, validate_atomic_claims, validate_extraction

ROOT = Path(__file__).resolve().parents[3]
GOLD_DIR = ROOT / "evaluation/gold/mv-hondius"


def _empty_metric():
    return {
        "reported": False,
        "name": None,
        "value_numeric": None,
        "value_text": None,
        "unit": None,
        "as_of_date": None,
        "as_of_year": None,
        "as_of_month": None,
        "as_of_precision": "unknown",
        "as_of_verbatim": None,
    }


def _kind(signal):
    role = signal["signal_role"]
    st = signal["signal_type"]
    if role == "surveillance_baseline": return "surveillance_baseline"
    if role == "background_context": return "historical_context"
    if st == "cluster": return "syndromic_cluster"
    if st == "outbreak": return "outbreak_update"
    if st == "laboratory_result": return "diagnostic_result"
    if st == "laboratory_investigation": return "laboratory_investigation"
    if st == "genomic_observation": return "genomic_finding"
    if st == "transmission_observation": return "transmission_statement"
    if st == "wildlife_event": return "wildlife_presence_absence" if role == "negative_evidence" else "wildlife_sampling"
    if st == "travel_or_mobility": return "mobility"
    if st == "intervention": return "intervention"
    if st == "official_alert": return "official_action"
    return "case_status"


def _claims_from_gold(gold):
    claims=[]
    for si, signal in enumerate(gold["expected"]["signals"],1):
        group=f"g{si:02d}"
        metrics=signal.get("metrics") or [None]
        hosts=signal.get("hosts") or [None]
        n=max(len(metrics),len(hosts),1)
        for j in range(n):
            metric=copy.deepcopy(metrics[j]) if j < len(metrics) else None
            if metric is None:
                metric=_empty_metric()
            else:
                metric={"reported":True,**metric}
            host=hosts[j] if j < len(hosts) else None
            subject={
                "verbatim": host.get("verbatim") if host else None,
                "canonical_name": host.get("canonical_name") if host else None,
                "subject_type": (host.get("host_type") if host else "other") or "other",
                "confidence": host.get("confidence",0.75) if host else 0.5,
            }
            claims.append({
                "claim_id": f"c{si:02d}-{j+1}",
                "group_id": group,
                "claim_kind": _kind(signal),
                "polarity": "negative" if signal["signal_role"] == "negative_evidence" else "uncertain" if signal["signal_type"] in {"transmission_observation","laboratory_investigation"} else "positive",
                "domains": copy.deepcopy(signal["domains"]),
                "disease_verbatim": signal["disease"].get("verbatim"),
                "pathogen_verbatim": signal["pathogen"].get("verbatim"),
                "subject": subject,
                "locations": copy.deepcopy(signal.get("locations",[])),
                "event_date": copy.deepcopy(signal["event_date"]),
                "reference_period": copy.deepcopy(signal["reference_period"]),
                "metric": metric,
                "diagnostics": copy.deepcopy(signal["diagnostics"]),
                "genomics": copy.deepcopy(signal["genomics"]),
                "transmission": copy.deepcopy(signal["transmission"]),
                "verification_status": signal["verification_status"],
                "summary": signal["signal_summary"],
                "evidence": copy.deepcopy(signal["evidence"]),
                "confidence": signal["extraction_confidence"],
            })
    return {
        "schema_version":"claims-0.1",
        "document":copy.deepcopy(gold["expected"]["document"]),
        "claims":claims,
        "warnings":[],
    }


def test_atomic_claims_schema_loads_and_validates_generated_claims():
    gold=json.loads((GOLD_DIR/"2026-05-04-initial-notification.gold.json").read_text(encoding="utf-8"))
    payload=_claims_from_gold(gold)
    validate_atomic_claims(payload, load_atomic_claims_schema())


def test_assembler_non_regression_20260504_reconstructs_all_gold_signals():
    gold=json.loads((GOLD_DIR/"2026-05-04-initial-notification.gold.json").read_text(encoding="utf-8"))
    claims=_claims_from_gold(gold)
    assembled=assemble_claims_payload(claims)
    validate_extraction(assembled)
    report=evaluate_payloads(assembled,gold)
    assert report["signal_detection"]["f1"] == 1.0
    assert report["field_metrics"]["signal_role_accuracy"] == 1.0
    assert report["field_metrics"]["signal_type_accuracy"] == 1.0
    assert report["field_metrics"]["evidence_support_f1"] == 1.0


def test_assembler_consolidates_same_update_metrics_into_one_outbreak():
    gold=json.loads((GOLD_DIR/"2026-05-19-ben-se18.gold.json").read_text(encoding="utf-8"))
    claims=_claims_from_gold(gold)
    assembled=assemble_claims_payload(claims)
    outbreak=[s for s in assembled["signals"] if s["signal_type"]=="outbreak"]
    assert len(outbreak)==1
    assert {m["name"] for m in outbreak[0]["metrics"]} == {"identified_cases","confirmed_cases","probable_cases","inconclusive_cases"}


def test_assembler_keeps_wildlife_diagnostic_genomic_relation_and_absence_separate():
    gold=json.loads((GOLD_DIR/"2026-06-29-tierra-del-fuego-rodents.gold.json").read_text(encoding="utf-8"))
    claims=_claims_from_gold(gold)
    assembled=assemble_claims_payload(claims)
    assert [s["signal_type"] for s in assembled["signals"]] == [
        "laboratory_result","genomic_observation","transmission_observation","wildlife_event"
    ]
    assert assembled["signals"][2]["signal_role"] == "negative_evidence"
    assert assembled["signals"][3]["signal_role"] == "negative_evidence"
