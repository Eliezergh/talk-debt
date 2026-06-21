from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".talk_debt.json"
DEFAULT_SPEAKER_LABEL = "Unassigned"


def _normalize_speaker_names(values: object) -> list[str]:
    if not isinstance(values, list):
        return []

    names: list[str] = []
    seen: set[str] = set()
    for value in values:
        name = str(value).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def _resolve_current_speaker(raw_value: object, speaker_names: list[str]) -> str:
    current = str(raw_value).strip() if raw_value is not None else ""
    if current and current in speaker_names:
        return current
    return speaker_names[0] if speaker_names else DEFAULT_SPEAKER_LABEL


@dataclass
class AppSettings:
    duration_seconds: int = 120
    window_x: int | None = None
    window_y: int | None = None
    mode: str = "normal"
    always_on_top: bool = True
    speaker_names: list[str] = field(default_factory=list)
    current_speaker: str = DEFAULT_SPEAKER_LABEL

    def __post_init__(self) -> None:
        self.speaker_names = _normalize_speaker_names(self.speaker_names or [])
        self.current_speaker = _resolve_current_speaker(self.current_speaker, self.speaker_names)


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

        speaker_names = _normalize_speaker_names(data.get("speaker_names", []))
        return AppSettings(
            duration_seconds=max(1, int(data.get("duration_seconds", 120))),
            window_x=data.get("window_x"),
            window_y=data.get("window_y"),
            mode=data.get("mode", "normal"),
            always_on_top=bool(data.get("always_on_top", True)),
            speaker_names=speaker_names,
            current_speaker=_resolve_current_speaker(data.get("current_speaker"), speaker_names),
        )

    def save(self, settings: AppSettings) -> None:
        self.path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
