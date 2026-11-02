import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import psycopg
import pytest

from test_extraction_persistence_postgres import extraction_transaction_database, persist
from test_extraction_snapshot_promotion_postgres import state, two_signals, promote

pytestmark = pytest.mark.skipif(os.environ.get('OETI_LOCAL_PG_TESTS') != '1',
    reason='Disposable localhost PostgreSQL not enabled')


@pytest.fixture
def legacy_database(extraction_transaction_database):
    repo, dsn, raw, payload = extraction_transaction_database
    migration = Path(__file__).resolve().parents[3] / 'supabase/migrations/20261102160000_legacy_snapshot_adoption_audit.sql'
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(migration.read_text(encoding='utf-8'))
    run, _ = persist(repo, raw, two_signals(payload))
    with psycopg.connect(dsn) as conn:
        conn.execute('update public.extraction_runs set snapshot_policy=null where id=%s',(run,))
        conn.execute('update public.signals set is_current=true where extraction_run_id=%s',(run,))
    return repo, dsn, raw, payload, run


def plan(repo, raw, run):
    return repo.plan_legacy_snapshot_adoption(raw_item_id=raw, run_id=run)


def adopt(repo, raw, run, expected):
    return repo.adopt_legacy_snapshot(raw_item_id=raw,run_id=run,expected_revision=0,
        expected_state_sha256=expected['expected_state_sha256'],actor='synthetic-operator',
        reason='Register unchanged technical baseline')


def test_plan_is_readonly_and_adoption_preserves_history_reviews_and_links(legacy_database):
    repo, dsn, raw, payload, run = legacy_database
    with psycopg.connect(dsn) as conn:
        ids = [row[0] for row in conn.execute('select id from public.signals order by id')]
        conn.execute("update public.signals set review_status='reviewed',reviewed_at=now() where id=%s",(ids[0],))
        event = conn.execute("insert into public.events(event_code,title) values('synthetic','Synthetic') returning id").fetchone()[0]
        conn.execute("insert into public.event_signals(event_id,signal_id,match_decision) values(%s,%s,'manual_linked')",(event,ids[0]))
        conn.execute("insert into public.signal_relations(source_signal_id,target_signal_id,relation) values(%s,%s,'possibly_related')",ids)
    before = state(dsn)
    expected = plan(repo, raw, run)
    assert state(dsn) == before
    assert expected['signal_count'] == 2 and expected['event_memberships'] == expected['relations'] == 1
    result = adopt(repo, raw, run, expected)
    assert result['signals_changed'] is False and result['scientific_acceptance'] is False
    after = state(dsn)
    for table in before:
        if table not in ('extraction_snapshot_heads','extraction_snapshot_promotions'):
            assert after[table] == before[table]
    audit = after['extraction_snapshot_promotions'][0][0]
    assert audit['operation'] == 'legacy_adoption'
    assert audit['baseline_state_sha256'] == expected['expected_state_sha256']
    assert audit['previous_run_id'] is None
    candidate, _ = persist(repo, raw, payload)
    with pytest.raises(ValueError,match='Human review'):
        promote(repo,raw,candidate,1)


@pytest.mark.parametrize('change', ['signal','source','evidence','event_link','relation'])
def test_changed_plan_rejected_without_adoption(legacy_database, change):
    repo, dsn, raw, _, run = legacy_database
    expected = plan(repo,raw,run)
    with psycopg.connect(dsn) as conn:
        ids = [row[0] for row in conn.execute('select id from public.signals order by id')]
        if change == 'signal':
            conn.execute("update public.signals set review_status='in_review' where id=%s",(ids[0],))
        elif change == 'source':
            conn.execute("update public.raw_items set title='Changed source metadata' where id=%s",(raw,))
        elif change == 'evidence':
            conn.execute("update public.signal_evidence set excerpt=excerpt || ' changed' where signal_id=%s",(ids[0],))
        elif change == 'event_link':
            event = conn.execute("insert into public.events(event_code,title) values('synthetic','Synthetic') returning id").fetchone()[0]
            conn.execute("insert into public.event_signals(event_id,signal_id,match_decision) values(%s,%s,'auto_linked')",(event,ids[0]))
        else:
            conn.execute("insert into public.signal_relations(source_signal_id,target_signal_id,relation) values(%s,%s,'possibly_related')",ids)
    before = state(dsn)
    with pytest.raises(ValueError,match='changed since planning'):
        adopt(repo,raw,run,expected)
    assert state(dsn) == before


