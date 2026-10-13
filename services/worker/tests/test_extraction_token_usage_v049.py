import pytest
from types import SimpleNamespace

from onehealth_worker.extraction import pipeline
from onehealth_worker.extraction.openai_provider import _extract_usage

from onehealth_worker.extraction.repository import (
    _usage_columns,
)


def test_usage_columns_preserve_provider_values():
    assert _usage_columns(
        {
            "input_tokens": 31842,
            "cached_input_tokens": 4096,
            "output_tokens": 4126,
            "reasoning_tokens": 1740,
            "total_tokens": 35968,
        }
    ) == (
        31842,
        4096,
        4126,
        1740,
        35968,
    )


def test_usage_columns_keep_unreported_usage_null_and_reject_negative():
    assert _usage_columns(
        None
    ) == (
        None,
        None,
        None,
        None,
        None,
    )

    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        _usage_columns(
            {
                "input_tokens": -1,
            }
        )


@pytest.mark.parametrize('data', [{}, {'usage': None}])
def test_provider_preserves_absent_usage(data):
    assert _extract_usage(data) is None


def test_provider_preserves_partial_usage_and_explicit_zero():
    assert _extract_usage({'usage': {'input_tokens': 0, 'output_tokens': 4}}) == {
        'input_tokens': 0, 'output_tokens': 4,
    }
    assert _usage_columns(_extract_usage({'usage': {'input_tokens': 0}})) == (0, None, None, None, None)


@pytest.mark.parametrize('value', [True, False, 1.9, -0.5, '12', float('nan'), float('inf')])
def test_repository_rejects_noninteger_usage(value):
    with pytest.raises(ValueError):
        _usage_columns({'input_tokens': value})


@pytest.mark.parametrize('value', [True, 1.9, -1, '12'])
def test_provider_rejects_invalid_reported_usage(value):
    with pytest.raises(ValueError):
        _extract_usage({'usage': {'input_tokens': value}})


@pytest.mark.parametrize('has_response,persist', [(True, True), (False, True), (True, False)])
def test_pipeline_records_known_usage_on_validation_failure(monkeypatch, has_response, persist):
    recorded = []
    usage = {'input_tokens': 12, 'output_tokens': 4, 'total_tokens': 16}
    response = SimpleNamespace(payload={}, response_id='response-id', usage=usage)

    class Repository:
        def __init__(self, dsn): pass
        def load_raw_document(self, identifier):
            return SimpleNamespace(raw_item_id=identifier, title='test', url='test',
                published_at=None, language='es', raw_text='test')
        def record_failed_run(self, **kwargs): recorded.append(kwargs)

    class Provider:
        def __init__(self, **kwargs): pass
        def extract(self, **kwargs):
            if not has_response:
                raise RuntimeError('network failure')
            return response

    def reject(*args): raise RuntimeError('validation failure')

    monkeypatch.setattr(pipeline, 'ExtractionRepository', Repository)
    monkeypatch.setattr(pipeline, 'OpenAIResponsesProvider', Provider)
    monkeypatch.setattr(pipeline, 'load_schema', lambda path: {'properties': {'schema_version': {'const': 'test'}}})
    monkeypatch.setattr(pipeline, 'load_atomic_claims_schema', lambda: {})
    monkeypatch.setattr(pipeline, 'build_document_input', lambda **kwargs: 'test')
    monkeypatch.setattr(pipeline, 'validate_atomic_claims', reject)
    with pytest.raises(RuntimeError):
        pipeline.extract_raw_item(database_url='unused', raw_item_id='raw', provider_name='openai',
            model_name='test', api_key='test', persist=persist)
    if persist:
        assert len(recorded) == 1
        assert recorded[0]['usage'] == (usage if has_response else None)
        assert recorded[0]['response_id'] == ('response-id' if has_response else None)
    else:
        assert recorded == []
