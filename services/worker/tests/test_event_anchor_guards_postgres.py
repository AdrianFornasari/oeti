"""Revalidate the positive membership underlying a planned attachment."""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from time import monotonic

import psycopg
import pytest

from onehealth_worker.evaluation.event_matching_repository_v049 import EventMatchingRepository
from test_extraction_persistence_postgres import extraction_transaction_database, persist
from test_extraction_snapshot_promotion_postgres import two_signals
from test_event_matching_persistence_v049 import _v049_persistable_result

pytestmark=pytest.mark.skipif(os.environ.get('OETI_LOCAL_PG_TESTS')!='1',reason='Disposable localhost PostgreSQL not enabled')


@pytest.fixture
def attachment(extraction_transaction_database):
    extraction,dsn,raw,payload=extraction_transaction_database
    persist(extraction,raw,two_signals(payload))
    with psycopg.connect(dsn) as conn:
        conn.execute('update public.signals set is_current=true,event_matching_eligible=true')
        ids=[str(r[0]) for r in conn.execute('select id from public.signals order by id')]
    repo=EventMatchingRepository(dsn)
    relation=repo.persist_matcher_relation(source_signal_id=ids[0],target_signal_id=ids[1],matcher_result=_v049_persistable_result())
    source,target=relation['source_signal_id'],relation['target_signal_id']
    with psycopg.connect(dsn) as conn:
        event=str(conn.execute("insert into public.events(event_code,title,lifecycle_status) values('synthetic-anchor','Synthetic','active') returning id").fetchone()[0])
        conn.execute("insert into public.event_signals(event_id,signal_id,match_decision) values(%s,%s,'manual_linked')",(event,source))
    item={'assignment_plan':{'action':'attach_target_to_event','event_id':event,'signal_ids':[target],
                            'write_allowed':True,'reason':'Synthetic positive anchor'},
          'signal_relation_id':relation['signal_relation_id']}
    return repo,dsn,item,source,target


def write(repo,item,batch):
    return repo.persist_event_signal_attachments_batch([item]) if batch else repo.persist_event_signal_attachment(**item)


def memberships(dsn):
    with psycopg.connect(dsn) as conn:
        return conn.execute('select to_jsonb(e) from public.event_signals e order by event_id,signal_id').fetchall()


@pytest.mark.parametrize('batch',[False,True])
@pytest.mark.parametrize('change',['removed','manual_unlinked','review_required','wrong_event','wrong_direction'])
def test_stale_anchor_or_direction_cannot_attach(attachment,batch,change):
    repo,dsn,item,source,target=attachment
    event=item['assignment_plan']['event_id']
    with psycopg.connect(dsn) as conn:
        if change=='removed':
            conn.execute('delete from public.event_signals')
        elif change in ('manual_unlinked','review_required'):
            conn.execute('update public.event_signals set match_decision=%s',(change,))
        elif change=='wrong_event':
            other=str(conn.execute("insert into public.events(event_code,title,lifecycle_status) values('other','Other','active') returning id").fetchone()[0])
            item['assignment_plan']['event_id']=other
        else:
            item['assignment_plan']['action']='attach_source_to_event'
    before=memberships(dsn)
    with pytest.raises(ValueError,match='anchor membership changed|direction'):
        write(repo,item,batch)
    assert memberships(dsn)==before


@pytest.mark.parametrize('batch',[False,True])
@pytest.mark.parametrize('decision',['auto_linked','manual_linked'])
def test_positive_anchor_allows_idempotent_attachment(attachment,batch,decision):
    repo,dsn,item,source,target=attachment
    with psycopg.connect(dsn) as conn:
        conn.execute('update public.event_signals set match_decision=%s',(decision,))
    write(repo,item,batch)
    before=memberships(dsn)
    assert len(before)==2
    write(repo,item,batch)
    assert memberships(dsn)==before


@pytest.mark.parametrize('batch',[False,True])
def test_waiting_attachment_rechecks_deleted_anchor(attachment,batch):
    repo,dsn,item,source,target=attachment
    with psycopg.connect(dsn) as removing,psycopg.connect(dsn,autocommit=True) as monitor:
        removing.execute('delete from public.event_signals')
        pid=removing.info.backend_pid
        with ThreadPoolExecutor(max_workers=1) as executor:
            future=executor.submit(write,repo,item,batch)
            blocked=False
            deadline=monotonic()+5
            try:
                while monotonic()<deadline and not future.done():
                    blocked=monitor.execute('select exists(select 1 from pg_stat_activity where %s=any(pg_blocking_pids(pid)))',(pid,)).fetchone()[0]
                    if blocked:
                        break
                    Event().wait(.01)
                assert blocked,'Attachment did not lock the anchor membership'
            finally:
                removing.commit()
            with pytest.raises(ValueError,match='anchor membership changed'):
                future.result(timeout=10)
    assert memberships(dsn)==[]


def test_second_stale_anchor_rolls_back_first_attachment(attachment):
    import copy
    from uuid import UUID
    repo,dsn,item,source,target=attachment
    # Batch order is event_id/signal_id. Ensure the valid attachment executes
    # first, then make the second event lack its required anchor membership.
    first_event=item['assignment_plan']['event_id']
    second_event=str(UUID(int=UUID(first_event).int+1))
    with psycopg.connect(dsn) as conn:
        conn.execute("insert into public.events(id,event_code,title,lifecycle_status) values(%s,'second','Second','active')",(second_event,))
    second=copy.deepcopy(item)
    second['assignment_plan']['event_id']=second_event
    before=memberships(dsn)
    with pytest.raises(ValueError,match='anchor membership changed'):
        repo.persist_event_signal_attachments_batch([item,second])
    assert memberships(dsn)==before
