import sys
from types import SimpleNamespace

import pytest

from onehealth_worker import __main__ as cli
from onehealth_worker import config
from onehealth_worker.extraction import repository

RAW = '00000000-0000-4000-8000-000000000001'
RUN = '00000000-0000-4000-8000-000000000002'


def arguments():
    return ['worker', 'promote-extraction-snapshot', '--raw-item-id', RAW, '--run-id', RUN,
            '--expected-revision', '0', '--actor', 'synthetic', '--reason', 'explicit review']


def test_cli_requires_execute_before_loading_settings(monkeypatch):
    monkeypatch.setattr(sys, 'argv', arguments())
    def forbidden():
        raise AssertionError('Settings must not load without explicit --execute')
    monkeypatch.setattr(config, 'Settings', forbidden)
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2


def test_cli_invokes_only_explicit_promotion(monkeypatch):
    calls = []
    class FakeRepository:
        def __init__(self, dsn):
            assert dsn == 'unused'
        def promote_extraction_snapshot(self, **kwargs):
            calls.append(kwargs)
            return {'status': 'promoted', 'revision': 1}
    monkeypatch.setattr(config, 'Settings', lambda: SimpleNamespace(database_url='unused'))
    monkeypatch.setattr(repository, 'ExtractionRepository', FakeRepository)
    monkeypatch.setattr(sys, 'argv', arguments() + ['--execute'])
    cli.main()
    assert calls == [dict(raw_item_id=RAW, run_id=RUN, expected_revision=0, actor='synthetic', reason='explicit review')]


@pytest.mark.parametrize('revision,actor,reason', [(-1, 'x', 'y'), (True, 'x', 'y'), (0, '', 'y'), (0, 'x', ' ')])
def test_invalid_promotion_request_does_not_connect(monkeypatch, revision, actor, reason):
    def forbidden(self):
        raise AssertionError('Invalid request must not connect')
    monkeypatch.setattr(repository.ExtractionRepository, 'connection', forbidden)
    with pytest.raises(ValueError):
        repository.ExtractionRepository('unused').promote_extraction_snapshot(
            raw_item_id=RAW, run_id=RUN, expected_revision=revision, actor=actor, reason=reason)
