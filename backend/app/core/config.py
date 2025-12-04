"""Application configuration settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "PopGraph"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://localhost:5432/popgraph"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Z-Image-Turbo (ModelScope API)
    modelscope_api_key: str = ""
    modelscope_base_url: str = "https://api-inference.modelscope.cn/"
    zimage_timeout: int = 30000  # milliseconds (异步API需要更长超时)

    # Storage
    s3_bucket: str = "popgraph-images"
    s3_endpoint: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
