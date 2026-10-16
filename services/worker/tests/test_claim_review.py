import copy
import json

import pytest

from onehealth_worker.evaluation.claim_review import review_claims
from onehealth_worker.evaluation.offline import run_frozen_corpus
from test_offline_frozen_corpus import FakeProvider, manifest
from test_assembly_host_types import claims


def item(locality='Villa Azul', quote='Foco en Villa Azul.', kind='outbreak_update', reported=False, result='unknown'):
    return {'claim_id': 'test', 'claim_kind': kind, 'locations': [{'locality': locality}],
        'diagnostics': {'test_reported': reported, 'result': result}, 'evidence': [{'text': quote}]}


@pytest.mark.parametrize('claim,codes', [
    (item(), []),
    (item('Villa Azul del Monte', 'Villa Azul emitió un comunicado.'), ['REVIEW-LOCALITY-QUOTE']),
    (item('Villa Azul', 'Foco en Villa Azulada.'), ['REVIEW-LOCALITY-QUOTE']),
    (item('Villa\nAzul', 'Foco en Villa   Azul.'), []),
    (item('VILLA AZUL', 'Foco en Villa Azul.'), []),
    (item('Villa (Norte)', 'Foco en Villa (Norte).'), []),
    (item(locality=None), []),
    (item(kind='diagnostic_result', result='positive'), ['REVIEW-TEST-RESULT']),
    (item(kind='laboratory_investigation', reported=True, result='pending'), []),
    (item(kind='laboratory_investigation'), ['REVIEW-INVESTIGATION-STATE']),
])
def test_review_hints_are_specific_and_do_not_mutate_claims(claim, codes):
    payload = {'claims': [claim]}
    before = copy.deepcopy(payload)
    assert [f['code'] for f in review_claims(payload)] == codes
    assert payload == before


def test_review_does_not_join_quotes_to_invent_locality_support():
    claim = item('Villa Azul')
    claim['evidence'] = [{'text': 'Villa'}, {'text': 'Azul'}]
    assert review_claims({'claims': [claim]})[0]['code'] == 'REVIEW-LOCALITY-QUOTE'
    assert review_claims({'claims': []}) == []


class ClaimProvider(FakeProvider):
    def extract(self, **kwargs):
        response = super().extract(**kwargs)
        payload = claims('animal')
        payload['document'] = response.payload['document']
        claim = payload['claims'][0]
        claim.update(claim_kind='diagnostic_result', polarity='positive')
        claim['diagnostics'].update(test_reported=False, result='positive')
        claim['evidence'] = [{'type': 'text', 'text': 'Documento 0: evidencia literal H5.',
            'location_in_document': None, 'page_number': None}]
        response.payload = payload
        return response


def test_optional_hints_do_not_change_status_outputs_usage_or_predictions(tmp_path):
    path = manifest(tmp_path)
    baseline = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'baseline',
        execute=True, provider=ClaimProvider())
    reviewed = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'reviewed',
        execute=True, provider=ClaimProvider(), include_review_hints=True)
    a, b = baseline['results'][0], reviewed['results'][0]
    assert a['status'] == b['status'] == 'generated'
    assert 'claim_review' not in baseline and 'claim_review' not in a
    assert a['usage'] == b['usage']
    for suffix in ['claims.json', 'signals.json']:
        assert (tmp_path/'baseline'/('001.'+suffix)).read_bytes() == (tmp_path/'reviewed'/('001.'+suffix)).read_bytes()
    assert b['claim_review']['status'] == 'reviewed'
    assert 'REVIEW-TEST-RESULT' in [f['code'] for f in b['claim_review']['findings']]
    assert reviewed['claim_review']['affects_validation'] is False


def test_empty_review_is_distinct_from_not_reviewed(tmp_path):
    path = manifest(tmp_path)
    prepared = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'prepared', include_review_hints=True)
    assert prepared['results'][0]['claim_review'] == {'status': 'not_reviewed', 'findings': None}
    reviewed = run_frozen_corpus(manifest_path=path, output_dir=tmp_path/'reviewed',
        execute=True, provider=FakeProvider(), include_review_hints=True)
    assert reviewed['results'][0]['claim_review'] == {'status': 'reviewed', 'findings': []}


def test_failed_binding_is_not_reviewed(tmp_path):
    report = run_frozen_corpus(manifest_path=manifest(tmp_path), output_dir=tmp_path/'run',
        execute=True, provider=FakeProvider(wrong_binding=True), include_review_hints=True)
    row = report['results'][0]
    assert row['status'] == 'failed'
    assert row['claim_review'] == {'status': 'not_reviewed', 'findings': None}


def test_review_failure_is_redacted_and_does_not_reject_valid_prediction(tmp_path, monkeypatch):
    from onehealth_worker.evaluation import claim_review
    def broken(_):
        raise RuntimeError('secret-do-not-save')
    monkeypatch.setattr(claim_review, 'review_claims', broken)
    report = run_frozen_corpus(manifest_path=manifest(tmp_path), output_dir=tmp_path/'run',
        execute=True, provider=FakeProvider(), include_review_hints=True)
    row = report['results'][0]
    assert row['status'] == 'generated'
    assert row['claim_review'] == {'status': 'review_error', 'findings': None, 'error_type': 'RuntimeError'}
    assert 'secret-do-not-save' not in (tmp_path/'run/report.json').read_text()
