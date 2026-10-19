import copy
import hashlib
import json

import pytest

from onehealth_worker.evaluation.evidence_references import (
    EvidenceReferenceError, build_catalog, resolve_references)


@pytest.fixture
def sample():
    source = '  Córdoba 🐦\r\nPCR positiva.\r\n\r\nOrigen desconocido.  '.encode('utf-8')
    catalog = build_catalog(document_id='D1', source_bytes=source)
    payload = json.loads(catalog)
    p = payload['paragraphs'][0]
    start = p['text'].index('PCR')
    ref = {'document_id': 'D1', 'source_sha256': payload['source_sha256'],
           'catalog_sha256': hashlib.sha256(catalog).hexdigest(), 'paragraph_id': p['id'],
           'start': start, 'end': start + len('PCR positiva.')}
    return {'document_id': 'D1', 'source_bytes': source, 'catalog_bytes': catalog,
            'expected_catalog_sha256': ref['catalog_sha256'], 'references': [ref]}


def test_exact_quote_unicode_crlf_and_no_input_mutation(sample):
    before = copy.deepcopy(sample)
    result = resolve_references(**sample)[0]
    assert result['text'] == 'PCR positiva.'
    assert sample['source_bytes'].decode()[result['unicode_start']:result['unicode_end']] == result['text']
    assert sample == before
    payload = json.loads(sample['catalog_bytes'])
    assert len(payload['paragraphs']) == 2 and '\r\n' in payload['paragraphs'][0]['text']
    assert build_catalog(document_id='D1', source_bytes=sample['source_bytes']) == sample['catalog_bytes']


@pytest.mark.parametrize('field,value', [('document_id','D2'), ('source_sha256','0'*64),
    ('catalog_sha256','0'*64), ('paragraph_id','P999'), ('paragraph_id',[]),
    ('start',-1), ('start',True), ('start',1.5), ('end',999), ('end',0)])
def test_invalid_references_rejected(sample, field, value):
    sample['references'][0][field] = value
    with pytest.raises(EvidenceReferenceError): resolve_references(**sample)


@pytest.mark.parametrize('refs', [None, [], {}, [None], ['P001'], [{'unexpected':'value'}]])
def test_malformed_reference_containers(sample, refs):
    sample['references'] = refs
    with pytest.raises(EvidenceReferenceError): resolve_references(**sample)


def test_duplicate_spans_rejected(sample):
    sample['references'] *= 2
    with pytest.raises(EvidenceReferenceError): resolve_references(**sample)


def test_multiple_paragraphs_keep_order_and_absolute_offsets(sample):
    payload = json.loads(sample['catalog_bytes'])
    second = payload['paragraphs'][1]
    reference = {**sample['references'][0], 'paragraph_id': second['id'],
                 'start': 0, 'end': len(second['text'])}
    sample['references'].insert(0, reference)
    result = resolve_references(**sample)
    assert [r['text'] for r in result] == ['Origen desconocido.', 'PCR positiva.']
    assert result[0]['unicode_start'] == second['start']


def test_identical_source_with_different_document_cannot_reuse_catalog(sample):
    other = build_catalog(document_id='D2', source_bytes=sample['source_bytes'])
    digest = hashlib.sha256(other).hexdigest()
    sample.update(catalog_bytes=other, expected_catalog_sha256=digest)
    sample['references'][0]['catalog_sha256'] = digest
    with pytest.raises(EvidenceReferenceError): resolve_references(**sample)


def test_whitespace_only_slice_rejected(sample):
    p = json.loads(sample['catalog_bytes'])['paragraphs'][0]
    start = p['text'].index('\r')
    sample['references'][0].update(start=start, end=start+2)
    with pytest.raises(EvidenceReferenceError): resolve_references(**sample)


@pytest.mark.parametrize('field,value', [('document_id','D2'), ('source_bytes',b'other'),
    ('expected_catalog_sha256','0'*64), ('expected_catalog_sha256',None), ('catalog_bytes',b'{}')])
def test_wrong_trusted_binding_rejected(sample, field, value):
    sample[field] = value
    with pytest.raises(EvidenceReferenceError): resolve_references(**sample)


@pytest.mark.parametrize('change', ['duplicate', 'text', 'offset', 'version', 'document', 'extra', 'format'])
def test_rehashed_catalog_still_requires_deterministic_source_binding(sample, change):
    payload = json.loads(sample['catalog_bytes'])
    if change == 'duplicate': payload['paragraphs'].append(dict(payload['paragraphs'][0]))
    if change == 'text': payload['paragraphs'][0]['text'] = 'invented'
    if change == 'offset': payload['paragraphs'][0]['start'] += 1
    if change == 'version': payload['version'] = 'unknown'
    if change == 'document': payload['document_id'] = 'D2'
    if change == 'extra': payload['extra'] = True
    data = json.dumps(payload, ensure_ascii=False,sort_keys=True,separators=(',', ':')).encode()
    if change == 'format': data += b' '
    digest = hashlib.sha256(data).hexdigest()
    sample.update(catalog_bytes=data, expected_catalog_sha256=digest)
    sample['references'][0]['catalog_sha256'] = digest
    with pytest.raises(EvidenceReferenceError): resolve_references(**sample)


@pytest.mark.parametrize('document,source', [('',b'text'), (' D1',b'text'), (None,b'text'),
    ('D1','text'), ('D1',b'\xff'), ('D1',b' \r\n\r\n '), ('D1',b'')])
def test_invalid_catalog_inputs(document, source):
    with pytest.raises(EvidenceReferenceError): build_catalog(document_id=document, source_bytes=source)


def test_error_does_not_contain_source_or_reference(sample):
    sample['references'][0]['text'] = 'SENSITIVE-CONTENT'
    with pytest.raises(EvidenceReferenceError) as error: resolve_references(**sample)
    assert 'SENSITIVE' not in str(error.value) and 'Córdoba' not in str(error.value)
