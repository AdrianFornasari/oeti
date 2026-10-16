"""Read-only validation of agent-provisional field-review records."""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re


class ReviewValidationError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise ReviewValidationError(message)


def _same(a, b):
    return json.dumps(a, sort_keys=True, ensure_ascii=False) == json.dumps(b, sort_keys=True, ensure_ascii=False)


def _file(root, base, value):
    _require(isinstance(value, str) and bool(value), 'invalid file reference')
    path = (base / value).resolve()
    _require(path.is_relative_to(root) and path.is_file(), 'file reference outside root or unavailable')
    return path


def _verified(path, digest):
    _require(isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest), 'invalid SHA-256')
    data = path.read_bytes()
    _require(hashlib.sha256(data).hexdigest() == digest, 'file hash mismatch')
    return data


def _pointer(value, pointer):
    _require(isinstance(pointer, str) and (pointer == '' or pointer.startswith('/')), 'invalid JSON pointer')
    if pointer == '':
        return value
    for token in pointer[1:].split('/'):
        _require(not re.search(r'~(?![01])', token), 'invalid JSON pointer escape')
        key = token.replace('~1', '/').replace('~0', '~')
        if isinstance(value, list):
            _require(bool(re.fullmatch(r'0|[1-9][0-9]*', key)), 'invalid array index')
            index = int(key)
            _require(index < len(value), 'array index out of bounds')
            value = value[index]
        else:
            _require(isinstance(value, dict) and key in value, 'pointer field missing')
            value = value[key]
    return value


def validate_field_review(*, decisions_path: Path, allowed_root: Path) -> dict:
    """Verify hashes, evidence spans and decisions; never apply proposals.

    Root is explicit. Absolute legacy references are allowed only inside it.
    This contract accepts agent-provisional records, not claims of human review.
    """
    try:
        return _validate(Path(decisions_path), Path(allowed_root))
    except ReviewValidationError:
        raise
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, AttributeError, OverflowError):
        raise ReviewValidationError('malformed or unavailable review data') from None


def _validate(decisions_path, allowed_root):
    root = allowed_root.resolve()
    _require(root.is_dir(), 'allowed root unavailable')
    path = _file(root, Path.cwd(), str(decisions_path))
    decisions_bytes = path.read_bytes()
    decisions = json.loads(decisions_bytes.decode('utf-8-sig'))
    _require(decisions.get('status') == 'closed_agent_provisional_not_applied', 'unsupported review status')
    _require(decisions.get('decisions_applied') == 0 and type(decisions.get('decisions_applied')) is int,
             'applied decisions unsupported')
    review_path = _file(root, path.parent, decisions['source_review_file'])
    review_sha = decisions['source_review_sha256']
    review = json.loads(_verified(review_path, review_sha).decode('utf-8-sig'))
    _require(review.get('status') == 'agent_provisional_review_not_applied', 'unsupported proposal status')
    rows = review.get('rows')
    entries = decisions.get('decisions')
    _require(isinstance(rows, list) and bool(rows) and isinstance(entries, list), 'review rows required')
    by_id = {}
    files = {path, review_path}
    for row in rows:
        identifier = row['review_id']
        _require(isinstance(identifier, str) and bool(identifier.strip()) and identifier not in by_id, 'invalid or duplicate review ID')
        _require(isinstance(row['document_id'], str) and bool(row['document_id'].strip()), 'document ID required')
        _require(row.get('human_review') is False, 'human review not established by this contract')
        artifact = _file(root, review_path.parent, row['artifact_path'])
        payload = json.loads(_verified(artifact, row['artifact_sha256']).decode('utf-8-sig'))
        _require(_same(_pointer(payload, row['field_pointer']), row['observed_value']), 'observed field mismatch')
        source = row['source']
        source_path = _file(root, review_path.parent, source['path'])
        text = _verified(source_path, source['sha256']).decode('utf-8')
        start, end = source['unicode_start'], source['unicode_end']
        _require(type(start) is int and type(end) is int and 0 <= start < end <= len(text), 'invalid source span')
        _require(isinstance(source['excerpt'], str) and text[start:end] == source['excerpt'], 'source span mismatch')
        files.update((artifact, source_path))
        if 'frozen_metadata_reference' in row:
            ref = row['frozen_metadata_reference']
            ref_path = _file(root, review_path.parent, ref['path'])
            metadata = json.loads(_verified(ref_path, ref['sha256']).decode('utf-8-sig'))
            _require(_same(_pointer(metadata, ref['pointer']), ref['value']), 'frozen metadata mismatch')
            files.add(ref_path)
        by_id[identifier] = row
    allowed = {'accept_review_proposal', 'reject_review_proposal', 'retain_validation_failure', 'confirm_current_value', 'abstain'}
    counts = {}
    seen = set()
    for entry in entries:
        identifier = entry['review_id']
        _require(identifier in by_id and identifier not in seen, 'unknown or duplicate decision ID')
        seen.add(identifier)
        row = by_id[identifier]
        _require(entry['document_id'] == row['document_id'] and entry['field_pointer'] == row['field_pointer'], 'decision target mismatch')
        _require(entry.get('reviewer_type') == 'agent' and entry.get('human_review') is False, 'unsupported reviewer attribution')
        _require(entry.get('applied') is False, 'decision already applied')
        _require(isinstance(entry.get('rationale'), str) and bool(entry['rationale'].strip()), 'decision rationale required')
        day = entry['decided_on']
        _require(isinstance(day, str) and date.fromisoformat(day).isoformat() == day, 'invalid decision date')
        disposition = entry['disposition']
        _require(disposition in allowed, 'unsupported disposition')
        _require(_same(entry['proposal_value'], row['proposed_value']), 'proposal value mismatch')
        if disposition == 'confirm_current_value':
            _require(_same(entry['proposal_value'], row['observed_value']), 'confirmed value differs')
        if disposition == 'retain_validation_failure':
            _require(row['proposed_action'] == 'retain_validation_failure', 'failure disposition mismatch')
        binding = entry['evidence_binding']
        _require(binding['review_file_sha256'] == review_sha and binding['artifact_sha256'] == row['artifact_sha256']
                 and binding['source_sha256'] == row['source']['sha256'], 'decision evidence binding mismatch')
        counts[disposition] = counts.get(disposition, 0) + 1
    _require(seen == set(by_id), 'missing decisions')
    _require(_same(decisions.get('counts'), counts), 'decision counts mismatch')
    return {'valid': True, 'validation_version': 'agent-field-review-1', 'decisions': len(entries),
        'verified_files': len(files), 'counts': counts, 'decisions_sha256': hashlib.sha256(decisions_bytes).hexdigest(),
        'decisions_applied': 0, 'semantic_correctness_verified': False, 'human_review_verified': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Validate local agent review records without applying changes.')
    parser.add_argument('--decisions', required=True, type=Path)
    parser.add_argument('--allowed-root', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate_field_review(decisions_path=args.decisions, allowed_root=args.allowed_root)
    except ReviewValidationError as error:
        print(json.dumps({'valid': False, 'error': str(error)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
