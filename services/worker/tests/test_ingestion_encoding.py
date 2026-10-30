from datetime import datetime, timezone

import pytest

from onehealth_worker.ingestion.html_parser import parse_html_document
from onehealth_worker.ingestion.models import FetchedDocument


@pytest.mark.parametrize('mime', [
    'text/html; charset=iso-8859-2',
    'TEXT/HTML; CHARSET="ISO-8859-2"',
    'text/html; profile="synthetic"; charset=iso-8859-2',
])
def test_declared_http_charset_preserves_literal_title_and_text(mime):
    text = 'Łódź'
    body = f'<html><head><title>{text}</title></head><body><main><p>{text}</p></main></body></html>'
    fetched = FetchedDocument('https://example.invalid/encoding', 200, mime,
        body.encode('iso-8859-2'), datetime.now(timezone.utc))
    original = fetched.body
    parsed = parse_html_document(fetched)
    assert parsed.title == text
    assert parsed.text == text
    assert parsed.metadata['http_charset'] == 'iso-8859-2'
    assert parsed.metadata['text_encoding'] == 'iso-8859-2'
    assert fetched.body == original


@pytest.mark.parametrize('mime', ['text/html', 'text/html; charset=unknown-synthetic-encoding'])
def test_missing_or_unrecognized_http_charset_preserves_html_meta_fallback(mime):
    text = 'Información de Córdoba: ningún caso.'
    body = f'<meta charset="utf-8"><title>{text}</title><main><p>{text}</p></main>'
    fetched = FetchedDocument('https://example.invalid/encoding', 200, mime,
        body.encode('utf-8'), datetime.now(timezone.utc))
    parsed = parse_html_document(fetched)
    assert parsed.title == text
    assert parsed.text == text
    assert parsed.metadata['text_encoding'] == 'utf-8'
