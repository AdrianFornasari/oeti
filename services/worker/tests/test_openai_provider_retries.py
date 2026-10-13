import httpx
import pytest

from onehealth_worker.extraction import openai_provider as module


@pytest.fixture
def transport(monkeypatch):
    attempts, sleeps, timeouts = [], [], []
    outcomes = []

    class Client:
        def __init__(self, *, timeout): timeouts.append(timeout)
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def post(self, url, **kwargs):
            attempts.append(url)
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception): raise outcome
            return outcome

    monkeypatch.setattr(module.httpx, 'Client', Client)
    monkeypatch.setattr(module.time, 'sleep', sleeps.append)
    return outcomes, attempts, sleeps, timeouts


def success():
    return httpx.Response(200, json={'id': 'test', 'status': 'completed',
        'output_text': '{"valid":true}'})


def extract():
    return module.OpenAIResponsesProvider('test', 'test', read_timeout_seconds=37).extract(
        instructions='test', document_input='test',
        schema={'type': 'object', 'properties': {}, 'additionalProperties': False})


@pytest.mark.parametrize('error_type', [httpx.ConnectTimeout, httpx.ConnectError])
def test_connect_failure_retries_then_succeeds(transport, error_type):
    outcomes, attempts, sleeps, _ = transport
    outcomes.extend([error_type('connection'), error_type('connection'), success()])
    assert extract().payload == {'valid': True}
    assert len(attempts) == 3
    assert sleeps == [1, 2]


@pytest.mark.parametrize('error_type', [httpx.ConnectTimeout, httpx.ConnectError])
def test_connect_failure_stops_after_three_attempts(transport, error_type):
    outcomes, attempts, sleeps, _ = transport
    error = error_type('connection')
    outcomes.extend([error]*3)
    with pytest.raises(module.LLMProviderError) as exc:
        extract()
    assert exc.value.__cause__ is error
    assert len(attempts) == 3
    assert sleeps == [1, 2]


@pytest.mark.parametrize('error_type', [httpx.ReadTimeout, httpx.ReadError,
    httpx.WriteTimeout, httpx.WriteError, httpx.PoolTimeout,
    httpx.RemoteProtocolError, httpx.CloseError])
def test_other_transport_errors_are_not_retried(transport, error_type):
    outcomes, attempts, sleeps, _ = transport
    error = error_type('transport')
    outcomes.extend([error, success()])
    with pytest.raises(module.LLMProviderError) as exc:
        extract()
    assert exc.value.__cause__ is error
    assert len(attempts) == 1
    assert sleeps == []


def test_timeout_phases_are_explicit(transport):
    outcomes, _, _, timeouts = transport
    outcomes.append(success())
    extract()
    assert timeouts[0].read == 37
    assert timeouts[0].connect == 20
    assert timeouts[0].write == 20
    assert timeouts[0].pool == 20


@pytest.mark.parametrize('value', [0, -1, float('nan'), float('inf'), float('-inf'), True, 'invalid'])
def test_timeout_must_be_finite_positive_number(value):
    with pytest.raises(ValueError):
        module.OpenAIResponsesProvider('test', 'test', read_timeout_seconds=value)


@pytest.mark.parametrize('status', [429, 500, 503])
def test_http_errors_do_not_repeat_inference(transport, status):
    outcomes, attempts, sleeps, _ = transport
    outcomes.extend([httpx.Response(status, json={'error': 'test'}), success()])
    with pytest.raises(module.LLMProviderError, match=f'HTTP {status}'):
        extract()
    assert len(attempts) == 1
    assert sleeps == []
