"""Opt-in extraction transaction tests on disposable localhost databases."""
import json
import os
from pathlib import Path
import re
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest

from onehealth_worker.extraction.repository import ExtractionRepository
from onehealth_worker.extraction.schema import validate_extraction
from test_attribution_review import artifacts

pytestmark = pytest.mark.skipif(os.environ.get('OETI_LOCAL_PG_TESTS') != '1',
    reason='Disposable localhost PostgreSQL not enabled')
ADMIN = 'host=127.0.0.1 port=55449 user=oeti_test dbname=postgres connect_timeout=5'


@pytest.fixture
def extraction_transaction_database():
    name = 'oeti_test_extraction_tx_' + uuid4().hex
    with psycopg.connect(ADMIN, autocommit=True) as admin:
        admin.execute(sql.SQL('create database {}').format(sql.Identifier(name)))
    dsn = f'host=127.0.0.1 port=55449 user=oeti_test dbname={name} connect_timeout=5'
    try:
        migrations = Path(__file__).resolve().parents[3] / 'supabase/migrations'
        core = (migrations / '20260910090000_initial_core_schema.sql').read_text(encoding='utf-8')
        runs = (migrations / '20260910183000_signal_extraction_runs.sql').read_text(encoding='utf-8')
        semantics = (migrations / '20260911160000_signal_semantics_v03.sql').read_text(encoding='utf-8')
        eligibility = (migrations / '20260911190000_diagnostics_matching_v035.sql').read_text(encoding='utf-8')
        tokens = (migrations / '20261008093000_extraction_run_token_usage.sql').read_text(encoding='utf-8')
        with psycopg.connect(dsn) as conn:
            conn.execute('create schema auth; create table auth.users(id uuid primary key)')
            for ddl in re.findall(r'create type public\.\w+ as enum \(.*?\);', core, re.S):
                conn.execute(ddl)
            for table in ('sources', 'raw_items', 'raw_item_payloads', 'diseases', 'pathogens',
                          'signals', 'signal_metrics', 'signal_evidence', 'events', 'event_signals', 'signal_relations'):
                conn.execute(re.search(rf'create table public\.{table} \(.*?\n\);', core, re.S).group())
            conn.execute(re.search(r'create unique index signals_one_current_version_idx.*?;', core, re.S).group())
            conn.execute(re.search(r'create table public.extraction_runs \(.*?\n\);', runs, re.S).group())
            conn.execute(re.search(r'alter table public.signals\s+add column extraction_run_id.*?;', runs, re.S).group())
            conn.execute(re.search(r'create type public.signal_role as enum \(.*?\);', semantics, re.S).group())
            conn.execute(re.search(r'alter table public.signals\s+add column signal_role.*?;', semantics, re.S).group())
            conn.execute(re.search(r'alter table public.signals\s+add column event_matching_eligible.*?;', eligibility, re.S).group())
            for ddl in re.findall(r'alter table public.extraction_runs\s+.*?;', tokens, re.S):
                conn.execute(ddl)
            snapshots = (migrations / '20261102120000_extraction_snapshot_promotion.sql').read_text(encoding='utf-8')
            # Disposable cluster roles only, so execute the complete migration,
            # including RLS/grants rather than a fixture-only table substitute.
            for role in ('anon', 'authenticated', 'service_role'):
                if not conn.execute('select 1 from pg_roles where rolname=%s', (role,)).fetchone():
                    conn.execute(sql.SQL('create role {}').format(sql.Identifier(role)))
            conn.commit()
            conn.autocommit = True
            conn.execute(snapshots)
            conn.autocommit = False
            source = conn.execute("insert into public.sources(code,name,kind,ingestion) values('synthetic','Synthetic','primary_official','manual') returning id").fetchone()[0]
            raw = conn.execute("insert into public.raw_items(source_id,url,content_sha256) values(%s,'https://example.invalid/synthetic','synthetic-hash') returning id", (source,)).fetchone()[0]
            fixture = artifacts()
            conn.execute('insert into public.raw_item_payloads(raw_item_id,raw_text) values(%s,%s)', (raw, fixture['raw_text']))
        payload = json.loads(fixture['signals_bytes'])
        payload['document']['raw_item_id'] = str(raw)
        payload['signals'][0]['hosts'] = []
        payload['signals'][0]['locations'] = []
        validate_extraction(payload)
        yield ExtractionRepository(dsn), dsn, str(raw), payload
    finally:
        with psycopg.connect(ADMIN, autocommit=True) as admin:
            admin.execute(sql.SQL('drop database {} with (force)').format(sql.Identifier(name)))


def persist(repo, raw, payload):
    return repo.persist_extraction(raw_item_id=raw, payload=payload, provider='synthetic',
        model_name='synthetic', response_id='synthetic-response', input_char_count=10,
        usage={'input_tokens': 12, 'output_tokens': 4})


