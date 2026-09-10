from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../../.env"), extra="ignore")

    database_url: str
    supabase_url: str | None = None
    supabase_secret_key: str | None = None
    supabase_service_role_key: str | None = None  # compatibilidad temporal / self-hosted
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
