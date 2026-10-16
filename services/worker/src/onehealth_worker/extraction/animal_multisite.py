"""Conservative preparation of explicit one-to-one animal facility detections."""
from collections import Counter
from copy import deepcopy
import re
from typing import Any


def prepare_animal_multisite_claims(claims: list[dict[str, Any]], warnings: list[str]) -> list[dict[str, Any]]:
    groups = Counter(str(c.get('group_id') or c.get('claim_id') or '?') for c in claims)
    occupied = {str(c.get(key)) for c in claims for key in ('claim_id', 'group_id')}
    result = []
    for claim in claims:
        locations = claim.get('locations') or []
        localities = {str(loc.get('locality') or '').casefold() for loc in locations}
        if (claim.get('claim_kind') != 'diagnostic_result'
            or (claim.get('subject') or {}).get('subject_type') != 'animal'
            or len(localities - {''}) < 2):
            result.append(claim)
            continue
        group = str(claim.get('group_id') or claim.get('claim_id') or '?')
        children = _split_if_safe(claim, groups[group], occupied)
        if children is None:
            warnings.append(f"ASM-MULTISITE-REVIEW {claim.get('claim_id')}: retained unsplit; one-to-one facility attribution or indivisible fields require review.")
            result.append(claim)
        else:
            warnings.append(f"ASM-MULTISITE-01 {claim.get('claim_id')}: explicit one-to-one facility detections separated without allocating aggregate facts.")
            result.extend(children)
            occupied.update(str(c[key]) for c in children for key in ('claim_id', 'group_id'))
    return result


def _split_if_safe(claim: dict[str, Any], group_size: int, occupied: set[str]):
    locations = claim.get('locations') or []
    subject = claim.get('subject') or {}
    verbatim = ' '.join(str(subject.get('verbatim') or '').casefold().split())
    diagnostics = claim.get('diagnostics') or {}
    metric = claim.get('metric') or {}
    genomics = claim.get('genomics') or {}
    date = claim.get('event_date') or {}
    period = claim.get('reference_period') or {}
    if (group_size != 1 or len(locations) != 2
        or any(loc.get('role') != 'event_location' or not loc.get('locality') for loc in locations)
        or not locations[0].get('country_iso2')
        or any(locations[0].get(key) != locations[1].get(key) for key in ('country', 'country_iso2', 'admin1', 'admin2', 'region'))
        or claim.get('domains') != ['animal'] or claim.get('polarity') != 'positive'
        or claim.get('verification_status') != 'confirmed'
        or verbatim not in {'aves', 'aves de corral', 'aves de traspatio', 'cerdos', 'bovinos', 'ovinos', 'caprinos'}
        or subject.get('canonical_name') is not None
        or metric.get('reported') or metric.get('as_of_precision') != 'unknown'
        or any(v is not None for k, v in metric.items() if k not in {'reported', 'as_of_precision'})
        or date.get('start') or date.get('end') or date.get('precision') != 'unknown'
        or period.get('period_type') != 'unknown' or period.get('verbatim')
        or any(any(point.get(key) is not None for key in ('date', 'year', 'month', 'verbatim'))
            or point.get('precision') != 'unknown' for point in [period.get('start') or {}, period.get('end') or {}])
        or diagnostics.get('result') != 'positive' or diagnostics.get('test_reported')
        or any(diagnostics.get(k) is not None for k in ('method', 'target', 'test_type', 'specimen'))
        or genomics.get('sequence_reported') or any(genomics.get(k) is not None for k in ('lineage', 'clade', 'accession'))
        or genomics.get('test_result') not in {'unknown', 'not_applicable'}
        or any(v != 'unknown' for v in (claim.get('transmission') or {}).values())):
        return None
    # Match a complete one-to-one statement within an individual evidence item;
    # neither summaries nor concatenation of separate quotes can supply a link.
    names = [str(loc['locality']).casefold() for loc in locations]
    matched = False
    for evidence in claim.get('evidence') or []:
        text = ' '.join(str(evidence.get('text') or '').casefold().split())
        if re.search(r'\b(no|not|sin|posible|sospech\w*|presunt\w*|pasado)\b', text):
            continue
        for first, second in (names, names[::-1]):
            pattern = (r'\b(confirmó|confirmaron|detectó|detectaron) (dos )?casos positivos\b[^.!?]*?\ben '
                + re.escape(verbatim) + r' de dos (predios|establecimientos|granjas)\s*,?\s*uno en '
                + re.escape(first) + r' y otro en ' + re.escape(second) + r'(?=\s*(?:[.!?]|$))')
            matched = matched or bool(re.search(pattern, text))
    if not matched:
        return None
    children = []
    group = str(claim.get('group_id') or claim.get('claim_id') or '?')
    for index, location in enumerate(locations, 1):
        child = deepcopy(claim)
        child['claim_id'] = f"{claim.get('claim_id')}:site:{index}"
        child['group_id'] = f'{group}:site:{index}'
        if child['claim_id'] in occupied or child['group_id'] in occupied:
            return None
        child['claim_kind'] = 'outbreak_update'
        child['locations'] = [deepcopy(location)]
        child['summary'] = f"Detección focal confirmada en {subject.get('verbatim')}, {location['locality']}."
        children.append(child)
    return children
