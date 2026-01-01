from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    APP_NAME: str = "Code Review Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # Redis Configuration
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    @property
    def redis_dsn(self) -> str:
        """Construct Redis DSN (Redis Cloud or local)."""
        if self.REDIS_URL:
            # Ensure rediss:// URLs include ssl_cert_reqs for compatibility
            # with celery/redis backends that require this parameter.
            url = self.REDIS_URL
            # if url.startswith("rediss://"):
            #     # append ssl_cert_reqs if not present
            #     if "ssl_cert_reqs" not in url:
            #         sep = "&" if "?" in url else "?"
            #         url = f"{url}{sep}ssl_cert_reqs=CERT_REQUIRED"
            return url

        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


    # Celery Configuration
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 1800
    CELERY_TASK_SOFT_TIME_LIMIT: int = 1500

    # Task Settings
    TASK_RESULT_TTL: int = 86400  # 24 hours
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 60  # seconds

    @property
    def celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL or self.redis_dsn

    @property
    def celery_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.redis_dsn

    # GitHub
    GITHUB_TOKEN: Optional[str] = None

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_TIMEOUT: int = 300

    # Cache
    CACHE_TTL: int = 3600
    CACHE_ENABLED: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"

    class Config:
        env_file = Path(__file__).resolve().parent / ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
