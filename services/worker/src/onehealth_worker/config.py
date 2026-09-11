from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../../.env"), extra="ignore")

    database_url: str
    supabase_url: str | None = None
    supabase_secret_key: str | None = None
    supabase_service_role_key: str | None = None  # compatibilidad temporal / self-hosted

    # Sprint 1C - structured epidemiological extraction.
    # Keep credentials server-side only; never expose LLM_API_KEY to apps/web.
    llm_provider: str = "openai"
    llm_model: str = "gpt-5.2"
    llm_api_key: str | None = None
