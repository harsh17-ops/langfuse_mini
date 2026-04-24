from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Mini Langfuse NLP Observability"
    database_url: str = "sqlite:///./observability.db"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    groq_judge_model: str = "llama-3.3-70b-versatile"
    backend_cors_origins: str = "http://localhost:3000"
    enable_model_evals: bool = True
    enable_judge_evals: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    def cors_origins(self) -> list[str]:
        raw_value = self.backend_cors_origins.strip()
        if raw_value.startswith("[") and raw_value.endswith("]"):
            stripped = raw_value[1:-1]
            return [origin.strip().strip('"').strip("'") for origin in stripped.split(",") if origin.strip()]
        return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
