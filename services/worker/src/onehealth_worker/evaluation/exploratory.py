"""Evaluate frozen, agent-adjudicated corpora without granting release readiness."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from .offline import _preflight, _sha
from .scoring_v047 import evaluate_payloads
from ..extraction.schema import validate_extraction, validate_literal_evidence

CLASSIFICATION = 'exploratory_no_independent_review'


def _load(path):
    return json.loads(path.read_bytes().decode('utf-8-sig'))


def _inside(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError('artifact path must be relative')
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('artifact path escapes package')
    return path


def _verified(path, digest):
    raw = path.read_bytes()
    if _sha(raw) != digest:
        raise ValueError('artifact hash mismatch')
    return json.loads(raw.decode('utf-8-sig'))


def _aggregate(evaluated, expected_count):
    count = len(evaluated)
    tp = sum(row['report']['signal_detection']['tp'] for row in evaluated)
    fp = sum(row['report']['signal_detection']['fp'] for row in evaluated)
    fn = sum(row['report']['signal_detection']['fn'] for row in evaluated)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2*precision*recall/(precision+recall) if precision+recall else 0.0
    defined = [row for row in evaluated if row['report']['signal_detection']['matched_signals'] > 0]
    result = {
        'evaluated_documents': count, 'expected_documents': expected_count,
        'macro_document_signal_f1': round(sum(row['report']['signal_detection']['f1'] for row in evaluated)/count, 6),
        'micro': {'tp': tp, 'fp': fp, 'fn': fn, 'precision': round(precision,6),
                  'recall': round(recall,6), 'f1': round(f1,6)},
        'field_metric_document_denominator': len(defined),
        'matched_signal_denominator': tp,
        'field_metric_convention': 'Macro over documents with at least one matched signal; zero matches means undefined, not perfect accuracy.',
    }
    for field in ('signal_role_accuracy', 'signal_type_accuracy', 'evidence_exact_f1', 'evidence_support_f1'):
        result['mean_'+field] = round(sum(row['report']['field_metrics'][field] for row in defined)/len(defined),6) if defined else None
    return result


def evaluate_exploratory(*, preregistration_path: Path, run_dir: Path):
    preregistration_path = Path(preregistration_path).resolve()
    root, run_dir = preregistration_path.parent, Path(run_dir).resolve()
    prereg = _load(preregistration_path)
    if prereg.get('evaluation_class') != CLASSIFICATION:
        raise ValueError('exploratory classification required')
    if prereg.get('scoring_version') != '0.4.7':
        raise ValueError('unsupported scoring version')
    threshold = prereg.get('match_threshold')
    if isinstance(threshold, bool) or not isinstance(threshold, (int,float)) or not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError('invalid preregistered match threshold')
    manifest_path = _inside(root, prereg.get('run_manifest_path'))
    _verified(manifest_path, prereg.get('run_manifest_sha256'))
    manifest, manifest_sha, prepared = _preflight(manifest_path)
    if prereg.get('case_code') != manifest['case_code']:
        raise ValueError('case_code mismatch')
    gold_entries = prereg.get('gold_files', [])
    if not isinstance(gold_entries,list) or len(gold_entries) != len(prepared) or prereg.get('expected_documents') != len(prepared):
        raise ValueError('gold document count mismatch')
    gold_by_id, gold_paths = {}, set()
    documents = {item[0]: item for item in prepared}
    for entry in gold_entries:
        identifier = entry.get('document_id')
        if identifier in gold_by_id:
            raise ValueError('duplicate gold document')
        if identifier not in documents:
            raise ValueError('foreign gold document')
        path = _inside(root, entry.get('path'))
        if path in gold_paths:
            raise ValueError('duplicate gold path')
        gold_paths.add(path)
        gold = _verified(path, entry.get('sha256'))
        adjudication = gold.get('adjudication', {})
        if (gold.get('case_code') != manifest['case_code'] or gold.get('evaluation_class') != CLASSIFICATION
            or adjudication.get('status') != 'agent_provisional' or adjudication.get('human_review') is not False):
            raise ValueError('gold must explicitly retain agent-provisional status')
        expected = gold['expected']
        validate_extraction(expected)
        document = documents[identifier][3]
        if expected['document']['raw_item_id'] != document.raw_item_id:
            raise ValueError('gold binding differs from frozen input')
        validate_literal_evidence(expected, document.raw_text)
        if entry.get('signals') != len(expected['signals']):
            raise ValueError('gold signal count mismatch')
        gold_by_id[identifier] = gold
    if prereg.get('expected_signals') != sum(len(g['expected']['signals']) for g in gold_by_id.values()):
        raise ValueError('expected signal count mismatch')
    run_path = _inside(run_dir,'report.json')
    run = _load(run_path)
    if run.get('manifest_sha256') != manifest_sha:
        raise ValueError('run manifest hash mismatch')
    if run.get('case_code') != manifest['case_code'] or run.get('evaluation_class') != CLASSIFICATION:
        raise ValueError('run classification or case differs')
    if run.get('mode') not in ('prepare_only','injected_provider'):
        raise ValueError('unsupported run mode')
    results = {}
    for item in run.get('results', []):
        identifier = item.get('document_id')
        if identifier in results:
            raise ValueError('duplicate run result')
        if identifier not in documents:
            raise ValueError('foreign run result')
        if item.get('status') not in ('prepared','generated','failed'):
            raise ValueError('unknown run status')
        if run['mode'] == 'prepare_only' and item['status'] != 'prepared':
            raise ValueError('preparation cannot contain model results')
        results[identifier] = item
    rows, evaluated = [], []
    for index, (identifier, source, source_sha, document, document_input) in enumerate(prepared,1):
        item = results.get(identifier)
        row = {'document_id': identifier, 'status': item['status'] if item else 'missing',
               'adjudication': 'agent_provisional'}
        if item and item['status'] == 'generated':
            prefix = f'{index:03d}'
            phase = 'prediction_validation'
            try:
                expected_input = document_input.encode('utf-8')
                if (item.get('raw_item_id') != document.raw_item_id or item.get('source_sha256') != source_sha
                    or item.get('input_sha256') != _sha(expected_input) or item.get('input_path') != f'{prefix}.input.txt'
                    or _inside(run_dir,f'{prefix}.input.txt').read_bytes() != expected_input):
                    raise ValueError('input provenance mismatch')
                if item.get('signals_path') != f'{prefix}.signals.json':
                    raise ValueError('prediction filename mismatch')
                prediction = _verified(_inside(run_dir,f'{prefix}.signals.json'),item.get('signals_sha256'))
                validate_extraction(prediction)
                if prediction['document']['raw_item_id'] != document.raw_item_id:
                    raise ValueError('prediction binding mismatch')
                validate_literal_evidence(prediction,document.raw_text)
                if item.get('signals') != len(prediction['signals']):
                    raise ValueError('prediction signal count mismatch')
                phase = 'scoring'
                scored = evaluate_payloads(prediction,gold_by_id[identifier],threshold=threshold)
                scored.pop('release_gate',None)
                scored.pop('composite_score',None)
                if scored['signal_detection']['matched_signals'] == 0:
                    scored['field_metrics'] = {key: None for key in scored['field_metrics']}
                row.update(status='evaluated', report=scored,
                    prediction_sha256=item['signals_sha256'])
                evaluated.append(row)
            except Exception as error:
                row.update(status='evaluation_error' if phase == 'scoring' else 'invalid_prediction',
                    error_type=type(error).__name__)
        rows.append(row)
    complete = len(evaluated) == len(prepared)
    metrics = _aggregate(evaluated,len(prepared)) if evaluated else None
    return {
        'case_code': manifest['case_code'], 'evaluation_class': CLASSIFICATION,
        'evaluation_schema_version': 'exploratory-0.1',
        'independent_review': False, 'complete': complete,
        'scoring_version': '0.4.7', 'matching_threshold': threshold,
        'preregistration_sha256': _sha(preregistration_path.read_bytes()),
        'run_report_sha256': _sha(run_path.read_bytes()),
        'adapter_sha256': _sha(Path(__file__).read_bytes()),
        'scorer_sha256': {name: _sha(Path(__file__).with_name(name).read_bytes())
            for name in ('scoring.py','scoring_v046.py','scoring_v047.py')},
        'summary': {status: sum(row['status']==status for row in rows)
            for status in ('evaluated','failed','prepared','missing','invalid_prediction','evaluation_error')},
        'aggregate': metrics if complete else None,
        'conditional_metrics': {**metrics,'scope':'successful_documents_only_not_full_corpus'} if metrics and not complete else None,
        'results': rows,
        'release_gate': {'release_authorized': False, 'event_matcher_ready': False,
            'reason': 'Exploratory extraction with agent provisional gold; independent validation and event matching not measured.'},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description='Score a frozen exploratory corpus locally; no provider or database.')
    parser.add_argument('--preregistration',required=True,type=Path)
    parser.add_argument('--run-dir',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise ValueError('output already exists')
    report = evaluate_exploratory(preregistration_path=args.preregistration,run_dir=args.run_dir)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('xb') as stream:
        stream.write((json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    print(json.dumps({'complete':report['complete'],'summary':report['summary']},ensure_ascii=False))


if __name__ == '__main__':
    main()
