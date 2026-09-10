from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str
    supabase_service_role_key: str
    database_url: str
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
