import json
from types import SimpleNamespace

import pytest

from onehealth_worker.evaluation.extraction import extract_evaluation_corpus


@pytest.mark.parametrize('destination', ['prediction', 'sidecar'])
@pytest.mark.parametrize('protected', ['manifest', 'gold', 'claims'])
@pytest.mark.parametrize('alias', ['same_path', 'hardlink'])
def test_extraction_rejects_input_alias_before_initializing_services(
    tmp_path, monkeypatch, destination, protected, alias,
):
    from onehealth_worker.extraction import repository

    def forbidden_repository(*args, **kwargs):
        raise AssertionError('Repository must not initialize for conflicting outputs')

    monkeypatch.setattr(repository, 'ExtractionRepository', forbidden_repository)
    prediction = tmp_path / 'result.json'
    output = prediction if destination == 'prediction' else tmp_path / 'result.claims.json'
    target = output if alias == 'same_path' else tmp_path / 'protected.json'
    manifest = target if protected == 'manifest' else tmp_path / 'manifest.json'
    if protected != 'manifest':
        target.write_text('{}', encoding='utf-8')
    manifest.write_text(json.dumps({'documents': [
        {'status': 'adjudicated', 'prediction': prediction.name, 'source_url': 'https://example.invalid/test'},
        {'status': 'pending_adjudication', protected: target.name} if protected != 'manifest' else {},
    ]}), encoding='utf-8')
    if alias == 'hardlink':
        output.hardlink_to(target)
    originals = {p: p.read_bytes() for p in {manifest, target}}
    with pytest.raises(ValueError, match='entrada'):
        extract_evaluation_corpus(manifest_path=manifest, database_url='unused',
                                  provider_name='openai', model_name='unused', api_key='unused', force=True)
    assert all(p.read_bytes() == content for p, content in originals.items())


def test_extraction_checks_later_outputs_before_initializing_services(tmp_path, monkeypatch):
    from onehealth_worker.extraction import repository

    calls = []

    def forbidden_repository(*args, **kwargs):
        calls.append(True)
        raise AssertionError('Repository must not initialize')

    monkeypatch.setattr(repository, 'ExtractionRepository', forbidden_repository)
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'documents': [
        {'status': 'adjudicated', 'prediction': 'first.json', 'source_url': 'https://example.invalid/first'},
        {'status': 'adjudicated', 'prediction': manifest.name, 'source_url': 'https://example.invalid/second'},
    ]}), encoding='utf-8')
    with pytest.raises(ValueError, match='entrada'):
        extract_evaluation_corpus(manifest_path=manifest, database_url='unused',
                                  provider_name='openai', model_name='unused', api_key='unused', force=True)
    assert calls == []
    assert not (tmp_path / 'first.json').exists()


@pytest.mark.parametrize('existing', [False, True])
def test_separate_outputs_reach_service_boundary_without_writing(tmp_path, monkeypatch, existing):
    from onehealth_worker.extraction import repository

    class ServiceBoundary(Exception):
        pass

    def stop(*args, **kwargs):
        raise ServiceBoundary

    monkeypatch.setattr(repository, 'ExtractionRepository', stop)
    manifest = tmp_path / 'manifest.json'
    prediction = tmp_path / 'result.json'
    if existing:
        prediction.write_text('keep', encoding='utf-8')
    manifest.write_text(json.dumps({'documents': [
        {'status': 'adjudicated', 'prediction': prediction.name, 'source_url': 'https://example.invalid/test'},
        {'status': 'adjudicated', 'prediction': 'separate.json', 'source_url': 'https://example.invalid/other'},
    ]}), encoding='utf-8')
    before = manifest.read_bytes()
    with pytest.raises(ServiceBoundary):
        extract_evaluation_corpus(manifest_path=manifest, database_url='unused',
                                  provider_name='openai', model_name='unused', api_key='unused')
    assert manifest.read_bytes() == before
    assert prediction.read_text() == 'keep' if existing else not prediction.exists()


