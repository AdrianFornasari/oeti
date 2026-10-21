import copy
import hashlib
import json

import pytest

from onehealth_worker.evaluation.attribution_review import build_review
from onehealth_worker.evaluation.offline import run_frozen_corpus
from onehealth_worker.extraction.assembly_v046 import assemble_claims_payload
from onehealth_worker.extraction.normalization import normalize_extraction_payload
from onehealth_worker.extraction.schema import load_atomic_claims_schema, load_schema
from onehealth_worker.extraction.signal_semantics_v049 import harden_signal_semantics_v049
from test_assembly_host_types import claims
from test_offline_frozen_corpus import FakeProvider, manifest


def digest(value):
    return hashlib.sha256(value).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False).encode('utf-8')


def artifacts(*, quote='3 casos probables en Salta.', extra='', locations=None,
              metric_name='case_count', subject='casos probables', summary=None):
    payload = claims('population', subject)
    claim = payload['claims'][0]
    claim.update(claim_kind='case_status', polarity='positive', domains=['human'],
        disease_verbatim='chikungunya', pathogen_verbatim=None,
        summary=quote if summary is None else summary,
        evidence=[{'type': 'text', 'text': quote, 'location_in_document': None, 'page_number': None}])
    claim['locations'] = locations or []
    claim['event_date'] = {'start': None, 'end': None, 'precision': 'unknown'}
    point = {'date': None, 'year': None, 'month': None, 'precision': 'unknown', 'verbatim': None}
    claim['reference_period'] = {'start': point.copy(), 'end': point.copy(), 'period_type': 'unknown', 'verbatim': None}
    claim['metric'] = {'reported': True, 'name': metric_name, 'value_numeric': 3,
        'value_text': None, 'unit': 'cases', 'as_of_date': None, 'as_of_year': None,
        'as_of_month': None, 'as_of_precision': 'unknown', 'as_of_verbatim': None}
    claim['diagnostics'] = {'test_reported': False, 'test_type': None, 'method': None,
        'target': None, 'specimen': None, 'result': 'unknown'}
    signals = harden_signal_semantics_v049(normalize_extraction_payload(assemble_claims_payload(payload)))
    raw = quote + extra
    cb, sb = encoded(payload), encoded(signals)
    return {'claims_bytes': cb, 'signals_bytes': sb, 'raw_text': raw,
        'expected_claims_sha256': digest(cb), 'expected_signals_sha256': digest(sb),
        'expected_raw_text_sha256': digest(raw.encode('utf-8')),
        'expected_document': copy.deepcopy(payload['document']),
        'claims_schema': load_atomic_claims_schema(), 'signal_schema': load_schema()}


def location(**values):
    return {'country': None, 'country_iso2': None, 'admin1': None, 'admin2': None,
        'locality': None, 'region': None, 'precision': 'admin1', 'confidence': 0.9,
        'role': 'reporting_jurisdiction', **values}


@pytest.mark.parametrize('quote,extra,loc,codes', [
    ('3 casos probables en Salta, Argentina.', '', location(country='Argentina', admin1='Salta'), []),
    ('3 casos probables en Salta.', '', location(country='Argentina', admin1='Salta'), ['REVIEW-LOCATION-DOCUMENT']),
    ('3 casos probables en Salta.', ' Argentina publica un informe.', location(country='Argentina', admin1='Salta'), ['REVIEW-LOCATION-QUOTE']),
    ('3 casos probables en EE.UU.', '', location(country='Estados Unidos'), ['REVIEW-LOCATION-DOCUMENT']),
    ('3 casos probables en Córdoba.', '', location(admin1='Cordoba'), ['REVIEW-LOCATION-DOCUMENT']),
    ('3 casos probables en RÍO   NEGRO.', '', location(admin1='Río Negro'), []),
    ('3 casos probables en Metán.', '', location(country='Argentina', admin1='Salta', locality='Metán'), ['REVIEW-LOCATION-DOCUMENT', 'REVIEW-LOCATION-DOCUMENT']),
    ('3 casos probables en Argentinamente.', '', location(country='Argentina'), ['REVIEW-LOCATION-DOCUMENT']),
    ('3 casos probables en Salta.', '', location(admin1='Salta', country_iso2='AR'), []),
    # Prose presence is deliberately not a verification of the location role.
    ('3 casos probables; la muestra se procesó en Salta.', '', location(admin1='Salta'), []),
])
def test_geographic_presence_is_lexical_not_a_support_decision(quote, extra, loc, codes):
    result = build_review(**artifacts(quote=quote, extra=extra, locations=[loc]))
    assert [f['code'] for f in result['findings'] if f['code'].startswith('REVIEW-LOCATION')] == codes
    assert result['geographic_support_verified'] is False
    assert result['semantic_acceptance'] == 'not_assessed'


