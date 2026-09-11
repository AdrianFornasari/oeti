from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterator

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

from .prompt import EXTRACTOR_VERSION, PROMPT_VERSION


@dataclass(slots=True)
class RawDocument:
    raw_item_id: str
    title: str | None
    url: str
    published_at: datetime | None
    language: str | None
    raw_text: str


class ExtractionRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    @contextmanager
    def connection(self) -> Iterator[Connection]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as conn:
            yield conn

    def load_raw_document(self, raw_item_id: str) -> RawDocument:
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                select r.id, r.title, r.url, r.published_at, r.language, p.raw_text
                from public.raw_items r
                join public.raw_item_payloads p on p.raw_item_id = r.id
                where r.id = %s
                """,
                (raw_item_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"No existe raw_item con payload para id={raw_item_id!r}")
            return RawDocument(
                raw_item_id=str(row["id"]),
                title=row["title"],
                url=row["url"],
                published_at=row["published_at"],
                language=row["language"],
                raw_text=row["raw_text"],
            )

    def record_failed_run(
        self,
        *,
        raw_item_id: str,
        schema_version: str,
        provider: str,
        model_name: str,
        input_char_count: int,
        error_text: str,
        response_id: str | None = None,
    ) -> str:
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                insert into public.extraction_runs (
                  raw_item_id, schema_version, extractor_version, prompt_version,
                  provider, model_name, status, response_id, input_char_count, error_text
                ) values (%s, %s, %s, %s, %s, %s, 'failed', %s, %s, %s)
                returning id
                """,
                (
                    raw_item_id,
                    schema_version,
                    EXTRACTOR_VERSION,
                    PROMPT_VERSION,
                    provider,
                    model_name,
                    response_id,
                    input_char_count,
                    error_text[:10000],
                ),
            )
            run_id = str(cur.fetchone()["id"])
            conn.commit()
            return run_id

    def persist_extraction(
        self,
        *,
        raw_item_id: str,
        payload: dict[str, Any],
        provider: str,
        model_name: str,
        response_id: str | None,
        input_char_count: int,
    ) -> tuple[str, list[str]]:
        warnings: list[str] = list(payload.get("warnings", []))

        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into public.extraction_runs (
                      raw_item_id, schema_version, extractor_version, prompt_version,
                      provider, model_name, status, response_id, input_char_count,
                      output_json, warnings
                    ) values (%s, %s, %s, %s, %s, %s, 'succeeded', %s, %s, %s::jsonb, %s::jsonb)
                    returning id
                    """,
                    (
                        raw_item_id,
                        payload["schema_version"],
                        EXTRACTOR_VERSION,
                        PROMPT_VERSION,
                        provider,
                        model_name,
                        response_id,
                        input_char_count,
                        json.dumps(payload, ensure_ascii=False),
                        json.dumps(warnings, ensure_ascii=False),
                    ),
                )
                extraction_run_id = str(cur.fetchone()["id"])

                for signal in payload.get("signals", []):
                    self._persist_signal(cur, raw_item_id, extraction_run_id, payload["schema_version"], signal, model_name, warnings)

                cur.execute(
                    "update public.raw_items set processing_status = 'processed' where id = %s",
                    (raw_item_id,),
                )
                cur.execute(
                    "update public.extraction_runs set warnings = %s::jsonb where id = %s",
                    (json.dumps(warnings, ensure_ascii=False), extraction_run_id),
                )
            conn.commit()
        return extraction_run_id, warnings

    def _persist_signal(
        self,
        cur,
        raw_item_id: str,
        extraction_run_id: str,
        schema_version: str,
        signal: dict[str, Any],
        model_name: str,
        warnings: list[str],
    ) -> None:
        disease_id, disease_status = self._resolve_disease(cur, signal["disease"])
        pathogen_id, pathogen_status = self._resolve_pathogen(cur, signal["pathogen"])

        local_key = signal["local_signal_id"]
        # If the same extractor is rerun, supersede the current version instead of violating
        # the one-current-version partial unique index.
        cur.execute(
            """
            select id, version
            from public.signals
            where raw_item_id = %s and local_signal_key = %s and is_current = true
            order by version desc
            limit 1
            """,
            (raw_item_id, local_key),
        )
        previous = cur.fetchone()
        next_version = (previous["version"] + 1) if previous else 1
        previous_id = previous["id"] if previous else None
        if previous:
            cur.execute("update public.signals set is_current = false where id = %s", (previous_id,))

        cur.execute(
            """
            insert into public.signals (
              schema_version, raw_item_id, local_signal_key, version, supersedes_signal_id,
              is_current, domains, signal_role, signal_type, signal_summary, verification_status,
              extraction_confidence, disease_id, disease_verbatim, disease_confidence,
              disease_normalization_status, pathogen_id, pathogen_verbatim, pathogen_confidence,
              pathogen_normalization_status, occurred_start, occurred_end, date_precision, reference_period,
              transmission, extractor_version, model_name, warnings, review_status,
              extraction_run_id
            ) values (
              %s, %s, %s, %s, %s, true, %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb,
              %s::jsonb, %s, %s, '[]'::jsonb, 'pending', %s
            ) returning id
            """,
            (
                schema_version,
                raw_item_id,
                local_key,
                next_version,
                previous_id,
                signal["domains"],
                signal["signal_role"],
                signal["signal_type"],
                signal["signal_summary"],
                signal["verification_status"],
                signal["extraction_confidence"],
                disease_id,
                signal["disease"].get("verbatim"),
                signal["disease"].get("confidence"),
                disease_status,
                pathogen_id,
                signal["pathogen"].get("verbatim"),
                signal["pathogen"].get("confidence"),
                pathogen_status,
                signal["event_date"].get("start"),
                signal["event_date"].get("end"),
                signal["event_date"].get("precision"),
                json.dumps(signal["reference_period"], ensure_ascii=False),
                json.dumps(signal["transmission"], ensure_ascii=False),
                EXTRACTOR_VERSION,
                model_name,
                extraction_run_id,
            ),
        )
        signal_id = str(cur.fetchone()["id"])

        for location in signal.get("locations", []):
            location_id = self._resolve_or_create_location(cur, location)
            cur.execute(
                """
                insert into public.signal_locations (signal_id, location_id, location_role, confidence)
                values (%s, %s, %s, %s)
                on conflict do nothing
                """,
                (signal_id, location_id, location.get("role") or "unknown", location.get("confidence")),
            )

        for host in signal.get("hosts", []):
            host_id = self._resolve_host(cur, host)
            if host_id is None:
                warnings.append(
                    f"Signal {local_key}: host no resuelto en catálogo: {host.get('canonical_name') or host.get('verbatim')}"
                )
                continue
            cur.execute(
                """
                insert into public.signal_hosts (signal_id, host_id, host_role, confidence)
                values (%s, %s, 'affected', %s)
                on conflict do nothing
                """,
                (signal_id, host_id, host.get("confidence")),
            )

        for metric in signal.get("metrics", []):
            cur.execute(
                """
                insert into public.signal_metrics (
                  signal_id, metric_name, value_numeric, value_text, unit, as_of_date, metadata
                ) values (%s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    signal_id,
                    metric["name"],
                    metric.get("value_numeric"),
                    metric.get("value_text"),
                    metric.get("unit"),
                    metric.get("as_of_date"),
                    json.dumps({
                        "as_of_year": metric.get("as_of_year"),
                        "as_of_month": metric.get("as_of_month"),
                        "as_of_precision": metric.get("as_of_precision"),
                        "as_of_verbatim": metric.get("as_of_verbatim"),
                    }, ensure_ascii=False),
                ),
            )

        for evidence in signal.get("evidence", []):
            cur.execute(
                """
                insert into public.signal_evidence (
                  signal_id, evidence_type, excerpt, document_locator, page_number
                ) values (%s, %s, %s, %s, %s)
                """,
                (
                    signal_id,
                    evidence.get("type") or "source_span",
                    evidence["text"],
                    evidence.get("location_in_document"),
                    evidence.get("page_number"),
                ),
            )

        genomics = signal.get("genomics", {})
        if (
            genomics.get("sequence_reported")
            or genomics.get("lineage")
            or genomics.get("clade")
            or genomics.get("accession")
            or genomics.get("test_result") not in {None, "unknown", "not_applicable"}
        ):
            cur.execute(
                """
                insert into public.genomic_observations (
                  signal_id, pathogen_id, accession, lineage, clade, sequence_reported, test_result
                ) values (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    signal_id,
                    pathogen_id,
                    genomics.get("accession"),
                    genomics.get("lineage"),
                    genomics.get("clade"),
                    bool(genomics.get("sequence_reported")),
                    genomics.get("test_result") or "unknown",
                ),
            )

    @staticmethod
    def _resolve_disease(cur, entity: dict[str, Any]) -> tuple[str | None, str]:
        canonical = entity.get("canonical_name")
        verbatim = entity.get("verbatim")
        candidate = canonical or verbatim
        if not candidate:
            return None, "unresolved"
        cur.execute(
            """
            select id from public.diseases
            where lower(canonical_name) = lower(%s)
               or exists (select 1 from unnest(synonyms) s where lower(s) = lower(%s))
            limit 1
            """,
            (candidate, candidate),
        )
        row = cur.fetchone()
        return (str(row["id"]), "resolved") if row else (None, "unresolved")

    @staticmethod
    def _resolve_pathogen(cur, entity: dict[str, Any]) -> tuple[str | None, str]:
        canonical = entity.get("canonical_name")
        verbatim = entity.get("verbatim")
        candidate = canonical or verbatim
        if not candidate:
            return None, "unresolved"
        cur.execute(
            """
            select id from public.pathogens
            where lower(canonical_name) = lower(%s)
               or exists (select 1 from unnest(synonyms) s where lower(s) = lower(%s))
            limit 1
            """,
            (candidate, candidate),
        )
        row = cur.fetchone()
        return (str(row["id"]), "resolved") if row else (None, "unresolved")

    @staticmethod
    def _resolve_host(cur, host: dict[str, Any]) -> str | None:
        canonical = host.get("canonical_name")
        verbatim = host.get("verbatim")
        host_type = host.get("host_type")
        # Humans are normalized to the seeded Homo sapiens host independently of wording.
        if host_type == "human":
            cur.execute("select id from public.hosts where scientific_name = 'Homo sapiens' limit 1")
            row = cur.fetchone()
            return str(row["id"]) if row else None
        candidate = canonical or verbatim
        if not candidate:
            return None
        cur.execute(
            """
            select id from public.hosts
            where lower(common_name) = lower(%s)
               or lower(coalesce(scientific_name, '')) = lower(%s)
            limit 1
            """,
            (candidate, candidate),
        )
        row = cur.fetchone()
        return str(row["id"]) if row else None

    @staticmethod
    def _resolve_or_create_location(cur, location: dict[str, Any]) -> str:
        country_iso2 = location.get("country_iso2")
        country = location.get("country")
        admin1 = location.get("admin1")
        admin2 = location.get("admin2")
        locality = location.get("locality")
        region = location.get("region")
        precision = location.get("precision") or "unknown"
        cur.execute(
            """
            select id from public.locations
            where country_iso2 is not distinct from %s
              and admin1 is not distinct from %s
              and admin2 is not distinct from %s
              and locality is not distinct from %s
              and region_name is not distinct from %s
              and precision = %s
            limit 1
            """,
            (country_iso2, admin1, admin2, locality, region, precision),
        )
        row = cur.fetchone()
        if row:
            return str(row["id"])

        display = locality or admin2 or admin1 or region or country or country_iso2 or "Ubicación no resuelta"
        normalization_status = "resolved" if any([country_iso2, country, admin1, admin2, locality, region]) else "unresolved"
        cur.execute(
            """
            insert into public.locations (
              display_name, country_iso2, country_name, admin1, admin2, locality,
              region_name, precision, normalization_status, metadata
            ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            returning id
            """,
            (
                display,
                country_iso2,
                country,
                admin1,
                admin2,
                locality,
                region,
                precision,
                normalization_status,
                json.dumps({"source": "signal_extractor", "confidence": location.get("confidence")}),
            ),
        )
        return str(cur.fetchone()["id"])
