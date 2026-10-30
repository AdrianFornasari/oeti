import json

import pytest

from onehealth_worker.evaluation.corpus import evaluate_corpus


@pytest.mark.parametrize('minimum', [0, -1, 1.9, True, False, '6', None, float('nan'), float('inf')])
def test_gate_rejects_invalid_minimum_without_coercion(tmp_path, minimum):
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'documents': [], 'minimum_documents_for_event_matcher_gate': minimum}))
    with pytest.raises(ValueError, match='minimum_documents_for_event_matcher_gate'):
        evaluate_corpus(manifest)


@pytest.mark.parametrize('minimum', [1, 6])
def test_gate_preserves_valid_integer_minimum(tmp_path, minimum):
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'documents': [], 'minimum_documents_for_event_matcher_gate': minimum}))
    result = evaluate_corpus(manifest)
    assert result['release_gate']['minimum_documents'] == minimum
    assert result['release_gate']['corpus_complete'] is False
    assert result['release_gate']['event_matcher_ready'] is False


def test_gate_retains_default_minimum(tmp_path):
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'documents': []}))
    assert evaluate_corpus(manifest)['release_gate']['minimum_documents'] == 6


@pytest.mark.parametrize('reused_field', ['prediction', 'gold'])
@pytest.mark.parametrize('alias', ['same_path', 'hardlink'])
def test_reused_file_cannot_count_as_six_documents(tmp_path, reused_field, alias):
    from test_attribution_review import artifacts

    fixture = artifacts()
    prediction = tmp_path / 'prediction.json'
    gold = tmp_path / 'gold.json'
    prediction.write_bytes(fixture['signals_bytes'])
    gold.write_text(json.dumps({'expected': json.loads(fixture['signals_bytes'])}))
    originals = {p: p.read_bytes() for p in (prediction, gold)}
    documents = []
    for i in range(6):
        row = {'status': 'adjudicated', 'label': f'document-{i}'}
        for field, source in [('prediction', prediction), ('gold', gold)]:
            target = tmp_path / f'{field}-{i}.json'
            if field == reused_field:
                if alias == 'same_path':
                    target = source
                else:
                    target.hardlink_to(source)
            else:
                target.write_bytes(source.read_bytes())
            row[field] = target.name
        documents.append(row)
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'documents': documents}))
    with pytest.raises(ValueError, match='duplicate'):
        evaluate_corpus(manifest)
    assert all(p.read_bytes() == content for p, content in originals.items())