@pytest.mark.parametrize('name,subject,summary,expected', [
    ('case_count', 'casos probables', '3 casos probables.', True),
    ('CASES', 'confirmed cases', '3 confirmed cases.', True),
    ('casos', 'casos sospechosos', '3 casos sospechosos.', True),
    ('confirmed_cases', 'casos confirmados', '3 casos confirmados.', False),
    # Conflicting non-generic names and evidence-only cues are outside this helper.
    ('confirmed_cases', 'casos probables', '3 casos probables.', False),
    ('case_count', 'casos', '3 casos.', False),
])
def test_generic_metric_cues_are_narrow_and_never_assign_a_class(name, subject, summary, expected):
    result = build_review(**artifacts(metric_name=name, subject=subject, summary=summary))
    assert any(f['code'] == 'REVIEW-METRIC-CLASSIFICATION-SOURCE' for f in result['findings']) == expected
    assert result['metric_classification_assigned'] is False
    assert result['decisions_applied'] == 0


def test_missing_qualitative_metric_has_no_metric_hint():
    args = artifacts()
    payload = json.loads(args['claims_bytes'])
    payload['claims'][0]['metric'].update(reported=False, value_numeric=None)
    args['claims_bytes'] = encoded(payload)
    args['expected_claims_sha256'] = digest(args['claims_bytes'])
    signals = assemble_claims_payload(payload)
    args['signals_bytes'] = encoded(signals)
    args['expected_signals_sha256'] = digest(args['signals_bytes'])
    assert not build_review(**args)['findings']


def test_ambiguous_and_unmatched_bindings_are_not_classified():
    args = artifacts()
    payload = json.loads(args['claims_bytes'])
    other = copy.deepcopy(payload['claims'][0])
    other.update(claim_id='second', group_id='another')
    payload['claims'].append(other)
    args['claims_bytes'] = encoded(payload)
    args['expected_claims_sha256'] = digest(args['claims_bytes'])
    result = build_review(**args)
    assert result['findings'][0]['binding_status'] == 'ambiguous_metric_match'
    assert result['findings'][0]['candidate_claim_ids'] == ['test', 'second']
    payload['claims'][0]['metric']['value_numeric'] = 7
    payload['claims'][1]['metric']['value_numeric'] = 8
    args['claims_bytes'] = encoded(payload)
    args['expected_claims_sha256'] = digest(args['claims_bytes'])
    result = build_review(**args)
    assert result['findings'][0]['binding_status'] == 'unmatched'
    assert all(f['code'] != 'REVIEW-METRIC-CLASSIFICATION-SOURCE' for f in result['findings'])


@pytest.mark.parametrize('field', ['expected_claims_sha256', 'expected_signals_sha256', 'expected_raw_text_sha256'])
def test_hash_mismatch_rejects_only_review_generation(field):
    args = artifacts()
    args[field] = '0' * 64
    with pytest.raises(ValueError):
        build_review(**args)


def test_schema_binding_and_literal_evidence_are_required():
    for mode in ('schema', 'binding', 'literal'):
        args = artifacts()
        if mode == 'binding':
            args['expected_document']['language'] = 'en'
        else:
            payload = json.loads(args['claims_bytes'])
            if mode == 'schema':
                del payload['claims'][0]['metric']
            else:
                payload['claims'][0]['evidence'][0]['text'] = 'Invented quote.'
            args['claims_bytes'] = encoded(payload)
            args['expected_claims_sha256'] = digest(args['claims_bytes'])
        with pytest.raises(ValueError):
            build_review(**args)


def test_review_is_deterministic_and_has_no_input_or_document_alias_mutation():
    args = artifacts(locations=[location(country='Argentina', admin1='Salta')])
    before = copy.deepcopy(args)
    result = build_review(**args)
    assert result == build_review(**args)
    result['document']['language'] = 'changed'
    assert args == before


def test_review_does_not_join_quotes_into_geographic_support():
    args = artifacts(quote='Villa Norte tiene 3 casos probables.',
        locations=[location(locality='Villa Norte')])
    payload = json.loads(args['claims_bytes'])
    claim = payload['claims'][0]
    claim['evidence'] = [{'type': 'text', 'text': part, 'location_in_document': None, 'page_number': None}
        for part in ('Villa', 'Norte')]
    args['claims_bytes'] = encoded(payload)
    args['expected_claims_sha256'] = digest(args['claims_bytes'])
    findings = build_review(**args)['findings']
    assert any(f['code'] == 'REVIEW-LOCATION-QUOTE' and f['value'] == 'Villa Norte' for f in findings)


class NonemptyProvider(FakeProvider):
    def extract(self, **kwargs):
        response = super().extract(**kwargs)
        payload = json.loads(artifacts(quote='Documento 0: evidencia literal H5.',
            locations=[location(country='Argentina', admin1='Salta')])['claims_bytes'])
        payload['document'] = response.payload['document']
        response.payload = payload
        return response


