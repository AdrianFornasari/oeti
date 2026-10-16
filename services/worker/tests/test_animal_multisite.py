import copy

import pytest

from test_animal_facility_detection import detection
from test_animal_claim_semantics import assembled


def multisite():
    source = detection('Se confirmaron casos positivos en cerdos de dos predios, uno en Villa Norte y otro en Villa Sur.')
    claim = source['claims'][0]
    other = copy.deepcopy(claim['locations'][0])
    other['locality'] = 'Villa Sur'
    claim['locations'].append(other)
    claim['event_date'] = {'start': None, 'end': None, 'precision': 'unknown'}
    claim['diagnostics'] = {'test_reported': False, 'test_type': None, 'method': None,
        'target': None, 'specimen': None, 'result': 'positive'}
    return source


def test_explicit_two_facility_mapping_yields_two_focal_signals_without_invented_counts():
    source = multisite()
    result = assembled(source)
    assert len(result['signals']) == 2
    assert {s['locations'][0]['locality'] for s in result['signals']} == {'Villa Norte', 'Villa Sur'}
    for signal in result['signals']:
        assert signal['signal_type'] == 'outbreak'
        assert signal['metrics'] == []
        assert signal['event_date']['start'] is None
        assert signal['diagnostics']['method'] is None
        assert signal['hosts'][0]['verbatim'] == 'cerdos'
        assert signal['evidence'][0]['text'] == source['claims'][0]['evidence'][0]['text']
    assert result == assembled(source)


@pytest.mark.parametrize('change', ['no_mapping', 'different_sentence', 'metric', 'latent_metric',
    'event_date', 'method', 'test', 'sequence', 'lineage', 'transmission', 'canonical_host',
    'mixed_hosts', 'third_location', 'different_province', 'lab_location', 'negative',
    'unconfirmed', 'historical', 'extra_group_claim', 'id_collision',
    'prefix_locality', 'third_text_location', 'split_evidence'])
def test_ambiguous_or_indivisible_multisite_claim_is_preserved_for_review(change):
    source = multisite()
    c = source['claims'][0]
    if change == 'no_mapping': c['evidence'][0]['text'] = 'Se confirmaron casos positivos en cerdos de dos predios en Villa Norte y Villa Sur.'
    elif change == 'different_sentence': c['evidence'][0]['text'] = 'Se confirmaron casos positivos en cerdos de dos predios. Uno en Villa Norte y otro en Villa Sur.'
    elif change == 'metric': c['metric'].update(reported=True, name='cases', value_numeric=2)
    elif change == 'latent_metric': c['metric']['value_numeric'] = 2
    elif change == 'event_date': c['event_date'].update(start='2026-03-04', precision='day')
    elif change == 'method': c['diagnostics']['method'] = 'PCR'
    elif change == 'test': c['diagnostics']['test_reported'] = True
    elif change == 'sequence': c['genomics']['sequence_reported'] = True
    elif change == 'lineage': c['genomics']['lineage'] = 'X'
    elif change == 'transmission': c['transmission']['animal_to_human'] = 'suspected'
    elif change == 'canonical_host': c['subject']['canonical_name'] = 'Sus scrofa'
    elif change == 'mixed_hosts': c['subject']['verbatim'] = 'cerdos y bovinos'
    elif change == 'third_location':
        third = copy.deepcopy(c['locations'][0]); third['locality'] = 'Villa Este'; c['locations'].append(third)
    elif change == 'different_province': c['locations'][1]['admin1'] = 'Otra provincia'
    elif change == 'lab_location': c['locations'][1]['role'] = 'laboratory_location'
    elif change == 'negative': c['diagnostics']['result'] = 'negative'
    elif change == 'unconfirmed': c['verification_status'] = 'reported'
    elif change == 'historical': c['reference_period']['period_type'] = 'historical_period'
    elif change == 'extra_group_claim':
        extra = copy.deepcopy(c); extra['claim_id'] = 'extra'; extra['claim_kind'] = 'intervention'; source['claims'].append(extra)
    elif change == 'prefix_locality': c['evidence'][0]['text'] = c['evidence'][0]['text'].replace('Villa Sur.', 'Villa Sur del Monte.')
    elif change == 'third_text_location': c['evidence'][0]['text'] = c['evidence'][0]['text'].replace('Villa Sur.', 'Villa Sur y otro en Villa Este.')
    elif change == 'split_evidence':
        extra = copy.deepcopy(c['evidence'][0])
        c['evidence'][0]['text'] = 'Se confirmaron casos positivos en cerdos de dos predios,'
        extra['text'] = 'uno en Villa Norte y otro en Villa Sur.'
        c['evidence'].append(extra)
    else:
        extra = copy.deepcopy(c); extra.update(claim_id=c['claim_id']+':site:1', group_id='another', claim_kind='intervention'); source['claims'].append(extra)
    result = assembled(source)
    assert any('ASM-MULTISITE-REVIEW' in warning for warning in result['warnings'])
    assert not any('ASM-MULTISITE-01' in warning for warning in result['warnings'])
