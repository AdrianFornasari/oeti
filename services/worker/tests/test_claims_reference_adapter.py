import copy
import hashlib
import json
from pathlib import Path

import pytest

from onehealth_worker.evaluation.claims_reference_adapter import (
    reference_response_schema, adapt_reference_claims, ClaimsReferenceError)
from onehealth_worker.evaluation.evidence_references import build_catalog
from onehealth_worker.evaluation import claims_reference_adapter as adapter
from onehealth_worker.extraction.schema import load_atomic_claims_schema, validate_atomic_claims


def synthetic_value(node, root):
    if '$ref' in node:
        node = root['$defs'][node['$ref'].split('/')[-1]]
    if 'const' in node: return node['const']
    if 'enum' in node: return node['enum'][0]
    kind = node.get('type')
    if isinstance(kind, list) and 'null' in kind: return None
    if kind == 'object': return {key: synthetic_value(node['properties'][key], root) for key in node.get('required', [])}
    if kind == 'array': return [synthetic_value(node['items'], root) for _ in range(node.get('minItems', 0))]
    if kind == 'boolean': return False
    if kind == 'number': return 0.5
    if kind == 'integer': return 1
    return 'synthetic'


@pytest.fixture
def example():
    schema = load_atomic_claims_schema()
    source = 'Córdoba 🐦\r\nPCR positiva.\r\n\r\nOrigen desconocido.'.encode()
    catalog = build_catalog(document_id='D1', source_bytes=source)
    data = json.loads(catalog)
    digest = hashlib.sha256(catalog).hexdigest()
    p = data['paragraphs'][0]
    start = p['text'].index('PCR')
    claim = synthetic_value(schema['$defs']['claim'], schema)
    claim.pop('evidence')
    claim.update(claim_id='C1',group_id='G1',summary='PCR positiva.',
        evidence_refs=[{'document_id':'D1','source_sha256':data['source_sha256'],
            'catalog_sha256':digest,'paragraph_id':p['id'],'start':start,'end':start+13}])
    document = {'raw_item_id':'raw-1','language':'es','document_date':None}
    return {'payload':{'schema_version':'claims-refs-0.1','document':dict(document),'claims':[claim],'warnings':[]},
        'expected_document':document,'document_id':'D1','source_bytes':source,'catalog_bytes':catalog,
        'expected_catalog_sha256':digest,'claims_schema':schema}


def test_valid_copy_preserves_semantic_fields_and_inputs(example):
    before = copy.deepcopy(example)
    result = adapt_reference_claims(**example)
    assert example == before
    validate_atomic_claims(result,example['claims_schema'])
    assert result['schema_version']=='claims-0.1' and result['document']==example['expected_document']
    claim = result['claims'][0]
    assert claim['evidence'][0]['text']=='PCR positiva.' and claim['evidence'][0]['page_number'] is None
    assert {k:v for k,v in claim.items() if k!='evidence'} == {
        k:v for k,v in example['payload']['claims'][0].items() if k!='evidence_refs'}


@pytest.mark.parametrize('change', [
    lambda e:e['payload']['document'].update(document_date='2026-01-01'),
    lambda e:e['payload']['document'].update(language='en'),
    lambda e:e['payload']['document'].update(raw_item_id='other'),
    lambda e:e['payload']['claims'][0]['evidence_refs'][0].update(paragraph_id='missing'),
    lambda e:e['payload']['claims'][0]['evidence_refs'][0].update(end=9999),
    lambda e:e['payload']['claims'][0]['evidence_refs'][0].update(start=True),
    lambda e:e['payload']['claims'][0]['evidence_refs'][0].update(text='SECRET-QUOTE'),
    lambda e:e['payload']['claims'][0].update(evidence=[]),
    lambda e:e['payload']['claims'][0].update(evidence_refs=[]),
    lambda e:e['payload']['claims'][0].update(confidence=float('nan')),
    lambda e:e['payload'].update(schema_version='claims-0.1'),
    lambda e:e.update(expected_catalog_sha256='0'*64),
    lambda e:e.update(source_bytes=b'changed'),
    lambda e:e.update(payload=None),
])
def test_invalid_payloads_and_bindings_redacted(example, change):
    change(example)
    before=copy.deepcopy(example['payload'])
    with pytest.raises(ClaimsReferenceError) as error: adapt_reference_claims(**example)
    assert str(error.value)=='invalid experimental claims or binding'
    assert 'SECRET' not in str(error.value)
    # JSON serializations also compare the NaN case without NaN != NaN pitfalls.
    assert json.dumps(example['payload'])==json.dumps(before)


def test_duplicate_reference_rejected(example):
    example['payload']['claims'][0]['evidence_refs'] *= 2
    with pytest.raises(ClaimsReferenceError): adapt_reference_claims(**example)


@pytest.mark.parametrize('text', ['', 'NOT IN SOURCE'])
def test_post_conversion_schema_and_literal_checks_are_enforced(example, monkeypatch, text):
    monkeypatch.setattr(adapter, 'resolve_references', lambda **kwargs: [
        {'text':text, 'unicode_start':0, 'unicode_end':1}])
    with pytest.raises(ClaimsReferenceError) as error: adapt_reference_claims(**example)
    assert 'SOURCE' not in str(error.value)


def test_result_has_no_shared_mutable_fields_with_input(example):
    result=adapt_reference_claims(**example)
    result['document']['language']='en'
    result['claims'][0]['summary']='changed'
    assert example['payload']['document']['language']=='es'
    assert example['payload']['claims'][0]['summary']=='PCR positiva.'


def test_empty_claims_still_require_correct_catalog_binding(example):
    example['payload']['claims']=[]
    assert adapt_reference_claims(**example)['claims']==[]
    example['catalog_bytes'] += b' '
    with pytest.raises(ClaimsReferenceError): adapt_reference_claims(**example)


def test_schema_snapshot_is_derived_without_base_mutation():
    schema=load_atomic_claims_schema()
    original=copy.deepcopy(schema)
    generated=reference_response_schema(schema)
    snapshot=Path(__file__).resolve().parents[3]/'shared/schemas/atomic-claims-refs-v0.1.experimental.schema.json'
    assert generated==json.loads(snapshot.read_text(encoding='utf-8'))
    assert schema==original
