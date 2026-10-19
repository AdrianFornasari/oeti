import copy
import hashlib
import json

import pytest

from test_offline_frozen_corpus import manifest, FakeProvider
from test_claims_reference_adapter import synthetic_value
from onehealth_worker.evaluation.offline import run_frozen_corpus
from onehealth_worker.extraction.schema import load_atomic_claims_schema
from onehealth_worker.extraction import assembly_v046

POLICY={'mode':'unknown_only','basis':'Reviewed scope contains reference periods, not event dates.'}
UNKNOWN={'start':None,'end':None,'precision':'unknown'}
DAY={'start':'2026-10-19','end':None,'precision':'day'}


def set_policy(path,value,index=0):
    data=json.loads(path.read_text())
    data['documents'][index]['event_date_policy']=value
    path.write_text(json.dumps(data))


class DatedProvider(FakeProvider):
    def __init__(self,event_date=UNKNOWN):
        super().__init__();self.event_date=copy.deepcopy(event_date)

    def extract(self,**kwargs):
        response=super().extract(**kwargs)
        schema=load_atomic_claims_schema()
        claim=synthetic_value(schema['$defs']['claim'],schema)
        text=kwargs['document_input'].split('DOCUMENT_TEXT_BEGIN\n',1)[1].split('\nDOCUMENT_TEXT_END',1)[0]
        claim.update(claim_id='C1',group_id='G1',claim_kind='case_status',summary='Synthetic case.',
            event_date=copy.deepcopy(self.event_date),evidence=[{'type':'text','text':text,
                'location_in_document':None,'page_number':None}])
        response.payload['claims']=[claim]
        return response


@pytest.mark.parametrize('policy',[None,{},True,{'mode':'auto','basis':'x'},
    {'mode':'unknown_only','basis':''},{'mode':'unknown_only','basis':7},
    {'mode':'unknown_only','basis':'x','extra':True}])
def test_bad_policy_fails_preflight_before_calls_or_outputs(tmp_path,policy):
    path=manifest(tmp_path);set_policy(path,policy);provider=DatedProvider()
    with pytest.raises(ValueError):
        run_frozen_corpus(manifest_path=path,output_dir=tmp_path/'run',execute=True,provider=provider)
    assert not provider.calls and not (tmp_path/'run').exists()


def test_unknown_policy_keeps_uuid_inputs_claims_and_signals_identical(tmp_path):
    path=manifest(tmp_path)
    a=run_frozen_corpus(manifest_path=path,output_dir=tmp_path/'old',execute=True,provider=DatedProvider())
    set_policy(path,POLICY)
    b=run_frozen_corpus(manifest_path=path,output_dir=tmp_path/'new',execute=True,provider=DatedProvider())
    assert a['results'][0]['status']==b['results'][0]['status']=='generated'
    assert 'verified_event_date_policy' not in a['results'][0]
    assert b['results'][0]['verified_event_date_policy']==POLICY
    for suffix in ['input.txt','claims.json','signals.json']:
        assert (tmp_path/'old'/f'001.{suffix}').read_bytes()==(tmp_path/'new'/f'001.{suffix}').read_bytes()


@pytest.mark.parametrize('event_date',[DAY,{'start':'2026-01-01','end':'2026-06-30','precision':'unknown'},
    {'start':None,'end':None,'precision':'year'}])
def test_rejects_known_dates_and_false_unknown_without_repair(tmp_path,event_date):
    path=manifest(tmp_path);set_policy(path,POLICY)
    result=run_frozen_corpus(manifest_path=path,output_dir=tmp_path/'run',execute=True,provider=DatedProvider(event_date))['results'][0]
    assert result['status']=='failed' and result['error_type']=='EventDatePolicyError'
    assert result['phase']=='validation' and result['usage']['total_tokens']==10
    assert result['response_id']=='fake-response'
    saved=json.loads((tmp_path/'run/001.claims.json').read_text())
    assert saved['claims'][0]['event_date']==event_date
    assert not (tmp_path/'run/001.signals.json').exists()


def test_explicit_source_day_without_policy_remains_valid(tmp_path):
    path=manifest(tmp_path)
    source=path.parent/'0.txt'
    source.write_bytes(b'The event occurred on 2026-10-19.\n')
    data=json.loads(path.read_text());data['documents'][0]['evaluation_input_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    path.write_text(json.dumps(data))
    result=run_frozen_corpus(manifest_path=path,output_dir=tmp_path/'run',execute=True,provider=DatedProvider(DAY))
    assert result['results'][0]['status']=='generated'


def test_post_assembly_policy_is_also_enforced(tmp_path,monkeypatch):
    path=manifest(tmp_path);set_policy(path,POLICY)
    original=assembly_v046.assemble_claims_payload
    def dated(payload):
        output=original(payload);output['signals'][0]['event_date']=dict(DAY);return output
    monkeypatch.setattr(assembly_v046,'assemble_claims_payload',dated)
    result=run_frozen_corpus(manifest_path=path,output_dir=tmp_path/'run',execute=True,provider=DatedProvider())
    assert result['results'][0]['error_type']=='EventDatePolicyError'
    assert not (tmp_path/'run/001.signals.json').exists()


def test_policy_is_per_document_and_prepare_only_records_it(tmp_path):
    path=manifest(tmp_path,2);set_policy(path,POLICY,index=1)
    prepared=run_frozen_corpus(manifest_path=path,output_dir=tmp_path/'plan')
    assert 'verified_event_date_policy' not in prepared['results'][0]
    assert prepared['results'][1]['verified_event_date_policy']==POLICY
    result=run_frozen_corpus(manifest_path=path,output_dir=tmp_path/'run',execute=True,provider=DatedProvider(DAY))
    assert [r['status'] for r in result['results']]==['generated','failed']


def test_empty_claims_allowed_under_policy(tmp_path):
    path=manifest(tmp_path);set_policy(path,POLICY)
    report=run_frozen_corpus(manifest_path=path,output_dir=tmp_path/'run',execute=True,provider=FakeProvider())
    assert report['results'][0]['status']=='generated'


def test_invalid_second_policy_prevents_first_call(tmp_path):
    path=manifest(tmp_path,2);set_policy(path,None,index=1);provider=DatedProvider()
    with pytest.raises(ValueError):
        run_frozen_corpus(manifest_path=path,output_dir=tmp_path/'run',execute=True,provider=provider)
    assert not provider.calls and not (tmp_path/'run').exists()
