import copy

import pytest

from onehealth_worker.extraction.assembly_v045 import assemble_claims_payload as assemble_v045
from onehealth_worker.extraction.assembly_v046 import assemble_claims_payload as assemble_v046
from onehealth_worker.extraction.normalization import normalize_extraction_payload
from onehealth_worker.extraction.schema import (
    validate_atomic_claims,
    validate_extraction,
    validate_literal_claim_evidence,
    validate_literal_evidence,
)
from onehealth_worker.extraction.signal_semantics_v049 import harden_signal_semantics_v049


def _payload(period_type="season", *, reported=False, kind="surveillance_baseline"):
    text = "Se notificaron 0 casos confirmados." if reported else "No se registran casos confirmados."
    endpoint = {"date": None, "year": None, "month": None, "precision": "unknown", "verbatim": None}
    claim = {
        "claim_id": "absence",
        "group_id": "season",
        "claim_kind": kind,
        "polarity": "negative",
        "domains": ["human"],
        "disease_verbatim": None,
        "pathogen_verbatim": None,
        "subject": {"verbatim": "casos confirmados", "canonical_name": None,
                    "subject_type": "population", "confidence": 0.9},
        "locations": [],
        "event_date": {"start": None, "end": None, "precision": "unknown"},
        "reference_period": {"start": copy.deepcopy(endpoint), "end": copy.deepcopy(endpoint),
                             "period_type": period_type, "verbatim": None},
        "metric": {"reported": reported, "name": "casos confirmados" if reported else None,
                   "value_numeric": 0 if reported else None, "value_text": "0" if reported else None,
                   "unit": "cases" if reported else None, "as_of_date": None, "as_of_year": None,
                   "as_of_month": None, "as_of_precision": "unknown", "as_of_verbatim": None},
        "diagnostics": {"test_reported": False, "test_type": None, "method": None,
                        "target": None, "specimen": None, "result": "unknown"},
        "genomics": {"sequence_reported": False, "lineage": None, "clade": None,
                     "accession": None, "test_result": "unknown"},
        "transmission": {"human_to_human": "unknown", "animal_to_human": "unknown", "vector_borne": "unknown"},
        "verification_status": "reported",
        "summary": text,
        "evidence": [{"type": "text", "text": text, "location_in_document": None, "page_number": None}],
        "confidence": 0.9,
    }
    return {"schema_version": "claims-0.1",
            "document": {"raw_item_id": "d7526fe6-3cac-47c1-ad58-b05e4a91c498", "language": "es", "document_date": None},
            "claims": [claim], "warnings": []}


@pytest.mark.parametrize("assemble", [assemble_v045, assemble_v046])
@pytest.mark.parametrize("period_type", ["season", "surveillance_period", "observation_window", "unknown"])
def test_nonhistorical_qualitative_baseline_survives_pipeline_without_inventing_zero(assemble, period_type):
    original = _payload(period_type)
    snapshot = copy.deepcopy(original)
    text = original["claims"][0]["evidence"][0]["text"]
    validate_atomic_claims(original)
    validate_literal_claim_evidence(original, text)
    assembled = assemble(original)
    normalized = normalize_extraction_payload(assembled)
    hardened = harden_signal_semantics_v049(normalized)
    for payload in [assembled, normalized, hardened]:
        validate_extraction(payload)
        validate_literal_evidence(payload, text)
        assert len(payload["signals"]) == 1
        signal = payload["signals"][0]
        assert signal["signal_role"] == "surveillance_baseline"
        assert signal["reference_period"]["period_type"] == period_type
        assert signal["metrics"] == []
        assert signal["diagnostics"]["test_reported"] is False
        assert signal["diagnostics"]["result"] == "unknown"
        assert signal["signal_summary"] == text
    assert original == snapshot


@pytest.mark.parametrize("assemble", [assemble_v045, assemble_v046])
def test_explicit_historical_qualitative_baseline_remains_suppressed_and_raw_intact(assemble):
    original = _payload("historical_period")
    snapshot = copy.deepcopy(original)
    assert assemble(original)["signals"] == []
    assert original == snapshot


@pytest.mark.parametrize("assemble", [assemble_v045, assemble_v046])
def test_historical_explicit_zero_is_not_suppressed_by_qualitative_guard(assemble):
    original = _payload("historical_period", reported=True)
    signal = assemble(original)["signals"][0]
    assert signal["metrics"][0]["value_numeric"] == 0
    assert signal["diagnostics"]["test_reported"] is False


@pytest.mark.parametrize("assemble", [assemble_v045, assemble_v046])
def test_negative_case_status_keeps_its_existing_role(assemble):
    signal = assemble(_payload(kind="case_status"))["signals"][0]
    assert signal["signal_role"] == "negative_evidence"
    assert signal["metrics"] == []


@pytest.mark.parametrize("assemble", [assemble_v045, assemble_v046])
def test_shared_group_preserves_qualitative_absence_and_positive_count_separately(assemble):
    original = _payload()
    positive = copy.deepcopy(original["claims"][0])
    positive.update(claim_id="count", claim_kind="case_status", polarity="positive",
                    summary="Se notificaron 3 casos probables.")
    positive["subject"]["verbatim"] = "casos probables"
    positive["metric"].update(reported=True, name="casos probables", value_numeric=3,
                               value_text="3", unit="cases")
    positive["evidence"][0]["text"] = positive["summary"]
    original["claims"].append(positive)
    snapshot = copy.deepcopy(original)
    signals = assemble(original)["signals"]
    assert len(signals) == 2
    absence = next(signal for signal in signals if signal["signal_role"] == "surveillance_baseline")
    assert absence["metrics"] == []
    count = next(signal for signal in signals if signal["signal_role"] == "primary_event")
    assert count["metrics"][0]["value_numeric"] == 3
    assert original == snapshot
