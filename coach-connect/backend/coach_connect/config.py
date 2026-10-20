"""Runtime settings, read from environment variables and the backend .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else BACKEND_DIR / path


def _float(name: str) -> float | None:
    value = (os.getenv(name) or "").strip().replace(",", ".")
    return float(value) if value else None


@dataclass(frozen=True)
class Settings:
    demo: bool = False
    db_path: Path = BACKEND_DIR / "data" / "garmin.db"
    token_dir: Path = Path("~/.garminconnect").expanduser()
    api_token: str | None = None
    cors_origins: tuple[str, ...] = ("*",)
    sync_page_size: int = 50
    sync_max_pages: int = 20
    # Daily vital signs kept fresh for the coach, and how many missing days one sync may backfill.
    wellness_days: int = 14
    wellness_max_days_per_sync: int = 6
    athlete_name: str | None = None
    athlete_height_cm: float | None = None
    athlete_weight_kg: float | None = None
    # Free coach: an Ollama server on this computer. When no model is set, the first installed chat model is used.
    ollama_url: str = "http://localhost:11434"
    ollama_model: str | None = None
    ollama_num_ctx: int = 8192
    # Optional paid alternative: any OpenAI-compatible chat completions endpoint, used when a key is set.
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str | None = None
    llm_model: str | None = None
    # Local models on a laptop CPU can take a while to answer.
    llm_timeout_s: float = 180.0
    chat_history_messages: int = 20
    # Online (a Hugging Face Space): the built web app served by the backend, and a private dataset that keeps
    # the database and the Garmin tokens, because the Space disk is wiped on every restart.
    web_dir: Path | None = None
    hf_token: str | None = None
    hf_data_repo: str | None = None

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv(BACKEND_DIR / ".env")
        demo = _flag("GARMIN_DEMO")
        # Demo data lives in its own database so it never mixes with real activities.
        default_db = "data/demo.db" if demo else "data/garmin.db"
        origins = os.getenv("CORS_ORIGINS") or "*"
        return cls(
            demo=demo,
            db_path=_path(os.getenv("DB_PATH") or default_db),
            token_dir=_path(os.getenv("GARMIN_TOKEN_DIR") or "~/.garminconnect"),
            api_token=os.getenv("API_TOKEN") or None,
            cors_origins=tuple(o.strip() for o in origins.split(",") if o.strip()),
            sync_page_size=int(os.getenv("SYNC_PAGE_SIZE") or 50),
            sync_max_pages=int(os.getenv("SYNC_MAX_PAGES") or 20),
            wellness_days=int(os.getenv("WELLNESS_DAYS") or 14),
            wellness_max_days_per_sync=int(os.getenv("WELLNESS_MAX_DAYS_PER_SYNC") or 6),
            athlete_name=(os.getenv("ATHLETE_NAME") or "").strip() or None,
            athlete_height_cm=_float("ATHLETE_HEIGHT_CM"),
            athlete_weight_kg=_float("ATHLETE_WEIGHT_KG"),
            ollama_url=(os.getenv("OLLAMA_URL") or "http://localhost:11434").rstrip("/"),
            ollama_model=os.getenv("OLLAMA_MODEL") or None,
            ollama_num_ctx=int(os.getenv("OLLAMA_NUM_CTX") or 8192),
            llm_base_url=(os.getenv("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/"),
            llm_api_key=os.getenv("LLM_API_KEY") or None,
            llm_model=os.getenv("LLM_MODEL") or None,
            llm_timeout_s=float(os.getenv("LLM_TIMEOUT_S") or 180),
            chat_history_messages=int(os.getenv("CHAT_HISTORY_MESSAGES") or 20),
            web_dir=_path(os.environ["WEB_DIR"]) if os.getenv("WEB_DIR") else None,
            hf_token=os.getenv("HF_TOKEN") or None,
            hf_data_repo=os.getenv("HF_DATA_REPO") or None,
        )
