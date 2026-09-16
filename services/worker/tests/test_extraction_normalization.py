from onehealth_worker.extraction.normalization import normalize_extraction_payload


def _payload(as_of_date):
    return {
        "schema_version": "0.2",
        "document": {"raw_item_id": "11111111-1111-4111-8111-111111111111", "language": "es", "document_date": "2026-05-04"},
        "signals": [
            {
                "local_signal_id": "S4",
                "metrics": [
                    {
                        "name": "case_count",
                        "value_numeric": 1,
                        "value_text": None,
                        "unit": "cases",
                        "as_of_date": as_of_date,
                    }
                ],
            }
        ],
        "warnings": [],
    }


def test_year_only_metric_date_is_preserved_without_inventing_day():
    normalized = normalize_extraction_payload(_payload("2004"))
    metric = normalized["signals"][0]["metrics"][0]
    assert metric["as_of_date"] is None
    assert metric["as_of_year"] == 2004
    assert metric["as_of_month"] is None
    assert metric["as_of_precision"] == "year"
    assert metric["as_of_verbatim"] == "2004"
    assert any("precisión anual" in warning for warning in normalized["warnings"])


def test_full_metric_date_keeps_exact_date():
    normalized = normalize_extraction_payload(_payload("2026-05-04"))
    metric = normalized["signals"][0]["metrics"][0]
    assert metric["as_of_date"] == "2026-05-04"
    assert metric["as_of_year"] == 2026
    assert metric["as_of_month"] == 5
    assert metric["as_of_precision"] == "day"


def test_reference_period_year_is_preserved_without_fake_date():
    payload = {
        "warnings": [],
        "signals": [{
            "local_signal_id": "S-context",
            "metrics": [],
            "reference_period": {
                "start": {"date": "1996", "year": None, "month": None, "precision": "unknown", "verbatim": None},
                "end": {"date": "2026-05-04", "year": None, "month": None, "precision": "unknown", "verbatim": None},
            },
        }],
    }
    result = normalize_extraction_payload(payload)
    start = result["signals"][0]["reference_period"]["start"]
    end = result["signals"][0]["reference_period"]["end"]
    assert start["date"] is None
    assert start["year"] == 1996
    assert start["precision"] == "year"
    assert end["date"] == "2026-05-04"
    assert end["year"] == 2026
    assert end["month"] == 5
    assert end["precision"] == "day"


def test_explicit_andes_strain_is_normalized_to_andes_virus():
    payload = {
        "warnings": [],
        "signals": [{
            "local_signal_id": "S-andes",
            "metrics": [],
            "reference_period": {},
            "pathogen": {
                "verbatim": "cepa Andes",
                "canonical_name": "Hantavirus",
                "normalization_status": "ambiguous",
                "confidence": 0.7,
            },
            "hosts": [],
        }],
    }
    result = normalize_extraction_payload(payload)
    pathogen = result["signals"][0]["pathogen"]
    assert pathogen["canonical_name"] == "Andes virus"
    assert pathogen["normalization_status"] == "resolved"


def test_non_biological_vessel_is_removed_from_hosts():
    payload = {
        "warnings": [],
        "signals": [{
            "local_signal_id": "S-host",
            "metrics": [],
            "reference_period": {},
            "pathogen": {"verbatim": None, "canonical_name": None, "normalization_status": "unresolved", "confidence": 0.2},
            "hosts": [
                {"verbatim": "la embarcación", "canonical_name": None, "host_type": "other", "confidence": 0.5},
                {"verbatim": "pasajeros", "canonical_name": "Homo sapiens", "host_type": "human", "confidence": 0.8},
            ],
        }],
    }
    result = normalize_extraction_payload(payload)
    assert len(result["signals"][0]["hosts"]) == 1
    assert result["signals"][0]["hosts"][0]["host_type"] == "human"
    assert any("host no biológico" in warning for warning in result["warnings"])


def test_exact_duplicate_signals_are_removed_deterministically():
    base = {
        "metrics": [],
        "reference_period": {},
        "pathogen": {"verbatim": None, "canonical_name": None, "normalization_status": "unresolved", "confidence": 0.2},
        "hosts": [],
        "signal_role": "primary_event",
        "signal_type": "official_alert",
        "evidence": [{"type": "text", "text": "mismo hecho", "location_in_document": None, "page_number": None}],
    }
    payload = {
        "warnings": [],
        "signals": [
            {**base, "local_signal_id": "S1", "signal_summary": "A", "extraction_confidence": 0.8},
            {**base, "local_signal_id": "S2", "signal_summary": "B", "extraction_confidence": 0.7},
        ],
    }
    result = normalize_extraction_payload(payload)
    assert [s["local_signal_id"] for s in result["signals"]] == ["S1"]
    assert any("duplicado exacto" in warning for warning in result["warnings"])
