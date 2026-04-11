from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field, AliasChoices
from functools import lru_cache

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", populate_by_name=True)
    service_name: str = "sd-llm-service"
    service_version: str = "1.0.0"
    environment: str = "development"
    anthropic_api_key: str = Field(validation_alias=AliasChoices("ANTHROPIC_API_KEY", "SD_LLM_ANTHROPIC_API_KEY"))
    anthropic_default_timeout: int = 60
    redis_url: str = "redis://localhost:6379/0"
    max_requests_per_minute: int = 60
    routing_config_path: str = "app/config/routing_rules.json"
    cost_per_million_input_tokens: dict = {"claude-haiku-4-5":0.80,"claude-sonnet-4-6":3.00,"claude-opus-4-6":15.00}
    cost_per_million_output_tokens: dict = {"claude-haiku-4-5":4.00,"claude-sonnet-4-6":15.00,"claude-opus-4-6":75.00}

@lru_cache()
def get_settings() -> Settings:
    return Settings()
