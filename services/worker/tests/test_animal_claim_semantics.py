import copy

import pytest

from test_assembly_host_types import claims
from onehealth_worker.extraction.assembly_v046 import assemble_claims_payload
from onehealth_worker.extraction.schema import validate_atomic_claims, validate_extraction


def diagnostic(text='Se confirmó un brote de enfermedad X en animales de Villa Norte.'):
    source = claims('animal')
    claim = source['claims'][0]
    claim.update(claim_kind='diagnostic_result', polarity='positive', verification_status='confirmed',
        evidence=[{'type': 'text', 'text': text, 'location_in_document': 'body', 'page_number': None}])
    claim['diagnostics'].update(test_reported=True, result='positive')
    claim['locations'] = [{'country': 'Argentina', 'country_iso2': 'AR',
        'admin1': None, 'admin2': None, 'locality': 'Villa Norte', 'region': None,
        'precision': 'locality', 'role': 'event_location', 'confidence': 0.9}]
    return source


def assembled(source):
    before = copy.deepcopy(source)
    validate_atomic_claims(source)
    result = assemble_claims_payload(source)
    validate_extraction(result)
    assert source == before
    return result


@pytest.mark.parametrize('text', ['Se confirmó un\nbrote de enfermedad X en animales.',
    'Officials confirmed an outbreak in livestock.'])
def test_explicit_confirmed_animal_outbreak_is_not_just_a_lab_result(text):
    result = assembled(diagnostic(text))
    assert result['signals'][0]['signal_type'] == 'outbreak'
    assert result['signals'][0]['diagnostics']['result'] == 'positive'


@pytest.mark.parametrize('text', ['Se confirmó un resultado positivo de enfermedad X.',
    'No se confirmó un brote de enfermedad X.', 'Se investiga un posible brote.',
    'Se confirmó un brote en el pasado, pero este resultado no lo confirma.'])
def test_ambiguous_or_negated_text_does_not_promote_a_diagnosis(text):
    assert assembled(diagnostic(text))['signals'][0]['signal_type'] == 'laboratory_result'


@pytest.mark.parametrize('change', ['negative', 'unconfirmed', 'laboratory_location', 'multiple_locations'])
def test_outbreak_promotion_requires_confirmed_positive_and_one_event_location(change):
    source = diagnostic()
    claim = source['claims'][0]
    if change == 'negative': claim['diagnostics']['result'] = 'negative'
    elif change == 'unconfirmed': claim['verification_status'] = 'reported'
    elif change == 'laboratory_location': claim['locations'][0]['role'] = 'laboratory_location'
    else:
        location = copy.deepcopy(claim['locations'][0])
        location['locality'] = 'Villa Sur'
        claim['locations'].append(location)
    assert assembled(source)['signals'][0]['signal_type'] == 'laboratory_result'


@pytest.mark.parametrize('change', ['negative_polarity', 'historical_period', 'human_subject',
    'non_animal_domain', 'unresolved_event_location'])
def test_non_target_contexts_do_not_promote_an_outbreak(change):
    source = diagnostic()
    claim = source['claims'][0]
    if change == 'negative_polarity': claim['polarity'] = 'negative'
    elif change == 'historical_period': claim['reference_period']['period_type'] = 'historical_period'
    elif change == 'human_subject': claim['subject']['subject_type'] = 'human'
    elif change == 'non_animal_domain': claim['domains'] = ['human']
    else:
        location = copy.deepcopy(claim['locations'][0])
        location['locality'] = None
        claim['locations'].append(location)
    assert assembled(source)['signals'][0]['signal_type'] != 'outbreak'


def facility_absence():
    source = diagnostic('No se encuentran granjas comerciales en las proximidades del foco.')
    claim = source['claims'][0]
    claim.update(claim_kind='wildlife_presence_absence', polarity='negative')
    claim['subject'].update(subject_type='other', verbatim='granjas comerciales')
    claim['diagnostics'].update(test_reported=False, result='not_applicable')
    claim['metric'].update(reported=True, name='facility_count', value_numeric=0, unit='granjas')
    return source


def test_absence_of_facilities_is_not_a_wildlife_negative_finding():
    result = assembled(facility_absence())
    assert result['signals'] == []
    assert any('facility inventory' in warning for warning in result['warnings'])


@pytest.mark.parametrize('change', ['animal_subject', 'negative_test', 'outbreak_absence', 'no_zero_inventory'])
def test_actual_negative_findings_are_not_removed_as_facility_inventory(change):
    source = facility_absence()
    claim = source['claims'][0]
    if change == 'animal_subject': claim['subject']['subject_type'] = 'wildlife'
    elif change == 'negative_test': claim['diagnostics'].update(test_reported=True, result='negative')
    elif change == 'outbreak_absence': claim['evidence'][0]['text'] = 'No se registran brotes en las granjas comerciales.'
    else: claim['metric']['value_numeric'] = None
    assert len(assembled(source)['signals']) == 1