@pytest.mark.parametrize('predictions', [
    ('result.json', 'result.json'),
    ('result.json', 'result.claims.json'),
    ('result.claims.json', 'result.json'),
    ('result.json', 'result.txt'),
])
@pytest.mark.parametrize('force', [False, True])
def test_colliding_generated_outputs_are_rejected_before_services(tmp_path, monkeypatch, predictions, force):
    from onehealth_worker.extraction import repository

    def stop(*args, **kwargs):
        raise AssertionError('Output collision reached services')

    monkeypatch.setattr(repository, 'ExtractionRepository', stop)
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'documents': [
        {'status': 'adjudicated', 'prediction': name, 'source_url': f'https://example.invalid/{i}'}
        for i, name in enumerate(predictions)
    ]}), encoding='utf-8')
    before = manifest.read_bytes()
    with pytest.raises(ValueError, match='destino'):
        extract_evaluation_corpus(manifest_path=manifest, database_url='unused',
                                  provider_name='openai', model_name='unused', api_key='unused', force=force)
    assert manifest.read_bytes() == before
    assert {p.name for p in tmp_path.iterdir()} == {'manifest.json'}


@pytest.mark.parametrize('within_document', [False, True])
def test_hardlinked_generated_outputs_are_rejected(tmp_path, monkeypatch, within_document):
    from onehealth_worker.extraction import repository

    def stop(*args, **kwargs):
        raise AssertionError('Output collision reached services')

    monkeypatch.setattr(repository, 'ExtractionRepository', stop)
    first = tmp_path / 'first.json'
    first.write_text('preserve', encoding='utf-8')
    second = tmp_path / ('first.claims.json' if within_document else 'second.json')
    second.hardlink_to(first)
    names = [first.name] if within_document else [first.name, second.name]
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'documents': [
        {'status': 'adjudicated', 'prediction': name, 'source_url': f'https://example.invalid/{i}'}
        for i, name in enumerate(names)
    ]}), encoding='utf-8')
    with pytest.raises(ValueError, match='destino'):
        extract_evaluation_corpus(manifest_path=manifest, database_url='unused',
                                  provider_name='openai', model_name='unused', api_key='unused', force=True)
    assert first.read_text() == second.read_text() == 'preserve'


@pytest.mark.parametrize('existing,force', [(False, False), (True, False), (True, True)])
def test_full_extraction_with_fake_services_preserves_inputs_and_skip_behavior(
    tmp_path, monkeypatch, existing, force,
):
    from onehealth_worker.extraction import repository, openai_provider
    from onehealth_worker.extraction.schema import load_schema, validate_extraction
    from test_attribution_review import artifacts

    fixture = artifacts()
    claims = json.loads(fixture['claims_bytes'])
    calls = []
    document = SimpleNamespace(raw_item_id=claims['document']['raw_item_id'], title='Synthetic test',
                               url='https://example.invalid/test', published_at=None,
                               language='es', raw_text=fixture['raw_text'])

    class FakeRepository:
        def __init__(self, database_url):
            assert database_url == 'unused'

        def load_raw_document_by_url(self, url):
            calls.append(('load', url))
            return document

    class FakeProvider:
        def __init__(self, **kwargs):
            pass

        def extract(self, **kwargs):
            assert document.raw_text in kwargs['document_input']
            calls.append(('extract',))
            return SimpleNamespace(payload=claims, response_id='synthetic-response')

    monkeypatch.setattr(repository, 'ExtractionRepository', FakeRepository)
    monkeypatch.setattr(openai_provider, 'OpenAIResponsesProvider', FakeProvider)
    manifest = tmp_path / 'manifest.json'
    gold = tmp_path / 'gold.json'
    gold.write_text('{}', encoding='utf-8')
    prediction = tmp_path / 'result.json'
    sidecar = tmp_path / 'result.claims.json'
    if existing:
        prediction.write_text('previous-prediction', encoding='utf-8')
        sidecar.write_text('previous-claims', encoding='utf-8')
    manifest.write_text(json.dumps({'case_code': 'SYNTHETIC', 'documents': [
        {'status': 'adjudicated', 'prediction': prediction.name, 'gold': gold.name,
         'source_url': document.url},
    ]}), encoding='utf-8')
    originals = {p: p.read_bytes() for p in (manifest, gold)}
    result = extract_evaluation_corpus(manifest_path=manifest, database_url='unused',
                                      provider_name='openai', model_name='unused', api_key='unused', force=force)
    if existing and not force:
        assert result['results'][0]['status'] == 'existing'
        assert calls == []
        assert prediction.read_text() == 'previous-prediction'
        assert sidecar.read_text() == 'previous-claims'
    else:
        assert result['results'][0]['status'] == 'generated'
        assert calls == [('load', document.url), ('extract',)]
        assert json.loads(sidecar.read_text()) == claims
        payload = json.loads(prediction.read_text())
        validate_extraction(payload, load_schema())
        assert payload['signals']
    assert all(p.read_bytes() == content for p, content in originals.items())
