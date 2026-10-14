from copy import deepcopy
from pathlib import Path
import unicodedata

import pytest

from onehealth_worker.evaluation.event_matching_v048 import (
    detect_hard_conflict, evaluate_signal_pair_v048, load_event_matching_benchmark,
)

PHRASES = [
    'La ANLIS descartó vínculo, sin relación con el brote',
    'La señal no tiene relación: sin relación con el brote',
    'La ANLIS descartó el vínculo',
    'LA ANLIS DESCARTÓ VÍNCULO, SIN RELACIÓN CON EL BROTE',
    unicodedata.normalize('NFD', 'La ANLIS descartó vínculo, sin relación con el brote'),
    'La ANLIS descarto vinculo, sin relacion con el brote',
    'The sequence is unrelated to the outbreak',
]


@pytest.mark.parametrize('phrase', PHRASES)
@pytest.mark.parametrize('channel', ['signal_summary', 'evidence'])
@pytest.mark.parametrize('genomic', [False, True])
def test_explicit_refutation_veto_handles_accents_and_preserves_input(phrase, channel, genomic):
    negative = {'signal_role': 'negative_evidence', 'verification_status': 'refuted',
        'signal_summary': '', 'evidence': [], 'genomics': {'sequence_reported': genomic}}
    if channel == 'signal_summary': negative[channel] = phrase
    else: negative[channel] = [{'text': phrase}]
    counterpart = {'genomics': {'sequence_reported': genomic}}
    original = deepcopy((negative, counterpart))
    policy = {'explicit_genomic_incompatibility': genomic, 'explicit_official_non_relation': True}
    reason = 'explicit_genomic_incompatibility' if genomic else 'explicit_official_non_relation'
    for first, second in ((negative, counterpart), (counterpart, negative)):
        assert detect_hard_conflict(first, second, policy) == {'hard_conflict': True, 'reason': reason}
    assert (negative, counterpart) == original


@pytest.mark.parametrize('role,status', [('primary_event', 'refuted'), ('negative_evidence', 'unknown')])
def test_text_marker_does_not_remove_refutation_preconditions(role, status):
    signal = {'signal_role': role, 'verification_status': status,
        'signal_summary': PHRASES[0]}
    assert detect_hard_conflict(signal, {}, {'explicit_official_non_relation': True})['hard_conflict'] is False


@pytest.mark.parametrize('phrase', [PHRASES[0], PHRASES[4]])
def test_full_matcher_rejects_accented_official_non_relation(phrase):
    manifest_path = Path(__file__).resolve().parents[3] / 'config/evaluation/mv-hondius-event-matching-v048.json'
    benchmark = load_event_matching_benchmark(manifest_path)
    negative = deepcopy(benchmark.signal_index['GS-MVH-20260629-03'])
    counterpart = deepcopy(benchmark.signal_index['GS-MVH-20260526-02'])
    negative.update({'signal_summary': phrase, 'evidence': [], 'signal_role': 'negative_evidence',
        'verification_status': 'refuted', 'transmission': {}, 'genomics': {'sequence_reported': True}})
    counterpart['genomics'] = {'sequence_reported': True}
    original = deepcopy((negative, counterpart))
    for first, second in ((negative, counterpart), (counterpart, negative)):
        result = evaluate_signal_pair_v048(first, second, benchmark.manifest)
        assert result['gate'] == 'eligible'
        assert result['hard_conflict'] is True
        assert result['decision'] == 'rejected'
        assert result['merge_allowed'] is False
        assert result['hard_conflict_reason'] == 'explicit_genomic_incompatibility'
    assert (negative, counterpart) == original
