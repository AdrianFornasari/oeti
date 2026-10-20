import copy
import hashlib
import json
from pathlib import Path

import pytest

from test_offline_frozen_corpus import FakeProvider, manifest
from test_offline_event_date_policy import DatedProvider, DAY, POLICY, set_policy
from onehealth_worker.evaluation.offline import run_frozen_corpus
from onehealth_worker.evaluation import metric_period_provenance


class MetricProvider(DatedProvider):
    def __init__(self, *, duplicate=False, failure=None):
        super().__init__()
        self.duplicate = duplicate
        self.failure = failure

    def extract(self, **kwargs):
        response = super().extract(**kwargs)
        claim = response.payload['claims'][0]
        claim['polarity'] = 'positive'
        claim['diagnostics'].update(test_reported=False, result='unknown')
        claim['metric'].update(reported=True, name='cases', value_numeric=3,
            value_text=None, unit='cases', as_of_date=None, as_of_year=None,
            as_of_month=None, as_of_precision='unknown', as_of_verbatim=None)
        if self.duplicate:
            other = copy.deepcopy(claim)
            other['claim_id'] = 'C2'
            other['reference_period']['verbatim'] = 'different period'
            response.payload['claims'].append(other)
        if self.failure == 'schema':
            claim['unexpected'] = True
        elif self.failure == 'binding':
            response.payload['document']['raw_item_id'] = 'wrong'
        elif self.failure == 'literal':
            claim['evidence'][0]['text'] = 'Not in the frozen document.'
        return response


def run(path, output, provider, enabled=True, **kwargs):
    return run_frozen_corpus(manifest_path=path, output_dir=output, execute=True,
        provider=provider, include_metric_period_provenance=enabled, **kwargs)


def mapping(output, report):
    state = report['results'][0]['metric_period_provenance']
    assert state['status'] == 'generated'
    data = (output / state['path']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == state['sha256']
    return json.loads(data)


def test_opt_in_keeps_provider_arguments_claims_signals_and_acceptance_identical(tmp_path):
    path = manifest(tmp_path)
    first, second = MetricProvider(), MetricProvider()
    old = run(path, tmp_path/'old', first, enabled=False)
    new = run(path, tmp_path/'new', second)
    assert first.calls == second.calls
    assert 'metric_period_provenance' not in old
    assert 'metric_period_provenance' not in old['results'][0]
    assert not list((tmp_path/'old').glob('*.metric-periods.json'))
    for suffix in ['input.txt', 'claims.json', 'signals.json']:
        assert (tmp_path/'old'/f'001.{suffix}').read_bytes() == (tmp_path/'new'/f'001.{suffix}').read_bytes()
    assert old['summary'] == new['summary'] == {'prepared': 0, 'generated': 1, 'failed': 0}
    for key, value in old['results'][0].items():
        assert new['results'][0][key] == value
    metadata = new['metric_period_provenance']
    assert metadata['affects_validation'] is False
    assert metadata['code_sha256'] == hashlib.sha256(Path(metric_period_provenance.__file__).read_bytes()).hexdigest()
    doc = mapping(tmp_path/'new', new)
    assert doc['claims_sha256'] == new['results'][0]['claims_sha256']
    assert doc['signals_sha256'] == new['results'][0]['signals_sha256']
    assert doc['rows'][0]['binding_status'] == 'unique_metric_match'


def test_prepare_only_does_not_call_provider_or_generate_maps(tmp_path):
    path = manifest(tmp_path)
    provider = MetricProvider()
    report = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'plan',
        provider=provider, include_metric_period_provenance=True)
    assert not provider.calls
    assert report['results'][0]['metric_period_provenance'] == {'status': 'not_generated'}
    assert not list((tmp_path/'plan').glob('*.metric-periods.json'))


def test_valid_empty_claims_generate_empty_map(tmp_path):
    path = manifest(tmp_path)
    report = run(path, tmp_path/'run', FakeProvider())
    assert mapping(tmp_path/'run', report)['rows'] == []
    assert report['results'][0]['status'] == 'generated'


