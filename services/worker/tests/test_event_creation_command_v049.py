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


def test_validate_plan_uses_read_only_executor(monkeypatch):
    connection = SimpleNamespace(read_only=False, isolation_level=None)
    plan = {'mode': 'plan_only'}

    @contextmanager
    def connect(*args, **kwargs): yield connection

    class Executor:
        def __init__(self, repository): self.repository = repository
        def execute_planned_cohort(self, *, report, expected_event_code, dry_run):
            assert report is plan
            assert expected_event_code == 'reviewed'
            assert dry_run is True
            assert connection.read_only is True
            assert connection.isolation_level == psycopg.IsolationLevel.REPEATABLE_READ
            assert self.repository.event_creation_writes_enabled is False
            with self.repository.connection() as conn: assert conn is connection
            return {'status': 'already_exists', 'dry_run': True}

    monkeypatch.setattr(command.psycopg, 'connect', connect)
    monkeypatch.setattr(command, 'EventCreationExecutor', Executor)
    assert command.validate_event_creation_plan('unused', plan, 'reviewed')['status'] == 'already_exists'


def test_cli_validates_selected_plan_and_preserves_input(monkeypatch, capsys, tmp_path):
    from onehealth_worker import config
    monkeypatch.setattr(config, 'Settings', lambda: SimpleNamespace(database_url='unused'))
    plan_path, output = tmp_path / 'plan.json', tmp_path / 'validation.json'
    original = '{"mode":"plan_only"}'
    plan_path.write_text(original, encoding='utf-8')
    def validate(dsn, report, code):
        assert dsn == 'unused' and report == {'mode': 'plan_only'} and code == 'reviewed'
        return {'status': 'blocked', 'dry_run': True, 'reason': 'current-state'}
    monkeypatch.setattr(command, 'validate_event_creation_plan', validate)
    monkeypatch.setattr('sys.argv', ['worker', 'validate-event-creation-plan', '--plan-file',
        str(plan_path), '--event-code', 'reviewed', '--output', str(output)])
    cli.main()
    assert json.loads(capsys.readouterr().out) == json.loads(output.read_text(encoding='utf-8'))
    assert plan_path.read_text(encoding='utf-8') == original


@pytest.mark.parametrize('arguments', [[], ['--plan-file', 'plan.json'],
    ['--plan-file', 'plan.json', '--event-code', 'reviewed', '--persist']])
def test_validate_cli_requires_selection_and_has_no_write_flag(arguments):
    with pytest.raises(SystemExit) as exc:
        cli._parser().parse_args(['validate-event-creation-plan', *arguments])
    assert exc.value.code == 2


def test_validate_cli_rejects_overwriting_reviewed_plan(monkeypatch, tmp_path):
    from onehealth_worker import config
    monkeypatch.setattr(config, 'Settings', lambda: SimpleNamespace(database_url='unused'))
    path = tmp_path / 'plan.json'
    path.write_text('{"mode":"plan_only"}', encoding='utf-8')
    monkeypatch.setattr('sys.argv', ['worker', 'validate-event-creation-plan', '--plan-file',
        str(path), '--event-code', 'reviewed', '--output', str(path)])
    with pytest.raises(ValueError, match='entrada'):
        cli.main()
    assert path.read_text(encoding='utf-8') == '{"mode":"plan_only"}'


def test_execute_command_defaults_to_existing_read_only_path(monkeypatch):
    calls = []
    def validate(*args):
        calls.append(args)
        return {'status': 'ready_to_create', 'dry_run': True}
    monkeypatch.setattr(command, 'validate_event_creation_plan', validate)
    plan = {'mode': 'plan_only'}
    assert command.execute_event_creation_plan('unused', plan, 'reviewed')['dry_run'] is True
    assert calls == [('unused', plan, 'reviewed')]


def test_execute_command_explicitly_enables_only_its_repository(monkeypatch):
    repositories = []
    class Repository:
        def __init__(self, dsn, *, event_creation_writes_enabled=False):
            assert dsn == 'unused'
            self.enabled = event_creation_writes_enabled
            repositories.append(self)
    class Executor:
        def __init__(self, repository): self.repository = repository
        def execute_planned_cohort(self, **kwargs):
            assert self.repository.enabled is True
            assert kwargs == {'report': {'mode': 'plan_only'}, 'expected_event_code': 'reviewed', 'dry_run': False}
            return {'status': 'created', 'dry_run': False}
    monkeypatch.setattr(command, 'EventMatchingRepository', Repository)
    monkeypatch.setattr(command, 'EventCreationExecutor', Executor)
    assert command.execute_event_creation_plan('unused', {'mode': 'plan_only'}, 'reviewed', execute=True)['status'] == 'created'
    assert len(repositories) == 1


