import json
from contextlib import contextmanager
from types import SimpleNamespace

import psycopg
import pytest

from onehealth_worker import __main__ as cli
from onehealth_worker.evaluation import event_creation_command_v049 as command


def test_command_plans_in_one_database_read_only_snapshot(monkeypatch):
    calls = []
    connection = SimpleNamespace(read_only=False, isolation_level=None)

    @contextmanager
    def connect(dsn, **kwargs):
        calls.append((dsn, kwargs))
        yield connection

    class Planner:
        def __init__(self, repository):
            self.repository = repository

        def plan_cohorts(self, identifiers):
            assert connection.read_only is True
            assert connection.isolation_level == psycopg.IsolationLevel.REPEATABLE_READ
            assert self.repository.event_creation_writes_enabled is False
            with self.repository.connection() as first:
                with self.repository.connection() as second:
                    assert first is second is connection
            assert identifiers == ['a', 'b']
            return {'mode': 'plan_only', 'summary': {'blocked': 1}}

    monkeypatch.setattr(command.psycopg, 'connect', connect)
    monkeypatch.setattr(command, 'EventCreationPlanner', Planner)
    assert command.plan_event_creation_cohorts('unused', ['a', 'b'])['mode'] == 'plan_only'
    assert len(calls) == 1


def test_cli_outputs_planning_report(monkeypatch, capsys, tmp_path):
    from onehealth_worker import config
    monkeypatch.setattr(config, 'Settings', lambda: SimpleNamespace(database_url='unused'))
    report = {'mode': 'plan_only', 'cohorts': [], 'summary': {'ready_to_create': 0}}
    monkeypatch.setattr(command, 'plan_event_creation_cohorts', lambda dsn, ids: report)
    output = tmp_path / 'report.json'
    monkeypatch.setattr('sys.argv', ['worker', 'plan-event-creation-cohorts', '--relation-id',
                                    '583a2172-9226-4e29-9ec2-8e3dbe982d24', '--output', str(output)])
    cli.main()
    assert json.loads(capsys.readouterr().out) == report
    assert json.loads(output.read_text(encoding='utf-8')) == report


@pytest.mark.parametrize('arguments', [[], ['--relation-id', 'invalid'],
    ['--relation-id', '583a2172-9226-4e29-9ec2-8e3dbe982d24', '--persist']])
def test_cli_rejects_missing_invalid_ids_and_write_flag(arguments):
    with pytest.raises(SystemExit) as exc:
        cli._parser().parse_args(['plan-event-creation-cohorts', *arguments])
    assert exc.value.code == 2
