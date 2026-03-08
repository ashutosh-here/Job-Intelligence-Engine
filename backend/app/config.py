from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Job Intelligence Engine"
    environment: Literal["dev", "staging", "prod", "test"] = "dev"
    api_prefix: str = ""
    log_level: str = "INFO"

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@postgres:5432/jie"
    )
    redis_url: str = "redis://redis:6379/0"
    app_secret_key: str = "CHANGE_ME_STRONG_SECRET"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7
    jwt_algorithm: str = "HS256"

    clearbit_api_key: str = ""
    local_llm_endpoint: str = "http://localhost:11434/api/generate"
    local_llm_model: str = "llama3.2:3b"

    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    embedding_batch_size: int = 32

    source_rate_limit_per_minute: int = 30
    source_max_pages: int = 5
    source_max_scrolls: int = 6
    source_session_state_dir: str = "artifacts/browser_state"
    source_request_timeout_seconds: int = 60
    source_block_resource_types: list[str] = ["image", "font", "media"]
    source_rotate_user_agents: bool = True
    source_enable_proxy_rotation: bool = False
    source_proxies: list[str] = []
    source_proxy_max_failures: int = 3
    source_proxy_cooldown_seconds: int = 180
    source_proxy_sticky_minutes: int = 10
    source_challenge_solver_enabled: bool = False
    source_challenge_solver_provider: str = "signed_http_v1"
    source_challenge_solver_endpoint: str = ""
    source_challenge_solver_api_key: str = ""
    source_challenge_solver_signing_secret: str = ""
    source_challenge_response_max_skew_seconds: int = 120
    source_challenge_retry_limit: int = 1

    metrics_enabled: bool = True

    score_weight_semantic: float = 0.4
    score_weight_salary: float = 0.2
    score_weight_company_stability: float = 0.15
    score_weight_recency: float = 0.15
    score_weight_remote_bonus: float = 0.1

    @field_validator("source_proxies", "source_block_resource_types", mode="before")
    @classmethod
    def _parse_comma_separated_list(cls, value):
        if isinstance(value, str):
            if not value.strip():
                return []
            return [chunk.strip() for chunk in value.split(",") if chunk.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