@pytest.mark.parametrize('execute', [False, True])
def test_execute_cli_forwards_explicit_flag_and_preserves_plan(monkeypatch, tmp_path, capsys, execute):
    from onehealth_worker import config
    monkeypatch.setattr(config, 'Settings', lambda: SimpleNamespace(database_url='unused'))
    path, output = tmp_path / 'plan.json', tmp_path / 'result.json'
    original = '{"mode":"plan_only"}'
    path.write_text(original, encoding='utf-8')
    def run(dsn, report, code, *, execute):
        assert dsn == 'unused' and report == {'mode': 'plan_only'} and code == 'reviewed'
        return {'status': 'created' if execute else 'ready_to_create', 'dry_run': not execute}
    monkeypatch.setattr(command, 'execute_event_creation_plan', run)
    arguments = ['worker', 'execute-event-creation-plan', '--plan-file', str(path),
        '--event-code', 'reviewed', '--output', str(output)]
    if execute: arguments.append('--execute')
    monkeypatch.setattr('sys.argv', arguments)
    cli.main()
    result = json.loads(capsys.readouterr().out)
    assert result['dry_run'] is (not execute)
    assert json.loads(output.read_text(encoding='utf-8')) == result
    assert path.read_text(encoding='utf-8') == original


def test_execute_cli_output_failure_does_not_repeat_execution(monkeypatch, tmp_path):
    from onehealth_worker import config
    monkeypatch.setattr(config, 'Settings', lambda: SimpleNamespace(database_url='unused'))
    path = tmp_path / 'plan.json'
    path.write_text('{"mode":"plan_only"}', encoding='utf-8')
    calls = []
    def run(*args, **kwargs):
        calls.append(kwargs)
        return {'status': 'created', 'dry_run': False}
    monkeypatch.setattr(command, 'execute_event_creation_plan', run)
    monkeypatch.setattr('sys.argv', ['worker', 'execute-event-creation-plan', '--plan-file', str(path),
        '--event-code', 'reviewed', '--execute', '--output', str(tmp_path)])
    with pytest.raises(OSError): cli.main()
    assert calls == [{'execute': True}]


def test_execute_cli_rejects_overwriting_plan_before_execution(monkeypatch, tmp_path):
    from onehealth_worker import config
    monkeypatch.setattr(config, 'Settings', lambda: SimpleNamespace(database_url='unused'))
    path = tmp_path / 'plan.json'
    path.write_text('{"mode":"plan_only"}', encoding='utf-8')
    calls = []
    monkeypatch.setattr(command, 'execute_event_creation_plan', lambda *args, **kwargs: calls.append(kwargs))
    monkeypatch.setattr('sys.argv', ['worker', 'execute-event-creation-plan', '--plan-file', str(path),
        '--event-code', 'reviewed', '--execute', '--output', str(path)])
    with pytest.raises(ValueError): cli.main()
    assert calls == []
    assert path.read_text(encoding='utf-8') == '{"mode":"plan_only"}'


@pytest.mark.parametrize('command_name,execute', [
    ('validate-event-creation-plan', False),
    ('execute-event-creation-plan', False),
    ('execute-event-creation-plan', True),
])
def test_cli_rejects_hardlinked_output_before_repository_call(
    monkeypatch, tmp_path, command_name, execute,
):
    from onehealth_worker import config
    monkeypatch.setattr(config, 'Settings', lambda: SimpleNamespace(database_url='unused'))
    plan = tmp_path / 'reviewed-plan.json'
    output = tmp_path / 'result.json'
    original = b'{"mode":"plan_only"}'
    plan.write_bytes(original)
    output.hardlink_to(plan)
    calls = []

    def run(*args, **kwargs):
        calls.append((args, kwargs))
        return {'status': 'created' if execute else 'ready_to_create', 'dry_run': not execute}

    monkeypatch.setattr(command, 'validate_event_creation_plan', run)
    monkeypatch.setattr(command, 'execute_event_creation_plan', run)
    arguments = ['worker', command_name, '--plan-file', str(plan),
                 '--event-code', 'reviewed', '--output', str(output)]
    if execute:
        arguments.append('--execute')
    monkeypatch.setattr('sys.argv', arguments)
    with pytest.raises(ValueError, match='entrada'):
        cli.main()
    assert calls == []
    assert plan.read_bytes() == output.read_bytes() == original