@pytest.mark.parametrize('failure', ['schema', 'binding', 'literal', 'date_policy'])
def test_rejected_claims_never_generate_map(tmp_path, failure):
    path = manifest(tmp_path)
    if failure == 'date_policy':
        set_policy(path, POLICY)
        provider = DatedProvider(DAY)
    else:
        provider = MetricProvider(failure=failure)
    report = run(path, tmp_path/'run', provider)
    item = report['results'][0]
    assert item['status'] == 'failed'
    assert item['usage'] is not None
    assert item['metric_period_provenance'] == {'status': 'not_generated'}
    assert not list((tmp_path/'run').glob('*.metric-periods.json'))


def test_invalid_signal_never_generates_map(tmp_path, monkeypatch):
    from onehealth_worker.extraction import assembly_v046

    path = manifest(tmp_path)
    monkeypatch.setattr(assembly_v046, 'assemble_claims_payload', lambda _: {})
    report = run(path, tmp_path/'run', MetricProvider())
    assert report['results'][0]['status'] == 'failed'
    assert report['results'][0]['metric_period_provenance'] == {'status': 'not_generated'}
    assert not list((tmp_path/'run').glob('*.metric-periods.json'))


def test_builder_error_is_redacted_and_does_not_change_accepted_signals(tmp_path, monkeypatch):
    path = manifest(tmp_path)

    def fail(**kwargs):
        raise RuntimeError('sensitive diagnostic')

    monkeypatch.setattr(metric_period_provenance, 'build_metric_period_provenance', fail)
    old = run(path, tmp_path/'old', MetricProvider(), enabled=False)
    new = run(path, tmp_path/'new', MetricProvider())
    assert old['summary'] == new['summary']
    item = new['results'][0]
    assert item['status'] == 'generated' and item['usage'] is not None
    assert item['metric_period_provenance'] == {'status': 'generation_error', 'error_type': 'RuntimeError'}
    assert 'sensitive' not in json.dumps(new)
    assert (tmp_path/'old/001.signals.json').read_bytes() == (tmp_path/'new/001.signals.json').read_bytes()


def test_map_write_is_exclusive_and_failure_does_not_reject_signals(tmp_path, monkeypatch):
    path = manifest(tmp_path)
    original = Path.open
    modes = []

    def denied(self, mode='r', *args, **kwargs):
        if self.name.endswith('.metric-periods.json'):
            modes.append(mode)
            raise FileExistsError('sensitive existing output')
        return original(self, mode, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', denied)
    report = run(path, tmp_path/'run', MetricProvider())
    assert modes == ['xb']
    assert report['results'][0]['status'] == 'generated'
    assert report['results'][0]['metric_period_provenance'] == {
        'status': 'generation_error', 'error_type': 'FileExistsError'}


def test_duplicate_metrics_keep_both_period_candidates(tmp_path):
    path = manifest(tmp_path)
    report = run(path, tmp_path/'run', MetricProvider(duplicate=True))
    rows = mapping(tmp_path/'run', report)['rows']
    assert len(rows) == 1
    assert rows[0]['binding_status'] == 'ambiguous_metric_match'
    assert len(rows[0]['source_claims']) == 2


def test_preflight_failure_creates_no_output_or_provider_call(tmp_path):
    path = manifest(tmp_path)
    (path.parent/'0.txt').write_text('tampered')
    provider = MetricProvider()
    with pytest.raises(ValueError):
        run(path, tmp_path/'run', provider)
    assert not provider.calls and not (tmp_path/'run').exists()


def test_normalized_metric_without_exact_match_is_explicit(tmp_path, monkeypatch):
    from onehealth_worker.extraction import normalization

    path = manifest(tmp_path)
    original = normalization.normalize_extraction_payload

    def changed(payload):
        result = original(payload)
        result['signals'][0]['metrics'][0]['name'] = 'normalized different name'
        return result

    monkeypatch.setattr(normalization, 'normalize_extraction_payload', changed)
    report = run(path, tmp_path/'run', MetricProvider())
    assert report['results'][0]['status'] == 'generated'
    row = mapping(tmp_path/'run', report)['rows'][0]
    assert row['binding_status'] == 'unmatched'
    assert row['source_claims'] == []


def test_mapping_and_review_hints_remain_separate(tmp_path):
    path = manifest(tmp_path)
    report = run(path, tmp_path/'run', MetricProvider(), include_review_hints=True)
    item = report['results'][0]
    assert item['claim_review']['status'] == 'reviewed'
    assert item['metric_period_provenance']['status'] == 'generated'
    assert report['claim_review']['affects_validation'] is False
    assert report['metric_period_provenance']['affects_validation'] is False
