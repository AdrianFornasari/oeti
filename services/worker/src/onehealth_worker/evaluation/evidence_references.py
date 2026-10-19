"""Experimental source-bound evidence references; not used by extraction.

Pure in-memory API. Literal reconstruction does not establish semantic support.
"""
import hashlib
import json
import re


VERSION = 'evidence-paragraphs-1'


class EvidenceReferenceError(ValueError):
    """Invalid source, catalog or reference; messages contain no source content."""


def _require(condition):
    if not condition:
        raise EvidenceReferenceError('invalid evidence reference contract')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def build_catalog(*, document_id: str, source_bytes: bytes) -> bytes:
    """Return deterministic UTF-8 JSON bytes without normalizing source text."""
    _require(isinstance(document_id, str) and bool(document_id.strip()) and document_id == document_id.strip())
    _require(isinstance(source_bytes, bytes))
    try:
        text = source_bytes.decode('utf-8')
        document_id.encode('utf-8')
    except UnicodeError:
        raise EvidenceReferenceError('invalid UTF-8 input') from None
    paragraphs, start = [], 0
    separators = re.finditer(r'\r?\n[ \t]*\r?\n', text)
    for match in [*separators, None]:
        end = match.start() if match else len(text)
        raw = text[start:end]
        left, right = len(raw) - len(raw.lstrip()), len(raw.rstrip())
        if right > left:
            begin, stop = start + left, start + right
            paragraphs.append({'id': f'P{len(paragraphs)+1:03d}', 'start': begin,
                               'end': stop, 'text': text[begin:stop]})
        if match:
            start = match.end()
    _require(bool(paragraphs))
    catalog = {'version': VERSION, 'document_id': document_id,
               'source_sha256': _sha(source_bytes), 'source_characters': len(text),
               'paragraphs': paragraphs}
    return json.dumps(catalog, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def resolve_references(*, document_id: str, source_bytes: bytes, catalog_bytes: bytes,
                       expected_catalog_sha256: str, references: list) -> list[dict]:
    """Resolve exact relative Unicode spans after checking a trusted catalog hash.

    expected_catalog_sha256 must come from the caller's frozen manifest, not
    from the untrusted references. Catalog bytes must equal a fresh source-only
    catalog. No approximate matching, repairs, I/O or mutation is performed.
    """
    _require(isinstance(catalog_bytes, bytes))
    _require(isinstance(expected_catalog_sha256, str)
             and re.fullmatch('[0-9a-f]{64}', expected_catalog_sha256) is not None)
    _require(_sha(catalog_bytes) == expected_catalog_sha256)
    expected = build_catalog(document_id=document_id, source_bytes=source_bytes)
    _require(catalog_bytes == expected)
    catalog = json.loads(expected)
    paragraphs = {p['id']: p for p in catalog['paragraphs']}
    _require(isinstance(references, list) and bool(references))
    text = source_bytes.decode('utf-8')
    result, seen = [], set()
    keys = {'document_id', 'source_sha256', 'catalog_sha256', 'paragraph_id', 'start', 'end'}
    for ref in references:
        _require(isinstance(ref, dict) and set(ref) == keys)
        _require(ref['document_id'] == document_id and ref['source_sha256'] == catalog['source_sha256']
                 and ref['catalog_sha256'] == expected_catalog_sha256)
        _require(isinstance(ref['paragraph_id'], str) and ref['paragraph_id'] in paragraphs)
        paragraph = paragraphs[ref['paragraph_id']]
        start, end = ref['start'], ref['end']
        _require(type(start) is int and type(end) is int and 0 <= start < end <= len(paragraph['text']))
        span = (paragraph['start'] + start, paragraph['start'] + end)
        _require(span not in seen)
        quote = text[span[0]:span[1]]
        _require(bool(quote.strip()))
        seen.add(span)
        result.append({'text': quote, 'unicode_start': span[0], 'unicode_end': span[1],
                       'paragraph_id': ref['paragraph_id'], 'document_id': document_id,
                       'source_sha256': catalog['source_sha256'], 'catalog_sha256': expected_catalog_sha256})
    return result
