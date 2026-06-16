from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .settings import AppSettings, SettingsStore
from .timer import TalkDebtTimer
from .tray import TrayController
from .ui import TimerWindow


class TalkDebtApp:
    def __init__(self) -> None:
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setQuitOnLastWindowClosed(False)

        self.settings_store = SettingsStore()
        self.settings = self.settings_store.load()
        self.timer_model = TalkDebtTimer(duration_seconds=self.settings.duration_seconds)
        self.window = TimerWindow(self.timer_model)

        self.window.start_pause_requested.connect(self._toggle_start_pause)
        self.window.reset_requested.connect(self._reset)
        self.window.next_speaker_requested.connect(self._next_speaker)

        self.tray = TrayController(
            self.window,
            start_pause=self._toggle_start_pause,
            reset=self._reset,
            next_speaker=self._next_speaker,
            set_duration_seconds=self._set_duration_seconds,
            set_mode=self._set_mode,
            toggle_click_through=self._set_click_through,
            toggle_always_on_top=self._set_always_on_top,
            quit_app=self.quit,
        )

        self._apply_loaded_settings()
        self.window.show()

    def _apply_loaded_settings(self) -> None:
        if self.settings.window_x is not None and self.settings.window_y is not None:
            self.window.move(self.settings.window_x, self.settings.window_y)
        self._set_mode(self.settings.mode)
        self._set_click_through(self.settings.click_through)
        self._set_always_on_top(self.settings.always_on_top)

    def _toggle_start_pause(self) -> None:
        self.timer_model.toggle()
        self.window.refresh()

    def _reset(self) -> None:
        self.timer_model.reset()
        self.window.refresh()

    def _next_speaker(self) -> None:
        self.timer_model.next_speaker()
        self.window.refresh()

    def _set_duration_seconds(self, seconds: int) -> None:
        self.timer_model.set_duration(seconds, restart=False)
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

    def _set_click_through(self, enabled: bool) -> None:
        self.window.set_click_through(enabled)
        self.settings.click_through = enabled
        self.tray.set_click_through_checked(enabled)
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

    def run(self) -> int:
        return self.qt_app.exec()

    def quit(self) -> None:
        self._save_settings()
        self.qt_app.quit()


def main() -> int:
    app = TalkDebtApp()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
