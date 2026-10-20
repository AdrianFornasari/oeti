"""Frozen-file corpus runner. CLI prepares only; execution requires provider injection.

No Settings, environment credentials, repository or database connection is loaded.
Outputs go to a new directory outside the immutable source package.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from .extraction import scoped_document_input

REPOSITORY_ROOT = Path(__file__).resolve().parents[5]


class EventDatePolicyError(ValueError):
    """An output conflicts with a declared source-review constraint."""


@dataclass(frozen=True)
class FrozenDocument:
    raw_item_id: str
    title: str
    url: str
    published_at: date | None
    language: str
    raw_text: str


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))


def _preflight(manifest_path: Path):
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes.decode('utf-8-sig'))
    case = manifest.get('case_code')
    if not isinstance(case, str) or not case.strip():
        raise ValueError('case_code is required')
    items = manifest.get('documents')
    if not isinstance(items, list) or not items:
        raise ValueError('documents must be a nonempty list')
    scope = manifest.get('proposed_run', {}).get('evaluation_scope')
    if scope is not None and (not isinstance(scope, str) or not scope.strip()):
        raise ValueError('evaluation_scope must be nonempty text or null')
    code_files = manifest.get('code_freeze', {}).get('files', [])
    for entry in code_files:
        relative = entry.get('path')
        if not isinstance(relative, str) or Path(relative).is_absolute():
            raise ValueError('code path must be relative')
        code = (REPOSITORY_ROOT / relative).resolve()
        if not code.is_relative_to(REPOSITORY_ROOT):
            raise ValueError('code path escapes repository')
        if _sha(code.read_bytes()) != entry.get('sha256'):
            raise ValueError('frozen code hash mismatch')
    prepared = []
    identifiers, source_paths = set(), set()
    root = manifest_path.parent
    for item in items:
        if 'event_date_policy' in item:
            policy = item['event_date_policy']
            if (not isinstance(policy, dict) or set(policy) != {'mode', 'basis'}
                    or policy['mode'] != 'unknown_only' or not isinstance(policy['basis'], str)
                    or not policy['basis'].strip()):
                raise ValueError('invalid declared event date policy')
        identifier = item.get('document_id')
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError('document_id is required')
        if identifier in identifiers:
            raise ValueError('duplicate document_id')
        identifiers.add(identifier)
        relative = item.get('evaluation_input_path')
        digest = item.get('evaluation_input_sha256')
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise ValueError('source path must be relative')
        source = (root / relative).resolve()
        if not source.is_relative_to(root) or source == manifest_path:
            raise ValueError('source path escapes frozen package')
        if source in source_paths:
            raise ValueError('duplicate source path')
        source_paths.add(source)
        if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', digest):
            raise ValueError('invalid source hash')
        raw = source.read_bytes()
        if _sha(raw) != digest.lower():
            raise ValueError(f'source hash mismatch: {identifier}')
        text = raw.decode('utf-8')
        if not text.strip():
            raise ValueError('source is empty')
        title, url = item.get('title'), item.get('requested_url')
        if not isinstance(title, str) or not isinstance(url, str) or not url:
            raise ValueError('title and requested_url metadata are required')
        published = item.get('declared_page_date')
        published_date = date.fromisoformat(published) if published is not None else None
        binding = json.dumps([case, identifier, digest.lower(), title, url, published, scope], ensure_ascii=False)
        document = FrozenDocument(str(uuid5(NAMESPACE_URL, binding)), title, url, published_date, 'es', text)
        document_input = scoped_document_input(document, scope)
        prepared.append((identifier, relative, digest.lower(), document, document_input))
    return manifest, _sha(manifest_bytes), prepared


def _validate_document_binding(payload: dict[str, Any], document: FrozenDocument) -> None:
    expected = {
        'raw_item_id': document.raw_item_id,
        'language': document.language,
        'document_date': document.published_at.isoformat() if document.published_at else None,
    }
    if any(payload['document'].get(key) != value for key, value in expected.items()):
        raise ValueError('document metadata differs from frozen input')


def _validate_event_date_policy(payload: dict[str, Any], policy: dict | None) -> None:
    if policy is None:
        return
    for item in payload.get('claims', payload.get('signals', [])):
        if item['event_date'] != {'start': None, 'end': None, 'precision': 'unknown'}:
            raise EventDatePolicyError('event date conflicts with declared source policy')


def run_frozen_corpus(*, manifest_path: Path, output_dir: Path,
                      execute: bool = False, provider=None,
                      include_review_hints: bool = False,
                      include_metric_period_provenance: bool = False) -> dict[str, Any]:
    """Prepare all inputs or process with an explicitly supplied provider.

    The default never calls the provider. No overwrite/resume/force is supported:
    each attempt retains a distinct complete report, including failed responses.
    """
    manifest_path, output_dir = Path(manifest_path).resolve(), Path(output_dir).resolve()
    if output_dir.exists() or output_dir.is_relative_to(manifest_path.parent):
        raise ValueError('output must be a new directory outside frozen sources')
    if execute and provider is None:
        raise ValueError('execute requires an explicitly injected provider')
    manifest, manifest_sha, prepared = _preflight(manifest_path)
    date_policies = {item['document_id']: item.get('event_date_policy') for item in manifest['documents']}
    runtime_freeze = None
    if 'runtime_freeze' in manifest:
        from .runtime_freeze import verify_runtime_freeze
        runtime_freeze = verify_runtime_freeze(manifest['runtime_freeze'], repository_root=REPOSITORY_ROOT)
    if execute:
        # Keep preparation independent from DB and network/provider packages.
        from ..extraction.assembly_v046 import assemble_claims_payload
        from ..extraction.normalization import normalize_extraction_payload
        from ..extraction.signal_semantics_v049 import harden_signal_semantics_v049
        from ..extraction.prompt import SYSTEM_INSTRUCTIONS
        from ..extraction.schema import (load_atomic_claims_schema, load_schema,
            validate_atomic_claims, validate_extraction, validate_literal_claim_evidence,
            validate_literal_evidence)
        claims_schema, signal_schema = load_atomic_claims_schema(), load_schema()
    output_dir.mkdir(parents=True, exist_ok=False)
    report = {'case_code': manifest['case_code'], 'manifest_sha256': manifest_sha,
        'mode': 'injected_provider' if execute else 'prepare_only',
        'evaluation_class': 'exploratory_no_independent_review',
        'started_at': datetime.now(timezone.utc).isoformat(),
        'runtime': {'python': platform.python_version()},
        'runner_sha256': _sha(Path(__file__).read_bytes()),
        'verified_code_files': manifest.get('code_freeze', {}).get('files', []),
        'declared_model': manifest.get('proposed_run', {}).get('model'),
        'provider_class': type(provider).__name__ if execute else None,
        'production_sequence': ['assembly_v046', 'normalization', 'signal_semantics_v049'],
        'results': []}
    if include_review_hints:
        from . import claim_review
        report['claim_review'] = {'version': claim_review.REVIEW_VERSION,
            'code_sha256': _sha(Path(claim_review.__file__).read_bytes()), 'affects_validation': False}
    if runtime_freeze is not None:
        report['verified_runtime_freeze'] = runtime_freeze
    if include_metric_period_provenance:
        from . import metric_period_provenance
        report['metric_period_provenance'] = {'version': 'metric-period-provenance-1',
            'code_sha256': _sha(Path(metric_period_provenance.__file__).read_bytes()),
            'affects_validation': False, 'semantic_correctness_verified': False}
    if execute:
        report['schemas_sha256'] = {name: _sha(json.dumps(schema, sort_keys=True).encode())
            for name, schema in [('claims', claims_schema), ('signals', signal_schema)]}
    for index, (identifier, source, source_sha, document, document_input) in enumerate(prepared, 1):
        prefix = f'{index:03d}'
        input_bytes = document_input.encode('utf-8')
        (output_dir / f'{prefix}.input.txt').write_bytes(input_bytes)
        result = {'document_id': identifier, 'raw_item_id': document.raw_item_id,
            'source_path': source, 'source_sha256': source_sha,
            'input_path': f'{prefix}.input.txt', 'input_sha256': _sha(input_bytes),
            'status': 'prepared', 'usage': None, 'response_id': None}
        date_policy = date_policies[identifier]
        if date_policy is not None:
            result['verified_event_date_policy'] = date_policy
        if include_review_hints:
            result['claim_review'] = {'status': 'not_reviewed', 'findings': None}
        if include_metric_period_provenance:
            result['metric_period_provenance'] = {'status': 'not_generated'}
        if execute:
            phase = 'provider'
            try:
                response = provider.extract(instructions=SYSTEM_INSTRUCTIONS,
                    document_input=document_input, schema=claims_schema)
                result.update(usage=response.usage, response_id=response.response_id)
                phase = 'validation'
                _write(output_dir / f'{prefix}.claims.json', response.payload)
                result.update(claims_path=f'{prefix}.claims.json',
                    claims_sha256=_sha((output_dir / f'{prefix}.claims.json').read_bytes()))
                validate_atomic_claims(response.payload, claims_schema)
                _validate_document_binding(response.payload, document)
                _validate_event_date_policy(response.payload, date_policy)
                validate_literal_claim_evidence(response.payload, document.raw_text)
                if include_review_hints:
                    try:
                        result['claim_review'] = {'status': 'reviewed',
                            'findings': claim_review.review_claims(response.payload)}
                    except Exception as review_error:
                        result['claim_review'] = {'status': 'review_error', 'findings': None,
                            'error_type': type(review_error).__name__}
                payload = assemble_claims_payload(response.payload)
                payload = harden_signal_semantics_v049(normalize_extraction_payload(payload))
                validate_extraction(payload, signal_schema)
                _validate_document_binding(payload, document)
                _validate_event_date_policy(payload, date_policy)
                validate_literal_evidence(payload, document.raw_text)
                _write(output_dir / f'{prefix}.signals.json', payload)
                result.update(status='generated', signals=len(payload['signals']),
                    signals_path=f'{prefix}.signals.json',
                    signals_sha256=_sha((output_dir / f'{prefix}.signals.json').read_bytes()))
                if include_metric_period_provenance:
                    try:
                        mapping = metric_period_provenance.build_metric_period_provenance(
                            claims_bytes=(output_dir / result['claims_path']).read_bytes(),
                            signals_bytes=(output_dir / result['signals_path']).read_bytes(),
                            expected_claims_sha256=result['claims_sha256'],
                            expected_signals_sha256=result['signals_sha256'],
                            expected_document=payload['document'],
                            claims_schema=claims_schema, signal_schema=signal_schema)
                        mapping_path = f'{prefix}.metric-periods.json'
                        with (output_dir / mapping_path).open('xb') as stream:
                            stream.write(mapping)
                        result['metric_period_provenance'] = {'status': 'generated',
                            'path': mapping_path, 'sha256': _sha(mapping)}
                    except Exception as mapping_error:
                        # Auxiliary mapping must not change extraction acceptance.
                        result['metric_period_provenance'] = {'status': 'generation_error',
                            'error_type': type(mapping_error).__name__}
            except Exception as error:
                # Exception messages from transports may contain URLs/credentials.
                result.update(status='failed', error_type=type(error).__name__, phase=phase)
        report['results'].append(result)
        _write(output_dir / 'report.json', report)
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    report['summary'] = {status: sum(r['status'] == status for r in report['results'])
                         for status in ('prepared', 'generated', 'failed')}
    _write(output_dir / 'report.json', report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description='Prepare a frozen corpus offline; no LLM or database access.')
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    report = run_frozen_corpus(manifest_path=args.manifest, output_dir=args.output)
    print(json.dumps({'mode': report['mode'], 'summary': report['summary']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
