from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    PROJECT_NAME: str = "RecoverX API"
    API_V1_STR: str = "/api/v1"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://recoverx:recoverx_secret@localhost:5432/recoverx_db"
    SYNC_DATABASE_URL: str = "postgresql://recoverx:recoverx_secret@localhost:5432/recoverx_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Security
    JWT_SECRET: str = "super_secret_jwt_key_for_development_replace_in_prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Razorpay
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # Execution Engine Configuration
    EXECUTION_MODE: str = "local_deterministic"  # "local_deterministic", "razorpay_sandbox"

    # AI Diagnostic Agent Configuration
    LLM_PROVIDER: str = "mock"  # "mock", "gemini", "openai"
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_API_KEY: str = ""
    LLM_TIMEOUT_SECONDS: int = 15
    LLM_MAX_RETRIES: int = 1


settings = Settings()
