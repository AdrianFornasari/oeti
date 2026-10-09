from __future__ import annotations

import json
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Iterator

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row


@dataclass(slots=True)
class PersistedMatcherSignal:
    signal_id: str
    payload: dict[str, Any]


def _as_mapping(
    value: Any,
) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}

        if isinstance(parsed, Mapping):
            return dict(parsed)

    return {}


def _as_list(
    value: Any,
) -> list[Any]:
    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []

        if isinstance(parsed, list):
            return parsed

    return []


def _iso_date(
    value: Any,
) -> str | None:
    if value is None:
        return None

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, str):
        return value

    return str(value)


def _optional_float(
    value: Any,
) -> float | None:
    if value is None:
        return None

    if isinstance(
        value,
        (int, float, Decimal),
    ):
        return float(value)

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_matcher_signal_payload(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """Reconstruct the v0.4.8 matcher payload from persisted DB data."""

    diagnostics = {
        "test_reported": False,
        "test_type": None,
        "method": None,
        "target": None,
        "specimen": None,
        "result": "unknown",
    }

    diagnostics.update(
        _as_mapping(
            row.get("diagnostics")
        )
    )

    genomics = {
        "sequence_reported": False,
        "accession": None,
        "lineage": None,
        "clade": None,
        "test_result": "unknown",
    }

    genomics.update(
        _as_mapping(
            row.get("genomics")
        )
    )

    transmission = _as_mapping(
        row.get("transmission")
    )

    reference_period = _as_mapping(
        row.get("reference_period")
    )

    return {
        "database_signal_id": str(
            row["signal_id"]
        ),
        "local_signal_id": row.get(
            "local_signal_key"
        ),
        "schema_version": row.get(
            "schema_version"
        ),
        "signal_role": row.get(
            "signal_role"
        ),
        "signal_type": row.get(
            "signal_type"
        ),
        "signal_summary": row.get(
            "signal_summary"
        ),
        "verification_status": row.get(
            "verification_status"
        ),
        "event_matching_eligible": bool(
            row.get(
                "event_matching_eligible"
            )
        ),
        "is_current": bool(
            row.get("is_current")
        ),
        "domains": _as_list(
            row.get("domains")
        ),
        "extraction_confidence": (
            _optional_float(
                row.get(
                    "extraction_confidence"
                )
            )
        ),
        "disease": {
            "verbatim": row.get(
                "disease_verbatim"
            ),
            "canonical_name": row.get(
                "disease_canonical_name"
            ),
            "normalization_status": (
                row.get(
                    "disease_normalization_status"
                )
                or "unresolved"
            ),
            "confidence": (
                _optional_float(
                    row.get(
                        "disease_confidence"
                    )
                )
            ),
        },
        "pathogen": {
            "verbatim": row.get(
                "pathogen_verbatim"
            ),
            "canonical_name": row.get(
                "pathogen_canonical_name"
            ),
            "normalization_status": (
                row.get(
                    "pathogen_normalization_status"
                )
                or "unresolved"
            ),
            "confidence": (
                _optional_float(
                    row.get(
                        "pathogen_confidence"
                    )
                )
            ),
        },
        "event_date": {
            "start": _iso_date(
                row.get(
                    "occurred_start"
                )
            ),
            "end": _iso_date(
                row.get(
                    "occurred_end"
                )
            ),
            "precision": row.get(
                "date_precision"
            ),
        },
        "reference_period": (
            reference_period
        ),
        "transmission": transmission,
        "locations": _as_list(
            row.get("locations")
        ),
        "hosts": _as_list(
            row.get("hosts")
        ),
        "metrics": _as_list(
            row.get("metrics")
        ),
        "evidence": _as_list(
            row.get("evidence")
        ),
        "diagnostics": diagnostics,
        "genomics": genomics,
    }


@dataclass(slots=True, frozen=True)
class CandidateSignalRef:
    signal_id: str
    same_disease: bool
    same_pathogen: bool
    temporal_distance_days: int | None


def canonical_signal_pair(
    source_signal_id: str,
    target_signal_id: str,
) -> tuple[str, str]:
    """Return one stable orientation for a symmetric matcher pair."""

    source = str(source_signal_id)
    target = str(target_signal_id)

    if source == target:
        raise ValueError(
            "Una seÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â±al no puede formar un par consigo misma."
        )

    return tuple(
        sorted(
            (
                source,
                target,
            )
        )
    )

class EventMatchingRepository:
    """Read adapter between normalized PostgreSQL rows and Event Matcher."""

    def __init__(
        self,
        database_url: str,
        *,
        event_creation_writes_enabled: bool = False,
    ):
        self.database_url = database_url
        self.event_creation_writes_enabled = event_creation_writes_enabled

    @contextmanager
    def connection(
        self,
    ) -> Iterator[Connection]:
        with psycopg.connect(
            self.database_url,
            row_factory=dict_row,
        ) as conn:
            yield conn


    def persist_event_creation_cohort(
        self,
        *,
        event_seed: Mapping[str, Any],
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """Validate a cohort, or persist it atomically when explicitly enabled.

        Writes are disabled by default. Dry-run readiness is a read-only snapshot;
        the write path locks and revalidates before inserting any rows.
        """
        from uuid import UUID

        if not isinstance(event_seed, Mapping):
            raise ValueError(
                "event_seed must be a mapping."
            )

        event_code = event_seed.get("event_code")

        if (
            not isinstance(event_code, str)
            or not event_code.strip()
        ):
            raise ValueError(
                "event_seed requires event_code."
            )

        signal_ids = _as_list(
            event_seed.get("source_signal_ids")
        )

        relation_ids = _as_list(
            event_seed.get("source_relation_ids")
        )

        if len(signal_ids) < 2:
            raise ValueError(
                "Cohort requires at least two signals."
            )

        if not relation_ids:
            raise ValueError(
                "Cohort requires persisted relations."
            )

        for identifier in signal_ids + relation_ids:
            try:
                UUID(str(identifier))
            except (ValueError, TypeError, AttributeError):
                raise ValueError(
                    "Invalid cohort UUID."
                ) from None

        if not isinstance(dry_run, bool):
            raise ValueError("dry_run must be a boolean.")

        if not dry_run and not self.event_creation_writes_enabled:
            raise RuntimeError(
                "Event creation writes are not enabled."
            )

        from contextlib import nullcontext

        with self.connection() as conn:
            with conn.transaction() if not dry_run else nullcontext():
                with conn.cursor() as cur:
                    if not dry_run:
                        # Reads must get a fresh snapshot after waiting for the
                        # table locks, so a concurrent replay sees the first commit.
                        cur.execute("set transaction isolation level read committed")
                        cur.execute("set local lock_timeout = '5s'")
                        # Table locks protect against manual/non-cooperating writers
                        # too, including membership phantoms and evidence changes.
                        cur.execute("""
                            lock table public.diseases, public.pathogens,
                              public.raw_items, public.raw_item_payloads,
                              public.signals, public.signal_evidence,
                              public.signal_relations, public.events,
                              public.event_signals in share row exclusive mode
                        """)
                    result = self._validate_event_creation_cohort(
                        cur, event_seed=event_seed, event_code=event_code,
                        signal_ids=signal_ids, relation_ids=relation_ids,
                    )
                    if not dry_run:
                        result["dry_run"] = False
                        if result["status"] == "ready_to_create":
                            result = self._insert_event_creation_cohort(cur, result)
                    return result

    def _validate_event_creation_cohort(
        self, cur, *, event_seed, event_code, signal_ids, relation_ids,
    ) -> dict[str, Any]:
        """Rebuild and validate using the caller's transaction and cursor."""
        cur.execute(
            """
            select id
            from public.signals
            where id = any(%s::uuid[])
              and is_current = true
              and event_matching_eligible = true
            """,
            (signal_ids,),
        )

        rows = cur.fetchall()

        found_ids = {
            str(row["id"])
            for row in rows
        }

        missing_ids = sorted(
            set(signal_ids) - found_ids
        )

        if missing_ids:
            return {
                "status": "blocked",
                "dry_run": True,
                "event_code": event_code,
                "reason": (
                    "Signals are missing, stale "
                    "or ineligible."
                ),
                "missing_signal_ids": missing_ids,
            }

        cur.execute(
            """
            select
              id,
              source_signal_id,
              target_signal_id,
              relation::text as relation,
              hard_conflict,
              rationale
            from public.signal_relations
            where id = any(%s::uuid[])
              and rationale ->> 'producer'
                = %s
            """,
            (
                relation_ids,
                "oeti_event_matcher",
            ),
        )

        relation_rows = cur.fetchall()

        found_relation_ids = {
            str(row["id"])
            for row in relation_rows
        }

        missing_relation_ids = sorted(
            set(relation_ids)
            - found_relation_ids
        )

        if missing_relation_ids:
            return {
                "status": "blocked",
                "dry_run": True,
                "event_code": event_code,
                "reason": (
                    "Matcher relations are missing "
                    "or belong to another producer."
                ),
                "missing_relation_ids": (
                    missing_relation_ids
                ),
            }

        cohort_signal_ids = set(signal_ids)
        covered_signal_ids = set()
        invalid_relation_ids = []
        invalid_context_relation_ids = []
        mismatched_context_relation_ids = []
        invalid_context_version_relation_ids = []
        incompatible_context_version_relation_ids = []

        seed_context_anchors = {
            anchor.strip().casefold()
            for anchor in _as_list(
                event_seed.get(
                    "strong_event_context_anchors"
                )
            )
            if isinstance(anchor, str)
            and anchor.strip()
        }

        for row in relation_rows:
            rationale = _as_mapping(row.get("rationale"))

            source_id = str(row["source_signal_id"])
            target_id = str(row["target_signal_id"])

            valid = (
                rationale.get("gate") == "eligible"
                and rationale.get("decision") == "auto_linked"
                and rationale.get("merge_allowed") is True
                and row.get("hard_conflict") is False
                and row.get("relation") in {
                    "duplicates",
                    "refines",
                }
                and source_id in cohort_signal_ids
                and target_id in cohort_signal_ids
            )

            if not valid:
                invalid_relation_ids.append(str(row["id"]))
                continue

            override_reason = rationale.get(
                "auto_link_guard_override_reason"
            )

            if (
                override_reason
                == "shared_strong_event_context_anchor"
            ):
                shared_anchors = _as_list(
                    rationale.get(
                        "shared_event_context_anchors"
                    )
                )

                valid_anchor = any(
                    isinstance(anchor, str)
                    and bool(anchor.strip())
                    for anchor in shared_anchors
                )

                if not valid_anchor:
                    invalid_context_relation_ids.append(
                        str(row["id"])
                    )
                    continue

                persisted_context_anchors = {
                    anchor.strip().casefold()
                    for anchor in shared_anchors
                    if isinstance(anchor, str)
                    and anchor.strip()
                }

                if seed_context_anchors.isdisjoint(
                    persisted_context_anchors
                ):
                    mismatched_context_relation_ids.append(
                        str(row["id"])
                    )
                    continue

                required_versions = (
                    "matcher_version",
                    "policy_version",
                    "context_resolver_version",
                )

                invalid_versions = [
                    field
                    for field in required_versions
                    if (
                        not isinstance(
                            rationale.get(field),
                            str,
                        )
                        or not rationale.get(field).strip()
                    )
                ]

                if invalid_versions:
                    invalid_context_version_relation_ids.append(
                        str(row["id"])
                    )
                    continue

                expected_versions = {
                    "matcher_version": "0.4.8",
                    "policy_version": "0.4.9",
                    "context_resolver_version": "0.4.9",
                }

                incompatible = any(
                    rationale.get(field) != expected
                    for field, expected in expected_versions.items()
                )

                if incompatible:
                    incompatible_context_version_relation_ids.append(
                        str(row["id"])
                    )
                    continue

            covered_signal_ids.update(
                (source_id, target_id)
            )

        if invalid_context_relation_ids:
            return {
                "status": "blocked",
                "dry_run": True,
                "event_code": event_code,
                "reason": "invalid_context_override",
                "invalid_relation_ids": sorted(
                    invalid_context_relation_ids
                ),
            }

        if mismatched_context_relation_ids:
            return {
                "status": "blocked",
                "dry_run": True,
                "event_code": event_code,
                "reason": "context_anchor_mismatch",
                "invalid_relation_ids": sorted(
                    mismatched_context_relation_ids
                ),
            }

        if invalid_context_version_relation_ids:
            return {
                "status": "blocked",
                "dry_run": True,
                "event_code": event_code,
                "reason": "invalid_context_versions",
                "invalid_relation_ids": sorted(
                    invalid_context_version_relation_ids
                ),
            }

        if incompatible_context_version_relation_ids:
            return {
                "status": "blocked",
                "dry_run": True,
                "event_code": event_code,
                "reason": "incompatible_context_versions",
                "invalid_relation_ids": sorted(
                    incompatible_context_version_relation_ids
                ),
            }

        if invalid_relation_ids:
            return {
                "status": "blocked",
                "dry_run": True,
                "event_code": event_code,
                "reason": "invalid_matcher_relations",
                "invalid_relation_ids": sorted(
                    invalid_relation_ids
                ),
            }

        uncovered_signal_ids = sorted(
            cohort_signal_ids - covered_signal_ids
        )

        if uncovered_signal_ids:
            return {
                "status": "blocked",
                "dry_run": True,
                "event_code": event_code,
                "reason": "uncovered_cohort_signals",
                "uncovered_signal_ids": uncovered_signal_ids,
            }

        from .event_creation_v049 import build_event_creation_cohort_seed

        # Compatibility is required for every creation relation, including
        # ordinary auto-links that do not use a contextual override.
        expected_versions = {
            "matcher_version": "0.4.8", "policy_version": "0.4.9",
            "context_resolver_version": "0.4.9",
        }
        missing_version_ids = []
        incompatible_version_ids = []
        for row in relation_rows:
            rationale = _as_mapping(row.get("rationale"))
            if any(not isinstance(rationale.get(field), str) or not rationale[field].strip()
                   for field in expected_versions):
                missing_version_ids.append(str(row["id"]))
            elif any(rationale[field] != expected for field, expected in expected_versions.items()):
                incompatible_version_ids.append(str(row["id"]))
        if missing_version_ids or incompatible_version_ids:
            return {
                "status": "blocked", "dry_run": True, "event_code": event_code,
                "reason": "invalid_context_versions" if missing_version_ids else "incompatible_context_versions",
                "invalid_relation_ids": sorted(missing_version_ids or incompatible_version_ids),
            }

        cur.execute(
            """
            select s.id as signal_id, s.disease_id,
              d.canonical_name as disease_canonical_name,
              s.pathogen_id,
              p.canonical_name as pathogen_canonical_name,
              to_jsonb(s.domains) as domains, s.occurred_start,
              payload.raw_text,
              coalesce((
                select jsonb_agg(
                  jsonb_build_object('text', se.excerpt)
                  order by se.created_at, se.id
                )
                from public.signal_evidence se
                where se.signal_id = s.id
              ), '[]'::jsonb) as evidence,
              coalesce(r.published_at, s.created_at) as observed_at
            from public.signals s
            join public.raw_items r on r.id = s.raw_item_id
            left join public.raw_item_payloads payload
              on payload.raw_item_id = s.raw_item_id
            left join public.diseases d on d.id = s.disease_id
            left join public.pathogens p on p.id = s.pathogen_id
            where s.id = any(%s::uuid[])
              and s.is_current = true
              and s.event_matching_eligible = true
            """,
            (signal_ids,),
        )
        persisted_signals = []
        for row in cur.fetchall():
            signal = dict(row)
            for field in ("signal_id", "disease_id", "pathogen_id"):
                signal[field] = str(row[field]) if row.get(field) is not None else None
            signal["domains"] = _as_list(row.get("domains"))
            signal["occurred_start"] = _iso_date(row.get("occurred_start"))
            signal["observed_at"] = _iso_date(row.get("observed_at"))
            persisted_signals.append(signal)

        if {row["signal_id"] for row in persisted_signals} != cohort_signal_ids:
            return {
                "status": "blocked", "dry_run": True,
                "event_code": event_code,
                "reason": "incomplete_seed_signals",
            }

        persisted_relations = []
        persisted_anchors = set()
        for row in relation_rows:
            rationale = _as_mapping(row.get("rationale"))
            persisted_anchors.update(
                anchor.strip().casefold()
                for anchor in _as_list(rationale.get("shared_event_context_anchors"))
                if isinstance(anchor, str) and anchor.strip()
            )
            persisted_relations.append({
                "signal_relation_id": str(row["id"]),
                "source_signal_id": str(row["source_signal_id"]),
                "target_signal_id": str(row["target_signal_id"]),
                "matcher_result": {
                    **rationale,
                    "relation": row["relation"],
                    "hard_conflict": row["hard_conflict"],
                },
            })

        try:
            reconstructed_seed = build_event_creation_cohort_seed(
                signals=persisted_signals,
                relations=persisted_relations,
                strong_event_context_anchors=persisted_anchors,
            )
        except ValueError as exc:
            return {
                "status": "blocked", "dry_run": True,
                "event_code": event_code,
                "reason": "invalid_persisted_event_seed",
                "detail": str(exc),
            }

        unordered_fields = {
            "source_signal_ids", "source_relation_ids", "domains_present",
            "source_relations", "strong_event_context_anchors",
        }
        mismatched_fields = []
        for field, expected in reconstructed_seed.items():
            actual = event_seed.get(field)
            if field in unordered_fields and isinstance(actual, (list, tuple)):
                actual = sorted(actual) if all(isinstance(item, str) for item in actual) else actual
            if field not in event_seed or actual != expected:
                mismatched_fields.append(field)
        if mismatched_fields:
            return {
                "status": "blocked", "dry_run": True,
                "event_code": event_code,
                "reason": "event_seed_mismatch",
                "mismatched_fields": sorted(mismatched_fields),
            }

        from .event_context_v049 import resolve_signal_event_context_anchors

        # The resolver accepts direct summary anchors. Persistence requires
        # original-document support, so only located evidence is supplied.
        supported_anchors_by_signal = {}
        for signal in persisted_signals:
            raw_text = signal.get("raw_text")
            raw_text = raw_text if isinstance(raw_text, str) else ""
            located_evidence = [
                item for item in _as_list(signal.get("evidence"))
                if isinstance(item, Mapping)
                and isinstance(item.get("text"), str)
                and item["text"].strip()
                and item["text"] in raw_text
            ]
            supported_anchors_by_signal[signal["signal_id"]] = set(
                resolve_signal_event_context_anchors(
                    {"evidence": located_evidence}, raw_text,
                )
            )

        unsupported_context_relation_ids = []
        for relation in persisted_relations:
            declared_anchors = {
                anchor.strip().casefold()
                for anchor in _as_list(
                    relation["matcher_result"].get("shared_event_context_anchors")
                )
                if isinstance(anchor, str) and anchor.strip()
            }
            shared_supported = (
                supported_anchors_by_signal[relation["source_signal_id"]]
                & supported_anchors_by_signal[relation["target_signal_id"]]
            )
            if not declared_anchors.issubset(shared_supported):
                unsupported_context_relation_ids.append(relation["signal_relation_id"])

        if unsupported_context_relation_ids:
            return {
                "status": "blocked", "dry_run": True,
                "event_code": event_code,
                "reason": "unsupported_context_anchors",
                "invalid_relation_ids": sorted(unsupported_context_relation_ids),
            }

        from .event_matching_policy_v049 import apply_v049_auto_link_guard

        invalid_policy_ids = []
        for relation in persisted_relations:
            matcher = relation["matcher_result"]
            guarded = apply_v049_auto_link_guard(
                matcher,
                source_context_anchors=supported_anchors_by_signal[relation["source_signal_id"]],
                target_context_anchors=supported_anchors_by_signal[relation["target_signal_id"]],
            )
            if (
                guarded.get("decision") != "auto_linked"
                or guarded.get("auto_link_guard_override_reason")
                != matcher.get("auto_link_guard_override_reason")
            ):
                invalid_policy_ids.append(relation["signal_relation_id"])
        if invalid_policy_ids:
            return {
                "status": "blocked", "dry_run": True, "event_code": event_code,
                "reason": "invalid_matcher_policy",
                "invalid_relation_ids": sorted(invalid_policy_ids),
            }

        from .event_creation_cohort_v049 import build_event_creation_cohorts

        # Coverage alone is insufficient: disconnected groups must share a
        # supported strong anchor to constitute one event-creation cohort.
        # Reuse the planner's grouping after evidence has been validated.
        validated_cohorts = build_event_creation_cohorts(persisted_relations)
        if len(validated_cohorts) != 1:
            return {
                "status": "blocked", "dry_run": True,
                "event_code": event_code,
                "reason": "multiple_event_creation_cohorts",
                "cohort_count": len(validated_cohorts),
            }

        cur.execute(
            """
            select id, event_code, title, disease_id, pathogen_id,
              to_jsonb(domains_present) as domains_present,
              event_start_date, first_signal_at,
              lifecycle_status::text as lifecycle_status,
              priority::text as priority,
              evidence_confidence::text as evidence_confidence,
              cross_sector_convergence::text as cross_sector_convergence,
              contradictions_present, review_status::text as review_status,
              summary, reviewed_by, reviewed_at
            from public.events
            where event_code = %s
            """,
            (event_code,),
        )
        existing_event = cur.fetchone()
        existing_event_id = str(existing_event["id"]) if existing_event else None

        # Include every cohort signal's membership, even manual_unlinked.
        # Include all target-event members for the subsequent equivalence
        # check; the composite PK does not prevent cross-event membership.
        cur.execute(
            """
            select es.event_id, es.signal_id,
              es.match_decision::text as match_decision,
              es.linked_by, es.rationale, es.match_score,
              es.relation_to_event::text as relation_to_event,
              e.lifecycle_status::text as lifecycle_status
            from public.event_signals es
            join public.events e on e.id = es.event_id
            where es.signal_id = any(%s::uuid[])
               or es.event_id = %s::uuid
            """,
            (signal_ids, existing_event_id),
        )
        memberships = cur.fetchall()
        manual_memberships = [
            row for row in memberships
            if row.get("match_decision") in {"manual_linked", "manual_unlinked"}
            or row.get("linked_by") is not None
        ]
        if manual_memberships:
            return {
                "status": "blocked", "dry_run": True,
                "event_code": event_code,
                "reason": "manual_membership_conflict",
                "conflicting_signal_ids": sorted({str(row["signal_id"]) for row in manual_memberships}),
                "conflicting_event_ids": sorted({str(row["event_id"]) for row in manual_memberships}),
            }

        other_memberships = [
            row for row in memberships
            if str(row["event_id"]) != existing_event_id
        ]
        if other_memberships:
            return {
                "status": "blocked", "dry_run": True,
                "event_code": event_code,
                "reason": "other_event_membership_conflict",
                "conflicting_signal_ids": sorted({str(row["signal_id"]) for row in other_memberships}),
                "conflicting_event_ids": sorted({str(row["event_id"]) for row in other_memberships}),
            }

        if existing_event and existing_event.get("lifecycle_status") not in {"active", "monitoring"}:
            return {
                "status": "blocked", "dry_run": True,
                "event_code": event_code,
                "reason": "event_lifecycle_blocked",
                "event_id": existing_event_id,
                "lifecycle_status": existing_event.get("lifecycle_status"),
            }

        membership_rationale = {
            "producer": "oeti_event_creation",
            "event_code": reconstructed_seed["event_code"],
            "source_signal_ids": reconstructed_seed["source_signal_ids"],
            "source_relation_ids": reconstructed_seed["source_relation_ids"],
            "strong_event_context_anchors": reconstructed_seed["strong_event_context_anchors"],
            "matcher_version": reconstructed_seed["matcher_version"],
            "event_creation_version": reconstructed_seed["event_creation_version"],
            "source_relation_audit": [
                {
                    "signal_relation_id": relation["signal_relation_id"],
                    **{field: relation["matcher_result"].get(field) for field in (
                        "matcher_version", "policy_version", "context_resolver_version",
                    )},
                }
                for relation in sorted(persisted_relations, key=lambda row: row["signal_relation_id"])
            ],
        }
        planned_memberships = [
            {
                "signal_id": identifier,
                "relation_to_event": "supports", "match_score": None,
                "match_decision": "auto_linked", "linked_by": None,
                "rationale": membership_rationale,
            }
            for identifier in reconstructed_seed["source_signal_ids"]
        ]

        if existing_event:
            event_fields = (
                "event_code", "title", "disease_id", "pathogen_id",
                "domains_present", "event_start_date", "first_signal_at",
                "lifecycle_status", "priority", "evidence_confidence",
                "cross_sector_convergence", "contradictions_present", "review_status",
            )
            mismatched_event_fields = []
            for field in event_fields:
                actual = existing_event.get(field)
                expected = reconstructed_seed[field]
                if field in {"disease_id", "pathogen_id"}:
                    actual = str(actual) if actual is not None else None
                elif field == "domains_present":
                    actual = sorted(_as_list(actual))
                elif field in {"event_start_date", "first_signal_at"}:
                    actual = _iso_date(actual)
                    if field == "first_signal_at" and actual and expected:
                        from datetime import datetime
                        actual = datetime.fromisoformat(actual)
                        expected = datetime.fromisoformat(expected)
                if field not in existing_event or actual != expected:
                    mismatched_event_fields.append(field)
            for field in ("summary", "reviewed_by", "reviewed_at"):
                if field not in existing_event or existing_event[field] is not None:
                    mismatched_event_fields.append(field)
            if mismatched_event_fields:
                return {
                    "status": "blocked", "dry_run": True,
                    "event_code": event_code, "event_id": existing_event_id,
                    "reason": "existing_event_mismatch",
                    "mismatched_fields": sorted(mismatched_event_fields),
                }

            existing_by_signal = {str(row["signal_id"]): row for row in memberships}
            invalid_membership_ids = []
            for planned in planned_memberships:
                existing = existing_by_signal.get(planned["signal_id"])
                if existing is None or any(
                    field not in existing or (
                        _as_mapping(existing[field]) if field == "rationale" else existing[field]
                    ) != planned[field]
                    for field in ("relation_to_event", "match_score", "match_decision", "linked_by", "rationale")
                ):
                    invalid_membership_ids.append(planned["signal_id"])
            if set(existing_by_signal) != cohort_signal_ids or invalid_membership_ids:
                return {
                    "status": "blocked", "dry_run": True,
                    "event_code": event_code, "event_id": existing_event_id,
                    "reason": "existing_membership_mismatch",
                    "invalid_signal_ids": sorted(set(invalid_membership_ids) | (set(existing_by_signal) - cohort_signal_ids)),
                }

        return {
            "status": "already_exists" if existing_event else "ready_to_create",
            "dry_run": True, "event_code": event_code,
            "event_id": existing_event_id,
            "event_seed": reconstructed_seed,
            "memberships": planned_memberships,
        }

    def _insert_event_creation_cohort(self, cur, plan) -> dict[str, Any]:
        """Insert one validated event and every membership; caller owns rollback."""
        seed = plan["event_seed"]
        fields = (
            "event_code", "title", "disease_id", "pathogen_id", "domains_present",
            "event_start_date", "first_signal_at", "lifecycle_status", "priority",
            "evidence_confidence", "cross_sector_convergence", "contradictions_present",
            "review_status",
        )
        cur.execute(
            """
            insert into public.events (
              event_code, title, disease_id, pathogen_id, domains_present,
              event_start_date, first_signal_at, lifecycle_status, priority,
              evidence_confidence, cross_sector_convergence,
              contradictions_present, review_status
            ) values (
              %s, %s, %s::uuid, %s::uuid, %s::public.one_health_domain[],
              %s::date, %s::timestamptz, %s::public.event_lifecycle_status,
              %s::public.event_priority, %s::public.evidence_confidence,
              %s::public.cross_sector_convergence, %s, %s::public.review_status
            ) returning id
            """,
            tuple(seed[field] for field in fields),
        )
        event_id = str(cur.fetchone()["id"])
        for membership in plan["memberships"]:
            cur.execute(
                """
                insert into public.event_signals (
                  event_id, signal_id, relation_to_event, match_score,
                  match_decision, rationale
                ) values (
                  %s::uuid, %s::uuid, %s::public.relation_type, %s,
                  %s::public.match_decision, %s::jsonb
                )
                """,
                (event_id, membership["signal_id"], membership["relation_to_event"],
                 membership["match_score"], membership["match_decision"],
                 json.dumps(membership["rationale"], ensure_ascii=False)),
            )
        return {**plan, "status": "created", "event_id": event_id, "dry_run": False}

    def load_raw_text_for_signal(
        self,
        signal_id: str,
    ) -> str:
        """Load the source raw text associated with a persisted signal."""

        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select
                      payload.raw_text
                    from public.signals as signal
                    join public.raw_item_payloads as payload
                      on payload.raw_item_id = signal.raw_item_id
                    where signal.id = %s
                    limit 1
                    """,
                    (signal_id,),
                )

                row = cur.fetchone()

        if row is None:
            raise ValueError(
                f"Signal not found or raw payload unavailable: {signal_id}"
            )

        raw_text = row["raw_text"]

        if raw_text is None:
            return ""

        return str(raw_text)


    def load_signal_for_matching(
        self,
        signal_id: str,
    ) -> PersistedMatcherSignal:
        with (
            self.connection() as conn,
            conn.cursor() as cur,
        ):
            cur.execute(
                """
                select
                  s.id as signal_id,
                  s.local_signal_key,
                  s.schema_version,
                  s.signal_role::text as signal_role,
                  s.signal_type::text as signal_type,
                  s.signal_summary,
                  s.verification_status::text
                    as verification_status,
                  s.event_matching_eligible,
                  s.is_current,
                  to_jsonb(s.domains) as domains,
                  s.extraction_confidence,

                  s.disease_verbatim,
                  d.canonical_name
                    as disease_canonical_name,
                  s.disease_normalization_status::text
                    as disease_normalization_status,
                  s.disease_confidence,

                  s.pathogen_verbatim,
                  p.canonical_name
                    as pathogen_canonical_name,
                  s.pathogen_normalization_status::text
                    as pathogen_normalization_status,
                  s.pathogen_confidence,

                  s.occurred_start,
                  s.occurred_end,
                  s.date_precision,
                  s.reference_period,
                  s.transmission,

                  coalesce(
                    loc.locations,
                    '[]'::jsonb
                  ) as locations,

                  coalesce(
                    hst.hosts,
                    '[]'::jsonb
                  ) as hosts,

                  coalesce(
                    met.metrics,
                    '[]'::jsonb
                  ) as metrics,

                  coalesce(
                    ev.evidence,
                    '[]'::jsonb
                  ) as evidence,

                  coalesce(
                    diag.diagnostics,
                    '{}'::jsonb
                  ) as diagnostics,

                  coalesce(
                    gen.genomics,
                    '{}'::jsonb
                  ) as genomics

                from public.signals s

                left join public.diseases d
                  on d.id = s.disease_id

                left join public.pathogens p
                  on p.id = s.pathogen_id

                left join lateral (
                  select jsonb_agg(
                    jsonb_build_object(
                      'country_iso2',
                        l.country_iso2,
                      'country',
                        l.country_name,
                      'admin1',
                        l.admin1,
                      'admin2',
                        l.admin2,
                      'locality',
                        l.locality,
                      'region',
                        l.region_name,
                      'precision',
                        l.precision::text,
                      'role',
                        sl.location_role,
                      'confidence',
                        sl.confidence
                    )
                    order by
                      sl.location_role,
                      l.display_name
                  ) as locations
                  from public.signal_locations sl
                  join public.locations l
                    on l.id = sl.location_id
                  where sl.signal_id = s.id
                ) loc on true

                left join lateral (
                  select jsonb_agg(
                    jsonb_build_object(
                      'verbatim',
                        h.common_name,
                      'canonical_name',
                        coalesce(
                          h.scientific_name,
                          h.common_name
                        ),
                      'host_type',
                        h.host_type::text,
                      'confidence',
                        sh.confidence
                    )
                    order by
                      h.host_type,
                      h.common_name
                  ) as hosts
                  from public.signal_hosts sh
                  join public.hosts h
                    on h.id = sh.host_id
                  where sh.signal_id = s.id
                ) hst on true

                left join lateral (
                  select jsonb_agg(
                    jsonb_build_object(
                      'name',
                        sm.metric_name,
                      'value_numeric',
                        sm.value_numeric,
                      'value_text',
                        sm.value_text,
                      'unit',
                        sm.unit,
                      'as_of_date',
                        sm.as_of_date,
                      'as_of_year',
                        sm.metadata -> 'as_of_year',
                      'as_of_month',
                        sm.metadata -> 'as_of_month',
                      'as_of_precision',
                        sm.metadata -> 'as_of_precision',
                      'as_of_verbatim',
                        sm.metadata -> 'as_of_verbatim'
                    )
                    order by
                      sm.created_at,
                      sm.id
                  ) as metrics
                  from public.signal_metrics sm
                  where sm.signal_id = s.id
                ) met on true

                left join lateral (
                  select jsonb_agg(
                    jsonb_build_object(
                      'type',
                        se.evidence_type,
                      'text',
                        se.excerpt,
                      'location_in_document',
                        se.document_locator,
                      'page_number',
                        se.page_number
                    )
                    order by
                      se.created_at,
                      se.id
                  ) as evidence
                  from public.signal_evidence se
                  where se.signal_id = s.id
                ) ev on true

                left join lateral (
                  select jsonb_build_object(
                    'test_reported',
                      observation.test_reported,
                    'test_type',
                      observation.test_type,
                    'method',
                      observation.test_method,
                    'target',
                      observation.target,
                    'specimen',
                      observation.specimen,
                    'result',
                      observation.test_result::text
                  ) as diagnostics
                  from public.diagnostic_observations
                    observation
                  where observation.signal_id = s.id
                  order by
                    observation.created_at desc,
                    observation.id desc
                  limit 1
                ) diag on true

                left join lateral (
                  select jsonb_build_object(
                    'sequence_reported',
                      observation.sequence_reported,
                    'accession',
                      observation.accession,
                    'lineage',
                      observation.lineage,
                    'clade',
                      observation.clade,
                    'test_result',
                      observation.test_result::text
                  ) as genomics
                  from public.genomic_observations
                    observation
                  where observation.signal_id = s.id
                  order by
                    observation.created_at desc,
                    observation.id desc
                  limit 1
                ) gen on true

                where s.id = %s
                  and s.is_current = true

                limit 1
                """,
                (
                    signal_id,
                ),
            )

            row = cur.fetchone()

            if not row:
                raise ValueError(
                    "No existe una seÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±al actual "
                    f"con id={signal_id!r}."
                )

            return PersistedMatcherSignal(
                signal_id=str(
                    row["signal_id"]
                ),
                payload=(
                    build_matcher_signal_payload(
                        row
                    )
                ),
            )


    def load_candidate_signal_refs(
        self,
        anchor_signal_id: str,
        *,
        max_candidates: int = 250,
    ) -> list[CandidateSignalRef]:
        """Return current eligible matcher candidates in deterministic order.

        Candidate generation is intentionally high-recall. Disease, pathogen
        and temporality rank candidates but do not exclude them.
        """

        if (
            not isinstance(max_candidates, int)
            or isinstance(max_candidates, bool)
            or max_candidates < 1
            or max_candidates > 5000
        ):
            raise ValueError(
                "max_candidates debe ser un entero entre 1 y 5000."
            )

        with (
            self.connection() as conn,
            conn.cursor() as cur,
        ):
            cur.execute(
                """
                select
                  id,
                  disease_id,
                  pathogen_id,
                  occurred_start,
                  occurred_end
                from public.signals
                where id = %s
                  and is_current = true
                  and event_matching_eligible = true
                limit 1
                """,
                (
                    anchor_signal_id,
                ),
            )

            anchor = cur.fetchone()

            if not anchor:
                raise ValueError(
                    "No existe una seÃƒÆ’Ã‚Â±al actual y elegible "
                    f"con id={anchor_signal_id!r}."
                )

            cur.execute(
                """
                with anchor as (
                  select
                    %s::uuid as signal_id,
                    %s::uuid as disease_id,
                    %s::uuid as pathogen_id,
                    %s::date as occurred_start,
                    %s::date as occurred_end
                )
                select
                  candidate.id as signal_id,

                  (
                    anchor.pathogen_id is not null
                    and candidate.pathogen_id
                      = anchor.pathogen_id
                  ) as same_pathogen,

                  (
                    anchor.disease_id is not null
                    and candidate.disease_id
                      = anchor.disease_id
                  ) as same_disease,

                  case
                    when anchor.occurred_start
                           is not null
                     and candidate.occurred_start
                           is not null
                    then abs(
                      candidate.occurred_start
                      - anchor.occurred_start
                    )
                    else null
                  end as temporal_distance_days

                from public.signals candidate
                cross join anchor

                where candidate.is_current = true
                  and candidate.event_matching_eligible = true
                  and candidate.id <> anchor.signal_id

                order by
                  same_pathogen desc,
                  same_disease desc,
                  temporal_distance_days asc nulls last,
                  candidate.created_at desc,
                  candidate.id asc

                limit %s
                """,
                (
                    anchor["id"],
                    anchor["disease_id"],
                    anchor["pathogen_id"],
                    anchor["occurred_start"],
                    anchor["occurred_end"],
                    max_candidates,
                ),
            )

            rows = cur.fetchall()

        return [
            CandidateSignalRef(
                signal_id=str(
                    row["signal_id"]
                ),
                same_disease=bool(
                    row["same_disease"]
                ),
                same_pathogen=bool(
                    row["same_pathogen"]
                ),
                temporal_distance_days=(
                    int(
                        row[
                            "temporal_distance_days"
                        ]
                    )
                    if row[
                        "temporal_distance_days"
                    ]
                    is not None
                    else None
                ),
            )
            for row in rows
        ]


    def persist_matcher_relation(
        self,
        *,
        source_signal_id: str,
        target_signal_id: str,
        matcher_result: Mapping[str, Any],
        matcher_version: str = "0.4.8",
        candidate_prefilter: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persist one canonical automatic matcher relation idempotently.

        Only eligible matcher results are persisted. One matcher-managed row
        is maintained per canonical signal pair. Rows from other producers
        are never silently overwritten.
        """

        (
            canonical_source_id,
            canonical_target_id,
        ) = canonical_signal_pair(
            source_signal_id,
            target_signal_id,
        )

        if matcher_result.get("gate") != "eligible":
            raise ValueError(
                "SÃƒÂ³lo pueden persistirse resultados "
                "elegibles del Event Matcher."
            )

        relation = matcher_result.get(
            "relation"
        )

        allowed_relations = {
            "supports",
            "duplicates",
            "refines",
            "contradicts",
            "possibly_related",
            "unrelated",
            "unknown",
        }

        if relation not in allowed_relations:
            raise ValueError(
                "RelaciÃƒÂ³n del Event Matcher invÃƒÂ¡lida: "
                f"{relation!r}."
            )

        decision = matcher_result.get(
            "decision"
        )

        if decision not in {
            "auto_linked",
            "review_required",
            "rejected",
        }:
            raise ValueError(
                "DecisiÃƒÂ³n automÃƒÂ¡tica invÃƒÂ¡lida: "
                f"{decision!r}."
            )

        raw_score = matcher_result.get(
            "score"
        )

        score = _optional_float(
            raw_score
        )

        if (
            score is not None
            and not 0.0 <= score <= 1.0
        ):
            raise ValueError(
                "El score debe estar entre 0 y 1."
            )

        producer = (
            "oeti_event_matcher"
        )

        rationale = {
            "producer": producer,
            "matcher_version": (
                matcher_version
            ),
            "gate": matcher_result.get(
                "gate"
            ),
            "decision": decision,
            "merge_allowed": (
                matcher_result.get(
                    "merge_allowed"
                )
            ),
            "hard_conflict_reason": (
                matcher_result.get(
                    "hard_conflict_reason"
                )
            ),
            "information_coverage": (
                matcher_result.get(
                    "information_coverage"
                )
            ),
            "component_scores": (
                matcher_result.get(
                    "component_scores"
                )
                or {}
            ),
            "raw_score": score,
            "base_decision": (
                matcher_result.get(
                    "base_decision"
                )
            ),
            "policy_version": (
                matcher_result.get(
                    "policy_version"
                )
            ),
            "context_resolver_version": (
                matcher_result.get(
                    "context_resolver_version"
                )
            ),
            "auto_link_guard_reason": (
                matcher_result.get(
                    "auto_link_guard_reason"
                )
            ),
            "auto_link_guard_override_reason": (
                matcher_result.get(
                    "auto_link_guard_override_reason"
                )
            ),
            "shared_event_context_anchors": (
                matcher_result.get(
                    "shared_event_context_anchors"
                )
                or []
            ),
            "source_event_context_anchors": (
                matcher_result.get(
                    "source_event_context_anchors"
                )
                or []
            ),
            "target_event_context_anchors": (
                matcher_result.get(
                    "target_event_context_anchors"
                )
                or []
            ),
            "candidate_prefilter": (
                dict(
                    candidate_prefilter
                    or {}
                )
            ),
        }

        with (
            self.connection() as conn,
            conn.cursor() as cur,
        ):
            # Do not overwrite a relation owned by another producer.
            cur.execute(
                """
                select id
                from public.signal_relations
                where source_signal_id = %s
                  and target_signal_id = %s
                  and relation =
                    %s::public.relation_type
                  and coalesce(
                    rationale ->> 'producer',
                    ''
                  ) <> %s
                limit 1
                for update
                """,
                (
                    canonical_source_id,
                    canonical_target_id,
                    relation,
                    producer,
                ),
            )

            foreign_relation = (
                cur.fetchone()
            )

            if foreign_relation:
                raise ValueError(
                    "Existe una relaciÃƒÂ³n del mismo "
                    "tipo para este par perteneciente "
                    "a otro productor; no se "
                    "sobrescribirÃƒÂ¡ automÃƒÂ¡ticamente."
                )

            # Locate any previous matcher-managed relation for the pair,
            # even when the relation classification has changed.
            cur.execute(
                """
                select
                  id,
                  relation::text as relation
                from public.signal_relations
                where source_signal_id = %s
                  and target_signal_id = %s
                  and rationale ->> 'producer'
                    = %s
                order by created_at asc, id asc
                for update
                """,
                (
                    canonical_source_id,
                    canonical_target_id,
                    producer,
                ),
            )

            existing = cur.fetchall()

            rationale_json = json.dumps(
                rationale,
                ensure_ascii=False,
            )

            hard_conflict = bool(
                matcher_result.get(
                    "hard_conflict"
                )
            )

            if existing:
                relation_id = str(
                    existing[0]["id"]
                )

                # Defensive cleanup in case an older implementation
                # produced more than one matcher row for the pair.
                cur.execute(
                    """
                    delete from public.signal_relations
                    where source_signal_id = %s
                      and target_signal_id = %s
                      and rationale ->> 'producer'
                        = %s
                      and id <> %s
                    """,
                    (
                        canonical_source_id,
                        canonical_target_id,
                        producer,
                        relation_id,
                    ),
                )

                cur.execute(
                    """
                    update public.signal_relations
                    set
                      relation =
                        %s::public.relation_type,
                      score = %s,
                      hard_conflict = %s,
                      rationale = %s::jsonb
                    where id = %s
                    returning id
                    """,
                    (
                        relation,
                        score,
                        hard_conflict,
                        rationale_json,
                        relation_id,
                    ),
                )

                persisted_id = str(
                    cur.fetchone()["id"]
                )

                action = "updated"

            else:
                cur.execute(
                    """
                    insert into public.signal_relations (
                      source_signal_id,
                      target_signal_id,
                      relation,
                      score,
                      hard_conflict,
                      rationale
                    ) values (
                      %s,
                      %s,
                      %s::public.relation_type,
                      %s,
                      %s,
                      %s::jsonb
                    )
                    returning id
                    """,
                    (
                        canonical_source_id,
                        canonical_target_id,
                        relation,
                        score,
                        hard_conflict,
                        rationale_json,
                    ),
                )

                persisted_id = str(
                    cur.fetchone()["id"]
                )

                action = "inserted"

            conn.commit()

        return {
            "signal_relation_id": (
                persisted_id
            ),
            "source_signal_id": (
                canonical_source_id
            ),
            "target_signal_id": (
                canonical_target_id
            ),
            "relation": relation,
            "score": score,
            "hard_conflict": (
                hard_conflict
            ),
            "decision": decision,
            "action": action,
            "matcher_version": (
                matcher_version
            ),
        }


    def persist_matcher_relations_batch(
        self,
        items: list[Mapping[str, Any]],
        *,
        matcher_version: str = "0.4.8",
    ) -> list[dict[str, Any]]:
        """Persist a complete matcher run atomically.

        All items are validated before opening the transaction. Canonical
        pairs are sorted to keep advisory-lock acquisition deterministic.
        Either the full batch commits or none of it does.
        """

        prepared: list[
            dict[str, Any]
        ] = []

        seen_pairs: set[
            tuple[str, str]
        ] = set()

        allowed_relations = {
            "supports",
            "duplicates",
            "refines",
            "contradicts",
            "possibly_related",
            "unrelated",
            "unknown",
        }

        allowed_decisions = {
            "auto_linked",
            "review_required",
            "rejected",
        }

        producer = (
            "oeti_event_matcher"
        )

        for item in items:
            matcher_result = item.get(
                "matcher_result"
            )

            if not isinstance(
                matcher_result,
                Mapping,
            ):
                raise ValueError(
                    "Cada item debe contener "
                    "matcher_result."
                )

            (
                source_signal_id,
                target_signal_id,
            ) = canonical_signal_pair(
                str(
                    item[
                        "source_signal_id"
                    ]
                ),
                str(
                    item[
                        "target_signal_id"
                    ]
                ),
            )

            pair = (
                source_signal_id,
                target_signal_id,
            )

            if pair in seen_pairs:
                raise ValueError(
                    "El batch contiene el mismo "
                    "par canónico más de una vez: "
                    f"{source_signal_id} / "
                    f"{target_signal_id}."
                )

            seen_pairs.add(
                pair
            )

            if (
                matcher_result.get("gate")
                != "eligible"
            ):
                raise ValueError(
                    "SÃ³lo pueden persistirse "
                    "resultados elegibles del "
                    "Event Matcher."
                )

            relation = (
                matcher_result.get(
                    "relation"
                )
            )

            if (
                relation
                not in allowed_relations
            ):
                raise ValueError(
                    "RelaciÃ³n del Event Matcher "
                    f"invÃ¡lida: {relation!r}."
                )

            decision = (
                matcher_result.get(
                    "decision"
                )
            )

            if (
                decision
                not in allowed_decisions
            ):
                raise ValueError(
                    "DecisiÃ³n automÃ¡tica "
                    f"invÃ¡lida: {decision!r}."
                )

            score = _optional_float(
                matcher_result.get(
                    "score"
                )
            )

            if (
                score is not None
                and not 0.0
                <= score
                <= 1.0
            ):
                raise ValueError(
                    "El score debe estar "
                    "entre 0 y 1."
                )

            rationale = {
                "producer": producer,
                "matcher_version": (
                    matcher_version
                ),
                "gate": (
                    matcher_result.get(
                        "gate"
                    )
                ),
                "decision": decision,
                "merge_allowed": (
                    matcher_result.get(
                        "merge_allowed"
                    )
                ),
                "hard_conflict_reason": (
                    matcher_result.get(
                        "hard_conflict_reason"
                    )
                ),
                "information_coverage": (
                    matcher_result.get(
                        "information_coverage"
                    )
                ),
                "component_scores": (
                    matcher_result.get(
                        "component_scores"
                    )
                    or {}
                ),
                "raw_score": score,
                "base_decision": (
                    matcher_result.get(
                        "base_decision"
                    )
                ),
                "policy_version": (
                    matcher_result.get(
                        "policy_version"
                    )
                ),
                "context_resolver_version": (
                    matcher_result.get(
                        "context_resolver_version"
                    )
                ),
                "auto_link_guard_reason": (
                    matcher_result.get(
                        "auto_link_guard_reason"
                    )
                ),
                "auto_link_guard_override_reason": (
                    matcher_result.get(
                        "auto_link_guard_override_reason"
                    )
                ),
                "shared_event_context_anchors": (
                    matcher_result.get(
                        "shared_event_context_anchors"
                    )
                    or []
                ),
                "source_event_context_anchors": (
                    matcher_result.get(
                        "source_event_context_anchors"
                    )
                    or []
                ),
                "target_event_context_anchors": (
                    matcher_result.get(
                        "target_event_context_anchors"
                    )
                    or []
                ),
                "candidate_prefilter": (
                    dict(
                        item.get(
                            "candidate_prefilter"
                        )
                        or {}
                    )
                ),
            }

            prepared.append(
                {
                    "source_signal_id": (
                        source_signal_id
                    ),
                    "target_signal_id": (
                        target_signal_id
                    ),
                    "relation": relation,
                    "decision": decision,
                    "score": score,
                    "hard_conflict": bool(
                        matcher_result.get(
                            "hard_conflict"
                        )
                    ),
                    "rationale": rationale,
                }
            )

        if not prepared:
            return []

        prepared.sort(
            key=lambda item: (
                item[
                    "source_signal_id"
                ],
                item[
                    "target_signal_id"
                ],
            )
        )

        persisted: list[
            dict[str, Any]
        ] = []

        with (
            self.connection() as conn,
            conn.cursor() as cur,
        ):
            for item in prepared:
                source_signal_id = item[
                    "source_signal_id"
                ]

                target_signal_id = item[
                    "target_signal_id"
                ]

                relation = item[
                    "relation"
                ]

                pair_lock_key = (
                    f"{source_signal_id}:"
                    f"{target_signal_id}"
                )

                # Serialize concurrent writes for the same canonical pair.
                cur.execute(
                    """
                    select pg_advisory_xact_lock(
                      hashtextextended(%s, 0)
                    )
                    """,
                    (
                        pair_lock_key,
                    ),
                )

                # Never overwrite a row belonging to another producer.
                cur.execute(
                    """
                    select id
                    from public.signal_relations
                    where source_signal_id = %s
                      and target_signal_id = %s
                      and relation =
                        %s::public.relation_type
                      and coalesce(
                        rationale ->> 'producer',
                        ''
                      ) <> %s
                    limit 1
                    for update
                    """,
                    (
                        source_signal_id,
                        target_signal_id,
                        relation,
                        producer,
                    ),
                )

                foreign_relation = (
                    cur.fetchone()
                )

                if foreign_relation:
                    raise ValueError(
                        "Existe una relaciÃ³n del "
                        "mismo tipo para este par "
                        "perteneciente a otro "
                        "productor; el batch fue "
                        "abortado."
                    )

                cur.execute(
                    """
                    select
                      id,
                      relation::text as relation
                    from public.signal_relations
                    where source_signal_id = %s
                      and target_signal_id = %s
                      and rationale ->> 'producer'
                        = %s
                    order by created_at asc, id asc
                    for update
                    """,
                    (
                        source_signal_id,
                        target_signal_id,
                        producer,
                    ),
                )

                existing = (
                    cur.fetchall()
                )

                rationale_json = (
                    json.dumps(
                        item["rationale"],
                        ensure_ascii=False,
                    )
                )

                if existing:
                    relation_id = str(
                        existing[0]["id"]
                    )

                    cur.execute(
                        """
                        delete from public.signal_relations
                        where source_signal_id = %s
                          and target_signal_id = %s
                          and rationale ->> 'producer'
                            = %s
                          and id <> %s
                        """,
                        (
                            source_signal_id,
                            target_signal_id,
                            producer,
                            relation_id,
                        ),
                    )

                    cur.execute(
                        """
                        update public.signal_relations
                        set
                          relation =
                            %s::public.relation_type,
                          score = %s,
                          hard_conflict = %s,
                          rationale = %s::jsonb
                        where id = %s
                        returning id
                        """,
                        (
                            relation,
                            item["score"],
                            item[
                                "hard_conflict"
                            ],
                            rationale_json,
                            relation_id,
                        ),
                    )

                    persisted_id = str(
                        cur.fetchone()["id"]
                    )

                    action = "updated"

                else:
                    cur.execute(
                        """
                        insert into public.signal_relations (
                          source_signal_id,
                          target_signal_id,
                          relation,
                          score,
                          hard_conflict,
                          rationale
                        ) values (
                          %s,
                          %s,
                          %s::public.relation_type,
                          %s,
                          %s,
                          %s::jsonb
                        )
                        returning id
                        """,
                        (
                            source_signal_id,
                            target_signal_id,
                            relation,
                            item["score"],
                            item[
                                "hard_conflict"
                            ],
                            rationale_json,
                        ),
                    )

                    persisted_id = str(
                        cur.fetchone()["id"]
                    )

                    action = "inserted"

                persisted.append(
                    {
                        "signal_relation_id": (
                            persisted_id
                        ),
                        "source_signal_id": (
                            source_signal_id
                        ),
                        "target_signal_id": (
                            target_signal_id
                        ),
                        "relation": relation,
                        "score": (
                            item["score"]
                        ),
                        "hard_conflict": (
                            item[
                                "hard_conflict"
                            ]
                        ),
                        "decision": (
                            item["decision"]
                        ),
                        "action": action,
                        "matcher_version": (
                            matcher_version
                        ),
                    }
                )

            conn.commit()

        return persisted


    def load_persisted_matcher_relations_for_signal(
        self,
        signal_id: str,
    ) -> list[dict[str, Any]]:
        """Load matcher-managed persisted relations for one signal."""

        producer = "oeti_event_matcher"

        with (
            self.connection() as conn,
            conn.cursor() as cur,
        ):
            cur.execute(
                """
                select
                  id,
                  source_signal_id,
                  target_signal_id,
                  relation::text as relation,
                  score,
                  hard_conflict,
                  rationale
                from public.signal_relations
                where (
                    source_signal_id = %s
                    or target_signal_id = %s
                )
                  and rationale ->> 'producer' = %s
                order by
                  source_signal_id,
                  target_signal_id,
                  id
                """,
                (
                    signal_id,
                    signal_id,
                    producer,
                ),
            )

            rows = cur.fetchall()

        results: list[dict[str, Any]] = []

        for row in rows:
            rationale = _as_mapping(
                row.get("rationale")
            )

            results.append(
                {
                    "signal_relation_id": str(
                        row["id"]
                    ),
                    "source_signal_id": str(
                        row["source_signal_id"]
                    ),
                    "target_signal_id": str(
                        row["target_signal_id"]
                    ),
                    "candidate_prefilter": (
                        _as_mapping(
                            rationale.get(
                                "candidate_prefilter"
                            )
                        )
                    ),
                    "matcher_result": {
                        "gate": rationale.get(
                            "gate"
                        ),
                        "relation": row[
                            "relation"
                        ],
                        "decision": rationale.get(
                            "decision"
                        ),
                        "merge_allowed": (
                            rationale.get(
                                "merge_allowed"
                            )
                            is True
                        ),
                        "hard_conflict": bool(
                            row[
                                "hard_conflict"
                            ]
                        ),
                        "hard_conflict_reason": (
                            rationale.get(
                                "hard_conflict_reason"
                            )
                        ),
                        "score": _optional_float(
                            row.get("score")
                        ),
                        "information_coverage": (
                            rationale.get(
                                "information_coverage"
                            )
                        ),
                        "component_scores": (
                            _as_mapping(
                                rationale.get(
                                    "component_scores"
                                )
                            )
                        ),
                    },
                    "matcher_version": (
                        rationale.get(
                            "matcher_version"
                        )
                    ),
                }
            )

        return results


    def load_event_memberships_for_signal(
        self,
        signal_id: str,
    ) -> list[dict[str, Any]]:
        """Read current persisted event memberships for one signal."""

        with (
            self.connection() as conn,
            conn.cursor() as cur,
        ):
            cur.execute(
                """
                select
                  es.event_id,
                  e.event_code,
                  e.lifecycle_status::text
                    as lifecycle_status,
                  es.relation_to_event::text
                    as relation_to_event,
                  es.match_score,
                  es.match_decision::text
                    as match_decision,
                  es.linked_at
                from public.event_signals es
                join public.events e
                  on e.id = es.event_id
                where es.signal_id = %s
                order by es.event_id
                """,
                (
                    signal_id,
                ),
            )

            rows = cur.fetchall()

        return [
            {
                "event_id": str(
                    row["event_id"]
                ),
                "event_code": (
                    row["event_code"]
                ),
                "lifecycle_status": (
                    row[
                        "lifecycle_status"
                    ]
                ),
                "relation_to_event": (
                    row[
                        "relation_to_event"
                    ]
                ),
                "match_score": (
                    _optional_float(
                        row.get(
                            "match_score"
                        )
                    )
                ),
                "match_decision": (
                    row[
                        "match_decision"
                    ]
                ),
                "linked_at": (
                    row["linked_at"]
                ),
            }
            for row in rows
        ]


    def persist_event_signal_attachment(
        self,
        *,
        assignment_plan: Mapping[str, Any],
        signal_relation_id: str,
    ) -> dict[str, Any]:
        """Attach one signal to an existing open event.

        The persisted signal relation is the source of truth. Event creation
        is intentionally out of scope for this method.
        """

        action = assignment_plan.get(
            "action"
        )

        if action not in {
            "attach_source_to_event",
            "attach_target_to_event",
        }:
            raise ValueError(
                "Only existing-event attachment "
                "plans can be persisted."
            )

        if (
            assignment_plan.get(
                "write_allowed"
            )
            is not True
        ):
            raise ValueError(
                "Assignment plan does not "
                "allow writes."
            )

        event_id = assignment_plan.get(
            "event_id"
        )

        if not event_id:
            raise ValueError(
                "Attachment plan requires event_id."
            )

        signal_ids = _as_list(
            assignment_plan.get(
                "signal_ids"
            )
        )

        if len(signal_ids) != 1:
            raise ValueError(
                "Attachment plan must contain "
                "exactly one signal."
            )

        signal_id = str(
            signal_ids[0]
        )

        producer = "oeti_event_matcher"

        with (
            self.connection() as conn,
            conn.cursor() as cur,
        ):
            # Recheck lifecycle inside the write transaction.
            cur.execute(
                """
                select
                  id,
                  lifecycle_status::text
                    as lifecycle_status
                from public.events
                where id = %s
                for update
                """,
                (
                    event_id,
                ),
            )

            event = cur.fetchone()

            if not event:
                raise ValueError(
                    "Target event does not exist."
                )

            lifecycle_status = event[
                "lifecycle_status"
            ]

            if lifecycle_status not in {
                "active",
                "monitoring",
            }:
                raise ValueError(
                    "Target event is not open: "
                    f"{lifecycle_status}."
                )

            # Prevent linking a signal that became stale between planning
            # and persistence.
            cur.execute(
                """
                select id
                from public.signals
                where id = %s
                  and is_current = true
                  and event_matching_eligible = true
                for update
                """,
                (
                    signal_id,
                ),
            )

            if not cur.fetchone():
                raise ValueError(
                    "Signal is no longer current "
                    "and eligible."
                )

            # The persisted matcher relation, not caller input, determines
            # whether automatic event attachment is still authorized.
            cur.execute(
                """
                select
                  id,
                  source_signal_id,
                  target_signal_id,
                  relation::text as relation,
                  score,
                  hard_conflict,
                  rationale
                from public.signal_relations
                where id = %s
                  and rationale ->> 'producer'
                    = %s
                for update
                """,
                (
                    signal_relation_id,
                    producer,
                ),
            )

            relation_row = cur.fetchone()

            if not relation_row:
                raise ValueError(
                    "Matcher relation does not exist "
                    "or is not matcher-managed."
                )

            endpoints = {
                str(
                    relation_row[
                        "source_signal_id"
                    ]
                ),
                str(
                    relation_row[
                        "target_signal_id"
                    ]
                ),
            }

            if signal_id not in endpoints:
                raise ValueError(
                    "Signal is not an endpoint of "
                    "the matcher relation."
                )

            relation_rationale = (
                _as_mapping(
                    relation_row.get(
                        "rationale"
                    )
                )
            )

            relation = relation_row[
                "relation"
            ]

            decision = (
                relation_rationale.get(
                    "decision"
                )
            )

            merge_allowed = (
                relation_rationale.get(
                    "merge_allowed"
                )
                is True
            )

            hard_conflict = bool(
                relation_row[
                    "hard_conflict"
                ]
            )

            if (
                decision != "auto_linked"
                or not merge_allowed
                or hard_conflict
            ):
                raise ValueError(
                    "Persisted matcher relation "
                    "does not authorize automatic "
                    "event attachment."
                )

            if relation not in {
                "duplicates",
                "refines",
            }:
                raise ValueError(
                    "Persisted matcher relation "
                    "has an invalid auto-link "
                    f"relation: {relation!r}."
                )

            score = _optional_float(
                relation_row.get(
                    "score"
                )
            )

            event_rationale = {
                "producer": producer,
                "matcher_version": (
                    relation_rationale.get(
                        "matcher_version"
                    )
                ),
                "source_signal_relation_id": (
                    str(
                        relation_row[
                            "id"
                        ]
                    )
                ),
                "assignment_action": action,
                "assignment_reason": (
                    assignment_plan.get(
                        "reason"
                    )
                ),
                "pair_relation": relation,
                "pair_decision": decision,
                "merge_allowed": True,
                "raw_score": (
                    relation_rationale.get(
                        "raw_score"
                    )
                ),
            }

            event_rationale_json = (
                json.dumps(
                    event_rationale,
                    ensure_ascii=False,
                )
            )

            cur.execute(
                """
                select
                  relation_to_event::text
                    as relation_to_event,
                  match_decision::text
                    as match_decision,
                  rationale,
                  linked_at
                from public.event_signals
                where event_id = %s
                  and signal_id = %s
                for update
                """,
                (
                    event_id,
                    signal_id,
                ),
            )

            existing = cur.fetchone()

            if existing:
                existing_decision = (
                    existing[
                        "match_decision"
                    ]
                )

                existing_rationale = (
                    _as_mapping(
                        existing.get(
                            "rationale"
                        )
                    )
                )

                if existing_decision in {
                    "manual_linked",
                    "manual_unlinked",
                }:
                    raise ValueError(
                        "Manual event membership "
                        "blocks automatic overwrite."
                    )

                if (
                    existing_rationale.get(
                        "producer"
                    )
                    != producer
                ):
                    raise ValueError(
                        "Existing event membership "
                        "belongs to another producer."
                    )

                cur.execute(
                    """
                    update public.event_signals
                    set
                      relation_to_event =
                        %s::public.relation_type,
                      match_score = %s,
                      match_decision =
                        'auto_linked'::public.match_decision,
                      rationale = %s::jsonb
                    where event_id = %s
                      and signal_id = %s
                    returning linked_at
                    """,
                    (
                        relation,
                        score,
                        event_rationale_json,
                        event_id,
                        signal_id,
                    ),
                )

                persisted = cur.fetchone()
                persistence_action = "updated"

            else:
                cur.execute(
                    """
                    insert into public.event_signals (
                      event_id,
                      signal_id,
                      relation_to_event,
                      match_score,
                      match_decision,
                      rationale
                    ) values (
                      %s,
                      %s,
                      %s::public.relation_type,
                      %s,
                      'auto_linked'::public.match_decision,
                      %s::jsonb
                    )
                    returning linked_at
                    """,
                    (
                        event_id,
                        signal_id,
                        relation,
                        score,
                        event_rationale_json,
                    ),
                )

                persisted = cur.fetchone()
                persistence_action = "inserted"

            conn.commit()

        return {
            "event_id": str(
                event_id
            ),
            "signal_id": signal_id,
            "signal_relation_id": str(
                signal_relation_id
            ),
            "relation_to_event": relation,
            "match_score": score,
            "match_decision": "auto_linked",
            "lifecycle_status": (
                lifecycle_status
            ),
            "action": (
                persistence_action
            ),
            "linked_at": (
                persisted.get(
                    "linked_at"
                )
                if persisted
                else None
            ),
        }


    def persist_event_signal_attachments_batch(
        self,
        items: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Persist existing-event attachments atomically.

        Event creation is intentionally out of scope. Every attachment is
        revalidated inside the same database transaction. Either the complete
        batch commits or none of it does.
        """

        producer = "oeti_event_matcher"

        prepared: list[
            dict[str, Any]
        ] = []

        seen_memberships: set[
            tuple[str, str]
        ] = set()

        for item in items:
            if not isinstance(
                item,
                Mapping,
            ):
                raise ValueError(
                    "Every batch item must be a mapping."
                )

            assignment_plan = item.get(
                "assignment_plan"
            )

            if not isinstance(
                assignment_plan,
                Mapping,
            ):
                raise ValueError(
                    "Every batch item requires assignment_plan."
                )

            action = assignment_plan.get(
                "action"
            )

            if action not in {
                "attach_source_to_event",
                "attach_target_to_event",
            }:
                raise ValueError(
                    "Batch persistence only supports "
                    "existing-event attachments."
                )

            if (
                assignment_plan.get(
                    "write_allowed"
                )
                is not True
            ):
                raise ValueError(
                    "Attachment plan does not allow writes."
                )

            event_id = assignment_plan.get(
                "event_id"
            )

            if not event_id:
                raise ValueError(
                    "Attachment plan requires event_id."
                )

            signal_ids = _as_list(
                assignment_plan.get(
                    "signal_ids"
                )
            )

            if len(signal_ids) != 1:
                raise ValueError(
                    "Attachment plan must contain "
                    "exactly one signal."
                )

            signal_id = str(
                signal_ids[0]
            )

            signal_relation_id = item.get(
                "signal_relation_id"
            )

            if not signal_relation_id:
                raise ValueError(
                    "Batch item requires signal_relation_id."
                )

            membership_key = (
                str(event_id),
                signal_id,
            )

            if (
                membership_key
                in seen_memberships
            ):
                raise ValueError(
                    "Batch contains duplicate "
                    "event/signal membership."
                )

            seen_memberships.add(
                membership_key
            )

            prepared.append(
                {
                    "event_id": str(
                        event_id
                    ),
                    "signal_id": signal_id,
                    "signal_relation_id": str(
                        signal_relation_id
                    ),
                    "action": action,
                    "reason": (
                        assignment_plan.get(
                            "reason"
                        )
                    ),
                }
            )

        if not prepared:
            return []

        prepared.sort(
            key=lambda item: (
                item["event_id"],
                item["signal_id"],
                item[
                    "signal_relation_id"
                ],
            )
        )

        persisted: list[
            dict[str, Any]
        ] = []

        with (
            self.connection() as conn,
            conn.cursor() as cur,
        ):
            for item in prepared:
                event_id = item[
                    "event_id"
                ]
                signal_id = item[
                    "signal_id"
                ]
                signal_relation_id = item[
                    "signal_relation_id"
                ]

                membership_lock_key = (
                    f"{event_id}:{signal_id}"
                )

                cur.execute(
                    """
                    select pg_advisory_xact_lock(
                      hashtextextended(%s, 0)
                    )
                    """,
                    (
                        membership_lock_key,
                    ),
                )

                cur.execute(
                    """
                    select
                      id,
                      lifecycle_status::text
                        as lifecycle_status
                    from public.events
                    where id = %s
                    for update
                    """,
                    (
                        event_id,
                    ),
                )

                event = cur.fetchone()

                if not event:
                    raise ValueError(
                        "Target event does not exist."
                    )

                lifecycle_status = event[
                    "lifecycle_status"
                ]

                if lifecycle_status not in {
                    "active",
                    "monitoring",
                }:
                    raise ValueError(
                        "Target event is not open: "
                        f"{lifecycle_status}."
                    )

                cur.execute(
                    """
                    select id
                    from public.signals
                    where id = %s
                      and is_current = true
                      and event_matching_eligible = true
                    for update
                    """,
                    (
                        signal_id,
                    ),
                )

                if not cur.fetchone():
                    raise ValueError(
                        "Signal is no longer current "
                        "and eligible."
                    )

                cur.execute(
                    """
                    select
                      id,
                      source_signal_id,
                      target_signal_id,
                      relation::text as relation,
                      score,
                      hard_conflict,
                      rationale
                    from public.signal_relations
                    where id = %s
                      and rationale ->> 'producer'
                        = %s
                    for update
                    """,
                    (
                        signal_relation_id,
                        producer,
                    ),
                )

                relation_row = (
                    cur.fetchone()
                )

                if not relation_row:
                    raise ValueError(
                        "Matcher relation does not exist "
                        "or is not matcher-managed."
                    )

                endpoints = {
                    str(
                        relation_row[
                            "source_signal_id"
                        ]
                    ),
                    str(
                        relation_row[
                            "target_signal_id"
                        ]
                    ),
                }

                if signal_id not in endpoints:
                    raise ValueError(
                        "Signal is not an endpoint "
                        "of the matcher relation."
                    )

                relation_rationale = (
                    _as_mapping(
                        relation_row.get(
                            "rationale"
                        )
                    )
                )

                relation = relation_row[
                    "relation"
                ]

                decision = (
                    relation_rationale.get(
                        "decision"
                    )
                )

                merge_allowed = (
                    relation_rationale.get(
                        "merge_allowed"
                    )
                    is True
                )

                hard_conflict = bool(
                    relation_row[
                        "hard_conflict"
                    ]
                )

                if (
                    decision != "auto_linked"
                    or not merge_allowed
                    or hard_conflict
                ):
                    raise ValueError(
                        "Persisted matcher relation "
                        "does not authorize automatic "
                        "event attachment."
                    )

                if relation not in {
                    "duplicates",
                    "refines",
                }:
                    raise ValueError(
                        "Persisted matcher relation "
                        "has invalid auto-link relation: "
                        f"{relation!r}."
                    )

                score = _optional_float(
                    relation_row.get(
                        "score"
                    )
                )

                event_rationale = {
                    "producer": producer,
                    "matcher_version": (
                        relation_rationale.get(
                            "matcher_version"
                        )
                    ),
                    "source_signal_relation_id": (
                        str(
                            relation_row[
                                "id"
                            ]
                        )
                    ),
                    "assignment_action": (
                        item["action"]
                    ),
                    "assignment_reason": (
                        item["reason"]
                    ),
                    "pair_relation": relation,
                    "pair_decision": decision,
                    "merge_allowed": True,
                    "raw_score": (
                        relation_rationale.get(
                            "raw_score"
                        )
                    ),
                }

                rationale_json = (
                    json.dumps(
                        event_rationale,
                        ensure_ascii=False,
                    )
                )

                cur.execute(
                    """
                    select
                      relation_to_event::text
                        as relation_to_event,
                      match_decision::text
                        as match_decision,
                      rationale,
                      linked_at
                    from public.event_signals
                    where event_id = %s
                      and signal_id = %s
                    for update
                    """,
                    (
                        event_id,
                        signal_id,
                    ),
                )

                existing = cur.fetchone()

                if existing:
                    existing_decision = (
                        existing[
                            "match_decision"
                        ]
                    )

                    existing_rationale = (
                        _as_mapping(
                            existing.get(
                                "rationale"
                            )
                        )
                    )

                    if existing_decision in {
                        "manual_linked",
                        "manual_unlinked",
                    }:
                        raise ValueError(
                            "Manual event membership "
                            "blocks automatic overwrite."
                        )

                    if (
                        existing_rationale.get(
                            "producer"
                        )
                        != producer
                    ):
                        raise ValueError(
                            "Existing event membership "
                            "belongs to another producer."
                        )

                    cur.execute(
                        """
                        update public.event_signals
                        set
                          relation_to_event =
                            %s::public.relation_type,
                          match_score = %s,
                          match_decision =
                            'auto_linked'::public.match_decision,
                          rationale = %s::jsonb
                        where event_id = %s
                          and signal_id = %s
                        returning linked_at
                        """,
                        (
                            relation,
                            score,
                            rationale_json,
                            event_id,
                            signal_id,
                        ),
                    )

                    row = cur.fetchone()
                    action = "updated"

                else:
                    cur.execute(
                        """
                        insert into public.event_signals (
                          event_id,
                          signal_id,
                          relation_to_event,
                          match_score,
                          match_decision,
                          rationale
                        ) values (
                          %s,
                          %s,
                          %s::public.relation_type,
                          %s,
                          'auto_linked'::public.match_decision,
                          %s::jsonb
                        )
                        returning linked_at
                        """,
                        (
                            event_id,
                            signal_id,
                            relation,
                            score,
                            rationale_json,
                        ),
                    )

                    row = cur.fetchone()
                    action = "inserted"

                persisted.append(
                    {
                        "event_id": event_id,
                        "signal_id": signal_id,
                        "signal_relation_id": (
                            signal_relation_id
                        ),
                        "relation_to_event": (
                            relation
                        ),
                        "match_score": score,
                        "match_decision": (
                            "auto_linked"
                        ),
                        "lifecycle_status": (
                            lifecycle_status
                        ),
                        "action": action,
                        "linked_at": (
                            row.get(
                                "linked_at"
                            )
                            if row
                            else None
                        ),
                    }
                )

            conn.commit()

        return persisted


    def load_event_creation_signal(
        self,
        signal_id: str,
    ) -> dict[str, Any]:
        """Load the minimal persisted signal projection for event creation."""

        with (
            self.connection() as conn,
            conn.cursor() as cur,
        ):
            cur.execute(
                """
                select
                  s.id as signal_id,
                  s.disease_id,
                  d.canonical_name
                    as disease_canonical_name,
                  s.pathogen_id,
                  p.canonical_name
                    as pathogen_canonical_name,
                  to_jsonb(s.domains) as domains,
                  s.occurred_start,
                  coalesce(
                    r.published_at,
                    s.created_at
                  ) as observed_at
                from public.signals s
                join public.raw_items r
                  on r.id = s.raw_item_id
                left join public.diseases d
                  on d.id = s.disease_id
                left join public.pathogens p
                  on p.id = s.pathogen_id
                where s.id = %s
                  and s.is_current = true
                  and s.event_matching_eligible = true
                limit 1
                """,
                (
                    signal_id,
                ),
            )

            row = cur.fetchone()

        if not row:
            raise ValueError(
                "Event-creation signal does not exist "
                "or is not current and eligible."
            )

        return {
            "signal_id": str(
                row["signal_id"]
            ),
            "disease_id": (
                str(
                    row["disease_id"]
                )
                if row.get(
                    "disease_id"
                )
                else None
            ),
            "disease_canonical_name": (
                row.get(
                    "disease_canonical_name"
                )
            ),
            "pathogen_id": (
                str(
                    row["pathogen_id"]
                )
                if row.get(
                    "pathogen_id"
                )
                else None
            ),
            "pathogen_canonical_name": (
                row.get(
                    "pathogen_canonical_name"
                )
            ),
            "domains": _as_list(
                row.get(
                    "domains"
                )
            ),
            "occurred_start": _iso_date(
                row.get(
                    "occurred_start"
                )
            ),
            "observed_at": _iso_date(
                row.get(
                    "observed_at"
                )
            ),
        }


    def load_persisted_matcher_relation_by_id(
        self,
        signal_relation_id: str,
    ) -> dict[str, Any]:
        """Load one matcher-managed persisted signal relation."""

        producer = "oeti_event_matcher"

        with (
            self.connection() as conn,
            conn.cursor() as cur,
        ):
            cur.execute(
                """
                select
                  id,
                  source_signal_id,
                  target_signal_id,
                  relation::text as relation,
                  score,
                  hard_conflict,
                  rationale
                from public.signal_relations
                where id = %s
                  and rationale ->> 'producer'
                    = %s
                limit 1
                """,
                (
                    signal_relation_id,
                    producer,
                ),
            )

            row = cur.fetchone()

        if not row:
            raise ValueError(
                "Matcher relation does not exist "
                "or is not matcher-managed."
            )

        rationale = _as_mapping(
            row.get(
                "rationale"
            )
        )

        return {
            "signal_relation_id": str(
                row["id"]
            ),
            "source_signal_id": str(
                row["source_signal_id"]
            ),
            "target_signal_id": str(
                row["target_signal_id"]
            ),
            "matcher_version": (
                rationale.get(
                    "matcher_version"
                )
            ),
            "matcher_result": {
                "gate": rationale.get(
                    "gate"
                ),
                "relation": row[
                    "relation"
                ],
                "decision": rationale.get(
                    "decision"
                ),
                "merge_allowed": (
                    rationale.get(
                        "merge_allowed"
                    )
                    is True
                ),
                "hard_conflict": bool(
                    row[
                        "hard_conflict"
                    ]
                ),
                "hard_conflict_reason": (
                    rationale.get(
                        "hard_conflict_reason"
                    )
                ),
                "score": _optional_float(
                    row.get(
                        "score"
                    )
                ),
                "information_coverage": (
                    rationale.get(
                        "information_coverage"
                    )
                ),
                "component_scores": (
                    _as_mapping(
                        rationale.get(
                            "component_scores"
                        )
                    )
                ),
                "base_decision": rationale.get(
                    "base_decision"
                ),
                "policy_version": rationale.get(
                    "policy_version"
                ),
                "context_resolver_version": rationale.get(
                    "context_resolver_version"
                ),
                "auto_link_guard_override_reason": (
                    rationale.get(
                        "auto_link_guard_override_reason"
                    )
                ),
                "shared_event_context_anchors": (
                    _as_list(
                        rationale.get(
                            "shared_event_context_anchors"
                        )
                    )
                ),
            },
        }

