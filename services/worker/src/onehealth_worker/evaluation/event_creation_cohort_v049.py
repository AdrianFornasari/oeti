from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from typing import Any


_STRONG_CONTEXT_PREFIXES = (
    "vessel:",
)


def _strong_anchors(
    matcher_result: Mapping[str, Any],
) -> tuple[str, ...]:
    values = (
        matcher_result.get(
            "shared_event_context_anchors"
        )
        or []
    )

    anchors = {
        value.strip().casefold()
        for value in values
        if (
            isinstance(value, str)
            and value.strip().casefold().startswith(
                _STRONG_CONTEXT_PREFIXES
            )
        )
    }

    return tuple(
        sorted(anchors)
    )


def _eligible_relation(
    matcher_result: Mapping[str, Any],
) -> bool:
    return (
        matcher_result.get("decision")
        == "auto_linked"
        and matcher_result.get(
            "merge_allowed"
        )
        is True
        and matcher_result.get(
            "hard_conflict"
        )
        is not True
    )


def build_event_creation_cohorts(
    relations: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build deterministic event-creation cohorts.

    Auto-linked relations are grouped when:
    - they share a signal, or
    - they resolve to the same strong event-context anchor.

    Review-required, rejected, non-mergeable, and hard-conflict
    relations never contribute to automatic event creation.
    """

    parent: dict[str, str] = {}

    def add(
        node: str,
    ) -> None:
        parent.setdefault(
            node,
            node,
        )

    def find(
        node: str,
    ) -> str:
        root = node

        while parent[root] != root:
            root = parent[root]

        while parent[node] != node:
            next_node = parent[node]
            parent[node] = root
            node = next_node

        return root

    def union(
        left: str,
        right: str,
    ) -> None:
        add(left)
        add(right)

        left_root = find(left)
        right_root = find(right)

        if left_root == right_root:
            return

        if left_root < right_root:
            parent[right_root] = left_root
        else:
            parent[left_root] = right_root

    prepared: list[
        dict[str, Any]
    ] = []

    for relation in relations:
        matcher_result = relation.get(
            "matcher_result"
        )

        if not isinstance(
            matcher_result,
            Mapping,
        ):
            continue

        if not _eligible_relation(
            matcher_result
        ):
            continue

        relation_id = str(
            relation[
                "signal_relation_id"
            ]
        )

        source_id = str(
            relation[
                "source_signal_id"
            ]
        )

        target_id = str(
            relation[
                "target_signal_id"
            ]
        )

        source_node = (
            f"signal:{source_id}"
        )

        target_node = (
            f"signal:{target_id}"
        )

        union(
            source_node,
            target_node,
        )

        anchors = _strong_anchors(
            matcher_result
        )

        for anchor in anchors:
            anchor_node = (
                f"context:{anchor}"
            )

            union(
                source_node,
                anchor_node,
            )

            union(
                target_node,
                anchor_node,
            )

        prepared.append(
            {
                "signal_relation_id": (
                    relation_id
                ),
                "source_signal_id": (
                    source_id
                ),
                "target_signal_id": (
                    target_id
                ),
                "score": (
                    matcher_result.get(
                        "score"
                    )
                ),
                "strong_context_anchors": (
                    anchors
                ),
            }
        )

    component_relations: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for item in prepared:
        root = find(
            f"signal:"
            f"{item['source_signal_id']}"
        )

        component_relations[
            root
        ].append(item)

    cohorts: list[
        dict[str, Any]
    ] = []

    for items in (
        component_relations.values()
    ):
        signal_ids = {
            signal_id
            for item in items
            for signal_id in (
                item["source_signal_id"],
                item["target_signal_id"],
            )
        }

        relation_ids = {
            item[
                "signal_relation_id"
            ]
            for item in items
        }

        anchors = {
            anchor
            for item in items
            for anchor in item[
                "strong_context_anchors"
            ]
        }

        # Highest matcher score becomes the deterministic
        # seed relation. Relation ID is the tie-breaker.
        ranked = sorted(
            items,
            key=lambda item: (
                -float(
                    item["score"]
                    if item["score"]
                    is not None
                    else -1.0
                ),
                item[
                    "signal_relation_id"
                ],
            ),
        )

        seed_relation_id = (
            ranked[0][
                "signal_relation_id"
            ]
        )

        cohorts.append(
            {
                "seed_relation_id": (
                    seed_relation_id
                ),
                "signal_relation_ids": (
                    sorted(relation_ids)
                ),
                "signal_ids": (
                    sorted(signal_ids)
                ),
                "strong_event_context_anchors": (
                    sorted(anchors)
                ),
                "relation_count": (
                    len(relation_ids)
                ),
                "signal_count": (
                    len(signal_ids)
                ),
            }
        )

    cohorts.sort(
        key=lambda item: (
            item[
                "seed_relation_id"
            ]
        )
    )

    return cohorts
