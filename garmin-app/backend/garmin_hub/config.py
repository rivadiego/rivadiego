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


@dataclass(frozen=True)
class Settings:
    demo: bool = False
    db_path: Path = BACKEND_DIR / "data" / "garmin.db"
    token_dir: Path = Path("~/.garminconnect").expanduser()
    api_token: str | None = None
    cors_origins: tuple[str, ...] = ("*",)
    sync_page_size: int = 50
    sync_max_pages: int = 20

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
        )
