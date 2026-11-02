"""Token persistence against disposable localhost PostgreSQL only."""
import os

import psycopg
from psycopg import sql
import pytest

import copy
from test_extraction_persistence_postgres import extraction_transaction_database
from onehealth_worker.extraction.token_usage import TOKEN_USAGE_KEYS

pytestmark = pytest.mark.skipif(os.environ.get('OETI_LOCAL_PG_TESTS') != '1',
    reason='Disposable localhost PostgreSQL not enabled')
@pytest.fixture
def extraction_database(extraction_transaction_database):
    repository, _, raw_id, payload = extraction_transaction_database
    historical = repository.record_failed_run(raw_item_id=raw_id, schema_version='test',
        provider='test', model_name='test', input_char_count=0, error_text='historical')
    return repository, raw_id, historical, payload


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
    repository, raw_id, historical, fixture_payload = extraction_database
    common = dict(raw_item_id=raw_id, provider='test', model_name='test',
        response_id='response-id', input_char_count=4, usage=usage)
    if status == 'failed':
        run_id = repository.record_failed_run(**common, schema_version='test', error_text='validation')
    else:
        payload = copy.deepcopy(fixture_payload)
        payload['signals'] = []
        run_id, _ = repository.persist_extraction(**common, payload=payload)
    assert read_usage(repository, run_id) == expected
    assert read_usage(repository, historical) == (None,)*5


@pytest.mark.parametrize('key', TOKEN_USAGE_KEYS)
def test_postgres_migration_rejects_negative_counts(extraction_database, key):
    repository, _, historical, _ = extraction_database
    with pytest.raises(psycopg.errors.CheckViolation):
        with repository.connection() as conn:
            conn.execute(sql.SQL('update public.extraction_runs set {}=-1 where id=%s').format(sql.Identifier(key)), (historical,))
    assert read_usage(repository, historical) == (None,)*5
