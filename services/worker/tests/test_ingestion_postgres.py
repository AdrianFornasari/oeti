"""Dedicated ingestion checks against disposable localhost PostgreSQL only."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import os
from pathlib import Path
import re
from threading import Barrier
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest

from onehealth_worker.ingestion.content import normalized_text_sha256
from onehealth_worker.ingestion.models import FetchedDocument, ParsedDocument
from onehealth_worker.ingestion.repository import IngestionRepository

pytestmark = pytest.mark.skipif(os.environ.get('OETI_LOCAL_PG_TESTS') != '1',
    reason='Disposable localhost PostgreSQL not enabled')
ADMIN = 'host=127.0.0.1 port=55449 user=oeti_test dbname=postgres connect_timeout=5'


@pytest.fixture
def ingestion_database():
    name = 'oeti_test_ingestion_' + uuid4().hex
    with psycopg.connect(ADMIN, autocommit=True) as admin:
        admin.execute(sql.SQL('create database {}').format(sql.Identifier(name)))
    dsn = f'host=127.0.0.1 port=55449 user=oeti_test dbname={name} connect_timeout=5'
    try:
        root = Path(__file__).resolve().parents[3]
        core = (root / 'supabase/migrations/20260910090000_initial_core_schema.sql').read_text(encoding='utf-8')
        with psycopg.connect(dsn) as conn:
            for ddl in re.findall(r'create type public\.\w+ as enum \(.*?\);', core, re.S):
                conn.execute(ddl)
            for table in ('sources', 'raw_items', 'raw_item_payloads'):
                conn.execute(re.search(rf'create table public\.{table} \(.*?\n\);', core, re.S).group())
            for code in ('synthetic-a', 'synthetic-b'):
                conn.execute("insert into public.sources(code,name,kind,ingestion) values(%s,%s,'primary_official','manual')", (code, code))
        yield IngestionRepository(dsn), dsn
    finally:
        with psycopg.connect(ADMIN, autocommit=True) as admin:
            admin.execute(sql.SQL('drop database {} with (force)').format(sql.Identifier(name)))


def documents(text='Contenido sintético de vigilancia.', title='Título sintético'):
    fetched = FetchedDocument('https://example.invalid/synthetic', 200, 'text/html; charset=utf-8',
        b'<p>synthetic</p>', datetime(2026, 10, 30, tzinfo=timezone.utc))
    parsed = ParsedDocument(fetched.url, title, None, 'es', text, {'parser': 'synthetic-test'})
    return fetched, parsed


def counts(dsn):
    with psycopg.connect(dsn) as conn:
        return conn.execute('select (select count(*) from public.raw_items), (select count(*) from public.raw_item_payloads)').fetchone()


def test_new_ingestion_persists_item_and_payload(ingestion_database):
    repo, dsn = ingestion_database
    fetched, parsed = documents()
    identifier, inserted = repo.store_document('synthetic-a', fetched, parsed)
    assert inserted is True
    assert counts(dsn) == (1, 1)
    with psycopg.connect(dsn) as conn:
        row = conn.execute('select r.content_sha256,r.url,p.raw_text from public.raw_items r join public.raw_item_payloads p on p.raw_item_id=r.id where r.id=%s', (identifier,)).fetchone()
    assert row == (normalized_text_sha256(parsed.text), parsed.url, parsed.text)


def test_repeat_refreshes_metadata_but_preserves_original_payload(ingestion_database):
    repo, dsn = ingestion_database
    fetched, parsed = documents(text='Contenido  sintético.\nOriginal.')
    identifier, _ = repo.store_document('synthetic-a', fetched, parsed)
    _, refreshed = documents(text='Contenido sintético. Original.', title='Título actualizado')
    again, inserted = repo.store_document('synthetic-a', fetched, refreshed)
    assert (again, inserted) == (identifier, False)
    assert counts(dsn) == (1, 1)
    with psycopg.connect(dsn) as conn:
        row = conn.execute('select r.title,r.metadata,p.raw_text from public.raw_items r join public.raw_item_payloads p on p.raw_item_id=r.id where r.id=%s', (identifier,)).fetchone()
    assert row[0] == 'Título actualizado'
    assert row[1]['deduplication'] == 'same_source_same_normalized_text'
    assert row[2] == parsed.text


def test_same_content_in_different_sources_remains_separate(ingestion_database):
    repo, dsn = ingestion_database
    fetched, parsed = documents()
    first = repo.store_document('synthetic-a', fetched, parsed)
    second = repo.store_document('synthetic-b', fetched, parsed)
    assert first[0] != second[0]
    assert first[1] is second[1] is True
    assert counts(dsn) == (2, 2)


def test_payload_failure_rolls_back_raw_item(ingestion_database):
    repo, dsn = ingestion_database
    with psycopg.connect(dsn) as conn:
        conn.execute('alter table public.raw_item_payloads add constraint synthetic_failure check (false)')
    with pytest.raises(psycopg.errors.CheckViolation):
        repo.store_document('synthetic-a', *documents())
    assert counts(dsn) == (0, 0)


def test_unrelated_unique_violation_propagates_without_retry(ingestion_database, monkeypatch):
    repo, dsn = ingestion_database
    fetched, parsed = documents()
    repo.store_document('synthetic-a', fetched, parsed)
    with psycopg.connect(dsn) as conn:
        conn.execute('alter table public.raw_item_payloads add constraint synthetic_payload_unique unique(raw_text)')
    original_connection = repo.connection
    connections = []

    @contextmanager
    def tracked_connection():
        connections.append(True)
        with original_connection() as connection:
            yield connection

    monkeypatch.setattr(repo, 'connection', tracked_connection)
    with pytest.raises(psycopg.errors.UniqueViolation) as error:
        repo.store_document('synthetic-b', fetched, parsed)
    assert error.value.diag.constraint_name == 'synthetic_payload_unique'
    assert len(connections) == 1
    assert counts(dsn) == (1, 1)


def test_simultaneous_same_source_and_hash_return_one_shared_item(ingestion_database):
    repo, dsn = ingestion_database
    barrier = Barrier(2)

    class CursorProxy:
        def __init__(self, cursor):
            self.cursor = cursor
            self.wait_for_peer = False

        def execute(self, query, params=None):
            self.wait_for_peer = ' '.join(str(query).lower().split()).startswith('select id from public.raw_items')
            return self.cursor.execute(query, params)

        def fetchone(self):
            result = self.cursor.fetchone()
            if self.wait_for_peer and result is None:
                self.wait_for_peer = False
                barrier.wait(timeout=10)
            return result

        def __getattr__(self, name):
            return getattr(self.cursor, name)

    class ConnectionProxy:
        def __init__(self, connection):
            self.connection = connection

        @contextmanager
        def cursor(self):
            with self.connection.cursor() as cursor:
                yield CursorProxy(cursor)

        def __getattr__(self, name):
            return getattr(self.connection, name)

    class SimultaneousRepository(IngestionRepository):
        @contextmanager
        def connection(self):
            with super().connection() as connection:
                yield ConnectionProxy(connection)

    def store():
        return SimultaneousRepository(dsn).store_document('synthetic-a', *documents())

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(store) for _ in range(2)]
        results = [future.result(timeout=20) for future in futures]
    assert results[0][0] == results[1][0]
    assert sorted(result[1] for result in results) == [False, True]
    assert counts(dsn) == (1, 1)
