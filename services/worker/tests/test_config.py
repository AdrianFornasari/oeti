from pathlib import Path

from onehealth_worker.config import Settings


def test_default_model_matches_documented_configuration(monkeypatch):
    monkeypatch.delenv('LLM_MODEL', raising=False)
    settings = Settings(database_url='postgresql://example.invalid/test', _env_file=None)
    example = Path(__file__).resolve().parents[3] / '.env.example'
    documented_model = next(
        line.split('=', 1)[1] for line in example.read_text().splitlines()
        if line.startswith('LLM_MODEL=')
    )
    assert settings.llm_model == documented_model


def test_environment_model_overrides_default(monkeypatch):
    monkeypatch.setenv('LLM_MODEL', 'custom-environment-model')
    settings = Settings(database_url='postgresql://example.invalid/test', _env_file=None)
    assert settings.llm_model == 'custom-environment-model'


def test_explicit_model_overrides_environment(monkeypatch):
    monkeypatch.setenv('LLM_MODEL', 'custom-environment-model')
    settings = Settings(database_url='postgresql://example.invalid/test',
                        llm_model='custom-explicit-model', _env_file=None)
    assert settings.llm_model == 'custom-explicit-model'
