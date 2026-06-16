from __future__ import annotations

from dataclasses import dataclass, field
import math
import time


def _clock() -> float:
    return time.monotonic()


def format_signed_mmss(total_seconds: int) -> str:
    sign = "-" if total_seconds < 0 else ""
    value = abs(total_seconds)
    minutes, seconds = divmod(value, 60)
    return f"{sign}{minutes:02d}:{seconds:02d}"


@dataclass
class TalkDebtTimer:
    duration_seconds: int = 120
    _elapsed_paused: float = 0.0
    _started_at: float | None = None
    _time_fn: callable = field(default=_clock, repr=False)

    @property
    def is_running(self) -> bool:
        return self._started_at is not None

    def _now(self) -> float:
        return float(self._time_fn())

    def elapsed_seconds(self) -> float:
        if self._started_at is None:
            return self._elapsed_paused
        return self._elapsed_paused + (self._now() - self._started_at)

    def signed_remaining_seconds(self) -> int:
        remaining = self.duration_seconds - self.elapsed_seconds()
        return math.ceil(remaining) if remaining >= 0 else math.floor(remaining)

    def start(self) -> None:
        if self._started_at is None:
            self._started_at = self._now()

    def pause(self) -> None:
        if self._started_at is not None:
            self._elapsed_paused = self.elapsed_seconds()
            self._started_at = None

    def toggle(self) -> None:
        if self.is_running:
            self.pause()
        else:
            self.start()

    def reset(self, keep_running: bool = False) -> None:
        self._elapsed_paused = 0.0
        if keep_running:
            self._started_at = self._now()
        else:
            self._started_at = None

    def next_speaker(self) -> None:
        self.reset(keep_running=True)

    def set_duration(self, duration_seconds: int, restart: bool = False) -> None:
        self.duration_seconds = max(1, int(duration_seconds))
        self.reset(keep_running=restart)
