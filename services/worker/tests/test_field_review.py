import copy
import hashlib
import json

import pytest

from onehealth_worker.evaluation.field_review import ReviewValidationError, validate_field_review, main


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def package(tmp_path):
    root = tmp_path/'package'
    root.mkdir()
    artifact = root/'prediction.json'
    dump(artifact, {'signals': [{'role': 'primary_event'}], 'a/b': {'~key': True}})
    source = root/'source.txt'
    source.write_bytes('Córdoba\r\nCita literal.'.encode('utf-8'))
    row = {'review_id': 'R1', 'document_id': 'D1', 'field_pointer': '/signals/0/role',
        'artifact_path': artifact.name, 'artifact_sha256': sha(artifact), 'observed_value': 'primary_event',
        'proposed_action': 'propose_field_correction', 'proposed_value': 'negative_evidence', 'human_review': False,
        'source': {'path': source.name, 'sha256': sha(source), 'unicode_start': 9, 'unicode_end': 22, 'excerpt': 'Cita literal.'}}
    review = root/'review.json'
    dump(review, {'status': 'agent_provisional_review_not_applied', 'rows': [row]})
    decision = {'review_id': 'R1', 'document_id': 'D1', 'field_pointer': row['field_pointer'],
        'disposition': 'accept_review_proposal', 'proposal_value': row['proposed_value'],
        'rationale': 'Revisar la atribución.', 'reviewer_type': 'agent', 'human_review': False,
        'decided_on': '2026-10-16', 'applied': False,
        'evidence_binding': {'review_file_sha256': sha(review), 'artifact_sha256': sha(artifact), 'source_sha256': sha(source)}}
    decisions = root/'decisions.json'
    dump(decisions, {'status': 'closed_agent_provisional_not_applied', 'decisions_applied': 0,
        'source_review_file': review.name, 'source_review_sha256': sha(review),
        'counts': {'accept_review_proposal': 1}, 'decisions': [decision]})
    return root, decisions


def rewrite_review(root, decisions, change):
    p = root/'review.json'
    review = json.loads(p.read_text(encoding='utf-8'))
    change(review)
    dump(p, review)
    d = json.loads(decisions.read_text(encoding='utf-8'))
    d['source_review_sha256'] = sha(p)
    for row in d['decisions']:
        row['evidence_binding']['review_file_sha256'] = sha(p)
    dump(decisions, d)


def test_valid_records_are_read_only_and_do_not_claim_semantic_validation(package):
    root, path = package
    before = {p: p.read_bytes() for p in root.iterdir()}
    result = validate_field_review(decisions_path=path, allowed_root=root)
    assert result['valid'] and result['decisions'] == 1
    assert result['decisions_applied'] == 0
    assert result['semantic_correctness_verified'] is False
    assert result['human_review_verified'] is False
    assert before == {p: p.read_bytes() for p in root.iterdir()}


@pytest.mark.parametrize('filename', ['source.txt', 'prediction.json', 'review.json'])
def test_stale_artifacts_are_rejected(package, filename):
    root, path = package
    with (root/filename).open('ab') as stream:
        stream.write(b' ')
    with pytest.raises(ReviewValidationError, match='hash mismatch'):
        validate_field_review(decisions_path=path, allowed_root=root)


@pytest.mark.parametrize('pointer', ['/signals/-1/role', '/signals/01/role', '/signals/-/role',
    '/signals/99/role', '/signals/0/missing', '/a~2b', 'signals/0/role'])
def test_bad_pointers_fail_even_when_review_hash_is_rebound(package, pointer):
    root, path = package
    rewrite_review(root, path, lambda r: r['rows'][0].update(field_pointer=pointer))
    with pytest.raises(ReviewValidationError):
        validate_field_review(decisions_path=path, allowed_root=root)


