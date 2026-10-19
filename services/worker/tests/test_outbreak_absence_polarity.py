import copy

import pytest

from test_assembly_host_types import claims
from onehealth_worker.extraction.atomic_claims import assemble_claims_payload as assemble_v044
from onehealth_worker.extraction.assembly_v045 import assemble_claims_payload as assemble_v045
from onehealth_worker.extraction.assembly_v046 import assemble_claims_payload as assemble_v046
from onehealth_worker.extraction.schema import validate_atomic_claims, validate_extraction
from onehealth_worker.extraction.normalization import normalize_extraction_payload
from onehealth_worker.extraction.signal_semantics_v049 import harden_signal_semantics_v049


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


def assemble_current_pipeline(payload):
    return harden_signal_semantics_v049(normalize_extraction_payload(assemble_v046(payload)))


ASSEMBLERS = [assemble_v044, assemble_v045, assemble_v046, assemble_current_pipeline]


def case_status(polarity='negative'):
    claim = outbreak(polarity, 'case-status')
    claim['claim_kind'] = 'case_status'
    claim['metric'].update(reported=True, name='confirmed cases', value_numeric=0, unit='cases')
    claim['summary'] = 'No confirmed cases have been reported this season.'
    claim['evidence'][0]['text'] = claim['summary']
    return claim


@pytest.mark.parametrize('assembler', ASSEMBLERS)
@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('positive_kind', ['case_status', 'outbreak_update', 'death_count'])
def test_negative_case_status_isolated_from_positive_counts(assembler, reverse, positive_kind):
    negative = case_status()
    positive = outbreak('positive', 'positive-count')
    positive['claim_kind'] = positive_kind
    positive['metric'].update(reported=True, name='probable cases', value_numeric=3, unit='cases')
    positive['evidence'][0]['text'] = 'Three probable cases have been reported.'
    items = [negative, positive]
    signals = assemble(assembler, list(reversed(items)) if reverse else items)
    assert len(signals) == 2
    absence = next(s for s in signals if s['signal_role'] == 'negative_evidence')
    event = next(s for s in signals if s['signal_role'] == 'primary_event')
    assert absence['signal_type'] == 'case_report'
    assert absence['metrics'] == [{k: v for k, v in negative['metric'].items() if k != 'reported'}]
    assert event['metrics'] == [{k: v for k, v in positive['metric'].items() if k != 'reported'}]
    assert [e['text'] for e in absence['evidence']] == [negative['evidence'][0]['text']]
    assert [e['text'] for e in event['evidence']] == [positive['evidence'][0]['text']]


@pytest.mark.parametrize('assembler', ASSEMBLERS)
@pytest.mark.parametrize('polarity,role', [('negative', 'negative_evidence'),
    ('positive', 'primary_event'), ('uncertain', 'primary_event')])
@pytest.mark.parametrize('reported', [True, False])
def test_case_status_role_uses_polarity_not_zero_or_metric_presence(assembler, polarity, role, reported):
    claim = case_status(polarity)
    if not reported:
        claim['metric'].update(reported=False, value_numeric=None)
    signals = assemble(assembler, [claim])
    assert len(signals) == 1
    assert signals[0]['signal_role'] == role
    assert signals[0]['signal_type'] == 'case_report'
    assert bool(signals[0]['metrics']) == reported


@pytest.mark.parametrize('assembler', ASSEMBLERS)
def test_negative_death_count_keeps_existing_grouping(assembler):
    positive = outbreak('positive', 'positive')
    negative = case_status()
    negative['claim_kind'] = 'death_count'
    negative['metric']['name'] = 'deaths'
    signals = assemble(assembler, [positive, negative])
    assert len(signals) == 1
    assert signals[0]['signal_role'] == 'primary_event'


@pytest.mark.parametrize('assembler', ASSEMBLERS)
def test_repeated_negative_case_status_still_consolidates(assembler):
    first, second = case_status(), case_status()
    second['claim_id'] = 'second-negative'
    second['evidence'][0]['text'] = 'No additional confirmed cases were reported.'
    signals = assemble(assembler, [first, second])
    assert len(signals) == 1
    assert signals[0]['signal_role'] == 'negative_evidence'
    assert len(signals[0]['metrics']) == 1
    assert len(signals[0]['evidence']) == 2
