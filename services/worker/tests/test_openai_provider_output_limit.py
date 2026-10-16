import httpx
import pytest

from onehealth_worker.extraction import openai_provider as module


@pytest.fixture
def requests(monkeypatch):
    bodies = []
    outcomes = []

    class Client:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def post(self, url, **kwargs):
            bodies.append(kwargs['json'])
            return outcomes.pop(0)

    monkeypatch.setattr(module.httpx, 'Client', Client)
    return bodies, outcomes


def extract(provider):
    return provider.extract(instructions='test', document_input='test',
        schema={'type': 'object', 'properties': {}, 'additionalProperties': False})


@pytest.mark.parametrize('limit', [None, 1, 8192])
def test_output_limit_is_optional_and_sent_exactly(requests, limit):
    bodies, outcomes = requests
    outcomes.append(httpx.Response(200, json={'status': 'completed', 'output_text': '{}'}))
    provider = module.OpenAIResponsesProvider('test', 'test', max_output_tokens=limit)
    assert extract(provider).payload == {}
    if limit is None:
        assert 'max_output_tokens' not in bodies[0]
    else:
        assert bodies[0]['max_output_tokens'] == limit
    assert bodies[0]['store'] is False
    assert bodies[0]['text']['format']['strict'] is True


@pytest.mark.parametrize('limit', [True, False, 0, -1, 8192.0, '8192', float('inf'), float('nan')])
def test_invalid_output_limit_is_rejected_before_transport(requests, limit):
    bodies, _ = requests
    with pytest.raises(ValueError, match='max_output_tokens'):
        module.OpenAIResponsesProvider('test', 'test', max_output_tokens=limit)
    assert bodies == []


def test_existing_constructor_keeps_output_limit_omitted(requests):
    bodies, outcomes = requests
    outcomes.append(httpx.Response(200, json={'status': 'completed', 'output_text': '{}'}))
    extract(module.OpenAIResponsesProvider('test', 'test'))
    assert 'max_output_tokens' not in bodies[0]


def test_incomplete_response_is_not_accepted_or_retried(requests):
    bodies, outcomes = requests
    outcomes.append(httpx.Response(200, json={'status': 'incomplete',
        'incomplete_details': {'reason': 'max_output_tokens'}, 'output_text': '{}'}))
    with pytest.raises(module.LLMProviderError, match='incomplete'):
        extract(module.OpenAIResponsesProvider('test', 'test', max_output_tokens=8192))
    assert len(bodies) == 1
    assert bodies[0]['max_output_tokens'] == 8192
