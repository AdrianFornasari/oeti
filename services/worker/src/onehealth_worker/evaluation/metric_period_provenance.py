"""Pure evaluation-only mapping; exact metric equality is not semantic provenance."""
from __future__ import annotations

import copy
import hashlib
import json
import re

from jsonschema import Draft202012Validator, FormatChecker, SchemaError, ValidationError


class MetricProvenanceError(ValueError):
    """Invalid artifact, schema or binding; messages exclude source contents."""


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError('non-finite JSON number')


def _local_references(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {'$ref', '$dynamicRef', '$recursiveRef'}:
                if not isinstance(child, str) or not child.startswith('#'):
                    raise ValueError('external schema reference')
            _local_references(child)
    elif isinstance(value, list):
        for child in value:
            _local_references(child)


def _load(data, digest, schema):
    if (not isinstance(data, bytes) or not isinstance(digest, str)
            or re.fullmatch(r'[0-9a-f]{64}', digest) is None
            or hashlib.sha256(data).hexdigest() != digest):
        raise ValueError('artifact binding')
    payload = json.loads(data.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    _canonical(payload)  # Also reject overflowed JSON floats such as 1e999.
    _local_references(schema)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)
    return payload


def _unique_ids(items, field):
    ids = [item[field] for item in items]
    if any(not isinstance(value, str) or not value.strip() for value in ids) or len(set(ids)) != len(ids):
        raise ValueError('invalid identifiers')


def build_metric_period_provenance(*, claims_bytes: bytes, signals_bytes: bytes,
                                   expected_claims_sha256: str, expected_signals_sha256: str,
                                   expected_document: dict, claims_schema: dict,
                                   signal_schema: dict) -> bytes:
    """Return canonical UTF-8 JSON without I/O, mutation, repairs or acceptance.

    Caller supplies trusted schemas, document metadata and artifact hashes.
    Every signal metric lists ALL exactly equal reported claim metrics across
    that document. No group membership or source semantics is inferred. Empty
    and ambiguous matches are explicit; qualitative claims are outside this map.
    """
    try:
        claims = _load(claims_bytes, expected_claims_sha256, claims_schema)
        signals = _load(signals_bytes, expected_signals_sha256, signal_schema)
        if (not isinstance(expected_document, dict)
                or _canonical(claims['document']) != _canonical(expected_document)
                or _canonical(signals['document']) != _canonical(expected_document)):
            raise ValueError('document binding')
        _unique_ids(claims['claims'], 'claim_id')
        _unique_ids(signals['signals'], 'local_signal_id')
        index = {}
        for ci, claim in enumerate(claims['claims']):
            metric = claim.get('metric') or {}
            if metric.get('reported') is not True:
                continue
            key = _canonical({k: v for k, v in metric.items() if k != 'reported'})
            index.setdefault(key, []).append({
                'claim_id': claim['claim_id'], 'claim_pointer': f'/claims/{ci}',
                'group_id': claim['group_id'], 'reference_period': claim['reference_period'],
                'event_date': claim['event_date'], 'evidence': claim['evidence'],
            })
        rows = []
        for si, signal in enumerate(signals['signals']):
            for mi, metric in enumerate(signal['metrics']):
                matches = index.get(_canonical(metric), [])
                rows.append({
                    'signal_id': signal['local_signal_id'],
                    'metric_pointer': f'/signals/{si}/metrics/{mi}', 'metric': metric,
                    'binding_status': ('unique_metric_match' if len(matches) == 1 else
                                       'ambiguous_metric_match' if matches else 'unmatched'),
                    'source_claims': matches,
                })
        result = {
            'version': 'metric-period-provenance-1', 'mode': 'evaluation_only_exact_metric_candidates',
            'claims_sha256': expected_claims_sha256, 'signals_sha256': expected_signals_sha256,
            'document': copy.deepcopy(expected_document), 'rows': rows,
            'semantic_correctness_verified': False, 'source_literalness_verified': False,
            'group_membership_verified': False, 'decisions_applied': 0,
        }
        return (_canonical(result) + '\n').encode('utf-8')
    except (ValueError, TypeError, KeyError, AttributeError, UnicodeError, OverflowError,
            RecursionError, SchemaError, ValidationError):
        raise MetricProvenanceError('invalid metric provenance artifacts or binding') from None
