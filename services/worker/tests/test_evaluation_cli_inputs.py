"""Evaluation reports must not replace the data being evaluated."""
import json

import pytest

from onehealth_worker import __main__ as cli


def event_cli_inputs(tmp_path, command_name):
    folder = tmp_path / 'manifests'
    folder.mkdir()
    inputs = {name: tmp_path / f'{name}.json'
              for name in ('event_gold', 'prediction', 'gold', 'claims')}
    inputs['event_manifest'] = folder / 'event.json'
    inputs['corpus_manifest'] = folder / 'corpus.json'
    for name, path in inputs.items():
        path.write_text(json.dumps({'preserve': name}), encoding='utf-8')
    inputs['event_manifest'].write_text(json.dumps({
        'source_gold_documents': ['../event_gold.json'],
    }), encoding='utf-8-sig')
    inputs['corpus_manifest'].write_text(json.dumps({'documents': [{
        'status': 'adjudicated', 'prediction': '../prediction.json',
        'gold': '../gold.json', 'claims': '../claims.json',
    }]}), encoding='utf-8-sig')
    if command_name == 'evaluate-event-matching':
        from onehealth_worker.evaluation import event_matching_v048 as module
        function = 'evaluate_event_matching_benchmark'
        args = ['worker', command_name, '--manifest', str(inputs['event_manifest'])]
    else:
        from onehealth_worker.evaluation import event_matching_predictions_v048 as module
        function = 'evaluate_event_matching_predictions'
        args = ['worker', command_name, '--event-manifest', str(inputs['event_manifest']),
                '--corpus-manifest', str(inputs['corpus_manifest'])]
    return inputs, args, module, function


EVENT_PROTECTED_INPUTS = [
    ('evaluate-event-matching', name) for name in ('event_manifest', 'event_gold')
] + [
    ('evaluate-event-matching-predictions', name) for name in
    ('event_manifest', 'event_gold', 'corpus_manifest', 'prediction', 'gold', 'claims')
]


@pytest.mark.parametrize('command_name,protected_input', EVENT_PROTECTED_INPUTS)
@pytest.mark.parametrize('alias', ['same_path', 'hardlink'])
def test_event_evaluation_rejects_output_alias_before_evaluation(
    monkeypatch, tmp_path, command_name, protected_input, alias,
):
    inputs, args, module, function = event_cli_inputs(tmp_path, command_name)
    originals = {path: path.read_bytes() for path in inputs.values()}
    output = inputs[protected_input]
    if alias == 'hardlink':
        target = output
        output = tmp_path / 'report.json'
        output.hardlink_to(target)
    calls = []

    def evaluate(*args, **kwargs):
        calls.append((args, kwargs))
        return {'report': 'must preserve evaluation inputs'}

    monkeypatch.setattr(module, function, evaluate)
    monkeypatch.setattr('sys.argv', [*args, '--output', str(output)])
    with pytest.raises(ValueError, match='entrada'):
        cli.main()
    assert calls == []
    for path, data in originals.items():
        assert path.read_bytes() == data


@pytest.mark.parametrize('command_name', [
    'evaluate-event-matching', 'evaluate-event-matching-predictions',
])
def test_event_evaluation_allows_separate_report(monkeypatch, tmp_path, capsys, command_name):
    inputs, args, module, function = event_cli_inputs(tmp_path, command_name)
    originals = {path: path.read_bytes() for path in inputs.values()}
    output = tmp_path / 'reports/result.json'
    report = {'pairs': 1}
    calls = []

    def evaluate(*args, **kwargs):
        calls.append((args, kwargs))
        return report

    monkeypatch.setattr(module, function, evaluate)
    monkeypatch.setattr('sys.argv', [*args, '--output', str(output)])
    cli.main()
    assert len(calls) == 1
    assert json.loads(output.read_text(encoding='utf-8')) == report
    assert json.loads(capsys.readouterr().out) == report
    for path, data in originals.items():
        assert path.read_bytes() == data