def test_audit_failure_rolls_back_head(legacy_database):
    repo, dsn, raw, _, run = legacy_database
    expected = plan(repo,raw,run)
    with psycopg.connect(dsn) as conn:
        conn.execute('alter table public.extraction_snapshot_promotions add constraint synthetic_failure check(false) not valid')
    before = state(dsn)
    with pytest.raises(psycopg.errors.CheckViolation):
        adopt(repo,raw,run,expected)
    assert state(dsn) == before


def test_concurrent_adoption_has_one_winner(legacy_database):
    repo, dsn, raw, _, run = legacy_database
    expected = plan(repo,raw,run)
    barrier = Barrier(2)
    def attempt(_):
        barrier.wait(timeout=10)
        try:
            return adopt(repo,raw,run,expected)['status']
        except ValueError as exc:
            assert 'head already exists' in str(exc)
            return 'rejected'
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(attempt,range(2))) == ['legacy_adopted','rejected']
    assert len(state(dsn)['extraction_snapshot_promotions']) == 1


@pytest.mark.parametrize('damage',['retired','mixed','failed','candidate','foreign_document','payload_keys','empty'])
def test_invalid_legacy_state_cannot_be_planned(legacy_database,damage):
    repo, dsn, raw, _, run = legacy_database
    with psycopg.connect(dsn) as conn:
        if damage == 'retired':
            conn.execute('update public.signals set is_current=false where id=(select id from public.signals limit 1)')
        elif damage == 'mixed':
            conn.execute('update public.signals set extraction_run_id=null where id=(select id from public.signals limit 1)')
        elif damage == 'failed':
            conn.execute("update public.extraction_runs set status='failed',error_text='synthetic failure' where id=%s",(run,))
        elif damage == 'candidate':
            conn.execute("update public.extraction_runs set snapshot_policy='document-v1' where id=%s",(run,))
        else:
            payload = conn.execute('select output_json from public.extraction_runs where id=%s',(run,)).fetchone()[0]
            if damage == 'foreign_document':
                payload['document']['raw_item_id'] = '00000000-0000-4000-8000-000000000001'
            elif damage == 'payload_keys':
                payload['signals'][1]['local_signal_id'] = payload['signals'][0]['local_signal_id']
            else:
                payload['signals'] = []
            from psycopg.types.json import Jsonb
            conn.execute('update public.extraction_runs set output_json=%s where id=%s',(Jsonb(payload),run))
    before = state(dsn)
    with pytest.raises(ValueError):
        plan(repo,raw,run)
    assert state(dsn) == before


def test_normal_promotion_keeps_its_audit_category(legacy_database):
    repo, dsn, raw, payload, run = legacy_database
    adopt(repo,raw,run,plan(repo,raw,run))
    candidate, _ = persist(repo,raw,payload)
    promote(repo,raw,candidate,1)
    audit = state(dsn)['extraction_snapshot_promotions']
    assert {r[0]['operation'] for r in audit} == {'legacy_adoption','candidate_promotion'}
    assert next(r[0] for r in audit if r[0]['operation']=='candidate_promotion')['baseline_state_sha256'] is None


def test_adoption_does_not_bypass_link_guard_for_future_replacement(legacy_database):
    repo, dsn, raw, payload, run = legacy_database
    with psycopg.connect(dsn) as conn:
        ids = [r[0] for r in conn.execute('select id from public.signals order by id')]
        conn.execute("insert into public.signal_relations(source_signal_id,target_signal_id,relation) values(%s,%s,'possibly_related')",ids)
    adopt(repo,raw,run,plan(repo,raw,run))
    candidate, _ = persist(repo,raw,payload)
    before = state(dsn)
    with pytest.raises(ValueError,match='links'):
        promote(repo,raw,candidate,1)
    assert state(dsn) == before


def test_missing_adoption_migration_rolls_back_head(legacy_database):
    repo, dsn, raw, _, run = legacy_database
    expected = plan(repo,raw,run)
    with psycopg.connect(dsn) as conn:
        conn.execute('alter table public.extraction_snapshot_promotions drop column operation, drop column baseline_state_sha256')
    before = state(dsn)
    with pytest.raises(psycopg.errors.UndefinedColumn):
        adopt(repo,raw,run,expected)
    assert state(dsn) == before
