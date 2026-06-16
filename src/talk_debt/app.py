from __future__ import annotations

import sys
from datetime import datetime
from html import escape

from PySide6.QtWidgets import QApplication

from .icon import create_app_icon
from .settings import SettingsStore
from .stats import SessionStat, StatsStore
from .timer import TalkDebtTimer
from .tray import TrayController
from .ui import StatsDialog, TimerWindow


class TalkDebtApp:
    def __init__(self) -> None:
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setQuitOnLastWindowClosed(False)
        self.app_icon = create_app_icon()
        self.qt_app.setWindowIcon(self.app_icon)

        self.settings_store = SettingsStore()
        self.stats_store = StatsStore()
        self.session_id = self.stats_store.start_session()
        self.settings = self.settings_store.load()
        self.timer_model = TalkDebtTimer(duration_seconds=self.settings.duration_seconds)
        self._loop_allocated_seconds = self.timer_model.duration_seconds
        self.window = TimerWindow(self.timer_model)
        self.window.setWindowIcon(self.app_icon)
        self.stats_dialog = StatsDialog(self.window)

        self.window.start_pause_requested.connect(self._toggle_start_stop)
        self.window.reset_requested.connect(self._reset)
        self.window.next_speaker_requested.connect(self._next_speaker)
        self.window.stats_requested.connect(self._show_stats)

        self.tray = TrayController(
            self.window,
            app_icon=self.app_icon,
            start_pause=self._toggle_start_stop,
            reset=self._reset,
            next_speaker=self._next_speaker,
            set_duration_seconds=self._set_duration_seconds,
            set_mode=self._set_mode,
            toggle_always_on_top=self._set_always_on_top,
            quit_app=self.quit,
        )

        self._apply_loaded_settings()
        self.window.show()

    def _apply_loaded_settings(self) -> None:
        if self.settings.window_x is not None and self.settings.window_y is not None:
            self.window.move(self.settings.window_x, self.settings.window_y)
        self._set_mode(self.settings.mode)
        self._set_always_on_top(self.settings.always_on_top)

    def _toggle_start_stop(self) -> None:
        if self.timer_model.is_running:
            self._finalize_current_loop()
            self.timer_model.reset()
            self._loop_allocated_seconds = self.timer_model.duration_seconds
        else:
            self.timer_model.start()
        self.window.refresh()

    def _reset(self) -> None:
        self._finalize_current_loop()
        self.timer_model.reset()
        self._loop_allocated_seconds = self.timer_model.duration_seconds
        self.window.refresh()

    def _next_speaker(self) -> None:
        self._finalize_current_loop()
        self.timer_model.next_speaker()
        self._loop_allocated_seconds = self.timer_model.duration_seconds
        self.window.refresh()

    def _set_duration_seconds(self, seconds: int) -> None:
        self._finalize_current_loop()
        self.timer_model.set_duration(seconds, restart=False)
        self._loop_allocated_seconds = self.timer_model.duration_seconds
        self.settings.duration_seconds = self.timer_model.duration_seconds
        self._save_settings()
        self.window.refresh()

    def _set_mode(self, mode: str) -> None:
        if mode not in {"normal", "compact", "screen_share"}:
            mode = "normal"
        self.window.apply_mode(mode)
        self.settings.mode = mode
        self.tray.set_mode_checked(mode)
        self._save_settings()

    def _set_always_on_top(self, enabled: bool) -> None:
        self.window.set_always_on_top(enabled)
        self.settings.always_on_top = enabled
        self.tray.set_always_on_top_checked(enabled)
        self._save_settings()

    def _save_settings(self) -> None:
        pos = self.window.pos()
        self.settings.window_x = int(pos.x())
        self.settings.window_y = int(pos.y())
        self.settings_store.save(self.settings)

    def _finalize_current_loop(self) -> None:
        consumed = int(round(self.timer_model.elapsed_seconds()))
        self.stats_store.add_loop(
            self.session_id,
            allocated_seconds=self._loop_allocated_seconds,
            consumed_seconds=consumed,
        )

    @staticmethod
    def _format_duration(seconds: int) -> str:
        value = max(0, int(seconds))
        minutes, sec = divmod(value, 60)
        return f"{minutes:02d}:{sec:02d}"

    def _render_session(self, session: SessionStat, *, title: str) -> list[str]:
        lines = [f"<h3>{escape(title)}</h3>"]
        started = datetime.fromisoformat(session.started_at).strftime("%Y-%m-%d %H:%M")
        lines.append(f"<p><b>Started:</b> {escape(started)}<br>")
        lines.append(f"<b>Loops:</b> {len(session.loops)}<br>")

        went_over = sum(1 for loop in session.loops if loop.went_over)
        lines.append(f"<b>Went over time:</b> {went_over}</p>")

        if not session.loops:
            lines.append("<p>No loops recorded yet.</p>")
            return lines

        lines.append("<p><b>Loop details:</b></p>")
        lines.append("<ul>")
        for idx, loop in enumerate(session.loops, start=1):
            color = "#ff4d4f" if loop.went_over else "#22c55e"
            status = "over time" if loop.went_over else "in time"
            detail = (
                f"{idx}. consumed {self._format_duration(loop.consumed_seconds)} / "
                f"planned {self._format_duration(loop.allocated_seconds)}"
            )
            if loop.went_over:
                detail += f" (over by {self._format_duration(loop.over_seconds)})"
            lines.append(
                f"<li><span style='color:{color};'><b>{escape(status)}</b></span> - {escape(detail)}</li>"
            )
        lines.append("</ul>")
        return lines

    def _show_stats(self) -> None:
        sessions = self.stats_store.list_sessions()
        current = self.stats_store.get_session(self.session_id)

        lines: list[str] = ["<div style='font-family: Helvetica Neue, Helvetica, Arial, sans-serif;'>"]
        if current is not None:
            lines.extend(self._render_session(current, title="Current session"))
        else:
            lines.append("<h3>Current session</h3>")
            lines.append("<p>No data available.</p>")

        other_sessions = [s for s in sessions if s.session_id != self.session_id]
        if other_sessions:
            lines.append("<h3>Previous sessions (last 7 days)</h3>")
            for idx, session in enumerate(reversed(other_sessions), start=1):
                lines.extend(self._render_session(session, title=f"Session {idx}"))

        lines.append("</div>")
        self.stats_dialog.set_report("\n".join(lines).rstrip(), rich=True)
        self.stats_dialog.show()
        self.stats_dialog.raise_()
        self.stats_dialog.activateWindow()

    def run(self) -> int:
        return self.qt_app.exec()

    def quit(self) -> None:
        self._finalize_current_loop()
        self.stats_store.end_session(self.session_id)
        self._save_settings()
        self.qt_app.quit()


def main() -> int:
    app = TalkDebtApp()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
