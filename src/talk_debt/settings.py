from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .paths import DEFAULT_CONFIG_PATH, LEGACY_CONFIG_PATH, ensure_app_data_dir

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
    def __init__(
        self,
        path: Path = DEFAULT_CONFIG_PATH,
        legacy_path: Path | None = None,
    ) -> None:
        self.path = path
        if legacy_path is not None:
            self.legacy_path = legacy_path
        elif path == DEFAULT_CONFIG_PATH:
            self.legacy_path = LEGACY_CONFIG_PATH
        else:
            self.legacy_path = None

    def _read_json(self, path: Path) -> dict[str, object] | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if not isinstance(payload, dict):
            return None
        return payload

    @staticmethod
    def _to_settings(data: dict[str, object]) -> AppSettings:
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

    def load(self) -> AppSettings:
        if self.path.exists():
            data = self._read_json(self.path)
            if data is not None:
                return self._to_settings(data)
            return AppSettings()

        if self.legacy_path is None or not self.legacy_path.exists():
            return AppSettings()

        data = self._read_json(self.legacy_path)
        if data is None:
            return AppSettings()

        settings = self._to_settings(data)
        self.save(settings)
        self.legacy_path.unlink(missing_ok=True)
        return settings

    def save(self, settings: AppSettings) -> None:
        ensure_app_data_dir()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
