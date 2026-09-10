from __future__ import annotations

from dataclasses import dataclass

from .html_parser import parse_html_document
from .http_client import fetch_document
from .repository import IngestionRepository


@dataclass(slots=True)
class IngestionResult:
    raw_item_id: str
    inserted: bool
    title: str | None
    published_at: str | None
    url: str
    text_length: int


def ingest_html_url(database_url: str, source_code: str, url: str) -> IngestionResult:
    fetched = fetch_document(url)
    mime = (fetched.mime_type or "").lower()
    if "html" not in mime and "text/" not in mime:
        raise ValueError(f"El endpoint devolvió un MIME no HTML: {fetched.mime_type!r}")

    parsed = parse_html_document(fetched)
    repository = IngestionRepository(database_url)
    raw_item_id, inserted = repository.store_document(source_code, fetched, parsed)

    return IngestionResult(
        raw_item_id=raw_item_id,
        inserted=inserted,
        title=parsed.title,
        published_at=parsed.published_at.isoformat() if parsed.published_at else None,
        url=parsed.url,
        text_length=len(parsed.text),
    )
