from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DISCLAIMER = (
    "GENESIS is a research and report-drafting prototype. It does not provide medical diagnosis "
    "or treatment recommendations. Results require review by qualified professionals."
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-5-5"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    ncbi_api_key: str = ""
    ncbi_email: str = ""
    ncbi_tool: str = "GenomeScope"
    offline_mode: bool = False
    cache_ttl_hours: int = 168
    max_upload_mb: int = 50
    max_variants: int = 15
    upload_ttl_hours: int = 24
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_origin: str = "http://localhost:5173"

    # Supabase (optional — falls back to file persistence if not set)
    supabase_url: str = ""
    supabase_key: str = ""

    data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    sample_data_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "sample_data"
    )
    uploads_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "uploads"
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
