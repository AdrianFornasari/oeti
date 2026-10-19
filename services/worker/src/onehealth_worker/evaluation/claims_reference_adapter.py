"""Experimental pure adapter; never connected to the active extractor."""
import copy
import hashlib
import json

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from .evidence_references import build_catalog, resolve_references, EvidenceReferenceError
from ..extraction.schema import validate_atomic_claims, validate_literal_claim_evidence, ExtractionSchemaError


class ClaimsReferenceError(ValueError):
    """Invalid experimental payload or binding, without document contents."""


def reference_response_schema(claims_schema: dict) -> dict:
    """Derive an independent schema from the caller's trusted claims-0.1 schema."""
    schema = copy.deepcopy(claims_schema)
    schema['$id'] = 'urn:oeti:experimental:claims-evidence-refs:0.1'
    schema['title'] = 'OETI experimental claims with evidence references'
    schema['properties']['schema_version']['const'] = 'claims-refs-0.1'
    claim = schema['$defs']['claim']
    claim['required'].remove('evidence')
    claim['required'].append('evidence_refs')
    del claim['properties']['evidence']
    fields = {'document_id': {'type': 'string', 'minLength': 1},
              'source_sha256': {'type': 'string', 'pattern': '^[0-9a-f]{64}$'},
              'catalog_sha256': {'type': 'string', 'pattern': '^[0-9a-f]{64}$'},
              'paragraph_id': {'type': 'string', 'minLength': 1},
              'start': {'type': 'integer', 'minimum': 0},
              'end': {'type': 'integer', 'minimum': 1}}
    claim['properties']['evidence_refs'] = {'type': 'array', 'minItems': 1, 'items': {
        'type': 'object', 'additionalProperties': False, 'required': list(fields), 'properties': fields}}
    return schema


def adapt_reference_claims(*, payload: dict, expected_document: dict, document_id: str,
                           source_bytes: bytes, catalog_bytes: bytes,
                           expected_catalog_sha256: str, claims_schema: dict) -> dict:
    """Validate and convert a copy to claims-0.1; no filesystem/network operations.

    The caller supplies trusted document metadata, catalog hash and base schema.
    Preserve the raw experimental response separately; this result is adapted,
    not a direct textual response from a model. No semantic corrections occur.
    """
    try:
        # Reject Python-only/non-finite values before schema validation.
        json.dumps(payload, allow_nan=False)
        Draft202012Validator(reference_response_schema(claims_schema),
                             format_checker=FormatChecker()).validate(payload)
        if not isinstance(expected_document, dict) or payload['document'] != expected_document:
            raise ClaimsReferenceError('invalid experimental claims or binding')
        # Required even when claims=[]; there would be no per-claim resolver call.
        expected = build_catalog(document_id=document_id, source_bytes=source_bytes)
        if not isinstance(catalog_bytes, bytes) or catalog_bytes != expected:
            raise ClaimsReferenceError('invalid experimental claims or binding')
        if hashlib.sha256(catalog_bytes).hexdigest() != expected_catalog_sha256:
            raise ClaimsReferenceError('invalid experimental claims or binding')
        result = copy.deepcopy(payload)
        result['schema_version'] = 'claims-0.1'
        for claim in result['claims']:
            resolved = resolve_references(document_id=document_id, source_bytes=source_bytes,
                catalog_bytes=catalog_bytes, expected_catalog_sha256=expected_catalog_sha256,
                references=claim.pop('evidence_refs'))
            claim['evidence'] = [{'type': 'text', 'text': r['text'],
                'location_in_document': f"Unicode [{r['unicode_start']}:{r['unicode_end']})",
                'page_number': None} for r in resolved]
        validate_atomic_claims(result, claims_schema)
        validate_literal_claim_evidence(result, source_bytes.decode('utf-8'))
        return result
    except (ValidationError, EvidenceReferenceError, ExtractionSchemaError, ValueError, TypeError):
        raise ClaimsReferenceError('invalid experimental claims or binding') from None
