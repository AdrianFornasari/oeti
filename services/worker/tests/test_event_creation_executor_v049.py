from copy import deepcopy
from uuid import uuid4

import pytest

from onehealth_worker.evaluation.event_creation_executor_v049 import EventCreationExecutor


def report():
    signals = [str(uuid4()), str(uuid4())]
    relations = [str(uuid4())]
    return {'mode': 'plan_only', 'cohorts': [{
        'cohort': {'signal_ids': signals, 'signal_relation_ids': relations},
        'event_seed': {'event_code': 'reviewed-code', 'source_signal_ids': signals,
                       'source_relation_ids': relations, 'title': 'reviewed-title'},
        'validation': {'status': 'ready_to_create', 'dry_run': True},
    }]}


class Repository:
    def __init__(self, result):
        self.result = result
        self.calls = []
        self.event_creation_writes_enabled = False
    def persist_event_creation_cohort(self, **kwargs):
        self.calls.append(kwargs)
        if not kwargs['dry_run'] and not self.event_creation_writes_enabled:
            raise RuntimeError('writes not enabled')
        return self.result


@pytest.mark.parametrize('dry_run,status', [(True, 'ready_to_create'), (True, 'already_exists'),
    (True, 'blocked'), (False, 'created'), (False, 'already_exists'), (False, 'blocked')])
def test_executor_preserves_seed_and_current_repository_result(dry_run, status):
    plan = report()
    original = deepcopy(plan)
    repository = Repository({'status': status, 'reason': 'current', 'event_id': 'current'})
    repository.event_creation_writes_enabled = not dry_run
    result = EventCreationExecutor(repository).execute_planned_cohort(
        report=plan, expected_event_code='reviewed-code', dry_run=dry_run)
    assert result == repository.result
    assert repository.calls == [{'event_seed': plan['cohorts'][0]['event_seed'], 'dry_run': dry_run}]
    assert plan == original
    assert repository.event_creation_writes_enabled is (not dry_run)


def test_executor_defaults_to_dry_run_and_selects_only_expected_cohort():
    plan = report()
    other = report()['cohorts'][0]
    other['event_seed']['event_code'] = 'other-code'
    plan['cohorts'].append(other)
    repository = Repository({'status': 'ready_to_create'})
    EventCreationExecutor(repository).execute_planned_cohort(report=plan, expected_event_code='reviewed-code')
    assert len(repository.calls) == 1
    assert repository.calls[0]['dry_run'] is True
    assert repository.calls[0]['event_seed']['event_code'] == 'reviewed-code'
    assert repository.event_creation_writes_enabled is False


@pytest.mark.parametrize('change', ['mode', 'missing', 'duplicate_code', 'blocked', 'validation_write',
    'seed_missing', 'signals_mismatch', 'relations_mismatch', 'duplicate_signal', 'invalid_uuid',
    'string_ids', 'empty_relations', 'malformed_entry'])
def test_executor_rejects_invalid_plan_before_repository(change):
    plan = report()
    item = plan['cohorts'][0]
    if change == 'mode': plan['mode'] = 'persist'
    elif change == 'missing': item['event_seed']['event_code'] = 'other'
    elif change == 'duplicate_code': plan['cohorts'].append(deepcopy(item))
    elif change == 'blocked': item['validation']['status'] = 'blocked'
    elif change == 'validation_write': item['validation']['dry_run'] = False
    elif change == 'seed_missing': item['event_seed'] = None
    elif change == 'signals_mismatch': item['cohort']['signal_ids'] = [str(uuid4()), str(uuid4())]
    elif change == 'relations_mismatch': item['cohort']['signal_relation_ids'] = [str(uuid4())]
    elif change == 'duplicate_signal': item['event_seed']['source_signal_ids'].append(item['event_seed']['source_signal_ids'][0])
    elif change == 'invalid_uuid': item['event_seed']['source_relation_ids'][0] = 'invalid'
    elif change == 'string_ids': item['event_seed']['source_signal_ids'] = 'invalid'
    elif change == 'empty_relations': item['event_seed']['source_relation_ids'].clear()
    else: plan['cohorts'].append(None)
    repository = Repository({'status': 'created'})
    with pytest.raises(ValueError):
        EventCreationExecutor(repository).execute_planned_cohort(report=plan, expected_event_code='reviewed-code')
    assert repository.calls == []


def test_executor_does_not_enable_writes():
    repository = Repository({'status': 'created'})
    with pytest.raises(RuntimeError, match='writes not enabled'):
        EventCreationExecutor(repository).execute_planned_cohort(report=report(),
            expected_event_code='reviewed-code', dry_run=False)
    assert repository.event_creation_writes_enabled is False


@pytest.mark.parametrize('dry_run,status', [(True, 'created'), (False, 'ready_to_create'), (True, 'unknown')])
def test_executor_rejects_unexpected_repository_status(dry_run, status):
    repository = Repository({'status': status})
    repository.event_creation_writes_enabled = True
    with pytest.raises(RuntimeError, match='status'):
        EventCreationExecutor(repository).execute_planned_cohort(report=report(),
            expected_event_code='reviewed-code', dry_run=dry_run)


def test_executor_propagates_database_failure():
    class FailingRepository(Repository):
        def persist_event_creation_cohort(self, **kwargs): raise RuntimeError('database failure')
    with pytest.raises(RuntimeError, match='database failure'):
        EventCreationExecutor(FailingRepository({})).execute_planned_cohort(
            report=report(), expected_event_code='reviewed-code')
