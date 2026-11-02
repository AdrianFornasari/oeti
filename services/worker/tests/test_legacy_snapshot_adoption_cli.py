import sys
from types import SimpleNamespace

import pytest

from onehealth_worker import __main__ as cli, config
from onehealth_worker.extraction import repository

RAW = '00000000-0000-4000-8000-000000000001'
RUN = '00000000-0000-4000-8000-000000000002'
HASH = 'a'*64


def arguments():
    return ['worker','adopt-legacy-snapshot','--raw-item-id',RAW,'--run-id',RUN,
            '--expected-revision','0','--expected-state-sha256',HASH,
            '--actor','synthetic','--reason','register baseline']


def test_adoption_requires_execute_before_settings(monkeypatch):
    def forbidden():
        raise AssertionError('Must not load settings')
    monkeypatch.setattr(config,'Settings',forbidden)
    monkeypatch.setattr(sys,'argv',arguments())
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2


def test_adoption_cli_passes_reviewed_state(monkeypatch):
    calls = []
    class FakeRepository:
        def __init__(self,dsn):
            assert dsn == 'unused'
        def adopt_legacy_snapshot(self,**kwargs):
            calls.append(kwargs)
            return {'status':'legacy_adopted'}
    monkeypatch.setattr(config,'Settings',lambda:SimpleNamespace(database_url='unused'))
    monkeypatch.setattr(repository,'ExtractionRepository',FakeRepository)
    monkeypatch.setattr(sys,'argv',arguments()+['--execute'])
    cli.main()
    assert calls == [dict(raw_item_id=RAW,run_id=RUN,expected_revision=0,
                         expected_state_sha256=HASH,actor='synthetic',reason='register baseline')]


def test_plan_cli_calls_only_readonly_method(monkeypatch):
    calls = []
    class FakeRepository:
        def __init__(self,dsn):
            assert dsn == 'unused'
        def plan_legacy_snapshot_adoption(self,**kwargs):
            calls.append(kwargs)
            return {'status':'planned'}
    monkeypatch.setattr(config,'Settings',lambda:SimpleNamespace(database_url='unused'))
    monkeypatch.setattr(repository,'ExtractionRepository',FakeRepository)
    monkeypatch.setattr(sys,'argv',['worker','plan-legacy-snapshot-adoption','--raw-item-id',RAW,'--run-id',RUN])
    cli.main()
    assert calls == [dict(raw_item_id=RAW,run_id=RUN)]


@pytest.mark.parametrize('revision,state_hash', [(1,HASH),(-1,HASH),(True,HASH),(0,''),(0,'A'*64),(0,None)])
def test_invalid_adoption_request_does_not_connect(monkeypatch,revision,state_hash):
    def forbidden(self):
        raise AssertionError('Invalid request must not connect')
    monkeypatch.setattr(repository.ExtractionRepository,'connection',forbidden)
    with pytest.raises(ValueError):
        repository.ExtractionRepository('unused').adopt_legacy_snapshot(raw_item_id=RAW,
            run_id=RUN,expected_revision=revision,expected_state_sha256=state_hash,actor='x',reason='y')
