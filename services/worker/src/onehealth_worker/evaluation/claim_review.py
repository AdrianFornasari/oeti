"""Deterministic review hints for schema-valid claims; no repair or rejection."""
from __future__ import annotations

import re
from typing import Any

REVIEW_VERSION = 'claim-review-hints-1'


def review_claims(payload: dict[str, Any]) -> list[dict[str, Any]]:
    findings = []
    for claim in payload.get('claims', []):
        identifier = claim.get('claim_id')
        quotes = [' '.join(str(e.get('text') or '').split()).casefold()
                  for e in claim.get('evidence', [])]
        for index, location in enumerate(claim.get('locations', [])):
            locality = location.get('locality')
            if not isinstance(locality, str) or not locality.strip():
                continue
            name = ' '.join(locality.split()).casefold()
            pattern = r'(?<!\w)' + re.escape(name) + r'(?!\w)'
            if not any(re.search(pattern, quote) for quote in quotes):
                findings.append({
                    'claim_id': identifier, 'code': 'REVIEW-LOCALITY-QUOTE',
                    'field': f'locations[{index}].locality', 'value': locality,
                    'meaning': 'Complete locality absent from claim evidence; review attribution. Not proof of error.',
                })
        diagnostics = claim.get('diagnostics') or {}
        result = diagnostics.get('result')
        if diagnostics.get('test_reported') is False and result in {'positive', 'negative', 'pending', 'inconclusive'}:
            findings.append({
                'claim_id': identifier, 'code': 'REVIEW-TEST-RESULT', 'field': 'diagnostics',
                'meaning': 'Reported test is false but a test outcome/state is set; review consistency.',
            })
        if claim.get('claim_kind') == 'laboratory_investigation' and result != 'pending':
            findings.append({
                'claim_id': identifier, 'code': 'REVIEW-INVESTIGATION-STATE', 'field': 'diagnostics.result',
                'meaning': 'Investigation lacks pending state; review whether source reports tests in progress.',
            })
    return findings