def test_rfc6901_escaped_keys_work_and_bool_is_not_integer(package):
    root, path = package
    rewrite_review(root, path, lambda r: r['rows'][0].update(field_pointer='/a~1b/~0key', observed_value=True))
    d = json.loads(path.read_text(encoding='utf-8'))
    d['decisions'][0]['field_pointer'] = '/a~1b/~0key'
    dump(path, d)
    assert validate_field_review(decisions_path=path, allowed_root=root)['valid']
    rewrite_review(root, path, lambda r: r['rows'][0].update(observed_value=1))
    with pytest.raises(ReviewValidationError, match='observed field'):
        validate_field_review(decisions_path=path, allowed_root=root)


@pytest.mark.parametrize('change', [
    lambda r: r['rows'].append(copy.deepcopy(r['rows'][0])),
    lambda r: r['rows'][0].update(observed_value='wrong'),
    lambda r: r['rows'][0]['source'].update(unicode_start=True),
    lambda r: r['rows'][0]['source'].update(unicode_end=999),
    lambda r: r['rows'][0]['source'].update(excerpt='reconstructed quote'),
    lambda r: r['rows'][0].update(human_review=True),
])
def test_invalid_review_contents_fail(package, change):
    root, path = package
    rewrite_review(root, path, change)
    with pytest.raises(ReviewValidationError):
        validate_field_review(decisions_path=path, allowed_root=root)


@pytest.mark.parametrize('field,value', [('document_id', 'other'), ('proposal_value', 'wrong'),
    ('disposition', 'auto_apply'), ('reviewer_type', 'human'), ('human_review', True),
    ('applied', True), ('rationale', ' '), ('decided_on', '2026-02-30')])
def test_invalid_decision_fields_fail(package, field, value):
    root, path = package
    d = json.loads(path.read_text(encoding='utf-8'))
    d['decisions'][0][field] = value
    dump(path, d)
    with pytest.raises(ReviewValidationError):
        validate_field_review(decisions_path=path, allowed_root=root)


@pytest.mark.parametrize('mode', ['duplicate', 'missing', 'foreign', 'wrong_count', 'stale_binding'])
def test_decision_coverage_and_binding_are_checked(package, mode):
    root, path = package
    d = json.loads(path.read_text(encoding='utf-8'))
    if mode == 'duplicate': d['decisions'] *= 2
    elif mode == 'missing': d['decisions'] = []
    elif mode == 'foreign': d['decisions'][0]['review_id'] = 'R2'
    elif mode == 'wrong_count': d['counts'] = {'accept_review_proposal': 2}
    else: d['decisions'][0]['evidence_binding']['source_sha256'] = '0'*64
    dump(path, d)
    with pytest.raises(ReviewValidationError):
        validate_field_review(decisions_path=path, allowed_root=root)


def test_paths_outside_explicit_root_are_rejected(package):
    root, path = package
    outside = root.parent/'outside.json'
    dump(outside, {})
    rewrite_review(root, path, lambda r: r['rows'][0].update(artifact_path='../outside.json', artifact_sha256=sha(outside)))
    with pytest.raises(ReviewValidationError, match='outside root'):
        validate_field_review(decisions_path=path, allowed_root=root)


def test_frozen_metadata_reference_is_checked(package):
    root, path = package
    metadata = root/'manifest.json'
    dump(metadata, {'date': None})
    rewrite_review(root, path, lambda r: r['rows'][0].update(frozen_metadata_reference={
        'path': metadata.name, 'sha256': sha(metadata), 'pointer': '/date', 'value': 'invented'}))
    with pytest.raises(ReviewValidationError, match='frozen metadata'):
        validate_field_review(decisions_path=path, allowed_root=root)


def test_cli_exit_status_and_redacted_malformed_json(package, capsys):
    root, path = package
    assert main(['--decisions', str(path), '--allowed-root', str(root)]) == 0
    assert json.loads(capsys.readouterr().out)['valid'] is True
    path.write_text('secret-do-not-print', encoding='utf-8')
    assert main(['--decisions', str(path), '--allowed-root', str(root)]) == 1
    output = capsys.readouterr().out
    assert 'secret-do-not-print' not in output
    assert json.loads(output)['valid'] is False
