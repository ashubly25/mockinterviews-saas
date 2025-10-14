from pydantic_settings import BaseSettings
from typing import Literal, List


class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    PROJECT_NAME: str = "Mock Interviews AI"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # AI Provider Settings
    AI_PROVIDER: Literal["anthropic", "openai"] = "anthropic"
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Model Settings - Model Routing
    ANTHROPIC_LARGE_MODEL: str = "claude-3-5-sonnet-20241022"
    ANTHROPIC_SMALL_MODEL: str = "claude-3-haiku-20240307"
    OPENAI_LARGE_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_SMALL_MODEL: str = "gpt-3.5-turbo"

    # Hybrid Inference - Routing Strategy
    ENABLE_MODEL_ROUTING: bool = True
    ROUTING_COMPLEXITY_THRESHOLD: int = 100  # tokens
    ENABLE_FALLBACK: bool = True
    FALLBACK_MODELS: List[str] = ["claude-3-haiku-20240307", "gpt-3.5-turbo"]

    # Semantic Caching
    ENABLE_SEMANTIC_CACHE: bool = True
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_SIMILARITY_THRESHOLD: float = 0.95
    CACHE_TTL: int = 3600  # 1 hour
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Prompt Compression
    ENABLE_PROMPT_COMPRESSION: bool = True
    MAX_CONTEXT_TOKENS: int = 8000
    COMPRESSION_RATIO: float = 0.7  # Keep 70% of content
    MIN_MESSAGE_LENGTH: int = 50  # Don't compress short messages

    # Session Summarization
    ENABLE_SESSION_SUMMARIZATION: bool = True
    SUMMARIZATION_TRIGGER: int = 10  # Summarize after 10 messages
    KEEP_RECENT_MESSAGES: int = 4  # Keep last 4 messages uncompressed

    # Database
    DATABASE_URL: str = "sqlite:///./interviews.db"

    # Monitoring
    ENABLE_METRICS: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
