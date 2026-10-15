import copy
import json
from pathlib import Path

import pytest

from onehealth_worker.extraction.assembly_v046 import assemble_claims_payload
from onehealth_worker.extraction.schema import validate_atomic_claims, validate_extraction

ROOT = Path(__file__).resolve().parents[3]


def claims(subject_type, verbatim='animal observado'):
    # Reuse only the structural shape of an existing validated claim, not H5 gold.
    original = json.loads((ROOT / 'evaluation/predictions/mv-hondius/2026-05-04-v044-atomic-automatic.claims.json').read_text(encoding='utf-8'))
    claim = copy.deepcopy(original['claims'][0])
    claim.update(claim_id='test', group_id='test', claim_kind='case_status',
        domains=['animal'], summary='Observación de prueba.')
    claim['subject'] = {'verbatim': verbatim, 'canonical_name': None,
        'subject_type': subject_type, 'confidence': 0.7}
    return {'schema_version': 'claims-0.1', 'document': original['document'],
        'claims': [claim], 'warnings': []}


@pytest.mark.parametrize('verbatim', ['animal observado', 'aves de corral', 'mamífero sin clasificar'])
def test_generic_animal_becomes_valid_host_without_inferring_domestication(verbatim):
    source = claims('animal', verbatim)
    before = copy.deepcopy(source)
    validate_atomic_claims(source)
    result = assemble_claims_payload(source)
    validate_extraction(result)
    assert result['signals'][0]['hosts'] == [{'verbatim': verbatim,
        'canonical_name': None, 'host_type': 'other', 'confidence': 0.7}]
    assert source == before


@pytest.mark.parametrize('subject_type', ['human', 'wildlife', 'vector'])
def test_explicit_biological_host_types_remain_supported(subject_type):
    source = claims(subject_type)
    validate_atomic_claims(source)
    result = assemble_claims_payload(source)
    validate_extraction(result)
    host = result['signals'][0]['hosts'][0]
    assert host['host_type'] == subject_type
    assert host['canonical_name'] == ('Homo sapiens' if subject_type == 'human' else None)


@pytest.mark.parametrize('subject_type', ['environment', 'pathogen', 'population', 'mobility', 'other'])
def test_non_host_subjects_are_not_promoted_to_hosts(subject_type):
    source = claims(subject_type)
    validate_atomic_claims(source)
    result = assemble_claims_payload(source)
    validate_extraction(result)
    assert result['signals'][0]['hosts'] == []
