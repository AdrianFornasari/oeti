import copy
import json
from pathlib import Path

import pytest

from onehealth_worker.evaluation.event_matching_v048 import (
    EventMatchingBenchmarkError,
    load_event_matching_benchmark,
    signal_matching_eligible,
    validate_event_matching_manifest,
)


ROOT = Path(__file__).resolve().parents[3]

MANIFEST = (
    ROOT
    / "config"
    / "evaluation"
    / "mv-hondius-event-matching-v048.json"
)


def _manifest() -> dict:
    return json.loads(
        MANIFEST.read_text(
            encoding="utf-8"
        )
    )


def test_v048_loads_six_gold_documents_and_thirty_signals():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    assert (
        benchmark.manifest[
            "benchmark_version"
        ]
        == "0.4.8"
    )

    assert len(
        benchmark.gold_documents
    ) == 6

    assert benchmark.signal_count == 30
    assert benchmark.pair_count == 14


def test_v048_signal_index_preserves_source_and_semantics():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    human = benchmark.signal_index[
        "GS-MVH-20260526-01"
    ]

    wildlife = benchmark.signal_index[
        "GS-MVH-20260629-03"
    ]

    assert (
        human["signal_role"]
        == "primary_event"
    )

    assert (
        human["signal_type"]
        == "outbreak"
    )

    assert (
        wildlife["signal_role"]
        == "negative_evidence"
    )

    assert (
        wildlife["signal_type"]
        == "transmission_observation"
    )

    source = benchmark.signal_sources[
        "GS-MVH-20260629-03"
    ]

    assert (
        source.name
        == "2026-06-29-tierra-del-fuego-rodents.gold.json"
    )


def test_v048_all_adjudicated_pair_references_resolve():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    for pair in benchmark.adjudicated_pairs:
        assert (
            pair["source_signal_id"]
            in benchmark.signal_index
        )

        assert (
            pair["target_signal_id"]
            in benchmark.signal_index
        )


def test_v048_deterministic_eligibility_gate_matches_roles_and_types():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    eligibility = benchmark.manifest[
        "eligibility"
    ]

    primary = benchmark.signal_index[
        "GS-MVH-20260512-01"
    ]

    negative = benchmark.signal_index[
        "GS-MVH-20260629-03"
    ]

    background = benchmark.signal_index[
        "GS-MVH-20260504-06"
    ]

    baseline = benchmark.signal_index[
        "GS-MVH-20260512-05"
    ]

    assert (
        signal_matching_eligible(
            primary,
            eligibility,
        )
        is True
    )

    assert (
        signal_matching_eligible(
            negative,
            eligibility,
        )
        is True
    )

    assert (
        signal_matching_eligible(
            background,
            eligibility,
        )
        is False
    )

    assert (
        signal_matching_eligible(
            baseline,
            eligibility,
        )
        is False
    )

    official_alert = {
        "signal_role": "primary_event",
        "signal_type": "official_alert",
    }

    assert (
        signal_matching_eligible(
            official_alert,
            eligibility,
        )
        is False
    )


def test_v048_manifest_rejects_official_alert_as_signal_role():
    manifest = _manifest()

    broken = copy.deepcopy(
        manifest
    )

    broken[
        "eligibility"
    ][
        "ineligible_signal_roles"
    ].append(
        "official_alert"
    )

    with pytest.raises(
        EventMatchingBenchmarkError,
        match="signal_type",
    ):
        validate_event_matching_manifest(
            broken
        )


def test_v048_manifest_rejects_weight_sum_other_than_one():
    manifest = _manifest()

    broken = copy.deepcopy(
        manifest
    )

    broken[
        "scoring"
    ][
        "weights"
    ][
        "etiology"
    ] = 0.34

    with pytest.raises(
        EventMatchingBenchmarkError,
        match="sum to 1.0",
    ):
        validate_event_matching_manifest(
            broken
        )


def test_v048_manifest_rejects_duplicate_pair_ids():
    manifest = _manifest()

    broken = copy.deepcopy(
        manifest
    )

    broken[
        "adjudicated_pairs"
    ][1][
        "pair_id"
    ] = broken[
        "adjudicated_pairs"
    ][0][
        "pair_id"
    ]

    with pytest.raises(
        EventMatchingBenchmarkError,
        match="duplicate pair_id",
    ):
        validate_event_matching_manifest(
            broken
        )


