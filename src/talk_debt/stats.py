from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from collections.abc import Callable

DEFAULT_STATS_PATH = Path.home() / ".talk_debt_stats.json"
RETENTION_DAYS = 7


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
        now_fn: Callable[[], datetime] = _utcnow,
    ) -> None:
        self.path = path
        self._now_fn = now_fn

    def _now(self) -> datetime:
        return self._now_fn()

    def _load(self) -> StatsData:
        if not self.path.exists():
            return StatsData()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return StatsData()

        sessions: list[SessionStat] = []
        for item in payload.get("sessions", []):
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
                    consumed_seconds=max(0, int(loop.get("consumed_seconds", loop.get("seconds", 0)))),
                )
                for loop in item.get("loops", [])
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

    def _save(self, data: StatsData) -> None:
        self.path.write_text(json.dumps(asdict(data), indent=2), encoding="utf-8")

    def _prune(self, data: StatsData) -> None:
        cutoff = self._now() - timedelta(days=RETENTION_DAYS)
        kept: list[SessionStat] = []
        for session in data.sessions:
            try:
                ended_or_started = _from_iso(session.ended_at) if session.ended_at else _from_iso(session.started_at)
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

    def add_loop(self, session_id: str, allocated_seconds: int, consumed_seconds: int) -> None:
        if consumed_seconds <= 0:
            return

        planned = max(1, int(allocated_seconds))
        consumed = max(0, int(consumed_seconds))
        data = self._load()
        self._prune(data)
        for session in data.sessions:
            if session.session_id == session_id:
                session.loops.append(
                    LoopStat(
                        timestamp=self._now().isoformat(),
                        allocated_seconds=planned,
                        consumed_seconds=consumed,
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
