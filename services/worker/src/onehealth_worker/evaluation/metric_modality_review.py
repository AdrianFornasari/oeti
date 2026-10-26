"""Explicit development-only modality review; no inference or canonical changes."""
from copy import deepcopy
import hashlib
import json
import re


class BindingError(ValueError):
    """Invalid artifact or annotation binding; messages exclude source content."""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _pairs(items):
    result = {}
    for key,value in items:
        if key in result:
            raise BindingError('duplicate key')
        result[key] = value
    return result


def _reject_constant(value):
    raise BindingError('non-finite number')


def _load(data,expected):
    if not isinstance(data,bytes) or digest(data)!=expected:
        raise BindingError('artifact hash mismatch')
    try:
        result=json.loads(data.decode('utf-8'),object_pairs_hook=_pairs,parse_constant=_reject_constant)
        json.dumps(result,allow_nan=False)
        return result
    except (ValueError,UnicodeError,TypeError,OverflowError):
        raise BindingError('invalid artifact') from None


def build_assertion_view(*,claims_bytes,claims_sha256,source_text,source_sha256,
                         annotation_bytes,annotation_sha256,claims_schema,expected_document):
    """No modality inference, deduplication, aggregation or semantic acceptance.

    Hashes and schema are supplied by the trusted caller. The annotation's
    reviewer string is provenance data, not authenticated identity/authorization.
    """
    from jsonschema import Draft202012Validator, FormatChecker
    claims=_load(claims_bytes,claims_sha256)
    annotations=_load(annotation_bytes,annotation_sha256)
    if not isinstance(source_text,str) or digest(source_text.encode())!=source_sha256:
        raise BindingError('source hash mismatch')
    # Caller must supply the trusted local schema, not an untrusted remote schema.
    def local_refs(value):
        if isinstance(value,dict):
            for key,child in value.items():
                if key in {'$ref','$dynamicRef','$recursiveRef'} and (not isinstance(child,str) or not child.startswith('#')):
                    raise BindingError('external schema reference')
                local_refs(child)
        elif isinstance(value,list):
            for child in value:
                local_refs(child)
    local_refs(claims_schema)
    Draft202012Validator.check_schema(claims_schema)
    if not Draft202012Validator(claims_schema,format_checker=FormatChecker()).is_valid(claims):
        raise BindingError('invalid claims schema')
    if not isinstance(annotations,dict) or set(annotations)!={'version','claims_sha256','source_sha256','entries'}:
        raise BindingError('invalid annotation envelope')
    if (annotations['version']!='offline-modality-annotation-draft-1'
            or annotations['claims_sha256']!=claims_sha256 or annotations['source_sha256']!=source_sha256
            or not isinstance(annotations['entries'],list)):
        raise BindingError('annotation binding mismatch')
    if (not isinstance(expected_document,dict)
            or json.dumps(claims['document'],sort_keys=True,allow_nan=False)
            != json.dumps(expected_document,sort_keys=True,allow_nan=False)):
        raise BindingError('document binding mismatch')
    ids=[c['claim_id'] for c in claims['claims']]
    if len(ids)!=len(set(ids)):
        raise BindingError('duplicate claim identity')
    # Literal checks protect binding only, not completeness or semantic relevance.
    for claim in claims['claims']:
        for evidence in claim['evidence']:
            quote=' '.join(evidence['text'].split())
            if not quote or quote not in ' '.join(source_text.split()):
                raise BindingError('nonliteral evidence')
    by_pointer={}
    for annotation in annotations['entries']:
        required={'claim_pointer','modality','reviewer','review_kind','evidence_pointer'}
        if not isinstance(annotation,dict) or set(annotation)!=required:
            raise BindingError('invalid annotation entry')
        pointer=annotation['claim_pointer']
        if not isinstance(pointer,str) or re.fullmatch(r'/claims/(0|[1-9][0-9]*)',pointer) is None:
            raise BindingError('invalid claim pointer')
        index=int(pointer.split('/')[-1])
        if index>=len(claims['claims']) or pointer in by_pointer:
            raise BindingError('unmatched or conflicting annotation')
        claim=claims['claims'][index]
        if not claim['metric']['reported']:
            raise BindingError('annotation targets nonmetric claim')
        evidence_pointer=annotation['evidence_pointer']
        if not isinstance(evidence_pointer,str) or not evidence_pointer.startswith(pointer+'/evidence/'):
            raise BindingError('evidence pointer mismatch')
        suffix=evidence_pointer[len(pointer+'/evidence/'):]
        if re.fullmatch(r'0|[1-9][0-9]*',suffix) is None or int(suffix)>=len(claim['evidence']):
            raise BindingError('evidence pointer mismatch')
        if not isinstance(annotation['modality'],str) or annotation['modality'] not in {'asserted','possible'}:
            raise BindingError('invalid explicit modality')
        if not isinstance(annotation['review_kind'],str) or annotation['review_kind'] not in {'constructed_control','assisted_user_review'}:
            raise BindingError('invalid review kind')
        if not isinstance(annotation['reviewer'],str) or not annotation['reviewer'].strip():
            raise BindingError('missing review provenance')
        by_pointer[pointer]=deepcopy(annotation)
    assertions=[]
    nonmetric=[]
    for index,claim in enumerate(claims['claims']):
        pointer=f'/claims/{index}'
        if not claim['metric']['reported']:
            nonmetric.append(dict(claim_pointer=pointer,claim=deepcopy(claim)))
            continue
        annotation=by_pointer.get(pointer)
        identity=digest((claims_sha256+':'+pointer+'/metric').encode())
        assertions.append(dict(assertion_id=identity,claims_sha256=claims_sha256,
            claim_pointer=pointer,metric_pointer=pointer+'/metric',claim_id=claim['claim_id'],
            metric=deepcopy(claim['metric']),original_claim=deepcopy(claim),
            modality=annotation['modality'] if annotation else 'not_evaluated',
            modality_annotation=annotation))
    return dict(version='offline-metric-assertion-view-draft-1',
        mode='offline_prototype_not_canonical_signal',claims_sha256=claims_sha256,
        source_sha256=source_sha256,annotation_sha256=annotation_sha256,
        document=deepcopy(claims['document']),assertions=assertions,nonmetric_claims=nonmetric,
        aggregate=None,semantic_acceptance='not_assessed',decisions_applied_to_originals=0)