def test_v048_hard_conflicts_are_rejected_and_never_mergeable():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    hard_conflicts = [
        pair
        for pair
        in benchmark.adjudicated_pairs
        if pair[
            "expected_hard_conflict"
        ]
    ]

    assert len(
        hard_conflicts
    ) == 2

    for pair in hard_conflicts:
        assert (
            pair[
                "expected_decision"
            ]
            == "rejected"
        )

        assert (
            pair[
                "expected_merge_allowed"
            ]
            is False
        )

        assert (
            pair[
                "expected_hard_conflict_reason"
            ]
            == "explicit_genomic_incompatibility"
        )

def _score_pair(
    benchmark,
    source_id: str,
    target_id: str,
):
    from onehealth_worker.evaluation.event_matching_v048 import (
        score_signal_pair_components,
    )

    return score_signal_pair_components(
        benchmark.signal_index[
            source_id
        ],
        benchmark.signal_index[
            target_id
        ],
        benchmark.manifest[
            "eligibility"
        ],
        benchmark.manifest[
            "scoring"
        ][
            "weights"
        ],
    )


def test_v048_component_scoring_short_circuits_ineligible_pairs():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    result = _score_pair(
        benchmark,
        "GS-MVH-20260504-07",
        "GS-MVH-20260512-01",
    )

    assert result["eligible"] is False
    assert result["score"] is None
    assert (
        result[
            "information_coverage"
        ]
        == 0.0
    )

    assert all(
        value is None
        for value
        in result[
            "component_scores"
        ].values()
    )


def test_v048_duplicate_genomic_observation_is_perfect_on_observed_dimensions():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    result = _score_pair(
        benchmark,
        "GS-MVH-20260512-03",
        "GS-MVH-20260526-02",
    )

    assert result["eligible"] is True
    assert result["score"] == 1.0

    assert (
        result[
            "information_coverage"
        ]
        == pytest.approx(
            0.60
        )
    )

    assert (
        result[
            "component_scores"
        ][
            "etiology"
        ]
        == 1.0
    )

    assert (
        result[
            "component_scores"
        ][
            "host"
        ]
        == 1.0
    )

    assert (
        result[
            "component_scores"
        ][
            "epidemiology"
        ]
        == 1.0
    )

    assert (
        result[
            "component_scores"
        ][
            "shared_context"
        ]
        == 1.0
    )

    assert (
        result[
            "component_scores"
        ][
            "geography"
        ]
        is None
    )

    assert (
        result[
            "component_scores"
        ][
            "temporality"
        ]
        is None
    )


def test_v048_one_health_cross_sector_pair_is_compatible_but_not_perfect():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    result = _score_pair(
        benchmark,
        "GS-MVH-20260519-04",
        "GS-MVH-20260629-01",
    )

    assert result["eligible"] is True

    assert (
        0.70
        < result["score"]
        < 0.85
    )

    assert (
        result[
            "component_scores"
        ][
            "geography"
        ]
        == 0.80
    )

    assert (
        result[
            "component_scores"
        ][
            "host"
        ]
        == 0.50
    )

    assert (
        result[
            "component_scores"
        ][
            "host"
        ]
        > 0.0
    )


def test_v048_future_hard_conflict_can_still_have_high_numeric_compatibility():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    result = _score_pair(
        benchmark,
        "GS-MVH-20260526-02",
        "GS-MVH-20260629-03",
    )

    assert result["eligible"] is True

    # This is intentional:
    # numeric compatibility must not replace
    # the later hard-conflict guard.
    assert result["score"] > 0.60

    assert (
        result[
            "component_scores"
        ][
            "host"
        ]
        == 0.50
    )


def test_v048_component_scoring_is_order_invariant():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    forward = _score_pair(
        benchmark,
        "GS-MVH-20260519-04",
        "GS-MVH-20260629-01",
    )

    reverse = _score_pair(
        benchmark,
        "GS-MVH-20260629-01",
        "GS-MVH-20260519-04",
    )

    assert (
        forward["score"]
        == reverse["score"]
    )

    assert (
        forward[
            "information_coverage"
        ]
        == reverse[
            "information_coverage"
        ]
    )

    assert (
        forward[
            "component_scores"
        ]
        == reverse[
            "component_scores"
        ]
    )


