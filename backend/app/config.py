from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CODEHAVEN_")

    app_name: str = "CodeHaven"
    host: str = "127.0.0.1"
    port: int = 8765

    ollama_base_url: str = "http://127.0.0.1:11434"
    chat_model: str = "qwen2.5-coder:7b"
    embed_model: str = "nomic-embed-text"

    data_dir: Path = Path(__file__).resolve().parents[2] / "data"
    offline_mode: bool = True


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
