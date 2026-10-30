import json

import pytest

from onehealth_worker.evaluation.corpus import (
    DEFAULT_RELEASE_THRESHOLDS, evaluate_corpus, evaluate_file,
)


INVALID = [-0.1, 1.1, True, False, '0.9', None, float('nan'), float('inf'), -float('inf')]


@pytest.mark.parametrize('value', INVALID)
@pytest.mark.parametrize('field', list(DEFAULT_RELEASE_THRESHOLDS))
def test_invalid_release_threshold_is_rejected(tmp_path, field, value):
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'documents': [], 'release_thresholds': {field: value}}))
    with pytest.raises(ValueError, match=field):
        evaluate_corpus(manifest)


@pytest.mark.parametrize('value', INVALID)
def test_invalid_matching_threshold_rejected_before_reading_inputs(tmp_path, value):
    with pytest.raises(ValueError, match='threshold'):
        evaluate_file(tmp_path / 'missing-prediction.json', tmp_path / 'missing-gold.json', threshold=value)
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'documents': []}))
    with pytest.raises(ValueError, match='threshold'):
        evaluate_corpus(manifest, threshold=value)


@pytest.mark.parametrize('value', [0, 0.5, 1])
def test_valid_threshold_boundaries_preserve_values(tmp_path, value):
    from test_attribution_review import artifacts

    fixture = artifacts()
    prediction, gold = tmp_path / 'prediction.json', tmp_path / 'gold.json'
    prediction.write_bytes(fixture['signals_bytes'])
    gold.write_text(json.dumps({'expected': json.loads(fixture['signals_bytes'])}))
    result = evaluate_file(prediction, gold, threshold=value)
    assert result['matching_threshold'] == value
    assert result['signal_detection']['f1'] == 1.0
    manifest = tmp_path / 'manifest.json'
    overrides = {field: value for field in DEFAULT_RELEASE_THRESHOLDS}
    manifest.write_text(json.dumps({'documents': [], 'release_thresholds': overrides}))
    assert evaluate_corpus(manifest, threshold=value)['release_gate']['thresholds'] == overrides
