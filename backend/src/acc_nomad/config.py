from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_secret: str = ""
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str] | None) -> list[str]:
        if value is None:
            return ["http://localhost:3000"]
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return ["http://localhost:3000"]
            if raw.startswith("["):
                import json

                return json.loads(raw)
            return [part.strip() for part in raw.split(",") if part.strip()]
        return ["http://localhost:3000"]

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    anthropic_model_fast: str = "claude-haiku-4-5"

    # LLM para classificação: auto | fallback | gemini | groq | openai | anthropic
    llm_provider: str = "auto"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    supabase_url: str = ""
    supabase_service_role_key: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from: str = ""

    whatsapp_api_url: str = ""
    whatsapp_api_token: str = ""
    whatsapp_provider: str = "generic"


settings = Settings()
