"""Optional lexical attribution hints; no repair, acceptance or classification."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re

from .metric_period_provenance import build_metric_period_provenance
from ..extraction.schema import validate_literal_claim_evidence, validate_literal_evidence


REVIEW_VERSION = 'attribution-review-sidecar-1'
_LOCATION_FIELDS = ('country', 'admin1', 'admin2', 'locality', 'region')
_GENERIC_METRICS = {'case_count', 'case count', 'case counts', 'cases', 'casos', 'conteo de casos'}
_LABEL_CUES = re.compile(
    r'(?<!\w)(?:confirmed|confirmados?|confirmadas?|probable|probables|suspected|sospechosos?|sospechosas?)(?!\w)', re.I)


def _folded(value):
    return ' '.join(value.split()).casefold()


def _mentioned(value, text):
    return re.search(r'(?<!\w)' + re.escape(_folded(value)) + r'(?!\w)', _folded(text)) is not None


def build_review(*, claims_bytes, signals_bytes, raw_text, expected_claims_sha256,
                 expected_signals_sha256, expected_raw_text_sha256, expected_document,
                 claims_schema, signal_schema):
    """Review hash-bound, schema-valid artifacts with literal evidence.

    Presence of a geographic term does not establish its scope. Absence may
    reflect aliases or normalization. Exact metric candidates do not prove
    semantic provenance or group membership. No hints is not an acceptance.
    """
    if (not isinstance(raw_text, str)
            or hashlib.sha256(raw_text.encode('utf-8')).hexdigest() != expected_raw_text_sha256):
        raise ValueError('raw text binding mismatch')
    mapping = json.loads(build_metric_period_provenance(
        claims_bytes=claims_bytes, signals_bytes=signals_bytes,
        expected_claims_sha256=expected_claims_sha256,
        expected_signals_sha256=expected_signals_sha256,
        expected_document=expected_document, claims_schema=claims_schema, signal_schema=signal_schema))
    claims, signals = json.loads(claims_bytes), json.loads(signals_bytes)
    validate_literal_claim_evidence(claims, raw_text)
    validate_literal_evidence(signals, raw_text)
    by_id = {claim['claim_id']: claim for claim in claims['claims']}
    findings = []
    for claim in claims['claims']:
        quotes = [evidence['text'] for evidence in claim['evidence']]
        for index, location in enumerate(claim['locations']):
            for field in _LOCATION_FIELDS:
                value = location.get(field)
                if (not isinstance(value, str) or not value.strip()
                        or any(_mentioned(value, quote) for quote in quotes)):
                    continue
                in_document = _mentioned(value, raw_text)
                findings.append({
                    'code': 'REVIEW-LOCATION-QUOTE' if in_document else 'REVIEW-LOCATION-DOCUMENT',
                    'claim_id': claim['claim_id'], 'field': f'locations[{index}].{field}', 'value': value,
                    'claim_quote_presence': False, 'document_presence': in_document,
                    'meaning': ('Text absent from claim quotes; present elsewhere in document, scope unverified.'
                        if in_document else 'Text absent from claim quotes and supplied document; review inference, alias or normalization. Not proof of error.'),
                })
    for row in mapping['rows']:
        context = {key: row[key] for key in ('signal_id', 'metric_pointer', 'metric', 'binding_status')}
        if row['binding_status'] != 'unique_metric_match':
            findings.append({**context, 'code': 'REVIEW-METRIC-BINDING',
                'candidate_claim_ids': [claim['claim_id'] for claim in row['source_claims']],
                'meaning': 'Exact metric origin is ambiguous or unmatched; no classification assigned.'})
            continue
        if _folded(str(row['metric'].get('name') or '')) not in _GENERIC_METRICS:
            continue
        claim = by_id[row['source_claims'][0]['claim_id']]
        fields = {'subject.verbatim': (claim.get('subject') or {}).get('verbatim'),
            'metric.name': (claim.get('metric') or {}).get('name'), 'summary': claim.get('summary')}
        cues = {field: value for field, value in fields.items()
            if isinstance(value, str) and _LABEL_CUES.search(value)}
        if cues:
            findings.append({**context, 'code': 'REVIEW-METRIC-CLASSIFICATION-SOURCE',
                'candidate_claim_ids': [claim['claim_id']], 'source_label_cues': cues,
                'source_evidence': claim['evidence'],
                'meaning': 'Metric name is generic; case-status wording survives in candidate source fields. Review association; no normalized classification assigned.'})
    return {'version': REVIEW_VERSION, 'mode': 'development_review_only',
        'document': deepcopy(expected_document), 'claims_sha256': expected_claims_sha256,
        'signals_sha256': expected_signals_sha256, 'raw_text_sha256': expected_raw_text_sha256,
        'findings': findings, 'decisions_applied': 0, 'semantic_acceptance': 'not_assessed',
        'geographic_support_verified': False, 'metric_classification_assigned': False,
        'group_membership_verified': False,
        'limitations': [
            'Lexical whole-term matching ignores aliases, translations and hierarchy; presence does not prove attribution.',
            'ISO codes intentionally not compared to prose. Geographic fields missing in input are not invented.',
            'Metric-name whitelist and status-word cues are narrow; absence of hints is not semantic acceptance.',
            'Exact metric matching is not semantic provenance; ambiguous/unmatched cases are never auto-assigned.',
        ]}
