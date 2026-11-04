"""Explicit registration of an unchanged legacy baseline, never replacement."""
import hashlib
import json
import re

from psycopg import sql

from .schema import validate_extraction, validate_literal_evidence
from .snapshot_promotion import validate_promotion_request


def inspect_legacy_snapshot(conn, *, raw_item_id, run_id):
    with conn.cursor() as cur:
        # Canonical timestamps make the plan independent of session timezone.
        cur.execute("set local timezone='UTC'")
        cur.execute('select to_jsonb(r) as data from public.raw_items r where id=%s', (raw_item_id,))
        raw = cur.fetchone()
        if not raw:
            raise ValueError('Source document does not exist.')
        cur.execute('select 1 from public.extraction_snapshot_heads where raw_item_id=%s', (raw_item_id,))
        if cur.fetchone():
            raise ValueError('A snapshot head already exists; adoption is first registration only.')
        cur.execute('select to_jsonb(r) as data from public.extraction_runs r where id=%s', (run_id,))
        row = cur.fetchone()
        run = row['data'] if row else None
        if (not run or run['raw_item_id'] != raw_item_id or run['status'] != 'succeeded'
                or run['snapshot_policy'] is not None):
            raise ValueError('Run is not a successful legacy extraction for this document.')
        cur.execute('select 1 from public.extraction_snapshot_promotions where run_id=%s', (run_id,))
        if cur.fetchone():
            raise ValueError('Run already has snapshot history.')
        payload = run['output_json']
        validate_extraction(payload)
        if payload['document']['raw_item_id'] != raw_item_id or not payload['signals']:
            raise ValueError('Legacy payload must be nonempty and bound to this document.')
        cur.execute('select to_jsonb(p) as data from public.raw_item_payloads p where raw_item_id=%s', (raw_item_id,))
        source = cur.fetchone()
        if not source or not isinstance(source['data']['raw_text'], str):
            raise ValueError('Legacy source text is missing.')
        validate_literal_evidence(payload, source['data']['raw_text'])
        cur.execute('''select to_jsonb(s) as data from public.signals s
            where extraction_run_id=%s or (raw_item_id=%s and is_current)
            order by id''', (run_id,raw_item_id))
        members = [row['data'] for row in cur.fetchall()]
        keys = [s['local_signal_id'] for s in payload['signals']]
        if (len(members) != len(keys) or len(set(keys)) != len(keys)
                or {s['local_signal_key'] for s in members} != set(keys)
                or any(s['raw_item_id'] != raw_item_id or s['extraction_run_id'] != run_id
                       or not s['is_current'] for s in members)):
            raise ValueError('Legacy membership is incomplete, mixed, or no longer current.')
        ids = [s['id'] for s in members]
        state = {'document':raw['data'],'run':run,'source':source['data'],'signals':members}
        for table in ('signal_metrics','signal_evidence','event_signals'):
            cur.execute(sql.SQL('select to_jsonb(t) as data from public.{} t where signal_id=any(%s::uuid[]) order by to_jsonb(t)::text').format(sql.Identifier(table)),(ids,))
            state[table] = [row['data'] for row in cur.fetchall()]
        cur.execute('''select to_jsonb(r) as data from public.signal_relations r
            where source_signal_id=any(%s::uuid[]) or target_signal_id=any(%s::uuid[])
            order by id''',(ids,ids))
        state['signal_relations'] = [row['data'] for row in cur.fetchall()]
    encoded = json.dumps(state,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')
    return {'status':'planned','raw_item_id':raw_item_id,'run_id':run_id,
            'expected_revision':0,'expected_state_sha256':hashlib.sha256(encoded).hexdigest(),
            'signal_count':len(members),'event_memberships':len(state['event_signals']),
            'relations':len(state['signal_relations'])}


def adopt_legacy_snapshot(conn, *, raw_item_id, run_id, expected_revision,
                          expected_state_sha256, actor, reason):
    with conn.cursor() as cur:
        # Rare operator operation: stop concurrent changes to fingerprinted
        # tables. No row in any of these tables is rewritten by adoption.
        cur.execute("set local lock_timeout='3s'")
        cur.execute('''lock table public.event_signals, public.extraction_runs,
            public.raw_item_payloads, public.raw_items, public.signal_evidence,
            public.signal_metrics, public.signal_relations, public.signals in share mode''')
        cur.execute('select id from public.raw_items where id=%s for update',(raw_item_id,))
        if not cur.fetchone():
            raise ValueError('Source document does not exist.')
    plan = inspect_legacy_snapshot(conn,raw_item_id=raw_item_id,run_id=run_id)
    if plan['expected_state_sha256'] != expected_state_sha256:
        raise ValueError('Legacy state changed since planning; review a new plan.')
    with conn.cursor() as cur:
        cur.execute('insert into public.extraction_snapshot_heads(raw_item_id,run_id,revision) values(%s,%s,1)',(raw_item_id,run_id))
        cur.execute('''insert into public.extraction_snapshot_promotions
            (raw_item_id,revision,previous_run_id,run_id,actor,reason,operation,baseline_state_sha256)
            values(%s,1,null,%s,%s,%s,'legacy_adoption',%s)''',
            (raw_item_id,run_id,actor.strip(),reason.strip(),expected_state_sha256))
    return {'status':'legacy_adopted','raw_item_id':raw_item_id,'run_id':run_id,
            'revision':1,'baseline_state_sha256':expected_state_sha256,
            'signals_changed':False,'scientific_acceptance':False}


def validate_adoption_request(expected_revision, expected_state_sha256, actor, reason):
    validate_promotion_request(expected_revision,actor,reason)
    if expected_revision != 0:
        raise ValueError('Legacy adoption requires expected revision zero.')
    if not isinstance(expected_state_sha256,str) or not re.fullmatch('[0-9a-f]{64}',expected_state_sha256):
        raise ValueError('Legacy adoption requires a reviewed state SHA256.')
