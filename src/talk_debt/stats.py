from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .paths import DEFAULT_STATS_PATH, LEGACY_STATS_PATH, ensure_app_data_dir

RETENTION_DAYS = 7
DEFAULT_SPEAKER_LABEL = "Unassigned"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _from_iso(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


@dataclass
class LoopStat:
    timestamp: str
    allocated_seconds: int
    consumed_seconds: int
    speaker_name: str = DEFAULT_SPEAKER_LABEL

    @property
    def over_seconds(self) -> int:
        return max(0, self.consumed_seconds - self.allocated_seconds)

    @property
    def went_over(self) -> bool:
        return self.over_seconds > 0


@dataclass
class SessionStat:
    session_id: str
    started_at: str
    ended_at: str | None = None
    loops: list[LoopStat] = field(default_factory=list)


@dataclass
class StatsData:
    sessions: list[SessionStat] = field(default_factory=list)


class StatsStore:
    def __init__(
        self,
        path: Path = DEFAULT_STATS_PATH,
        legacy_path: Path | None = None,
        now_fn: Callable[[], datetime] = _utcnow,
    ) -> None:
        self.path = path
        if legacy_path is not None:
            self.legacy_path = legacy_path
        elif path == DEFAULT_STATS_PATH:
            self.legacy_path = LEGACY_STATS_PATH
        else:
            self.legacy_path = None
        self._now_fn = now_fn

    def _now(self) -> datetime:
        return self._now_fn()

    @staticmethod
    def _decode(payload: dict[str, object]) -> StatsData:
        sessions: list[SessionStat] = []
        for item in payload.get("sessions", []):
            if not isinstance(item, dict):
                continue
            loops = [
                LoopStat(
                    timestamp=str(loop.get("timestamp")),
                    allocated_seconds=max(
                        1,
                        int(
                            loop.get(
                                "allocated_seconds",
                                loop.get("seconds", 0),
                            )
                        ),
                    ),
                    consumed_seconds=max(
                        0,
                        int(loop.get("consumed_seconds", loop.get("seconds", 0))),
                    ),
                    speaker_name=str(
                        loop.get("speaker_name", loop.get("speaker", DEFAULT_SPEAKER_LABEL))
                    ).strip()
                    or DEFAULT_SPEAKER_LABEL,
                )
                for loop in item.get("loops", [])
                if isinstance(loop, dict)
            ]
            sessions.append(
                SessionStat(
                    session_id=str(item.get("session_id")),
                    started_at=str(item.get("started_at")),
                    ended_at=item.get("ended_at"),
                    loops=loops,
                )
            )
        return StatsData(sessions=sessions)

    def _read(self, path: Path) -> StatsData | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if not isinstance(payload, dict):
            return None
        return self._decode(payload)

    def _load(self) -> StatsData:
        if self.path.exists():
            data = self._read(self.path)
            if data is not None:
                return data
            return StatsData()

        if self.legacy_path is None or not self.legacy_path.exists():
            return StatsData()

        legacy_data = self._read(self.legacy_path)
        if legacy_data is None:
            return StatsData()

        self._save(legacy_data)
        self.legacy_path.unlink(missing_ok=True)
        return legacy_data

    def _save(self, data: StatsData) -> None:
        ensure_app_data_dir()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(data), indent=2), encoding="utf-8")

    def _prune(self, data: StatsData) -> None:
        cutoff = self._now() - timedelta(days=RETENTION_DAYS)
        kept: list[SessionStat] = []
        for session in data.sessions:
            try:
                ended_or_started = (
                    _from_iso(session.ended_at)
                    if session.ended_at
                    else _from_iso(session.started_at)
                )
            except ValueError:
                continue
            if ended_or_started >= cutoff:
                kept.append(session)
        data.sessions = kept

    def start_session(self) -> str:
        data = self._load()
        self._prune(data)
        session_id = str(uuid.uuid4())
        data.sessions.append(SessionStat(session_id=session_id, started_at=self._now().isoformat()))
        self._save(data)
        return session_id

    def add_loop(
        self,
        session_id: str,
        allocated_seconds: int,
        consumed_seconds: int,
        *,
        speaker_name: str = DEFAULT_SPEAKER_LABEL,
    ) -> None:
        if consumed_seconds <= 0:
            return

        planned = max(1, int(allocated_seconds))
        consumed = max(0, int(consumed_seconds))
        speaker = str(speaker_name).strip() or DEFAULT_SPEAKER_LABEL
        data = self._load()
        self._prune(data)
        for session in data.sessions:
            if session.session_id == session_id:
                session.loops.append(
                    LoopStat(
                        timestamp=self._now().isoformat(),
                        allocated_seconds=planned,
                        consumed_seconds=consumed,
                        speaker_name=speaker,
                    )
                )
                break
        self._save(data)

    def end_session(self, session_id: str) -> None:
        data = self._load()
        self._prune(data)
        for session in data.sessions:
            if session.session_id == session_id and session.ended_at is None:
                session.ended_at = self._now().isoformat()
                break
        self._save(data)

    def list_sessions(self) -> list[SessionStat]:
        data = self._load()
        self._prune(data)
        self._save(data)
        return sorted(data.sessions, key=lambda s: s.started_at, reverse=True)

    def get_session(self, session_id: str) -> SessionStat | None:
        for session in self.list_sessions():
            if session.session_id == session_id:
                return session
        return None
