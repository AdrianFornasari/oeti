import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from onehealth_worker.evaluation.offline import run_frozen_corpus
from onehealth_worker.evaluation.exploratory import evaluate_exploratory


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def setup_case(tmp_path, count=2):
    root = tmp_path/'frozen'
    root.mkdir()
    docs=[]
    for index in range(count):
        source=root/f'{index}.txt'
        source.write_text('Documento sintético de prueba.\n', encoding='utf-8')
        docs.append({'document_id':f'D{index}', 'title':'Prueba sintética',
            'requested_url':f'https://example.invalid/{index}', 'declared_page_date':None,
            'evaluation_input_path':source.name, 'evaluation_input_sha256':sha(source)})
    manifest=root/'run.json'
    write(manifest,{'case_code':'SYNTHETIC','documents':docs})
    class FakeProvider:
        def extract(self, **kwargs):
            binding=kwargs['document_input'].splitlines()[0].removeprefix('RAW_ITEM_ID: ')
            return SimpleNamespace(payload={'schema_version':'claims-0.1',
                'document':{'raw_item_id':binding,'language':'es','document_date':None},
                'claims':[],'warnings':[]},response_id='fake',usage=None)
    run_dir=tmp_path/'run'
    report=run_frozen_corpus(manifest_path=manifest,output_dir=run_dir,execute=True,provider=FakeProvider())
    prototype=json.loads((Path(__file__).parent/'fixtures/extraction_valid_v04.json').read_text(encoding='utf-8'))
    entries=[]
    for index,result in enumerate(report['results']):
        expected=copy.deepcopy(prototype)
        expected['signals']=expected['signals'][:1]
        expected['signals'][0]['evidence']=[{'type':'text','text':'Documento sintético de prueba.',
                                          'location_in_document':None,'page_number':None}]
        expected['document']={'raw_item_id':result['raw_item_id'],'language':'es','document_date':None}
        gold=root/f'{index}.gold.json'
        write(gold,{'case_code':'SYNTHETIC','evaluation_class':'exploratory_no_independent_review',
            'adjudication':{'status':'agent_provisional','human_review':False},'expected':expected})
        entries.append({'document_id':result['document_id'],'path':gold.name,'sha256':sha(gold),'signals':1})
    prereg=root/'prereg.json'
    write(prereg,{'case_code':'SYNTHETIC','evaluation_class':'exploratory_no_independent_review',
        'run_manifest_path':manifest.name,'run_manifest_sha256':sha(manifest),
        'gold_files':entries,'expected_documents':count,'expected_signals':count,
        'scoring_version':'0.4.7','match_threshold':0.55})
    return prereg,run_dir


def test_complete_synthetic_run_is_exploratory_and_never_release_ready(tmp_path):
    prereg,run=setup_case(tmp_path)
    result=evaluate_exploratory(preregistration_path=prereg,run_dir=run)
    assert result['complete'] is True
    assert result['evaluation_class']=='exploratory_no_independent_review'
    assert result['aggregate']['macro_document_signal_f1']==0
    assert result['aggregate']['micro']['fn']==2
    assert result['aggregate']['mean_signal_role_accuracy'] is None
    assert result['aggregate']['field_metric_document_denominator']==0
    assert result['release_gate']['event_matcher_ready'] is False
    assert result['release_gate']['release_authorized'] is False


@pytest.mark.parametrize('status',['failed','prepared','missing'])
def test_incomplete_run_has_no_overall_metrics_and_labels_subset(tmp_path,status):
    prereg,run=setup_case(tmp_path)
    data=json.loads((run/'report.json').read_text(encoding='utf-8'))
    if status=='missing': data['results'].pop()
    else: data['results'][1]['status']=status
    write(run/'report.json',data)
    result=evaluate_exploratory(preregistration_path=prereg,run_dir=run)
    assert not result['complete']
    assert result['aggregate'] is None
    assert result['conditional_metrics']['evaluated_documents']==1
    assert result['conditional_metrics']['expected_documents']==2
    assert result['summary']['evaluated']==1


def test_all_missing_or_prepared_never_produces_a_score(tmp_path):
    prereg,run=setup_case(tmp_path)
    data=json.loads((run/'report.json').read_text(encoding='utf-8'))
    data['mode']='prepare_only'
    for item in data['results']: item['status']='prepared'
    write(run/'report.json',data)
    result=evaluate_exploratory(preregistration_path=prereg,run_dir=run)
    assert result['aggregate'] is None and result['conditional_metrics'] is None


def test_gold_tampering_or_manifest_tampering_is_rejected(tmp_path):
    prereg,run=setup_case(tmp_path)
    (prereg.parent/'0.gold.json').write_text('{}')
    with pytest.raises(ValueError,match='hash'):
        evaluate_exploratory(preregistration_path=prereg,run_dir=run)


def test_prediction_tampering_is_counted_as_invalid_not_silently_skipped(tmp_path):
    prereg,run=setup_case(tmp_path)
    (run/'002.signals.json').write_text('{}')
    result=evaluate_exploratory(preregistration_path=prereg,run_dir=run)
    assert result['summary']['invalid_prediction']==1
    assert result['aggregate'] is None
    assert result['conditional_metrics']['evaluated_documents']==1


