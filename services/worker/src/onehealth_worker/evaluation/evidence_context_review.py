"""Source windows for manual evidence review, without antecedent resolution."""
from __future__ import annotations

import json

from .attribution_review import build_review


def build_evidence_context_review(**review_inputs):
    review = build_review(**review_inputs)
    claims = json.loads(review_inputs['claims_bytes'])
    raw_text = review_inputs['raw_text']
    rows = []
    for claim_index, claim in enumerate(claims['claims']):
        for evidence_index, evidence in enumerate(claim['evidence']):
            quote = evidence['text']
            occurrences = []
            search_start = 0
            while quote:
                start = raw_text.find(quote, search_start)
                if start < 0:
                    break
                end = start + len(quote)
                window_start = max(0, start - 160)
                window_end = min(len(raw_text), end + 160)
                occurrences.append({
                    'quote_start': start, 'quote_end': end,
                    'window_start': window_start, 'window_end': window_end,
                    'text': raw_text[window_start:window_end],
                })
                search_start = start + 1
            rows.append({
                'claim_id': claim['claim_id'],
                'evidence_pointer': f'/claims/{claim_index}/evidence/{evidence_index}',
                'quote': quote, 'occurrences': occurrences,
                'occurrence_status': 'exact_matches' if occurrences else 'no_exact_match',
            })
    return {
        'version': 'evidence-context-review-1',
        'mode': 'development_review_only',
        'document': review['document'],
        'claims_sha256': review['claims_sha256'],
        'signals_sha256': review['signals_sha256'],
        'raw_text_sha256': review['raw_text_sha256'],
        'rows': rows, 'decisions_applied': 0,
        'semantic_acceptance': 'not_assessed',
        'antecedent_resolution': 'not_assessed',
        'limitations': [
            'All exact occurrences are retained; none is selected as the source occurrence.',
            'Offsets are zero-based Unicode code-point indices with exclusive ends.',
            'Windows contain up to 160 code points on each side, not resolved antecedents.',
            'Context is not replacement evidence and may contain unrelated statements.',
            'Literal validation allows normalization; no_exact_match does not locate a normalized quote.',
            'No anaphora detection, completeness judgment, repair or acceptance is performed.',
        ],
    }
