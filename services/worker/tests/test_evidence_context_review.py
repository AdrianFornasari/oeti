import copy
import hashlib
import json

import pytest

from onehealth_worker.evaluation.evidence_context_review import build_evidence_context_review
from test_attribution_review import artifacts, digest, encoded


def test_anaphoric_quote_displays_context_without_resolving_or_repairing():
    source = 'En la nueva temporada no se registran casos confirmados; '
    quote = 'se notificaron 3 probables en esa misma temporada'
    args = artifacts(quote=quote, extra='.')
    args['raw_text'] = source + quote + '.'
    args['expected_raw_text_sha256'] = hashlib.sha256(args['raw_text'].encode()).hexdigest()
    before = copy.deepcopy(args)
    result = build_evidence_context_review(**args)
    row = result['rows'][0]
    assert row['quote'] == quote
    assert row['evidence_pointer'] == '/claims/0/evidence/0'
    assert row['occurrences'][0]['text'] == args['raw_text']
    assert row['occurrences'][0]['quote_start'] == len(source)
    assert result['antecedent_resolution'] == 'not_assessed'
    assert result['semantic_acceptance'] == 'not_assessed'
    assert result['decisions_applied'] == 0
    assert args == before


def test_repeated_overlapping_occurrences_are_not_selected():
    result = build_evidence_context_review(**artifacts(quote='aaa', extra='aa'))
    occurrences = result['rows'][0]['occurrences']
    assert [item['quote_start'] for item in occurrences] == [0, 1, 2]
    assert [item['quote_end'] for item in occurrences] == [3, 4, 5]


def test_windows_are_bounded_and_unicode_offsets_are_exact():
    args = artifacts(quote='á', extra='x' * 400)
    result = build_evidence_context_review(**args)
    occurrence = result['rows'][0]['occurrences'][0]
    assert occurrence['window_start'] == 0
    assert occurrence['window_end'] == 161
    assert occurrence['text'] == args['raw_text'][:161]
    assert result == build_evidence_context_review(**args)


@pytest.mark.parametrize('field', [
    'expected_claims_sha256', 'expected_signals_sha256', 'expected_raw_text_sha256',
])
def test_integrity_checks_remain_required(field):
    args = artifacts()
    args[field] = '0' * 64
    with pytest.raises(ValueError):
        build_evidence_context_review(**args)


def test_normalized_literal_match_does_not_invent_exact_offsets():
    args = artifacts(quote='3 casos probables')
    args['raw_text'] = '3  casos\nprobables'
    args['expected_raw_text_sha256'] = digest(args['raw_text'].encode('utf-8'))
    row = build_evidence_context_review(**args)['rows'][0]
    assert row['occurrence_status'] == 'no_exact_match'
    assert row['occurrences'] == []
    assert row['quote'] == '3 casos probables'


@pytest.mark.parametrize('mode', ['schema', 'document', 'literal'])
def test_invalid_inputs_cannot_produce_context(mode):
    args = artifacts()
    payload = json.loads(args['claims_bytes'])
    if mode == 'schema':
        del payload['claims'][0]['metric']
    elif mode == 'document':
        args['expected_document']['language'] = 'en'
    else:
        payload['claims'][0]['evidence'][0]['text'] = 'Invented evidence.'
    args['claims_bytes'] = encoded(payload)
    args['expected_claims_sha256'] = digest(args['claims_bytes'])
    with pytest.raises(ValueError):
        build_evidence_context_review(**args)


def test_separate_quotes_and_qualitative_claims_keep_their_own_rows():
    args = artifacts(quote='No se registran casos; continúa la vigilancia.')
    payload = json.loads(args['claims_bytes'])
    claim = payload['claims'][0]
    claim['metric'].update(reported=False, value_numeric=None)
    claim['evidence'] = [dict(claim['evidence'][0], text=text)
                         for text in ('No se registran casos', 'continúa la vigilancia')]
    args['claims_bytes'] = encoded(payload)
    args['expected_claims_sha256'] = digest(args['claims_bytes'])
    result = build_evidence_context_review(**args)
    assert len(result['rows']) == 2
    assert [row['evidence_pointer'] for row in result['rows']] == [
        '/claims/0/evidence/0', '/claims/0/evidence/1']
    assert all(row['occurrence_status'] == 'exact_matches' for row in result['rows'])
    result['document']['language'] = 'changed'
    assert args['expected_document']['language'] != 'changed'
