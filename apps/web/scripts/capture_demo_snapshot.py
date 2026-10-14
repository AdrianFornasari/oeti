"""Capture the single approved demo event using a read-only transaction.

Run with the worker dependencies and PYTHONPATH pointing to services/worker/src.
Credentials stay in memory; only an explicit allowlist of display fields is saved.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from onehealth_worker.config import Settings

EVENT_ID = 'f3c0aefa-49e9-4553-aa67-ddf5a7cb84f6'
SIGNAL_IDS = {
    '013da99e-5666-4d89-827a-7ce683fa0d02', '4eb9f1fd-d769-4d31-bfb3-a3896f0b0b65',
    '8683a891-4217-4dfe-b2d6-e34ba28a4ea4', '95799c89-1605-4eb2-9f4d-fc3e76c3a11a',
    'dd3474d8-8628-4519-8362-96bae27d5045',
}
RELATION_IDS = {'583a2172-9226-4e29-9ec2-8e3dbe982d24',
                '6d1d9f0a-a2f0-48be-9387-48be304515f8', 'cb994680-0281-496e-a0e4-bb3afec3abd3'}


def capture(env_file, output):
    settings = Settings(_env_file=env_file)
    params = psycopg.conninfo.conninfo_to_dict(settings.database_url)
    project = 'sseahhgekesaybrkckth'
    if project not in params.get('host', '') and project not in params.get('user', ''):
        raise ValueError('Unexpected project')
    with psycopg.connect(settings.database_url, row_factory=dict_row, connect_timeout=10) as conn:
        conn.read_only = True
        conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
        conn.execute("set local statement_timeout = '15s'")
        transaction = conn.execute("select current_setting('transaction_read_only') as read_only, current_setting('transaction_isolation') as isolation").fetchone()
        assert transaction == {'read_only': 'on', 'isolation': 'repeatable read'}
        event = conn.execute('''select id, event_code, title, event_start_date,
            first_signal_at, to_jsonb(domains_present) as domains, lifecycle_status,
            priority, evidence_confidence, cross_sector_convergence, review_status,
            contradictions_present, created_at, updated_at
            from public.events where id = %s''', (EVENT_ID,)).fetchone()
        memberships = conn.execute('''select signal_id, relation_to_event, match_decision,
            match_score, linked_at from public.event_signals where event_id = %s
            order by signal_id''', (EVENT_ID,)).fetchall()
        assert event and {str(m['signal_id']) for m in memberships} == SIGNAL_IDS
        signals = conn.execute('''select s.id, s.raw_item_id, s.signal_type,
            s.signal_summary as summary, to_jsonb(s.domains) as domains,
            s.occurred_start, s.occurred_end, s.date_precision, s.review_status,
            s.verification_status, s.extractor_version, s.model_name,
            r.title as source_title, r.url as source_url, r.published_at,
            r.created_at as source_recorded_at
            from public.signals s join public.raw_items r on r.id = s.raw_item_id
            where s.id = any(%s::uuid[]) order by r.published_at nulls last, s.id''',
            (sorted(SIGNAL_IDS),)).fetchall()
        evidence = conn.execute('''select id, signal_id, excerpt, document_locator,
            page_number, char_start, char_end, evidence_hash
            from public.signal_evidence where signal_id = any(%s::uuid[])
            order by signal_id, id''', (sorted(SIGNAL_IDS),)).fetchall()
        relations = conn.execute('''select id, source_signal_id, target_signal_id,
            relation, score, hard_conflict,
            rationale->>'matcher_version' as matcher_version
            from public.signal_relations where id = any(%s::uuid[]) order by id''',
            (sorted(RELATION_IDS),)).fetchall()
        assert len(signals) == 5 and {str(r['id']) for r in relations} == RELATION_IDS
        assert all(str(r[k]) in SIGNAL_IDS for r in relations for k in ('source_signal_id', 'target_signal_id'))
    snapshot = {
        'schema_version': 1, 'captured_at': datetime.now(timezone.utc).isoformat(),
        'mode': 'frozen_readonly', 'implementation_base': 'caa2598ccd87ee4fb09679a3b14d2ec8e6947e49',
        'extraction_commit': None, 'transaction': transaction,
        'provenance': {
            'event': 'public.events', 'memberships': 'public.event_signals',
            'signals': 'public.signals + public.raw_items (source_* and published_at)',
            'evidence': 'public.signal_evidence', 'relations': 'public.signal_relations',
            'extraction_commit': 'Not recorded in the source rows; implementation_base is not the extraction commit',
        },
        'event': event, 'memberships': memberships, 'signals': signals,
        'evidence': evidence, 'relations': relations,
    }
    serialized = json.dumps(snapshot, ensure_ascii=False, indent=2, default=str) + '\n'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialized, encoding='utf-8')
    print(json.dumps({'signals': len(signals), 'relations': len(relations),
                      'evidence': len(evidence), 'sha256': hashlib.sha256(serialized.encode()).hexdigest()}))


if __name__ == '__main__':
    try:
        capture(sys.argv[1], Path(sys.argv[2]))
    except Exception as error:
        # Connection and validation errors may contain a DSN or host credentials.
        print(f'Capture failed: {type(error).__name__}; details suppressed', file=sys.stderr)
        sys.exit(1)