@pytest.mark.parametrize('protected_input', ['prediction', 'gold'])
@pytest.mark.parametrize('alias', ['same_path', 'hardlink'])
def test_evaluate_extraction_rejects_output_alias_before_evaluating(
    monkeypatch, tmp_path, protected_input, alias,
):
    prediction = tmp_path / 'prediction.json'
    gold = tmp_path / 'gold.json'
    originals = {prediction: b'{"prediction":"preserved"}',
                 gold: b'{"gold":"preserved"}'}
    for path, data in originals.items():
        path.write_bytes(data)
    target = prediction if protected_input == 'prediction' else gold
    output = target
    if alias == 'hardlink':
        output = tmp_path / 'report.json'
        output.hardlink_to(target)
    calls = []

    def evaluate(*args, **kwargs):
        calls.append((args, kwargs))
        return {'report': 'must not overwrite input'}

    monkeypatch.setattr(cli, 'evaluate_file', evaluate)
    monkeypatch.setattr('sys.argv', ['worker', 'evaluate-extraction',
        '--prediction', str(prediction), '--gold', str(gold), '--output', str(output)])
    with pytest.raises(ValueError, match='entrada'):
        cli.main()
    assert calls == []
    for path, data in originals.items():
        assert path.read_bytes() == data


@pytest.mark.parametrize('protected_input', ['manifest', 'prediction', 'gold'])
@pytest.mark.parametrize('alias', ['same_path', 'hardlink'])
def test_evaluate_corpus_rejects_output_alias_of_manifest_or_referenced_input(
    monkeypatch, tmp_path, protected_input, alias,
):
    folder = tmp_path / 'corpus'
    folder.mkdir()
    manifest = folder / 'manifest.json'
    prediction, gold = tmp_path / 'prediction.json', tmp_path / 'gold.json'
    originals = {prediction: b'{"prediction":"preserved"}', gold: b'{"gold":"preserved"}'}
    for path, data in originals.items():
        path.write_bytes(data)
    manifest.write_text(json.dumps({'documents': [{'status': 'adjudicated',
        'prediction': '../prediction.json', 'gold': '../gold.json'}]}), encoding='utf-8')
    originals[manifest] = manifest.read_bytes()
    target = {'manifest': manifest, 'prediction': prediction, 'gold': gold}[protected_input]
    output = target
    if alias == 'hardlink':
        output = tmp_path / 'report.json'
        output.hardlink_to(target)
    calls = []

    def evaluate(*args, **kwargs):
        calls.append((args, kwargs))
        return {'report': 'must not overwrite inputs'}

    monkeypatch.setattr(cli, 'evaluate_corpus', evaluate)
    monkeypatch.setattr('sys.argv', ['worker', 'evaluate-corpus',
        '--manifest', str(manifest), '--output', str(output)])
    with pytest.raises(ValueError, match='entrada'):
        cli.main()
    assert calls == []
    for path, data in originals.items():
        assert path.read_bytes() == data


def test_evaluate_corpus_allows_distinct_existing_report_with_missing_inputs(
    monkeypatch, tmp_path, capsys,
):
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'documents': [
        {'status': 'adjudicated', 'prediction': 'missing.json', 'gold': 'missing-gold.json'},
        {'status': 'pending_adjudication'},
    ]}), encoding='utf-8-sig')
    original = manifest.read_bytes()
    output = tmp_path / 'report.json'
    output.write_text('old report', encoding='utf-8')
    report = {'evaluated_documents': 0, 'release_gate': {'corpus_complete': False}}
    calls = []

    def evaluate(*args, **kwargs):
        calls.append((args, kwargs))
        return report

    monkeypatch.setattr(cli, 'evaluate_corpus', evaluate)
    monkeypatch.setattr('sys.argv', ['worker', 'evaluate-corpus',
        '--manifest', str(manifest), '--output', str(output)])
    cli.main()
    assert calls == [((manifest,), {'threshold': 0.55})]
    assert json.loads(output.read_text(encoding='utf-8')) == report
    assert json.loads(capsys.readouterr().out) == report
    assert manifest.read_bytes() == original


def test_evaluate_extraction_writes_distinct_report_and_preserves_inputs(
    monkeypatch, tmp_path, capsys,
):
    prediction, gold = tmp_path / 'prediction.json', tmp_path / 'gold.json'
    originals = {prediction: b'{"prediction":"preserved"}',
                 gold: b'{"gold":"preserved"}'}
    for path, data in originals.items():
        path.write_bytes(data)
    output = tmp_path / 'reports/report.json'
    report = {'signal_detection': {'tp': 2}}
    calls = []

    def evaluate(*args, **kwargs):
        calls.append((args, kwargs))
        return report

    monkeypatch.setattr(cli, 'evaluate_file', evaluate)
    monkeypatch.setattr('sys.argv', ['worker', 'evaluate-extraction',
        '--prediction', str(prediction), '--gold', str(gold), '--output', str(output)])
    cli.main()
    assert calls == [((prediction, gold), {'threshold': 0.55})]
    assert json.loads(output.read_text(encoding='utf-8')) == report
    assert json.loads(capsys.readouterr().out) == report
    for path, data in originals.items():
        assert path.read_bytes() == data
