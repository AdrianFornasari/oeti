import copy
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import psycopg
import pytest

from test_extraction_persistence_postgres import extraction_transaction_database, persist, snapshot

pytestmark = pytest.mark.skipif(os.environ.get('OETI_LOCAL_PG_TESTS') != '1',
    reason='Disposable localhost PostgreSQL not enabled')


def promote(repo, raw, run, revision):
    return repo.promote_extraction_snapshot(raw_item_id=raw, run_id=run, expected_revision=revision,
        actor='synthetic-operator', reason='synthetic explicit promotion')


def state(dsn):
    result = snapshot(dsn)
    with psycopg.connect(dsn) as conn:
        for table in ('extraction_snapshot_heads', 'extraction_snapshot_promotions', 'signal_relations'):
            result[table] = conn.execute(f'select to_jsonb(t) from public.{table} t order by to_jsonb(t)::text').fetchall()
        result['event_signals'] = conn.execute('select to_jsonb(t) from public.event_signals t order by event_id,signal_id').fetchall()
    return result


def two_signals(payload):
    result = copy.deepcopy(payload)
    second = copy.deepcopy(result['signals'][0])
    second['local_signal_id'] += '-second'
    second['signal_summary'] = 'Segundo hecho sintético para comprobar el conjunto.'
    result['signals'].append(second)
    return result


def test_staging_does_not_change_promoted_snapshot(extraction_transaction_database):
    repo, dsn, raw, payload = extraction_transaction_database
    first, _ = persist(repo, raw, payload)
    promote(repo, raw, first, 0)
    before = state(dsn)
    second, _ = persist(repo, raw, payload)
    after = state(dsn)
    assert after['extraction_snapshot_heads'] == before['extraction_snapshot_heads']
    assert after['extraction_snapshot_promotions'] == before['extraction_snapshot_promotions']
    assert {r[0]['extraction_run_id'] for r in after['signals'] if r[0]['is_current']} == {first}
    assert all(not r[0]['is_current'] for r in after['signals'] if r[0]['extraction_run_id'] == second)


def test_reduction_promotes_one_complete_run_and_retains_history(extraction_transaction_database):
    repo, dsn, raw, payload = extraction_transaction_database
    first, _ = persist(repo, raw, two_signals(payload))
    promote(repo, raw, first, 0)
    second, _ = persist(repo, raw, payload)
    assert promote(repo, raw, second, 1)['revision'] == 2
    after = state(dsn)
    assert len(after['signals']) == 3
    assert len([r for r in after['signals'] if r[0]['is_current']]) == 1
    assert {r[0]['extraction_run_id'] for r in after['signals'] if r[0]['is_current']} == {second}
    assert len(after['extraction_snapshot_promotions']) == 2


def test_snapshot_tables_have_server_side_permissions(extraction_transaction_database):
    _, dsn, _, _ = extraction_transaction_database
    with psycopg.connect(dsn) as conn:
        for table in ('extraction_snapshot_heads', 'extraction_snapshot_promotions'):
            assert conn.execute('select relrowsecurity from pg_class where oid=%s::regclass', ('public.' + table,)).fetchone()[0]
            for role in ('anon', 'authenticated'):
                assert not conn.execute("select has_table_privilege(%s,%s,'SELECT')", (role, 'public.' + table)).fetchone()[0]
            assert conn.execute("select has_table_privilege('service_role',%s,'INSERT')", ('public.' + table,)).fetchone()[0]
        for operation in ('UPDATE', 'DELETE'):
            assert not conn.execute("select has_table_privilege('service_role','public.extraction_snapshot_promotions',%s)", (operation,)).fetchone()[0]


def test_reordered_ordinals_do_not_create_semantic_supersedes(extraction_transaction_database):
    repo, dsn, raw, payload = extraction_transaction_database
    old = two_signals(payload)
    first, _ = persist(repo, raw, old)
    promote(repo, raw, first, 0)
    new = copy.deepcopy(old)
    a, b = [s['local_signal_id'] for s in new['signals']]
    new['signals'][0]['local_signal_id'], new['signals'][1]['local_signal_id'] = b, a
    second, _ = persist(repo, raw, new)
    promote(repo, raw, second, 1)
    assert all(r[0]['supersedes_signal_id'] is None for r in state(dsn)['signals'])


def test_empty_candidate_cannot_retire_current_snapshot(extraction_transaction_database):
    repo, dsn, raw, payload = extraction_transaction_database
    first, _ = persist(repo, raw, payload)
    promote(repo, raw, first, 0)
    empty = copy.deepcopy(payload)
    empty['signals'] = []
    candidate, _ = persist(repo, raw, empty)
    before = state(dsn)
    with pytest.raises(ValueError, match='Empty'):
        promote(repo, raw, candidate, 1)
    assert state(dsn) == before


@pytest.mark.parametrize('review_status', ['in_review', 'reviewed', 'rejected'])
def test_reviewed_current_snapshot_requires_reconciliation(extraction_transaction_database, review_status):
    repo, dsn, raw, payload = extraction_transaction_database
    first, _ = persist(repo, raw, payload)
    promote(repo, raw, first, 0)
    candidate, _ = persist(repo, raw, payload)
    with psycopg.connect(dsn) as conn:
        conn.execute('update public.signals set review_status=%s where is_current', (review_status,))
    before = state(dsn)
    with pytest.raises(ValueError, match='Human review'):
        promote(repo, raw, candidate, 1)
    assert state(dsn) == before


