"""Runtime settings, read from environment variables and the backend .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
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


def _date(name: str) -> date | None:
    value = (os.getenv(name) or "").strip()
    return date.fromisoformat(value) if value else None


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
    plan_start_date: date | None = None
    # Any OpenAI-compatible chat completions endpoint (OpenAI, Gemini, Anthropic, OpenRouter, Ollama…).
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_timeout_s: float = 60.0
    chat_history_messages: int = 20

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key and self.llm_model)

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
            plan_start_date=_date("PLAN_START_DATE"),
            llm_base_url=(os.getenv("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/"),
            llm_api_key=os.getenv("LLM_API_KEY") or None,
            llm_model=os.getenv("LLM_MODEL") or None,
            llm_timeout_s=float(os.getenv("LLM_TIMEOUT_S") or 60),
            chat_history_messages=int(os.getenv("CHAT_HISTORY_MESSAGES") or 20),
        )
