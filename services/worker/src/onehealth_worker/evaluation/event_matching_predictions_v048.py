from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .corpus import evaluate_file
from .event_matching_v048 import (
    EventMatchingBenchmark,
    evaluate_event_matching_benchmark,
    load_event_matching_benchmark,
)
from .reassembly import reassemble_evaluation_corpus


_MISMATCH_FIELDS = (
    "gate",
    "relation",
    "decision",
    "merge_allowed",
    "hard_conflict",
    "hard_conflict_reason",
)


def _read_json(
    path: Path,
) -> dict[str, Any]:
    return json.loads(
        path.read_text(
            encoding="utf-8-sig",
        )
    )


def _relative_path(
    path: Path,
    root: Path,
) -> str:
    try:
        return str(
            path.resolve().relative_to(
                root.resolve()
            )
        )
    except ValueError:
        return str(
            path.resolve()
        )


def evaluate_event_matching_predictions(
    *,
    event_manifest_path: Path,
    corpus_manifest_path: Path,
) -> dict[str, Any]:
    """Evaluate v0.4.8 event matching on reconstructed automatic signals.

    Missing assembled predictions are rebuilt deterministically from the
    versioned atomic-claims sidecars before evaluation. No LLM, network,
    database, or Supabase access is required.
    """

    event_manifest_path = (
        event_manifest_path.resolve()
    )

    corpus_manifest_path = (
        corpus_manifest_path.resolve()
    )

    repo_root = (
        event_manifest_path.parents[2]
    )

    base_benchmark = (
        load_event_matching_benchmark(
            event_manifest_path
        )
    )

    corpus_manifest = _read_json(
        corpus_manifest_path
    )

    corpus_version = str(
        corpus_manifest.get(
            "benchmark_version"
        )
        or ""
    ) or None

    reassembly = (
        reassemble_evaluation_corpus(
            manifest_path=corpus_manifest_path,
            force=False,
        )
    )

    corpus_base = (
        corpus_manifest_path.parent
    )

    gold_to_prediction: dict[
        str,
        dict[str, Any],
    ] = {}

    unmatched_gold: list[
        dict[str, Any]
    ] = []

    unmatched_prediction: list[
        dict[str, Any]
    ] = []

    document_mapping: list[
        dict[str, Any]
    ] = []

    for item in corpus_manifest.get(
        "documents",
        [],
    ):
        if item.get("status") != "adjudicated":
            continue

        prediction_rel = item.get(
            "prediction"
        )

        gold_rel = item.get(
            "gold"
        )

        if not prediction_rel or not gold_rel:
            raise ValueError(
                "Documento adjudicado sin "
                "prediction/gold configurados: "
                f"{item.get('label')}"
            )

        prediction_path = (
            corpus_base
            / prediction_rel
        ).resolve()

        gold_path = (
            corpus_base
            / gold_rel
        ).resolve()

        if not prediction_path.exists():
            raise FileNotFoundError(
                "La predicción no existe luego "
                "del reassembly determinístico: "
                f"{prediction_path}"
            )

        if not gold_path.exists():
            raise FileNotFoundError(
                f"Gold no encontrado: {gold_path}"
            )

        extraction_report = (
            evaluate_file(
                prediction_path,
                gold_path,
                benchmark_version=(
                    corpus_version
                ),
            )
        )

        matches_for_document: list[
            dict[str, Any]
        ] = []

        for match in extraction_report[
            "matched_signals"
        ]:
            gold_id = match[
                "gold_signal_id"
            ]

            predicted_id = match[
                "predicted_signal_id"
            ]

            if gold_id in gold_to_prediction:
                raise ValueError(
                    "Gold signal mapeada más "
                    f"de una vez: {gold_id}"
                )

            gold_to_prediction[
                gold_id
            ] = {
                "predicted_signal_id": (
                    predicted_id
                ),
                "prediction_path": (
                    prediction_path
                ),
                "gold_path": gold_path,
                "match_score": match[
                    "match_score"
                ],
            }

            matches_for_document.append(
                {
                    "gold_signal_id": (
                        gold_id
                    ),
                    "predicted_signal_id": (
                        predicted_id
                    ),
                    "match_score": match[
                        "match_score"
                    ],
                }
            )

        for signal in extraction_report[
            "unmatched_gold"
        ]:
            unmatched_gold.append(
                {
                    "gold_signal_id": (
                        signal.get(
                            "local_signal_id"
                        )
                    ),
                    "signal_role": (
                        signal.get(
                            "signal_role"
                        )
                    ),
                    "signal_type": (
                        signal.get(
                            "signal_type"
                        )
                    ),
                    "summary": (
                        signal.get(
                            "signal_summary"
                        )
                    ),
                    "gold_path": (
                        _relative_path(
                            gold_path,
                            repo_root,
                        )
                    ),
                }
            )

        for signal in extraction_report[
            "unmatched_prediction"
        ]:
            unmatched_prediction.append(
                {
                    "predicted_signal_id": (
                        signal.get(
                            "local_signal_id"
                        )
                    ),
                    "signal_role": (
                        signal.get(
                            "signal_role"
                        )
                    ),
                    "signal_type": (
                        signal.get(
                            "signal_type"
                        )
                    ),
                    "summary": (
                        signal.get(
                            "signal_summary"
                        )
                    ),
                    "prediction_path": (
                        _relative_path(
                            prediction_path,
                            repo_root,
                        )
                    ),
                }
            )

        document_mapping.append(
            {
                "label": item.get(
                    "label"
                ),
                "gold_signals": (
                    extraction_report[
                        "signal_detection"
                    ][
                        "gold_signals"
                    ]
                ),
                "predicted_signals": (
                    extraction_report[
                        "signal_detection"
                    ][
                        "predicted_signals"
                    ]
                ),
                "matched_signals": len(
                    matches_for_document
                ),
                "matches": (
                    matches_for_document
                ),
            }
        )

    required_gold_ids = {
        signal_id
        for pair
        in base_benchmark.adjudicated_pairs
        for signal_id
        in (
            pair["source_signal_id"],
            pair["target_signal_id"],
        )
    }

    missing_pair_gold_ids = sorted(
        required_gold_ids
        - set(
            gold_to_prediction
        )
    )

    if missing_pair_gold_ids:
        raise ValueError(
            "No se pueden evaluar todos los "
            "pares v0.4.8. Faltan señales gold "
            "con contraparte automática: "
            + ", ".join(
                missing_pair_gold_ids
            )
        )

    prediction_cache: dict[
        Path,
        dict[str, Any],
    ] = {}

    predicted_signal_index: dict[
        str,
        dict[str, Any],
    ] = {}

    predicted_sources: dict[
        str,
        Path,
    ] = {}

    predicted_ids: dict[
        str,
        str,
    ] = {}

    for gold_id, mapping in (
        gold_to_prediction.items()
    ):
        prediction_path = mapping[
            "prediction_path"
        ]

        if (
            prediction_path
            not in prediction_cache
        ):
            prediction_cache[
                prediction_path
            ] = _read_json(
                prediction_path
            )

        predicted_id = mapping[
            "predicted_signal_id"
        ]

        payload = prediction_cache[
            prediction_path
        ]

        matching_signals = [
            signal
            for signal
            in payload.get(
                "signals",
                [],
            )
            if signal.get(
                "local_signal_id"
            )
            == predicted_id
        ]

        if len(matching_signals) != 1:
            raise ValueError(
                f"{gold_id}: se esperaba "
                f"exactamente una señal "
                f"{predicted_id}; se encontraron "
                f"{len(matching_signals)}."
            )

        predicted_signal_index[
            gold_id
        ] = matching_signals[0]

        predicted_sources[
            gold_id
        ] = prediction_path

        predicted_ids[
            gold_id
        ] = predicted_id

    prediction_benchmark = (
        EventMatchingBenchmark(
            manifest_path=(
                base_benchmark.manifest_path
            ),
            manifest=(
                base_benchmark.manifest
            ),
            gold_paths=(
                base_benchmark.gold_paths
            ),
            gold_documents=(
                base_benchmark.gold_documents
            ),
            signal_index=(
                predicted_signal_index
            ),
            signal_sources=(
                predicted_sources
            ),
            adjudicated_pairs=(
                base_benchmark.adjudicated_pairs
            ),
        )
    )

    matcher_report = (
        evaluate_event_matching_benchmark(
            prediction_benchmark
        )
    )

    enriched_pairs: list[
        dict[str, Any]
    ] = []

    mismatches: list[
        dict[str, Any]
    ] = []

    functional_mismatches = 0
    explanation_only_mismatches = 0

    for pair in matcher_report[
        "pairs"
    ]:
        source_gold_id = pair[
            "source_signal_id"
        ]

        target_gold_id = pair[
            "target_signal_id"
        ]

        expected = pair[
            "expected"
        ]

        actual = pair[
            "actual"
        ]

        different_fields = [
            field
            for field
            in _MISMATCH_FIELDS
            if actual.get(field)
            != expected.get(field)
        ]

        enriched = {
            **pair,
            "prediction_source_signal_id": (
                predicted_ids[
                    source_gold_id
                ]
            ),
            "prediction_target_signal_id": (
                predicted_ids[
                    target_gold_id
                ]
            ),
            "different_fields": (
                different_fields
            ),
        }

        enriched_pairs.append(
            enriched
        )

        if not different_fields:
            continue

        if set(
            different_fields
        ) == {
            "hard_conflict_reason"
        }:
            mismatch_scope = (
                "explanation_only"
            )
            explanation_only_mismatches += 1
        else:
            mismatch_scope = (
                "functional"
            )
            functional_mismatches += 1

        mismatches.append(
            {
                "pair_id": pair[
                    "pair_id"
                ],
                "family": pair.get(
                    "family"
                ),
                "mismatch_scope": (
                    mismatch_scope
                ),
                "gold_source_signal_id": (
                    source_gold_id
                ),
                "gold_target_signal_id": (
                    target_gold_id
                ),
                "predicted_source_signal_id": (
                    predicted_ids[
                        source_gold_id
                    ]
                ),
                "predicted_target_signal_id": (
                    predicted_ids[
                        target_gold_id
                    ]
                ),
                "score": actual.get(
                    "score"
                ),
                "information_coverage": (
                    actual.get(
                        "information_coverage"
                    )
                ),
                "different_fields": (
                    different_fields
                ),
                "expected": expected,
                "actual": {
                    field: actual.get(
                        field
                    )
                    for field
                    in _MISMATCH_FIELDS
                },
            }
        )

    result = {
        **matcher_report,
        "benchmark_mode": (
            "automatic_predictions_v047_"
            "on_v048_event_matcher"
        ),
        "source_corpus_benchmark_version": (
            corpus_version
        ),
        "source_prediction_architecture": (
            corpus_manifest.get(
                "prediction_architecture"
            )
        ),
        "deterministic_reassembly": {
            "architecture": (
                reassembly.get(
                    "architecture"
                )
            ),
            "llm_invoked": (
                reassembly.get(
                    "llm_invoked"
                )
            ),
        },
        "mapping_summary": {
            "mapped_gold_signals": len(
                gold_to_prediction
            ),
            "pair_reference_gold_signals": (
                len(
                    required_gold_ids
                )
            ),
            "missing_pair_gold_signals": (
                missing_pair_gold_ids
            ),
            "unmatched_gold_count": len(
                unmatched_gold
            ),
            "unmatched_prediction_count": len(
                unmatched_prediction
            ),
            "unmatched_gold": (
                unmatched_gold
            ),
            "unmatched_prediction": (
                unmatched_prediction
            ),
            "documents": (
                document_mapping
            ),
        },
        "mismatch_summary": {
            "total": len(
                mismatches
            ),
            "functional": (
                functional_mismatches
            ),
            "explanation_only": (
                explanation_only_mismatches
            ),
        },
        "pairs": enriched_pairs,
        "mismatches": mismatches,
    }

    return result
