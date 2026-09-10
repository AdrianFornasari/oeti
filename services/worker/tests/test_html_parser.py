from datetime import datetime, timezone
from pathlib import Path

from onehealth_worker.ingestion.html_parser import parse_html_document
from onehealth_worker.ingestion.models import FetchedDocument
from onehealth_worker.ingestion.content import normalized_text_sha256


def test_argentina_article_parser() -> None:
    fixture = Path(__file__).parent / "fixtures" / "argentina_gob_article.html"
    fetched = FetchedDocument(
        url="https://www.argentina.gob.ar/noticias/test",
        status_code=200,
        mime_type="text/html; charset=UTF-8",
        body=fixture.read_bytes(),
        retrieved_at=datetime.now(timezone.utc),
    )

    parsed = parse_html_document(fetched)
    assert parsed.title == "Salud monitorea un evento epidemiológico"
    assert parsed.language == "es"
    assert parsed.published_at is not None
    assert parsed.published_at.date().isoformat() == "2026-05-04"
    assert "seguimiento epidemiológico" in parsed.text
    assert "Cabecera" not in parsed.text
    assert "Pie" not in parsed.text


def test_hash_is_stable_to_whitespace() -> None:
    assert normalized_text_sha256("uno  dos\n tres") == normalized_text_sha256("uno dos tres")
