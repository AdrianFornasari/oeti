from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .event_context_v049 import (
    CONTEXT_RESOLVER_VERSION,
    resolve_signal_event_context_anchors,
)
from .event_matching_policy_v049 import (
    apply_v049_auto_link_guard,
)
from .event_matching_repository_v049 import (
    EventMatchingRepository,
    canonical_signal_pair,
)
from .event_matching_v048 import (
    evaluate_signal_pair_v048,
)


def _load_raw_text_for_signal(
    repository: Any,
    signal_id: str,
) -> str:
    """Load source text when the repository supports it.

    Test doubles and legacy repository adapters may not expose
    load_raw_text_for_signal(). Missing source text must fail
    conservatively: no contextual anchor can be derived.
    """

    loader = getattr(
        repository,
        "load_raw_text_for_signal",
        None,
    )

    if not callable(loader):
        return ""

    value = loader(
        signal_id
    )

    if value is None:
        return ""

    return str(value)


class EventMatchingOrchestrator:
    """Execute DB-backed matching with the v0.4.9 production safety policy."""

    def __init__(
        self,
        repository: EventMatchingRepository,
        matcher_manifest: Mapping[str, Any],
    ):
        self.repository = repository
        self.matcher_manifest = dict(
            matcher_manifest
        )

    def evaluate_anchor(
        self,
        anchor_signal_id: str,
        *,
        max_candidates: int = 250,
        persist: bool = False,
    ) -> dict[str, Any]:
        anchor = (
            self.repository
            .load_signal_for_matching(
                anchor_signal_id
            )
        )

        anchor_raw_text = (
            _load_raw_text_for_signal(
                self.repository,
                anchor.signal_id,
            )
        )

        anchor_context_anchors = (
            resolve_signal_event_context_anchors(
                anchor.payload,
                anchor_raw_text,
            )
        )

        candidate_refs = (
            self.repository
            .load_candidate_signal_refs(
                anchor_signal_id,
                max_candidates=max_candidates,
            )
        )

        results: list[
            dict[str, Any]
        ] = []

        for rank, candidate_ref in enumerate(
            candidate_refs,
            start=1,
        ):
            candidate = (
                self.repository
                .load_signal_for_matching(
                    candidate_ref.signal_id
                )
            )

            candidate_raw_text = (
                _load_raw_text_for_signal(
                    self.repository,
                    candidate.signal_id,
                )
            )

            candidate_context_anchors = (
                resolve_signal_event_context_anchors(
                    candidate.payload,
                    candidate_raw_text,
                )
            )

            (
                source_signal_id,
                target_signal_id,
            ) = canonical_signal_pair(
                anchor.signal_id,
                candidate.signal_id,
            )

            if (
                source_signal_id
                == anchor.signal_id
            ):
                source_payload = (
                    anchor.payload
                )
                target_payload = (
                    candidate.payload
                )

                source_context_anchors = (
                    anchor_context_anchors
                )
                target_context_anchors = (
                    candidate_context_anchors
                )

            else:
                source_payload = (
                    candidate.payload
                )
                target_payload = (
                    anchor.payload
                )

                source_context_anchors = (
                    candidate_context_anchors
                )
                target_context_anchors = (
                    anchor_context_anchors
                )

            base_matcher_result = (
                evaluate_signal_pair_v048(
                    source_payload,
                    target_payload,
                    self.matcher_manifest,
                )
            )

            matcher_result = (
                apply_v049_auto_link_guard(
                    base_matcher_result,
                    source_context_anchors=(
                        source_context_anchors
                    ),
                    target_context_anchors=(
                        target_context_anchors
                    ),
                )
            )

            matcher_result[
                "context_resolver_version"
            ] = CONTEXT_RESOLVER_VERSION

            matcher_result[
                "source_event_context_anchors"
            ] = list(
                source_context_anchors
            )

            matcher_result[
                "target_event_context_anchors"
            ] = list(
                target_context_anchors
            )

            results.append(
                {
                    "candidate_rank": rank,
                    "pair_key": (
                        f"{source_signal_id}:"
                        f"{target_signal_id}"
                    ),
                    "source_signal_id": (
                        source_signal_id
                    ),
                    "target_signal_id": (
                        target_signal_id
                    ),
                    "anchor_signal_id": (
                        anchor.signal_id
                    ),
                    "candidate_signal_id": (
                        candidate.signal_id
                    ),
                    "candidate_prefilter": {
                        "same_disease": (
                            candidate_ref.same_disease
                        ),
                        "same_pathogen": (
                            candidate_ref.same_pathogen
                        ),
                        "temporal_distance_days": (
                            candidate_ref
                            .temporal_distance_days
                        ),
                    },
                    "source_context_anchors": list(
                        source_context_anchors
                    ),
                    "target_context_anchors": list(
                        target_context_anchors
                    ),
                    "matcher_result": (
                        matcher_result
                    ),
                }
            )

        decisions = {
            "auto_linked": 0,
            "review_required": 0,
            "rejected": 0,
            "ineligible": 0,
        }

        hard_conflicts = 0

        for item in results:
            matcher_result = item[
                "matcher_result"
            ]

            decision = matcher_result.get(
                "decision"
            )

            if decision in decisions:
                decisions[decision] += 1

            if (
                matcher_result.get("gate")
                == "ineligible"
            ):
                decisions["ineligible"] += 1

            if matcher_result.get(
                "hard_conflict"
            ):
                hard_conflicts += 1

        matcher_version = str(
            self.matcher_manifest.get(
                "benchmark_version"
            )
            or "0.4.8"
        )

        persistable_items = [
            {
                "source_signal_id": (
                    item[
                        "source_signal_id"
                    ]
                ),
                "target_signal_id": (
                    item[
                        "target_signal_id"
                    ]
                ),
                "matcher_result": (
                    item[
                        "matcher_result"
                    ]
                ),
                "candidate_prefilter": (
                    item[
                        "candidate_prefilter"
                    ]
                ),
            }
            for item in results
            if (
                item[
                    "matcher_result"
                ].get("gate")
                == "eligible"
            )
        ]

        persisted_records: list[
            dict[str, Any]
        ] = []

        if (
            persist
            and persistable_items
        ):
            persisted_records = (
                self.repository
                .persist_matcher_relations_batch(
                    persistable_items,
                    matcher_version=(
                        matcher_version
                    ),
                )
            )

        inserted = sum(
            1
            for item in persisted_records
            if item.get("action")
            == "inserted"
        )

        updated = sum(
            1
            for item in persisted_records
            if item.get("action")
            == "updated"
        )

        persistence = {
            "requested": persist,
            "persistable_pairs": len(
                persistable_items
            ),
            "persisted_pairs": len(
                persisted_records
            ),
            "inserted": inserted,
            "updated": updated,
            "skipped_ineligible": (
                len(results)
                - len(
                    persistable_items
                )
            ),
        }

        return {
            "matcher_version": (
                matcher_version
            ),
            "policy_version": "0.4.9",
            "mode": (
                "persist"
                if persist
                else "read_only"
            ),
            "persistence": persistence,
            "anchor_signal_id": (
                anchor.signal_id
            ),
            "anchor_context_anchors": list(
                anchor_context_anchors
            ),
            "candidate_count": len(
                candidate_refs
            ),
            "evaluated_pairs": len(
                results
            ),
            "summary": {
                **decisions,
                "hard_conflicts": (
                    hard_conflicts
                ),
            },
            "results": results,
        }