def test_runner_generates_hash_bound_nonempty_findings_without_changing_signals(tmp_path):
    path = manifest(tmp_path)
    plain_provider, reviewed_provider = NonemptyProvider(), NonemptyProvider()
    plain = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'plain',
        execute=True, provider=plain_provider)
    reviewed = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'reviewed',
        execute=True, provider=reviewed_provider, include_attribution_review=True)
    a, b = plain['results'][0], reviewed['results'][0]
    assert a['status'] == b['status'] == 'generated'
    assert plain_provider.calls == reviewed_provider.calls
    for suffix in ('claims.json', 'signals.json'):
        assert (tmp_path/'plain'/('001.'+suffix)).read_bytes() == (tmp_path/'reviewed'/('001.'+suffix)).read_bytes()
    sidecar = tmp_path/'reviewed'/b['attribution_review']['path']
    assert digest(sidecar.read_bytes()) == b['attribution_review']['sha256']
    data = json.loads(sidecar.read_bytes())
    codes = [f['code'] for f in data['findings']]
    assert codes.count('REVIEW-LOCATION-DOCUMENT') == 2
    assert codes.count('REVIEW-METRIC-CLASSIFICATION-SOURCE') == 1
    assert data['semantic_acceptance'] == 'not_assessed' and data['decisions_applied'] == 0
    assert data['claims_sha256'] == b['claims_sha256'] and data['signals_sha256'] == b['signals_sha256']


def test_literal_validation_failure_never_generates_attribution_sidecar(tmp_path):
    class NonliteralProvider(NonemptyProvider):
        def extract(self, **kwargs):
            response = super().extract(**kwargs)
            response.payload['claims'][0]['evidence'][0]['text'] = 'Invented source quote.'
            return response
    report = run_frozen_corpus(manifest_path=manifest(tmp_path), output_dir=tmp_path/'run',
        execute=True, provider=NonliteralProvider(), include_attribution_review=True)
    row = report['results'][0]
    assert row['status'] == 'failed' and row['phase'] == 'validation'
    assert row['attribution_review'] == {'status': 'not_generated'}
    assert not list((tmp_path/'run').glob('*.attribution-review.json'))


def test_default_disabled_and_opt_in_preserve_provider_inputs_and_predictions(tmp_path):
    path = manifest(tmp_path)
    plain_provider, reviewed_provider = FakeProvider(), FakeProvider()
    plain = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'plain', execute=True, provider=plain_provider)
    reviewed = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'reviewed', execute=True,
        provider=reviewed_provider, include_attribution_review=True, include_review_hints=True,
        include_metric_period_provenance=True)
    a, b = plain['results'][0], reviewed['results'][0]
    assert a['status'] == b['status'] == 'generated'
    assert 'attribution_review' not in plain and 'attribution_review' not in a
    assert plain_provider.calls == reviewed_provider.calls
    assert a['usage'] == b['usage'] and a['response_id'] == b['response_id']
    for suffix in ('input.txt', 'claims.json', 'signals.json'):
        assert (tmp_path/'plain'/('001.'+suffix)).read_bytes() == (tmp_path/'reviewed'/('001.'+suffix)).read_bytes()
    sidecar = tmp_path/'reviewed'/b['attribution_review']['path']
    assert digest(sidecar.read_bytes()) == b['attribution_review']['sha256']
    data = json.loads(sidecar.read_bytes())
    assert data['findings'] == [] and data['semantic_acceptance'] == 'not_assessed'
    assert data['claims_sha256'] == b['claims_sha256'] and data['signals_sha256'] == b['signals_sha256']
    assert data['raw_text_sha256'] == b['source_sha256']
    assert reviewed['attribution_review']['affects_validation'] is False
    assert b['metric_period_provenance']['status'] == 'generated'
    assert b['claim_review']['status'] == 'reviewed'


def test_prepare_and_failed_binding_do_not_generate_review(tmp_path):
    path = manifest(tmp_path)
    provider = FakeProvider()
    prepared = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'prepared',
        provider=provider, include_attribution_review=True)
    assert provider.calls == []
    assert prepared['results'][0]['attribution_review'] == {'status': 'not_generated'}
    failed = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'failed', execute=True,
        provider=FakeProvider(wrong_binding=True), include_attribution_review=True)
    assert failed['results'][0]['status'] == 'failed'
    assert failed['results'][0]['attribution_review'] == {'status': 'not_generated'}
    assert not list((tmp_path/'failed').glob('*.attribution-review.json'))


@pytest.mark.parametrize('failure', ['build', 'write'])
def test_review_failures_are_redacted_and_cannot_reject_prediction(tmp_path, monkeypatch, failure):
    from onehealth_worker.evaluation import attribution_review, offline
    path = manifest(tmp_path)
    original_write = offline._write
    def broken(*args, **kwargs):
        raise RuntimeError('secret-do-not-save')
    def write(path, value):
        if path.name.endswith('.attribution-review.json'):
            raise OSError('secret-do-not-save')
        original_write(path, value)
    if failure == 'build':
        monkeypatch.setattr(attribution_review, 'build_review', broken)
    else:
        monkeypatch.setattr(offline, '_write', write)
    report = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'run', execute=True,
        provider=FakeProvider(), include_attribution_review=True)
    row = report['results'][0]
    assert row['status'] == 'generated'
    assert row['attribution_review']['status'] == 'generation_error'
    assert row['attribution_review']['error_type'] == ('RuntimeError' if failure == 'build' else 'OSError')
    assert 'secret-do-not-save' not in (tmp_path/'run/report.json').read_text()
