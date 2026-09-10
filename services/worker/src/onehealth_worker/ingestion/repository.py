from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

from .content import normalized_text_sha256
from .models import FetchedDocument, ParsedDocument


class IngestionRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    @contextmanager
    def connection(self) -> Iterator[Connection]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as conn:
            yield conn

    def store_document(
        self,
        source_code: str,
        fetched: FetchedDocument,
        parsed: ParsedDocument,
    ) -> tuple[str, bool]:
        if not parsed.text.strip():
            raise ValueError("El documento no contiene texto utilizable después del parseo.")

        content_hash = normalized_text_sha256(parsed.text)
        mime_type = (fetched.mime_type or "").split(";", 1)[0] or None

        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select id from public.sources where code = %s and is_active = true", (source_code,))
                source = cur.fetchone()
                if not source:
                    raise ValueError(
                        f"No existe una fuente activa con code={source_code!r}. "
                        "Aplicá primero la migración bootstrap de catálogos."
                    )

                cur.execute(
                    """
                    select id
                    from public.raw_items
                    where source_id = %s and content_sha256 = %s
                    limit 1
                    """,
                    (source["id"], content_hash),
                )
                existing = cur.fetchone()
                if existing:
                    return str(existing["id"]), False

                cur.execute(
                    """
                    insert into public.raw_items (
                      source_id, url, title, published_at, retrieved_at, language,
                      mime_type, content_sha256, processing_status, metadata
                    ) values (
                      %s, %s, %s, %s, %s, %s, %s, %s, 'queued', %s::jsonb
                    )
                    returning id
                    """,
                    (
                        source["id"],
                        parsed.url,
                        parsed.title,
                        parsed.published_at,
                        fetched.retrieved_at,
                        parsed.language,
                        mime_type,
                        content_hash,
                        json.dumps(parsed.metadata, ensure_ascii=False),
                    ),
                )
                row = cur.fetchone()
                raw_item_id = row["id"]

                cur.execute(
                    """
                    insert into public.raw_item_payloads (
                      raw_item_id, raw_text, metadata
                    ) values (%s, %s, %s::jsonb)
                    """,
                    (
                        raw_item_id,
                        parsed.text,
                        json.dumps(
                            {
                                "body_bytes": len(fetched.body),
                                "content_hash_basis": "normalized_parsed_text",
                            },
                            ensure_ascii=False,
                        ),
                    ),
                )
            conn.commit()
            return str(raw_item_id), True