@pytest.mark.parametrize('command_name,execute', [
    ('validate-event-creation-plan', False),
    ('execute-event-creation-plan', False),
    ('execute-event-creation-plan', True),
])
@pytest.mark.parametrize('duplicate_level', ['report', 'seed'])
def test_cli_rejects_duplicate_plan_keys_before_repository_call(
    monkeypatch, tmp_path, command_name, execute, duplicate_level,
):
    from onehealth_worker import config
    from test_event_creation_executor_v049 import report
    monkeypatch.setattr(config, 'Settings', lambda: SimpleNamespace(database_url='unused'))
    original = json.dumps(report())
    if duplicate_level == 'report':
        original = original.replace('"mode": "plan_only"',
                                    '"mode": "other", "mode": "plan_only"')
    else:
        original = original.replace('"event_code": "reviewed-code"',
                                    '"event_code": "other-code", "event_code": "reviewed-code"')
    path = tmp_path / 'plan.json'
    output = tmp_path / 'result.json'
    path.write_text(original, encoding='utf-8')
    calls = []

    def run(*args, **kwargs):
        calls.append((args, kwargs))
        return {'status': 'created' if execute else 'ready_to_create', 'dry_run': not execute}

    monkeypatch.setattr(command, 'validate_event_creation_plan', run)
    monkeypatch.setattr(command, 'execute_event_creation_plan', run)
    arguments = ['worker', command_name, '--plan-file', str(path),
                 '--event-code', 'reviewed-code', '--output', str(output)]
    if execute:
        arguments.append('--execute')
    monkeypatch.setattr('sys.argv', arguments)
    with pytest.raises(ValueError, match='duplicadas'):
        cli.main()
    assert calls == []
    assert path.read_text(encoding='utf-8') == original
    assert not output.exists()


@pytest.mark.parametrize('command_name,execute', [
    ('validate-event-creation-plan', False),
    ('execute-event-creation-plan', False),
    ('execute-event-creation-plan', True),
])
@pytest.mark.parametrize('number', ['NaN', 'Infinity', '-Infinity', '1e999'])
def test_cli_rejects_nonfinite_plan_numbers_before_repository_call(
    monkeypatch, tmp_path, command_name, execute, number,
):
    from onehealth_worker import config
    from test_event_creation_executor_v049 import report
    monkeypatch.setattr(config, 'Settings', lambda: SimpleNamespace(database_url='unused'))
    payload = report()
    payload['cohorts'][0]['event_seed']['confidence'] = 'number-placeholder'
    original = json.dumps(payload).replace('"number-placeholder"', number)
    plan = tmp_path / 'plan.json'
    output = tmp_path / 'result.json'
    plan.write_text(original, encoding='utf-8')
    calls = []

    def run(*args, **kwargs):
        calls.append((args, kwargs))
        return {'status': 'created' if execute else 'ready_to_create', 'dry_run': not execute}

    monkeypatch.setattr(command, 'validate_event_creation_plan', run)
    monkeypatch.setattr(command, 'execute_event_creation_plan', run)
    arguments = ['worker', command_name, '--plan-file', str(plan),
                 '--event-code', 'reviewed-code', '--output', str(output)]
    if execute:
        arguments.append('--execute')
    monkeypatch.setattr('sys.argv', arguments)
    with pytest.raises(ValueError, match='finito'):
        cli.main()
    assert calls == []
    assert plan.read_text(encoding='utf-8') == original
    assert not output.exists()


def test_validate_cli_preserves_finite_decimal_in_plan(monkeypatch, tmp_path, capsys):
    from onehealth_worker import config
    from test_event_creation_executor_v049 import report
    monkeypatch.setattr(config, 'Settings', lambda: SimpleNamespace(database_url='unused'))
    payload = report()
    payload['cohorts'][0]['event_seed']['confidence'] = 0.75
    plan = tmp_path / 'plan.json'
    original = json.dumps(payload)
    plan.write_text(original, encoding='utf-8')
    calls = []

    def validate(dsn, parsed, code):
        calls.append(parsed)
        assert parsed == payload
        assert parsed['cohorts'][0]['event_seed']['confidence'] == 0.75
        return {'status': 'ready_to_create', 'dry_run': True}

    monkeypatch.setattr(command, 'validate_event_creation_plan', validate)
    monkeypatch.setattr('sys.argv', ['worker', 'validate-event-creation-plan',
        '--plan-file', str(plan), '--event-code', 'reviewed-code'])
    cli.main()
    assert len(calls) == 1
    assert json.loads(capsys.readouterr().out)['dry_run'] is True
    assert plan.read_text(encoding='utf-8') == original
