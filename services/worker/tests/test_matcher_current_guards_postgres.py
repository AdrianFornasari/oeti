"""Automatic relation writes must recheck current/eligible endpoints."""
import os

import psycopg
import pytest

from onehealth_worker.evaluation.event_matching_repository_v049 import EventMatchingRepository
from test_extraction_persistence_postgres import extraction_transaction_database, persist
from test_extraction_snapshot_promotion_postgres import two_signals
from test_event_matching_persistence_v049 import _v049_persistable_result

pytestmark = pytest.mark.skipif(os.environ.get('OETI_LOCAL_PG_TESTS') != '1',
    reason='Disposable localhost PostgreSQL not enabled')


@pytest.fixture
def endpoints(extraction_transaction_database):
    repo, dsn, raw, payload = extraction_transaction_database
    run,_=persist(repo,raw,two_signals(payload))
    with psycopg.connect(dsn) as conn:
        # Make eligibility independent of synthetic catalog resolution; this
        # suite tests the storage boundary, not the scientific matcher policy.
        conn.execute('update public.signals set is_current=true,event_matching_eligible=true')
        ids=[str(r[0]) for r in conn.execute('select id from public.signals order by id')]
    return EventMatchingRepository(dsn),dsn,ids


def rows(dsn):
    with psycopg.connect(dsn) as conn:
        return conn.execute('select to_jsonb(r) from public.signal_relations r order by id').fetchall()


def write(repo,ids,batch):
    item=dict(source_signal_id=ids[0],target_signal_id=ids[1],matcher_result=_v049_persistable_result())
    return repo.persist_matcher_relations_batch([item]) if batch else repo.persist_matcher_relation(**item)


@pytest.mark.parametrize('batch',[False,True])
@pytest.mark.parametrize('invalid',['candidate','ineligible','missing'])
@pytest.mark.parametrize('existing',[False,True])
def test_invalid_endpoint_prevents_insert_or_update(endpoints,batch,invalid,existing):
    repo,dsn,ids=endpoints
    if existing:
        write(repo,ids,batch)
    with psycopg.connect(dsn) as conn:
        if invalid=='candidate':
            conn.execute('update public.signals set is_current=false where id=%s',(ids[1],))
        elif invalid=='ineligible':
            conn.execute('update public.signals set event_matching_eligible=false where id=%s',(ids[1],))
        else:
            from uuid import uuid4
            ids[1]=str(uuid4())
    before=rows(dsn)
    with pytest.raises(ValueError,match='current and eligible'):
        write(repo,ids,batch)
    assert rows(dsn)==before


@pytest.mark.parametrize('batch',[False,True])
def test_current_eligible_pair_retains_idempotent_update(endpoints,batch):
    repo,dsn,ids=endpoints
    write(repo,ids,batch)
    before=rows(dsn)
    write(repo,ids,batch)
    assert rows(dsn)==before


def test_batch_rejects_all_pairs_if_one_endpoint_is_staged(endpoints):
    repo,dsn,ids=endpoints
    with psycopg.connect(dsn) as conn:
        candidate=str(conn.execute("""insert into public.signals
            (raw_item_id,local_signal_key,signal_type,signal_summary,extraction_confidence,event_matching_eligible,is_current)
            select raw_item_id,'third','case_report','Synthetic',0.8,true,false
            from public.signals limit 1 returning id""").fetchone()[0])
    before=rows(dsn)
    items=[dict(source_signal_id=ids[0],target_signal_id=target,matcher_result=_v049_persistable_result())
           for target in (ids[1],candidate)]
    with pytest.raises(ValueError,match='current and eligible'):
        repo.persist_matcher_relations_batch(items)
    assert rows(dsn)==before


@pytest.mark.parametrize('batch',[False,True])
def test_waiting_writer_rechecks_committed_retirement(endpoints,batch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from time import monotonic
    repo,dsn,ids=endpoints
    before=rows(dsn)
    with psycopg.connect(dsn) as retiring, psycopg.connect(dsn,autocommit=True) as monitor:
        retiring_pid=retiring.info.backend_pid
        retiring.execute('update public.signals set is_current=false where id=%s',(ids[1],))
        with ThreadPoolExecutor(max_workers=1) as executor:
            future=executor.submit(write,repo,ids,batch)
            deadline=monotonic()+5
            blocked=False
            try:
                while monotonic()<deadline and not future.done():
                    blocked=monitor.execute('select exists(select 1 from pg_stat_activity where %s=any(pg_blocking_pids(pid)))',(retiring_pid,)).fetchone()[0]
                    if blocked:
                        break
                    Event().wait(0.01)
                assert blocked, 'Relation writer did not lock the signal rows'
            finally:
                retiring.commit()
            with pytest.raises(ValueError,match='current and eligible'):
                future.result(timeout=10)
    assert rows(dsn)==before
