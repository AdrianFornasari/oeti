from datetime import datetime, timezone
from pathlib import Path
import pytest

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


@pytest.mark.parametrize('date_text', [
    '31 de febrero de 2026', '29 de febrero de 2025',
    '31 de abril de 2026', '0 de enero de 2026', '32 de diciembre de 2026',
])
def test_invalid_visible_publication_date_does_not_abort_document(date_text):
    fetched = FetchedDocument(url='https://example.invalid/article', status_code=200,
        mime_type='text/html', retrieved_at=datetime.now(timezone.utc),
        body=f'<main><p>{date_text}</p><p>Se conserva el texto completo del artículo.</p></main>'.encode())
    parsed = parse_html_document(fetched)
    assert parsed.published_at is None
    assert 'Se conserva el texto completo del artículo.' in parsed.text


def test_valid_leap_day_remains_a_publication_date():
    fetched = FetchedDocument(url='https://example.invalid/article', status_code=200,
        mime_type='text/html', retrieved_at=datetime.now(timezone.utc),
        body=b'<main><p>29 de febrero de 2024</p></main>')
    assert parse_html_document(fetched).published_at.date().isoformat() == '2024-02-29'


def test_valid_publication_metadata_takes_precedence_over_invalid_visible_date():
    fetched = FetchedDocument(url='https://example.invalid/article', status_code=200,
        mime_type='text/html', retrieved_at=datetime.now(timezone.utc),
        body=b'<meta property="article:published_time" content="2026-10-30T12:00:00+00:00">'
             b'<main><p>31 de febrero de 2026</p></main>')
    assert parse_html_document(fetched).published_at.isoformat() == '2026-10-30T12:00:00+00:00'
