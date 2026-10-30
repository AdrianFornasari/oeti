from datetime import datetime, timezone

import httpx
import pytest
from tenacity import wait_none

from onehealth_worker.ingestion import http_client, pipeline
from onehealth_worker.ingestion.models import FetchedDocument, ParsedDocument
from onehealth_worker.ingestion.repository import IngestionRepository


def test_pipeline_preserves_article_with_invalid_date_using_fake_repository(monkeypatch):
    fetched = FetchedDocument(url='https://example.invalid/final', status_code=200,
        mime_type='text/html', retrieved_at=datetime.now(timezone.utc),
        body=b'<main><p>31 de febrero de 2026</p><p>Texto del documento suficientemente largo.</p></main>')
    monkeypatch.setattr(pipeline, 'fetch_document', lambda url: fetched)
    calls = []

    class FakeRepository:
        def __init__(self, database_url):
            assert database_url == 'unused'

        def store_document(self, source_code, response, parsed):
            assert response is fetched
            assert parsed.published_at is None
            assert parsed.url == fetched.url
            assert 'Texto del documento' in parsed.text
            assert parsed.metadata['parser'] == 'beautifulsoup-html-v0.2.5'
            calls.append(source_code)
            return 'synthetic-id', True

    monkeypatch.setattr(pipeline, 'IngestionRepository', FakeRepository)
    result = pipeline.ingest_html_url('unused', 'synthetic-source', 'https://example.invalid/original')
    assert calls == ['synthetic-source']
    assert result.inserted is True
    assert result.published_at is None
    assert result.url == fetched.url


def test_empty_document_rejected_before_database_connection(monkeypatch):
    def forbidden_connection(self):
        raise AssertionError('Database must not be accessed')

    monkeypatch.setattr(IngestionRepository, 'connection', forbidden_connection)
    fetched = FetchedDocument('https://example.invalid', 200, 'text/html', b'', datetime.now(timezone.utc))
    parsed = ParsedDocument(fetched.url, None, None, None, ' \n\t')
    with pytest.raises(ValueError, match='texto utilizable'):
        IngestionRepository('unused').store_document('synthetic', fetched, parsed)


def install_transport(monkeypatch, handler):
    real_client = httpx.Client
    monkeypatch.setattr(http_client.httpx, 'Client',
        lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs))


def test_http_redirect_preserves_final_url_body_and_response_metadata(monkeypatch):
    requests = []

    def handler(request):
        requests.append(request)
        if request.url.path == '/start':
            return httpx.Response(302, headers={'location': '/final'})
        return httpx.Response(200, content=b'<p>Synthetic document</p>',
            headers={'content-type': 'text/html; charset=utf-8', 'etag': 'synthetic-etag'})

    install_transport(monkeypatch, handler)
    fetched = http_client.fetch_document('https://example.invalid/start')
    assert str(fetched.url) == 'https://example.invalid/final'
    assert fetched.body == b'<p>Synthetic document</p>'
    assert fetched.headers['etag'] == 'synthetic-etag'
    assert fetched.retrieved_at.utcoffset().total_seconds() == 0
    assert len(requests) == 2
    assert requests[0].headers['user-agent'] == http_client.USER_AGENT


def test_http_error_status_is_not_retried(monkeypatch):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(404)

    install_transport(monkeypatch, handler)
    with pytest.raises(httpx.HTTPStatusError):
        http_client.fetch_document('https://example.invalid/missing')
    assert len(calls) == 1


def test_transport_failure_stops_after_three_attempts(monkeypatch):
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ConnectError('Synthetic offline failure', request=request)

    install_transport(monkeypatch, handler)
    with pytest.raises(httpx.ConnectError):
        http_client.fetch_document.retry_with(wait=wait_none())('https://example.invalid/unavailable')
    assert len(calls) == 3


@pytest.mark.parametrize('mime', [
    'application/json; profile="html"', 'application/nothtml',
    'application/octet-stream; note="text/plain"', 'application/xtext/plain',
    'text/', 'application/pdf', None,
])
def test_non_document_mime_is_rejected_before_parser_or_repository(monkeypatch, mime):
    fetched = FetchedDocument('https://example.invalid', 200, mime, b'synthetic', datetime.now(timezone.utc))
    monkeypatch.setattr(pipeline, 'fetch_document', lambda url: fetched)

    def forbidden(*args, **kwargs):
        raise AssertionError('Unsupported MIME reached parser or repository')

    monkeypatch.setattr(pipeline, 'parse_html_document', forbidden)
    monkeypatch.setattr(pipeline, 'IngestionRepository', forbidden)
    with pytest.raises(ValueError, match='MIME'):
        pipeline.ingest_html_url('unused', 'synthetic', fetched.url)


@pytest.mark.parametrize('mime', [
    'text/html', 'TEXT/HTML; charset=UTF-8', 'application/xhtml+xml; charset=utf-8',
    'text/plain', ' text/html ; charset=utf-8 ',
])
def test_supported_mime_reaches_parser(monkeypatch, mime):
    fetched = FetchedDocument('https://example.invalid', 200, mime, b'synthetic', datetime.now(timezone.utc))
    monkeypatch.setattr(pipeline, 'fetch_document', lambda url: fetched)

    class ParserBoundary(Exception):
        pass

    def stop(response):
        assert response is fetched
        raise ParserBoundary

    monkeypatch.setattr(pipeline, 'parse_html_document', stop)
    with pytest.raises(ParserBoundary):
        pipeline.ingest_html_url('unused', 'synthetic', fetched.url)
