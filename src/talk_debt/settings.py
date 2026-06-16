from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".talk_debt.json"


@dataclass
class AppSettings:
    duration_seconds: int = 120
    window_x: int | None = None
    window_y: int | None = None
    mode: str = "normal"
    always_on_top: bool = True


class SettingsStore:
    def __init__(self, path: Path = DEFAULT_CONFIG_PATH) -> None:
        self.path = path

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return AppSettings()

        return AppSettings(
            duration_seconds=max(1, int(data.get("duration_seconds", 120))),
            window_x=data.get("window_x"),
            window_y=data.get("window_y"),
            mode=data.get("mode", "normal"),
            always_on_top=bool(data.get("always_on_top", True)),
        )

    def save(self, settings: AppSettings) -> None:
        self.path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
