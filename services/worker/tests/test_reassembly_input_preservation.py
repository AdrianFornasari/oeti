import json

import pytest

from onehealth_worker.evaluation.reassembly import reassemble_evaluation_corpus
from test_attribution_review import artifacts


def corpus_files(tmp_path):
    fixture = artifacts()
    claims = tmp_path / 'claims.json'
    other_claims = tmp_path / 'other-claims.json'
    gold = tmp_path / 'gold.json'
    claims.write_bytes(fixture['claims_bytes'])
    other_claims.write_bytes(fixture['claims_bytes'])
    gold.write_text(json.dumps({'expected': json.loads(fixture['signals_bytes'])}), encoding='utf-8')
    return claims, other_claims, gold


@pytest.mark.parametrize('protected_input', ['manifest', 'other_claims', 'gold'])
@pytest.mark.parametrize('alias', ['same_path', 'hardlink'])
def test_reassembly_rejects_input_alias_before_writing_any_prediction(
    tmp_path, protected_input, alias,
):
    claims, other_claims, gold = corpus_files(tmp_path)
    manifest = tmp_path / 'manifest.json'
    first_prediction = tmp_path / 'first-prediction.json'
    target = {'manifest': manifest, 'other_claims': other_claims, 'gold': gold}[protected_input]
    output = target if alias == 'same_path' else tmp_path / 'alias.json'
    manifest.write_text(json.dumps({'benchmark_version': '0.4.6', 'documents': [
        {'status': 'adjudicated', 'claims': claims.name, 'prediction': first_prediction.name,
         'gold': gold.name},
        {'status': 'adjudicated', 'claims': claims.name, 'prediction': output.name},
        {'status': 'pending_adjudication', 'claims': other_claims.name},
    ]}), encoding='utf-8')
    if alias == 'hardlink':
        output.hardlink_to(target)
    originals = {path: path.read_bytes() for path in (manifest, claims, other_claims, gold)}
    with pytest.raises(ValueError, match='entrada'):
        reassemble_evaluation_corpus(manifest_path=manifest, force=True)
    assert not first_prediction.exists()
    for path, data in originals.items():
        assert path.read_bytes() == data


def test_reassembly_writes_separate_prediction_and_preserves_all_inputs(tmp_path):
    claims, other_claims, gold = corpus_files(tmp_path)
    manifest = tmp_path / 'manifest.json'
    output = tmp_path / 'predictions/result.json'
    manifest.write_text(json.dumps({'benchmark_version': '0.4.6', 'documents': [
        {'status': 'adjudicated', 'claims': claims.name,
         'prediction': 'predictions/result.json', 'gold': gold.name},
    ]}), encoding='utf-8')
    originals = {path: path.read_bytes() for path in (manifest, claims, other_claims, gold)}
    result = reassemble_evaluation_corpus(manifest_path=manifest)
    assert result['results'][0]['status'] == 'reassembled'
    assert json.loads(output.read_text(encoding='utf-8'))['signals']
    for path, data in originals.items():
        assert path.read_bytes() == data


def test_reassembly_without_force_keeps_existing_prediction_alias_untouched(tmp_path):
    claims, _, _ = corpus_files(tmp_path)
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'documents': [
        {'status': 'adjudicated', 'claims': claims.name, 'prediction': claims.name},
    ]}), encoding='utf-8')
    before = claims.read_bytes()
    result = reassemble_evaluation_corpus(manifest_path=manifest)
    assert result['results'][0]['status'] == 'existing'
    assert claims.read_bytes() == before


@pytest.mark.parametrize('force', [False, True])
def test_reassembly_rejects_shared_prediction_from_different_claims_before_writing(tmp_path, force):
    claims, other_claims, gold = corpus_files(tmp_path)
    other = json.loads(other_claims.read_bytes())
    other['document']['raw_item_id'] = '00000000-0000-4000-8000-000000000002'
    other_claims.write_text(json.dumps(other), encoding='utf-8')
    manifest = tmp_path / 'manifest.json'
    output = tmp_path / 'shared.json'
    manifest.write_text(json.dumps({'benchmark_version': '0.4.6', 'documents': [
        {'status': 'adjudicated', 'claims': claims.name, 'prediction': output.name},
        {'status': 'adjudicated', 'claims': other_claims.name, 'prediction': output.name},
    ]}), encoding='utf-8')
    originals = {path: path.read_bytes() for path in (manifest, claims, other_claims, gold)}
    with pytest.raises(ValueError, match='destino'):
        reassemble_evaluation_corpus(manifest_path=manifest, force=force)
    assert not output.exists()
    for path, data in originals.items():
        assert path.read_bytes() == data


def test_forced_reassembly_rejects_hardlinked_predictions_from_different_claims(tmp_path):
    claims, other_claims, _ = corpus_files(tmp_path)
    output = tmp_path / 'first.json'
    alias = tmp_path / 'second.json'
    output.write_bytes(b'previous prediction')
    alias.hardlink_to(output)
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'documents': [
        {'status': 'adjudicated', 'claims': claims.name, 'prediction': output.name},
        {'status': 'adjudicated', 'claims': other_claims.name, 'prediction': alias.name},
    ]}), encoding='utf-8')
    with pytest.raises(ValueError, match='destino'):
        reassemble_evaluation_corpus(manifest_path=manifest, force=True)
    assert output.read_bytes() == alias.read_bytes() == b'previous prediction'


def test_reassembly_allows_shared_prediction_for_the_same_claims(tmp_path):
    claims, _, _ = corpus_files(tmp_path)
    manifest = tmp_path / 'manifest.json'
    output = tmp_path / 'shared.json'
    manifest.write_text(json.dumps({'documents': [
        {'status': 'adjudicated', 'claims': claims.name, 'prediction': output.name},
        {'status': 'adjudicated', 'claims': claims.name, 'prediction': output.name},
    ]}), encoding='utf-8')
    result = reassemble_evaluation_corpus(manifest_path=manifest)
    assert [row['status'] for row in result['results']] == ['reassembled', 'existing']
    assert json.loads(output.read_text(encoding='utf-8'))['signals']
