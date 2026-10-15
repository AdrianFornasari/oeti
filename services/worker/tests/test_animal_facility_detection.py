import copy

import pytest

from test_animal_claim_semantics import diagnostic, assembled


def detection(text='Se confirmó un caso positivo de enfermedad X en cerdos de un predio de Villa Norte.'):
    source = diagnostic(text)
    source['claims'][0]['subject']['verbatim'] = 'cerdos'
    source['claims'][0]['pathogen_verbatim'] = 'Agente X'
    return source


@pytest.mark.parametrize('text', [
    'Se confirmó un caso positivo de enfermedad X en cerdos de un predio de Villa Norte.',
    'Se detectó un caso positivo en bovinos de un establecimiento situado en Villa Norte.',
    'Officials confirmed a positive case in poultry at a farm in Villa Norte.',
])
def test_reported_animal_population_detection_at_one_facility_is_focal_event(text):
    source = detection(text)
    source['claims'][0]['subject']['verbatim'] = ('bovinos' if 'bovinos' in text else 'poultry' if 'poultry' in text else 'cerdos')
    result = assembled(source)
    assert result['signals'][0]['signal_type'] == 'outbreak'
    assert result['signals'][0]['diagnostics']['result'] == 'positive'
    assert result['signals'][0]['metrics'] == []


@pytest.mark.parametrize('text', [
    'Se confirmó un caso positivo de enfermedad X en un animal individual de Villa Norte.',
    'Se confirmó un caso positivo de enfermedad X en cerdos de Villa Norte.',
    'Se confirmó un resultado positivo en una muestra remitida desde un predio de Villa Norte.',
    'No se confirmó un caso positivo de enfermedad X en cerdos de un predio de Villa Norte.',
    'Se investiga un posible caso positivo en cerdos de un predio de Villa Norte.',
    'Se confirmó un caso positivo en cerdos. Hay un predio en Villa Sur.',
    'Se confirmó un caso positivo en cerdos de predios ubicados en Villa Norte y Villa Sur.',
    'Se confirmó un caso positivo en cerdos de un predio de Villa Norte del Monte.',
    'Se confirmó un caso positivo en cerdos de un predio de Villa Sur, con análisis en Villa Norte.',
    'Se confirmó un caso positivo en cerdos de un predio de Villa Sur y se analizó en Villa Norte.',
    'Se confirmó un caso positivo en cerdos de un predio —ubicado en Villa Sur— de Villa Norte.',
])
def test_incomplete_or_non_focal_reports_remain_diagnostics(text):
    assert assembled(detection(text))['signals'][0]['signal_type'] == 'laboratory_result'


@pytest.mark.parametrize('change', ['individual_subject', 'human_subject', 'wildlife_subject',
    'historical', 'negative', 'unconfirmed', 'lab_location', 'multiple_event_locations'])
def test_facility_detection_requires_population_and_confirmed_single_event(change):
    source = detection()
    claim = source['claims'][0]
    if change == 'individual_subject': claim['subject']['verbatim'] = 'un cerdo'
    elif change == 'human_subject': claim['subject']['subject_type'] = 'human'
    elif change == 'wildlife_subject': claim['subject']['subject_type'] = 'wildlife'
    elif change == 'historical': claim['reference_period']['period_type'] = 'historical_period'
    elif change == 'negative': claim['diagnostics']['result'] = 'negative'
    elif change == 'unconfirmed': claim['verification_status'] = 'reported'
    elif change == 'lab_location': claim['locations'][0]['role'] = 'laboratory_location'
    else:
        other = copy.deepcopy(claim['locations'][0])
        other['locality'] = 'Villa Sur'
        claim['locations'].append(other)
    assert assembled(source)['signals'][0]['signal_type'] != 'outbreak'


def with_lab_support():
    source = detection()
    support = copy.deepcopy(source['claims'][0])
    support.update(claim_id='lab', evidence=[{'type': 'text',
        'text': 'El laboratorio confirmó el resultado para el Agente X.',
        'location_in_document': 'body', 'page_number': None}])
    support['subject'].update(subject_type='other', verbatim='muestras')
    support['locations'][0].update(role='laboratory_location', locality='Ciudad Laboratorio')
    source['claims'].append(support)
    return source


def test_same_group_lab_confirmation_supports_one_focal_signal_without_duplication():
    source = with_lab_support()
    result = assembled(source)
    assert len(result['signals']) == 1
    signal = result['signals'][0]
    assert signal['signal_type'] == 'outbreak'
    assert len(signal['evidence']) == 2
    assert signal['metrics'] == []
    assert any('supporting laboratory confirmation' in warning for warning in result['warnings'])


@pytest.mark.parametrize('change', ['different_group', 'different_pathogen', 'unknown_pathogen',
    'independent_metric', 'event_location', 'negative_result', 'no_explicit_support',
    'different_date', 'genomic_observation', 'test_not_reported'])
def test_separate_or_ambiguous_lab_claim_is_not_absorbed(change):
    source = with_lab_support()
    support = source['claims'][1]
    if change == 'different_group': support['group_id'] = 'another'
    elif change == 'different_pathogen': support['pathogen_verbatim'] = 'Agente Y'
    elif change == 'unknown_pathogen': support['pathogen_verbatim'] = None
    elif change == 'independent_metric': support['metric'].update(reported=True, name='samples', value_numeric=4)
    elif change == 'event_location': support['locations'][0]['role'] = 'event_location'
    elif change == 'negative_result': support['diagnostics']['result'] = 'negative'
    elif change == 'different_date': support['event_date'].update(start='2026-06-01', end=None)
    elif change == 'genomic_observation': support['genomics']['sequence_reported'] = True
    elif change == 'test_not_reported': support['diagnostics']['test_reported'] = False
    else: support['evidence'][0]['text'] = 'Se describen resultados del laboratorio.'
    assert len(assembled(source)['signals']) == 2
