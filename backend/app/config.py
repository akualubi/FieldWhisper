from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent
KNOWLEDGE_ROOT = BACKEND_ROOT / "knowledge"
DATA_ROOT = BACKEND_ROOT / "data"
SEED_ROOT = REPO_ROOT / "seed"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    suian_db_path: str = str(BACKEND_ROOT / "suian.db")

    # Weather sources (按 seed/weather_api_notes.md)
    openmeteo_base: str = "https://api.open-meteo.com/v1"
    qweather_host: str = ""
    qweather_token: str = ""

    # LLM (按 seed/llm_api_notes.md，四家全 OpenAI 兼容)
    llm_provider: str = "none"    # deepseek | qwen | moonshot | anthropic | none
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"

    # 服务
    host: str = "0.0.0.0"
    port: int = 8000

    @property
    def knowledge_root(self) -> Path:
        return KNOWLEDGE_ROOT

    @property
    def data_root(self) -> Path:
        return DATA_ROOT

    @property
    def seed_root(self) -> Path:
        return SEED_ROOT


settings = Settings()
