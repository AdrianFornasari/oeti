"""Token persistence against disposable localhost PostgreSQL only."""
import os
import re
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from onehealth_worker.extraction.repository import ExtractionRepository
from onehealth_worker.extraction.token_usage import TOKEN_USAGE_KEYS

pytestmark = pytest.mark.skipif(os.environ.get('OETI_LOCAL_PG_TESTS') != '1',
    reason='Disposable localhost PostgreSQL not enabled')
ADMIN = 'host=127.0.0.1 port=55449 user=oeti_test dbname=postgres connect_timeout=5'


@pytest.fixture
def extraction_database():
    name = 'oeti_test_' + uuid4().hex
    with psycopg.connect(ADMIN, autocommit=True) as admin:
        admin.execute(sql.SQL('create database {}').format(sql.Identifier(name)))
    dsn = f'host=127.0.0.1 port=55449 user=oeti_test dbname={name} connect_timeout=5'
    try:
        root = Path(__file__).resolve().parents[3]
        core = (root / 'supabase/migrations/20260910090000_initial_core_schema.sql').read_text(encoding='utf-8')
        runs = (root / 'supabase/migrations/20260910183000_signal_extraction_runs.sql').read_text(encoding='utf-8')
        migration = (root / 'supabase/migrations/20261008093000_extraction_run_token_usage.sql').read_text(encoding='utf-8')
        with psycopg.connect(dsn) as conn:
            for ddl in re.findall(r'create type public\.\w+ as enum \(.*?\);', core, re.S):
                conn.execute(ddl)
            for table in ('sources', 'raw_items'):
                conn.execute(re.search(rf'create table public\.{table} \(.*?\n\);', core, re.S).group())
            conn.execute(re.search(r'create table public.extraction_runs \(.*?\n\);', runs, re.S).group())
            source = conn.execute("insert into public.sources(code,name,kind,ingestion) values('test','test','primary_official','manual') returning id").fetchone()[0]
            raw_id = conn.execute("insert into public.raw_items(source_id,url,content_sha256) values(%s,'test','test') returning id", (source,)).fetchone()[0]
            historical = conn.execute("insert into public.extraction_runs(raw_item_id,schema_version,extractor_version,prompt_version,provider,model_name,status,error_text) values(%s,'test','test','test','test','test','failed','historical') returning id", (raw_id,)).fetchone()[0]
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(migration)
        yield ExtractionRepository(dsn), str(raw_id), str(historical)
    finally:
        with psycopg.connect(ADMIN, autocommit=True) as admin:
            admin.execute(sql.SQL('drop database {} with (force)').format(sql.Identifier(name)))


def read_usage(repository, run_id):
    with repository.connection() as conn:
        row = conn.execute('select input_tokens,cached_input_tokens,output_tokens,reasoning_tokens,total_tokens from public.extraction_runs where id=%s', (run_id,)).fetchone()
        return tuple(row[key] for key in TOKEN_USAGE_KEYS)


@pytest.mark.parametrize('status', ['succeeded', 'failed'])
@pytest.mark.parametrize('usage,expected', [(None, (None,)*5),
    ({'input_tokens': 0, 'output_tokens': 4}, (0, None, 4, None, None)),
    ({'input_tokens': 12, 'cached_input_tokens': 0, 'output_tokens': 4,
      'reasoning_tokens': 2, 'total_tokens': 16}, (12, 0, 4, 2, 16))])
def test_postgres_persists_usage_for_success_and_failure(extraction_database, status, usage, expected):
    repository, raw_id, historical = extraction_database
    common = dict(raw_item_id=raw_id, provider='test', model_name='test',
        response_id='response-id', input_char_count=4, usage=usage)
    if status == 'failed':
        run_id = repository.record_failed_run(**common, schema_version='test', error_text='validation')
    else:
        run_id, _ = repository.persist_extraction(**common, payload={'schema_version': 'test', 'signals': []})
    assert read_usage(repository, run_id) == expected
    assert read_usage(repository, historical) == (None,)*5


@pytest.mark.parametrize('key', TOKEN_USAGE_KEYS)
def test_postgres_migration_rejects_negative_counts(extraction_database, key):
    repository, _, historical = extraction_database
    with pytest.raises(psycopg.errors.CheckViolation):
        with repository.connection() as conn:
            conn.execute(sql.SQL('update public.extraction_runs set {}=-1 where id=%s').format(sql.Identifier(key)), (historical,))
    assert read_usage(repository, historical) == (None,)*5
