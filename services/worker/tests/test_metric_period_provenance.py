import copy
import hashlib
import json

import pytest

from test_assembly_host_types import claims
from onehealth_worker.evaluation.metric_period_provenance import (
    MetricProvenanceError, build_metric_period_provenance,
)
from onehealth_worker.extraction.assembly_v046 import assemble_claims_payload
from onehealth_worker.extraction.schema import load_atomic_claims_schema, load_schema


def encoded(value):
    return json.dumps(value, ensure_ascii=False).encode('utf-8')


def arguments():
    payload = claims('population')
    payload['claims'][0]['metric'].update(reported=True, name='cases', value_numeric=8, unit='cases')
    signals = assemble_claims_payload(payload)
    cb, sb = encoded(payload), encoded(signals)
    return dict(claims_bytes=cb, signals_bytes=sb,
                expected_claims_sha256=hashlib.sha256(cb).hexdigest(),
                expected_signals_sha256=hashlib.sha256(sb).hexdigest(),
                expected_document=copy.deepcopy(payload['document']),
                claims_schema=load_atomic_claims_schema(), signal_schema=load_schema())


def replace(args, kind, value):
    data = value if isinstance(value, bytes) else encoded(value)
    args[f'{kind}_bytes'] = data
    args[f'expected_{kind}_sha256'] = hashlib.sha256(data).hexdigest()


def test_unique_mapping_preserves_period_evidence_hashes_and_inputs():
    args = arguments()
    before = copy.deepcopy(args)
    result_bytes = build_metric_period_provenance(**args)
    result = json.loads(result_bytes)
    claim = json.loads(args['claims_bytes'])['claims'][0]
    row = result['rows'][0]
    assert row['binding_status'] == 'unique_metric_match'
    assert row['metric_pointer'] == '/signals/0/metrics/0'
    assert row['source_claims'][0]['claim_pointer'] == '/claims/0'
    for field in ['group_id', 'reference_period', 'event_date', 'evidence']:
        assert row['source_claims'][0][field] == claim[field]
    assert result['claims_sha256'] == args['expected_claims_sha256']
    assert result['signals_sha256'] == args['expected_signals_sha256']
    assert result['decisions_applied'] == 0
    assert result['semantic_correctness_verified'] is False
    assert result['source_literalness_verified'] is False
    assert result['group_membership_verified'] is False
    assert build_metric_period_provenance(**args) == result_bytes
    assert args == before


def test_identical_metrics_preserve_all_candidates_even_across_groups():
    args = arguments()
    payload = json.loads(args['claims_bytes'])
    other = copy.deepcopy(payload['claims'][0])
    other.update(claim_id='second', group_id='other-group')
    other['reference_period']['verbatim'] = 'different period'
    payload['claims'].append(other)
    replace(args, 'claims', payload)
    row = json.loads(build_metric_period_provenance(**args))['rows'][0]
    assert row['binding_status'] == 'ambiguous_metric_match'
    assert [c['claim_id'] for c in row['source_claims']] == ['test', 'second']
    assert row['source_claims'][1]['reference_period']['verbatim'] == 'different period'


@pytest.mark.parametrize('change', ['value', 'cutoff', 'unreported'])
def test_no_match_is_explicit_and_never_repaired(change):
    args = arguments()
    payload = json.loads(args['claims_bytes'])
    metric = payload['claims'][0]['metric']
    if change == 'value':
        metric['value_numeric'] = 9
    elif change == 'cutoff':
        metric['as_of_verbatim'] = 'another cutoff'
    else:
        metric['reported'] = False
    replace(args, 'claims', payload)
    row = json.loads(build_metric_period_provenance(**args))['rows'][0]
    assert row['binding_status'] == 'unmatched'
    assert row['source_claims'] == []


@pytest.mark.parametrize('kind', ['claims', 'signals'])
def test_wrong_hash_rejected_before_mapping(kind):
    args = arguments()
    args[f'expected_{kind}_sha256'] = '0' * 64
    with pytest.raises(MetricProvenanceError, match='^invalid metric provenance artifacts or binding$'):
        build_metric_period_provenance(**args)


@pytest.mark.parametrize('kind', ['claims', 'signals'])
@pytest.mark.parametrize('failure', ['invalid_json', 'duplicate_key', 'nan', 'overflow', 'schema', 'metadata', 'duplicate_id'])
def test_bad_artifacts_fail_with_redacted_error(kind, failure):
    args = arguments()
    value = json.loads(args[f'{kind}_bytes'])
    if failure == 'invalid_json':
        value = b'sensitive text'
    elif failure == 'duplicate_key':
        value = b'{"sensitive":1,"sensitive":2}'
    elif failure == 'nan':
        value = b'{"sensitive":NaN}'
    elif failure == 'overflow':
        value = b'{"sensitive":1e999}'
    elif failure == 'schema':
        value['schema_version'] = 'sensitive'
    elif failure == 'metadata':
        value['document']['raw_item_id'] = 'sensitive'
    else:
        value[kind].append(copy.deepcopy(value[kind][0]))
    replace(args, kind, value)
    with pytest.raises(MetricProvenanceError) as error:
        build_metric_period_provenance(**args)
    assert str(error.value) == 'invalid metric provenance artifacts or binding'


def test_empty_artifacts_still_bind_metadata_and_hashes():
    args = arguments()
    for kind in ['claims', 'signals']:
        value = json.loads(args[f'{kind}_bytes'])
        value[kind] = []
        replace(args, kind, value)
    assert json.loads(build_metric_period_provenance(**args))['rows'] == []
    args['expected_document']['raw_item_id'] = 'different'
    with pytest.raises(MetricProvenanceError):
        build_metric_period_provenance(**args)


@pytest.mark.parametrize('kind', ['claims_schema', 'signal_schema'])
def test_external_schema_references_rejected_without_resolution(kind):
    args = arguments()
    args[kind] = {'$ref': 'https://example.invalid/schema.json'}
    with pytest.raises(MetricProvenanceError):
        build_metric_period_provenance(**args)


def test_distinct_metrics_keep_their_individual_periods_in_one_signal():
    args = arguments()
    payload = json.loads(args['claims_bytes'])
    first = payload['claims'][0]
    first['reference_period']['verbatim'] = 'season'
    second = copy.deepcopy(first)
    second['claim_id'] = 'second'
    second['metric']['value_numeric'] = 3
    second['reference_period']['verbatim'] = 'SE 22'
    payload['claims'].append(second)
    signals = assemble_claims_payload(payload)
    assert len(signals['signals']) == 1
    replace(args, 'claims', payload)
    replace(args, 'signals', signals)
    rows = json.loads(build_metric_period_provenance(**args))['rows']
    assert [r['source_claims'][0]['reference_period']['verbatim'] for r in rows] == ['season', 'SE 22']


def test_builder_does_not_open_files_or_network(monkeypatch):
    import builtins
    import socket

    args = arguments()

    def forbidden(*args, **kwargs):
        pytest.fail('unexpected I/O')

    monkeypatch.setattr(builtins, 'open', forbidden)
    monkeypatch.setattr(socket, 'socket', forbidden)
    monkeypatch.setattr(socket, 'getaddrinfo', forbidden)
    assert json.loads(build_metric_period_provenance(**args))['rows']