def test_v048_event_geography_ignores_laboratory_locations():
    from onehealth_worker.evaluation.event_matching_v048 import (
        score_signal_pair_components,
    )

    manifest = _manifest()

    source = {
        "local_signal_id": "A",
        "signal_role": "primary_event",
        "signal_type": "laboratory_result",
        "domains": ["human"],
        "disease": {
            "canonical_name": "Hantavirus disease",
        },
        "pathogen": {
            "canonical_name": "Andes virus",
        },
        "hosts": [
            {
                "canonical_name": "Homo sapiens",
                "host_type": "human",
            }
        ],
        "locations": [
            {
                "country": "SudÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡frica",
                "country_iso2": "ZA",
                "role": "laboratory_location",
            }
        ],
    }

    target = copy.deepcopy(
        source
    )

    target[
        "local_signal_id"
    ] = "B"

    target[
        "locations"
    ][0][
        "country"
    ] = "Suiza"

    target[
        "locations"
    ][0][
        "country_iso2"
    ] = "CH"

    result = score_signal_pair_components(
        source,
        target,
        manifest["eligibility"],
        manifest[
            "scoring"
        ][
            "weights"
        ],
    )

    assert (
        result[
            "component_scores"
        ][
            "geography"
        ]
        is None
    )


def test_v048_temporality_scores_close_events_without_making_time_a_conflict():
    from onehealth_worker.evaluation.event_matching_v048 import (
        score_signal_pair_components,
    )

    manifest = _manifest()

    source = {
        "local_signal_id": "A",
        "signal_role": "primary_event",
        "signal_type": "outbreak",
        "domains": ["human"],
        "disease": {
            "canonical_name": "Hantavirus disease",
        },
        "pathogen": {
            "canonical_name": "Andes virus",
        },
        "hosts": [
            {
                "canonical_name": "Homo sapiens",
                "host_type": "human",
            }
        ],
        "locations": [],
        "event_date": {
            "start": "2026-05-01",
            "end": None,
        },
    }

    target = copy.deepcopy(
        source
    )

    target[
        "local_signal_id"
    ] = "B"

    target[
        "event_date"
    ][
        "start"
    ] = "2026-05-06"

    result = score_signal_pair_components(
        source,
        target,
        manifest["eligibility"],
        manifest[
            "scoring"
        ][
            "weights"
        ],
    )

    assert (
        result[
            "component_scores"
        ][
            "temporality"
        ]
        == 0.90
    )

def _evaluate_pair(
    benchmark,
    source_id: str,
    target_id: str,
):
    from onehealth_worker.evaluation.event_matching_v048 import (
        evaluate_signal_pair_v048,
    )

    return evaluate_signal_pair_v048(
        benchmark.signal_index[
            source_id
        ],
        benchmark.signal_index[
            target_id
        ],
        benchmark.manifest,
    )


def test_v048_hard_conflict_overrides_numeric_compatibility():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    result = _evaluate_pair(
        benchmark,
        "GS-MVH-20260526-02",
        "GS-MVH-20260629-03",
    )

    assert result["score"] > 0.60

    assert (
        result[
            "hard_conflict"
        ]
        is True
    )

    assert (
        result[
            "hard_conflict_reason"
        ]
        == "explicit_genomic_incompatibility"
    )

    assert (
        result["relation"]
        == "contradicts"
    )

    assert (
        result["decision"]
        == "rejected"
    )

    assert (
        result["merge_allowed"]
        is False
    )


def test_v048_hard_conflict_detection_is_order_invariant():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    forward = _evaluate_pair(
        benchmark,
        "GS-MVH-20260519-03",
        "GS-MVH-20260629-03",
    )

    reverse = _evaluate_pair(
        benchmark,
        "GS-MVH-20260629-03",
        "GS-MVH-20260519-03",
    )

    for key in (
        "hard_conflict",
        "hard_conflict_reason",
        "relation",
        "decision",
        "merge_allowed",
    ):
        assert (
            forward[key]
            == reverse[key]
        )


def test_v048_one_health_investigation_is_not_auto_merged():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    result = _evaluate_pair(
        benchmark,
        "GS-MVH-20260519-04",
        "GS-MVH-20260629-01",
    )

    assert (
        result["hard_conflict"]
        is False
    )

    assert (
        result["relation"]
        == "possibly_related"
    )

    assert (
        result["decision"]
        == "review_required"
    )

    assert (
        result["merge_allowed"]
        is False
    )