def test_duplicate_or_foreign_result_is_rejected(tmp_path):
    prereg,run=setup_case(tmp_path)
    data=json.loads((run/'report.json').read_text(encoding='utf-8'))
    data['results'].append(data['results'][0])
    write(run/'report.json',data)
    with pytest.raises(ValueError,match='duplicate'):
        evaluate_exploratory(preregistration_path=prereg,run_dir=run)


def test_unsupported_scorer_does_not_fall_back_to_historical_version(tmp_path):
    prereg,run=setup_case(tmp_path)
    data=json.loads(prereg.read_text(encoding='utf-8')); data['scoring_version']='future'
    write(prereg,data)
    with pytest.raises(ValueError,match='scoring'):
        evaluate_exploratory(preregistration_path=prereg,run_dir=run)


def test_changed_run_manifest_binding_is_rejected(tmp_path):
    prereg,run=setup_case(tmp_path)
    data=json.loads((run/'report.json').read_text(encoding='utf-8')); data['manifest_sha256']='0'*64
    write(run/'report.json',data)
    with pytest.raises(ValueError,match='manifest'):
        evaluate_exploratory(preregistration_path=prereg,run_dir=run)


def test_zero_match_documents_do_not_inflate_field_macro(tmp_path):
    prereg,run=setup_case(tmp_path)
    gold=json.loads((prereg.parent/'0.gold.json').read_text(encoding='utf-8'))
    prediction=copy.deepcopy(gold['expected'])
    prediction['signals'][0]['local_signal_id']='SYNTHETIC-PREDICTION'
    write(run/'001.signals.json',prediction)
    data=json.loads((run/'report.json').read_text(encoding='utf-8'))
    data['results'][0].update(signals=1,signals_sha256=sha(run/'001.signals.json'))
    write(run/'report.json',data)
    result=evaluate_exploratory(preregistration_path=prereg,run_dir=run)
    assert result['complete'], result['results']
    assert result['aggregate']['macro_document_signal_f1']==0.5
    assert result['aggregate']['micro']['tp']==1
    assert result['aggregate']['micro']['fn']==1
    assert result['aggregate']['field_metric_document_denominator']==1
    assert result['aggregate']['mean_signal_role_accuracy']==1.0
    assert result['results'][1]['report']['field_metrics']['signal_role_accuracy'] is None


def test_a_changed_hash_cannot_make_wrong_prediction_binding_valid(tmp_path):
    prereg,run=setup_case(tmp_path)
    data=json.loads((run/'001.signals.json').read_text(encoding='utf-8'))
    data['document']['raw_item_id']='11111111-1111-4111-8111-111111111111'
    write(run/'001.signals.json',data)
    report=json.loads((run/'report.json').read_text(encoding='utf-8'))
    report['results'][0]['signals_sha256']=sha(run/'001.signals.json')
    write(run/'report.json',report)
    result=evaluate_exploratory(preregistration_path=prereg,run_dir=run)
    assert result['summary']['invalid_prediction']==1


def test_claiming_human_review_in_gold_is_not_accepted(tmp_path):
    prereg,run=setup_case(tmp_path)
    gold_path=prereg.parent/'0.gold.json'
    gold=json.loads(gold_path.read_text(encoding='utf-8')); gold['adjudication']['human_review']=True
    write(gold_path,gold)
    pre=json.loads(prereg.read_text(encoding='utf-8')); pre['gold_files'][0]['sha256']=sha(gold_path)
    write(prereg,pre)
    with pytest.raises(ValueError,match='agent-provisional'):
        evaluate_exploratory(preregistration_path=prereg,run_dir=run)


def test_invalid_prediction_json_with_updated_hash_still_counts_as_failure(tmp_path):
    prereg,run=setup_case(tmp_path)
    (run/'001.signals.json').write_text('not json')
    report=json.loads((run/'report.json').read_text(encoding='utf-8'))
    report['results'][0]['signals_sha256']=sha(run/'001.signals.json')
    write(run/'report.json',report)
    result=evaluate_exploratory(preregistration_path=prereg,run_dir=run)
    assert result['summary']['invalid_prediction']==1


def test_cli_does_not_overwrite_a_previous_evaluation(tmp_path):
    from onehealth_worker.evaluation.exploratory import main
    prereg,run=setup_case(tmp_path)
    output=tmp_path/'evaluation.json'
    output.write_text('keep previous measurement')
    with pytest.raises(ValueError,match='exists'):
        main(['--preregistration',str(prereg),'--run-dir',str(run),'--output',str(output)])
    assert output.read_text(encoding='utf-8')=='keep previous measurement'


def test_scorer_failure_is_not_attributed_to_invalid_model_output(tmp_path,monkeypatch):
    from onehealth_worker.evaluation import exploratory
    prereg,run=setup_case(tmp_path)
    def fails(*args,**kwargs):
        raise RuntimeError('internal scorer error')
    monkeypatch.setattr(exploratory,'evaluate_payloads',fails)
    result=evaluate_exploratory(preregistration_path=prereg,run_dir=run)
    assert result['summary']['evaluation_error']==2
    assert result['summary']['invalid_prediction']==0
    assert result['aggregate'] is None and result['conditional_metrics'] is None
