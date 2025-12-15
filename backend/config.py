from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings - cost-optimized configuration"""

    # Databricks Configuration
    DATABRICKS_HOST: str = os.getenv("DATABRICKS_HOST", "")
    DATABRICKS_TOKEN: str = os.getenv("DATABRICKS_TOKEN", "")

    # LLM Configuration - Using Foundation Model APIs (pay-per-token)
    # Much cheaper than dedicated endpoints
    DATABRICKS_LLM_ENDPOINT: str = "databricks-meta-llama-3-1-70b-instruct"
    # For even lower cost, use: "databricks-meta-llama-3-1-8b-instruct"

    # Vector Search Configuration
    DATABRICKS_VECTOR_INDEX: str = "main.avatar_assistant.databricks_docs_index"

    # TTS Configuration - Using Edge-TTS (FREE)
    TTS_PROVIDER: str = "edge-tts"  # Options: "edge-tts" (free), "kokoro" (open-source)
    TTS_VOICE: str = "en-US-JennyNeural"  # High quality Microsoft voice

    # Cost Control Settings
    MAX_TOKENS_PER_RESPONSE: int = 300  # Limit tokens to control LLM costs
    CACHE_TTL_SECONDS: int = 3600  # Cache responses for 1 hour
    ENABLE_RESPONSE_CACHE: bool = True

    # CORS Settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://*.cloud.databricks.com",
        "https://*.databricksapps.com"
    ]

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
