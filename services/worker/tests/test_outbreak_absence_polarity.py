import copy

import pytest

from test_assembly_host_types import claims
from onehealth_worker.extraction.atomic_claims import assemble_claims_payload as assemble_v044
from onehealth_worker.extraction.assembly_v045 import assemble_claims_payload as assemble_v045
from onehealth_worker.extraction.assembly_v046 import assemble_claims_payload as assemble_v046
from onehealth_worker.extraction.schema import validate_atomic_claims, validate_extraction


def outbreak(polarity, identifier='absence'):
    claim = claims('other')['claims'][0]
    claim.update(claim_id=identifier, group_id='shared', claim_kind='outbreak_update',
        polarity=polarity, summary='Estado de brotes en jurisdicción X.',
        event_date={'start': None, 'end': None, 'precision': 'unknown'})
    claim['diagnostics'].update(test_reported=False, result='not_applicable')
    claim['metric'].update(reported=False, value_numeric=None, value_text=None)
    claim['evidence'] = [{'type': 'text', 'text': 'No se registran brotes activos en jurisdicción X.',
        'location_in_document': None, 'page_number': None}]
    return claim


def assemble(assembler, items):
    payload = claims('other')
    payload['claims'] = items
    before = copy.deepcopy(payload)
    validate_atomic_claims(payload)
    result = assembler(payload)
    validate_extraction(result)
    assert payload == before
    return result['signals']


@pytest.mark.parametrize('assembler', [assemble_v044, assemble_v045, assemble_v046])
@pytest.mark.parametrize('polarity,role', [('negative', 'negative_evidence'),
    ('positive', 'primary_event'), ('uncertain', 'primary_event')])
def test_outbreak_role_preserves_explicit_negative_only(assembler, polarity, role):
    signals = assemble(assembler, [outbreak(polarity)])
    assert len(signals) == 1
    assert signals[0]['signal_type'] == 'outbreak'
    assert signals[0]['signal_role'] == role
    assert signals[0]['diagnostics']['result'] != 'negative'
    assert signals[0]['metrics'] == []


@pytest.mark.parametrize('assembler', [assemble_v044, assemble_v045, assemble_v046])
@pytest.mark.parametrize('reverse', [False, True])
def test_absence_does_not_merge_with_positive_update_or_count(assembler, reverse):
    negative = outbreak('negative')
    positive = outbreak('positive', 'positive')
    positive['evidence'][0]['text'] = 'Se confirmó un brote en jurisdicción Y.'
    count = copy.deepcopy(positive)
    count.update(claim_id='count', claim_kind='case_status')
    count['metric'].update(reported=True, name='cases', value_numeric=3, unit='cases')
    count['evidence'][0]['text'] = 'Se notificaron tres casos en jurisdicción Y.'
    items = [negative, positive, count]
    signals = assemble(assembler, list(reversed(items)) if reverse else items)
    assert len(signals) == 2
    absence = next(s for s in signals if s['signal_role'] == 'negative_evidence')
    event = next(s for s in signals if s['signal_role'] == 'primary_event')
    assert absence['signal_type'] == event['signal_type'] == 'outbreak'
    assert [e['text'] for e in absence['evidence']] == [negative['evidence'][0]['text']]
    assert absence['metrics'] == []
    assert any(m['value_numeric'] == 3 for m in event['metrics'])
    assert len(event['evidence']) == 2


@pytest.mark.parametrize('assembler', [assemble_v044, assemble_v045, assemble_v046])
def test_repeated_negative_updates_still_consolidate(assembler):
    a, b = outbreak('negative'), outbreak('negative', 'second')
    b['evidence'][0]['text'] = 'No hay focos activos en jurisdicción X.'
    signals = assemble(assembler, [a, b])
    assert len(signals) == 1
    assert signals[0]['signal_role'] == 'negative_evidence'
    assert len(signals[0]['evidence']) == 2