@pytest.mark.parametrize('link', ['auto_linked', 'manual_linked', 'relation'])
def test_persisted_links_are_preserved_and_block_replacement(extraction_transaction_database, link):
    repo, dsn, raw, payload = extraction_transaction_database
    first, _ = persist(repo, raw, payload)
    promote(repo, raw, first, 0)
    candidate, _ = persist(repo, raw, payload)
    with psycopg.connect(dsn) as conn:
        old = conn.execute('select id from public.signals where is_current').fetchone()[0]
        if link == 'relation':
            new = conn.execute('select id from public.signals where extraction_run_id=%s', (candidate,)).fetchone()[0]
            conn.execute("insert into public.signal_relations(source_signal_id,target_signal_id,relation) values(%s,%s,'possibly_related')", (old, new))
        else:
            event = conn.execute("insert into public.events(event_code,title) values('synthetic','Synthetic') returning id").fetchone()[0]
            conn.execute('insert into public.event_signals(event_id,signal_id,match_decision) values(%s,%s,%s)', (event, old, link))
    before = state(dsn)
    with pytest.raises(ValueError, match='links'):
        promote(repo, raw, candidate, 1)
    assert state(dsn) == before


def test_promotion_audit_failure_rolls_back_all_vigence(extraction_transaction_database):
    repo, dsn, raw, payload = extraction_transaction_database
    first, _ = persist(repo, raw, payload)
    promote(repo, raw, first, 0)
    candidate, _ = persist(repo, raw, payload)
    with psycopg.connect(dsn) as conn:
        conn.execute('alter table public.extraction_snapshot_promotions add constraint synthetic_failure check(false) not valid')
    before = state(dsn)
    with pytest.raises(psycopg.errors.CheckViolation):
        promote(repo, raw, candidate, 1)
    assert state(dsn) == before


def test_legacy_current_signals_are_not_adopted_silently(extraction_transaction_database):
    repo, dsn, raw, payload = extraction_transaction_database
    old, _ = persist(repo, raw, payload)
    with psycopg.connect(dsn) as conn:
        conn.execute('update public.signals set is_current=true where extraction_run_id=%s', (old,))
    candidate, _ = persist(repo, raw, payload)
    before = state(dsn)
    with pytest.raises(ValueError, match='Legacy'):
        promote(repo, raw, candidate, 0)
    assert state(dsn) == before


def test_concurrent_promotions_reject_stale_expected_revision(extraction_transaction_database):
    repo, dsn, raw, payload = extraction_transaction_database
    candidates = [persist(repo, raw, payload)[0] for _ in range(2)]
    barrier = Barrier(2)
    def attempt(run):
        barrier.wait(timeout=10)
        try:
            return promote(repo, raw, run, 0)['status']
        except ValueError as error:
            assert 'Stale' in str(error)
            return 'stale'
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(attempt, candidates)) == ['promoted', 'stale']
    assert len(state(dsn)['extraction_snapshot_promotions']) == 1


def test_foreign_run_and_incomplete_candidate_are_rejected(extraction_transaction_database):
    repo, dsn, raw, payload = extraction_transaction_database
    candidate, _ = persist(repo, raw, payload)
    with pytest.raises(ValueError, match='complete candidate'):
        promote(repo, raw, str(uuid4()), 0)
    with psycopg.connect(dsn) as conn:
        other = conn.execute("insert into public.raw_items(source_id,url,content_sha256) select source_id,'https://example.invalid/other','other-hash' from public.raw_items where id=%s returning id", (raw,)).fetchone()[0]
    with pytest.raises(ValueError, match='complete candidate'):
        promote(repo, str(other), candidate, 0)
    with psycopg.connect(dsn) as conn:
        conn.execute('delete from public.signal_evidence')
        conn.execute('delete from public.signal_metrics')
        conn.execute('delete from public.signals')
    before = state(dsn)
    with pytest.raises(ValueError, match='membership'):
        promote(repo, raw, candidate, 0)
    assert state(dsn) == before


def test_historical_run_cannot_be_repromoted_implicitly(extraction_transaction_database):
    repo, dsn, raw, payload = extraction_transaction_database
    old, _ = persist(repo, raw, payload)
    promote(repo, raw, old, 0)
    new, _ = persist(repo, raw, payload)
    promote(repo, raw, new, 1)
    before = state(dsn)
    with pytest.raises(ValueError, match='already been promoted'):
        promote(repo, raw, old, 2)
    assert state(dsn) == before


def test_failed_run_cannot_be_promoted(extraction_transaction_database):
    repo, dsn, raw, _ = extraction_transaction_database
    run = repo.record_failed_run(raw_item_id=raw, schema_version='synthetic', provider='synthetic',
        model_name='synthetic', input_char_count=0, error_text='synthetic failure')
    before = state(dsn)
    with pytest.raises(ValueError, match='complete candidate'):
        promote(repo, raw, run, 0)
    assert state(dsn) == before