def snapshot(dsn):
    with psycopg.connect(dsn) as conn:
        return {table: conn.execute(sql.SQL('select row_to_json(t) from public.{} t order by id').format(sql.Identifier(table))).fetchall()
                for table in ('raw_items', 'extraction_runs', 'signals', 'signal_metrics', 'signal_evidence')}


def fail_new_evidence(dsn):
    with psycopg.connect(dsn) as conn:
        conn.execute('alter table public.signal_evidence add constraint synthetic_evidence_failure check(false) not valid')


def test_success_persists_complete_signal_tree(extraction_transaction_database):
    repo, dsn, raw, payload = extraction_transaction_database
    run, _ = persist(repo, raw, payload)
    state = snapshot(dsn)
    assert state['raw_items'][0][0]['processing_status'] == 'processed'
    assert len(state['extraction_runs']) == len(state['signals']) == 1
    assert len(state['signal_metrics']) == len(state['signal_evidence']) == 1
    stored_run = state['extraction_runs'][0][0]
    signal = state['signals'][0][0]
    assert stored_run['id'] == run and stored_run['status'] == 'succeeded'
    assert stored_run['output_json'] == payload
    assert signal['raw_item_id'] == raw and signal['extraction_run_id'] == run
    assert signal['version'] == 1 and signal['is_current'] is False
    assert stored_run['snapshot_policy'] == 'document-v1'
    assert state['signal_metrics'][0][0]['signal_id'] == signal['id']
    assert state['signal_evidence'][0][0]['signal_id'] == signal['id']


def test_sequential_candidates_retain_history_without_semantic_supersedes(extraction_transaction_database):
    repo, dsn, raw, payload = extraction_transaction_database
    first_run, _ = persist(repo, raw, payload)
    before = snapshot(dsn)
    first_signal = before['signals'][0][0]
    second_run, _ = persist(repo, raw, payload)
    after = snapshot(dsn)
    signals = sorted((row[0] for row in after['signals']), key=lambda s: s['version'])
    assert len(after['extraction_runs']) == len(signals) == 2
    assert first_run != second_run
    assert signals[0]['id'] == first_signal['id'] and signals[0]['is_current'] is False
    assert signals[1]['version'] == 2 and signals[1]['is_current'] is False
    assert signals[1]['supersedes_signal_id'] is None
    assert signals[1]['extraction_run_id'] == second_run
    assert len(after['signal_metrics']) == len(after['signal_evidence']) == 2
    assert next(row for row in after['extraction_runs'] if row[0]['id'] == first_run) == before['extraction_runs'][0]


def test_child_failure_rolls_back_new_run_and_signal(extraction_transaction_database):
    repo, dsn, raw, payload = extraction_transaction_database
    before = snapshot(dsn)
    fail_new_evidence(dsn)
    with pytest.raises(psycopg.errors.CheckViolation):
        persist(repo, raw, payload)
    assert snapshot(dsn) == before


def test_replacement_failure_preserves_previous_current_version(extraction_transaction_database):
    repo, dsn, raw, payload = extraction_transaction_database
    run, _ = persist(repo, raw, payload)
    repo.promote_extraction_snapshot(raw_item_id=raw, run_id=run, expected_revision=0,
        actor='synthetic-reviewer', reason='synthetic acceptance')
    before = snapshot(dsn)
    fail_new_evidence(dsn)
    with pytest.raises(psycopg.errors.CheckViolation):
        persist(repo, raw, payload)
    assert snapshot(dsn) == before


def test_failure_records_retain_usage_history_without_processing_source(extraction_transaction_database):
    repo, dsn, raw, _ = extraction_transaction_database
    common = dict(raw_item_id=raw, schema_version='synthetic', provider='synthetic',
        model_name='synthetic', input_char_count=10)
    first = repo.record_failed_run(**common, error_text='previous synthetic failure')
    previous = snapshot(dsn)
    second = repo.record_failed_run(**common, error_text='x' * 10050,
        response_id='synthetic-response', usage={'input_tokens': 0, 'output_tokens': 4})
    after = snapshot(dsn)
    assert first != second and len(after['extraction_runs']) == 2
    current = next(row[0] for row in after['extraction_runs'] if row[0]['id'] == second)
    assert current['status'] == 'failed' and len(current['error_text']) == 10000
    assert current['response_id'] == 'synthetic-response'
    assert current['input_tokens'] == 0 and current['output_tokens'] == 4
    assert current['cached_input_tokens'] is None
    assert next(row for row in after['extraction_runs'] if row[0]['id'] == first) == previous['extraction_runs'][0]
    assert after['raw_items'] == previous['raw_items']
    assert after['raw_items'][0][0]['processing_status'] == 'queued'
    assert after['signals'] == after['signal_metrics'] == after['signal_evidence'] == []