def test_v048_clear_longitudinal_refinement_can_auto_link():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    result = _evaluate_pair(
        benchmark,
        "GS-MVH-20260512-01",
        "GS-MVH-20260519-01",
    )

    assert (
        result["relation"]
        == "refines"
    )

    assert (
        result["decision"]
        == "auto_linked"
    )

    assert (
        result["merge_allowed"]
        is True
    )


def test_v048_transmission_refinement_stays_human_reviewed():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    result = _evaluate_pair(
        benchmark,
        "GS-MVH-20260504-03",
        "GS-MVH-20260519-02",
    )

    assert (
        result["relation"]
        == "refines"
    )

    assert (
        result["decision"]
        == "review_required"
    )

    assert (
        result["merge_allowed"]
        is True
    )


def test_v048_ineligible_pair_short_circuits_full_policy():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    result = _evaluate_pair(
        benchmark,
        "GS-MVH-20260504-06",
        "GS-MVH-20260526-01",
    )

    assert (
        result["gate"]
        == "ineligible"
    )

    assert result["score"] is None
    assert result["relation"] is None
    assert result["decision"] is None

    assert (
        result["merge_allowed"]
        is False
    )


def test_v048_all_fourteen_adjudicated_pairs_match_policy():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    assert (
        benchmark.pair_count
        == 14
    )

    for pair in benchmark.adjudicated_pairs:
        result = _evaluate_pair(
            benchmark,
            pair[
                "source_signal_id"
            ],
            pair[
                "target_signal_id"
            ],
        )

        assert (
            result["gate"]
            == pair[
                "expected_gate"
            ]
        ), pair["pair_id"]

        assert (
            result["relation"]
            == pair[
                "expected_relation"
            ]
        ), pair["pair_id"]

        assert (
            result["decision"]
            == pair[
                "expected_decision"
            ]
        ), pair["pair_id"]

        assert (
            result["merge_allowed"]
            == pair[
                "expected_merge_allowed"
            ]
        ), pair["pair_id"]

        assert (
            result["hard_conflict"]
            == pair[
                "expected_hard_conflict"
            ]
        ), pair["pair_id"]

        expected_reason = pair.get(
            "expected_hard_conflict_reason"
        )

        if expected_reason:
            assert (
                result[
                    "hard_conflict_reason"
                ]
                == expected_reason
            ), pair["pair_id"]

def test_v048_unresolved_pathogen_is_missing_not_incompatible():
    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    result = _evaluate_pair(
        benchmark,
        "GS-MVH-20260504-04",
        "GS-MVH-20260512-02",
    )

    assert (
        result[
            "component_scores"
        ][
            "etiology"
        ]
        == 0.80
    )

    assert result["score"] >= 0.80

    assert (
        result["relation"]
        == "refines"
    )

    assert (
        result["decision"]
        == "auto_linked"
    )

    assert (
        result["merge_allowed"]
        is True
    )

def test_v048_aggregate_release_gate_passes_gold_on_gold():
    from onehealth_worker.evaluation.event_matching_v048 import (
        evaluate_event_matching_benchmark,
    )

    report = evaluate_event_matching_benchmark(
        MANIFEST
    )

    assert report[
        "evaluated_pairs"
    ] == 14

    assert report[
        "eligible_pairs"
    ] == 11

    assert report[
        "ineligible_pairs"
    ] == 3

    assert report[
        "expected_hard_conflicts"
    ] == 2

    assert report[
        "predicted_auto_links"
    ] == 5

    assert report[
        "release_gate"
    ][
        "metrics_pass"
    ] is True

    assert report[
        "release_gate"
    ][
        "event_matcher_validated"
    ] is True


def test_v048_aggregate_metrics_are_perfect_on_adjudicated_pairs():
    from onehealth_worker.evaluation.event_matching_v048 import (
        evaluate_event_matching_benchmark,
    )

    report = evaluate_event_matching_benchmark(
        MANIFEST
    )

    aggregate = report[
        "aggregate"
    ]

    assert (
        aggregate[
            "ineligible_gate_accuracy"
        ]
        == 1.0
    )

    assert (
        aggregate[
            "hard_conflict_recall"
        ]
        == 1.0
    )

    assert (
        aggregate[
            "hard_conflict_reason_accuracy"
        ]
        == 1.0
    )

    assert (
        aggregate[
            "hard_conflict_false_auto_links"
        ]
        == 0
    )

    assert (
        aggregate[
            "auto_link_precision"
        ]
        == 1.0
    )

    assert (
        aggregate[
            "pair_decision_accuracy"
        ]
        == 1.0
    )

    assert (
        aggregate[
            "relation_accuracy"
        ]
        == 1.0
    )

    assert (
        aggregate[
            "order_invariance"
        ]
        is True
    )


