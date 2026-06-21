from __future__ import annotations

from pathlib import Path

APP_DATA_DIR = Path.home() / ".talk-debt"

DEFAULT_CONFIG_PATH = APP_DATA_DIR / "settings.json"
LEGACY_CONFIG_PATH = Path.home() / ".talk_debt.json"

DEFAULT_STATS_PATH = APP_DATA_DIR / "stats.json"
LEGACY_STATS_PATH = Path.home() / ".talk_debt_stats.json"


def ensure_app_data_dir() -> None:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