def test_v048_aggregate_report_preserves_pair_traceability():
    from onehealth_worker.evaluation.event_matching_v048 import (
        evaluate_event_matching_benchmark,
    )

    report = evaluate_event_matching_benchmark(
        MANIFEST
    )

    pairs = {
        pair["pair_id"]: pair
        for pair in report[
            "pairs"
        ]
    }

    conflict = pairs[
        "EM-V048-010"
    ]

    assert (
        conflict[
            "expected"
        ][
            "hard_conflict"
        ]
        is True
    )

    assert (
        conflict[
            "actual"
        ][
            "hard_conflict_reason"
        ]
        == "explicit_genomic_incompatibility"
    )

    assert (
        conflict[
            "actual"
        ][
            "decision"
        ]
        == "rejected"
    )

    assert (
        conflict[
            "order_invariant"
        ]
        is True
    )


def test_v048_release_gate_detects_a_strict_decision_regression(
    monkeypatch,
):
    import onehealth_worker.evaluation.event_matching_v048 as matcher

    benchmark = matcher.load_event_matching_benchmark(
        MANIFEST
    )

    benchmark.manifest[
        "release_thresholds"
    ][
        "pair_decision_accuracy"
    ] = 1.0

    original = (
        matcher.evaluate_signal_pair_v048
    )

    def degraded(
        source,
        target,
        manifest,
    ):
        result = original(
            source,
            target,
            manifest,
        )

        source_id = source.get(
            "local_signal_id"
        )

        target_id = target.get(
            "local_signal_id"
        )

        pair_ids = {
            source_id,
            target_id,
        }

        if pair_ids == {
            "GS-MVH-20260512-01",
            "GS-MVH-20260519-01",
        }:
            result = dict(result)
            result[
                "decision"
            ] = "review_required"

        return result

    monkeypatch.setattr(
        matcher,
        "evaluate_signal_pair_v048",
        degraded,
    )

    report = (
        matcher.evaluate_event_matching_benchmark(
            benchmark
        )
    )

    assert (
        report[
            "aggregate"
        ][
            "pair_decision_accuracy"
        ]
        < 1.0
    )

    assert (
        report[
            "release_gate"
        ][
            "metrics_pass"
        ]
        is False
    )

    assert (
        report[
            "release_gate"
        ][
            "event_matcher_validated"
        ]
        is False
    )

def test_v048_ineligible_pair_is_order_invariant_with_swapped_endpoint_eligibility():
    from onehealth_worker.evaluation.event_matching_v048 import (
        _pair_order_invariant,
        evaluate_signal_pair_v048,
    )

    benchmark = load_event_matching_benchmark(
        MANIFEST
    )

    source = benchmark.signal_index[
        "GS-MVH-20260504-06"
    ]

    target = benchmark.signal_index[
        "GS-MVH-20260526-01"
    ]

    forward = evaluate_signal_pair_v048(
        source,
        target,
        benchmark.manifest,
    )

    reverse = evaluate_signal_pair_v048(
        target,
        source,
        benchmark.manifest,
    )

    assert forward["source_eligible"] is False
    assert forward["target_eligible"] is True

    assert reverse["source_eligible"] is True
    assert reverse["target_eligible"] is False

    assert (
        _pair_order_invariant(
            forward,
            reverse,
        )
        is True
    )

def test_v048_cli_writes_reproducible_event_matching_report(
    tmp_path,
    monkeypatch,
    capsys,
):
    import sys

    from onehealth_worker.__main__ import main

    output = (
        tmp_path
        / "event-matching-v048.json"
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "onehealth-worker",
            "evaluate-event-matching",
            "--manifest",
            str(MANIFEST),
            "--output",
            str(output),
        ],
    )

    main()

    assert output.exists()

    written = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    printed = json.loads(
        capsys.readouterr().out
    )

    assert written == printed

    assert (
        written[
            "benchmark_version"
        ]
        == "0.4.8"
    )

    assert (
        written[
            "evaluated_pairs"
        ]
        == 14
    )

    assert (
        written[
            "release_gate"
        ][
            "metrics_pass"
        ]
        is True
    )

    assert (
        written[
            "release_gate"
        ][
            "event_matcher_validated"
        ]
        is True
    )
