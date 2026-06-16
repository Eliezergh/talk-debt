from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QInputDialog,
    QMenu,
    QStyle,
    QSystemTrayIcon,
    QWidget,
)


class TrayController:
    def __init__(
        self,
        parent: QWidget,
        *,
        start_pause: Callable[[], None],
        reset: Callable[[], None],
        next_speaker: Callable[[], None],
        set_duration_seconds: Callable[[int], None],
        set_mode: Callable[[str], None],
        toggle_click_through: Callable[[bool], None],
        toggle_always_on_top: Callable[[bool], None],
        quit_app: Callable[[], None],
    ) -> None:
        self._start_pause = start_pause
        self._reset = reset
        self._next_speaker = next_speaker
        self._set_duration_seconds = set_duration_seconds
        self._set_mode = set_mode
        self._toggle_click_through = toggle_click_through
        self._toggle_always_on_top = toggle_always_on_top

        icon = parent.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon = QSystemTrayIcon(QIcon(icon), parent)
        self.menu = QMenu("Talk Debt", parent)

        self.start_pause_action = self.menu.addAction("Start / Pause")
        self.start_pause_action.triggered.connect(self._start_pause)
        self.reset_action = self.menu.addAction("Reset")
        self.reset_action.triggered.connect(self._reset)
        self.next_action = self.menu.addAction("Next speaker")
        self.next_action.triggered.connect(self._next_speaker)
        self.menu.addSeparator()

        duration_menu = self.menu.addMenu("Duration presets")
        for secs, label in [
            (30, "30 seconds"),
            (60, "1 minute"),
            (120, "2 minutes"),
            (180, "3 minutes"),
            (300, "5 minutes"),
        ]:
            action = duration_menu.addAction(label)
            action.triggered.connect(lambda checked=False, s=secs: self._set_duration_seconds(s))

        custom_seconds = duration_menu.addAction("Custom seconds...")
        custom_seconds.triggered.connect(self._ask_custom_seconds)
        custom_minutes = duration_menu.addAction("Custom minutes...")
        custom_minutes.triggered.connect(self._ask_custom_minutes)
        self.menu.addSeparator()

        self.compact_action = self.menu.addAction("Toggle compact mode")
        self.compact_action.setCheckable(True)
        self.compact_action.toggled.connect(self._toggle_compact_mode)
        self.screenshare_action = self.menu.addAction("Toggle screen-share mode")
        self.screenshare_action.setCheckable(True)
        self.screenshare_action.toggled.connect(self._toggle_screenshare_mode)

        self.click_through_action = self.menu.addAction("Toggle click-through mode")
        self.click_through_action.setCheckable(True)
        self.click_through_action.toggled.connect(self._toggle_click_through)

        self.on_top_action = self.menu.addAction("Toggle always-on-top")
        self.on_top_action.setCheckable(True)
        self.on_top_action.setChecked(True)
        self.on_top_action.toggled.connect(self._toggle_always_on_top)

        self.menu.addSeparator()
        self.quit_action = self.menu.addAction("Quit")
        self.quit_action.triggered.connect(quit_app)

        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.setToolTip("Talk Debt")
        self.tray_icon.show()

    def set_click_through_checked(self, enabled: bool) -> None:
        self.click_through_action.setChecked(enabled)

    def set_always_on_top_checked(self, enabled: bool) -> None:
        self.on_top_action.setChecked(enabled)

    def set_mode_checked(self, mode: str) -> None:
        self.compact_action.blockSignals(True)
        self.screenshare_action.blockSignals(True)
        self.compact_action.setChecked(mode == "compact")
        self.screenshare_action.setChecked(mode == "screen_share")
        self.compact_action.blockSignals(False)
        self.screenshare_action.blockSignals(False)

    def _toggle_compact_mode(self, enabled: bool) -> None:
        self._set_mode("compact" if enabled else "normal")
        if enabled:
            self.screenshare_action.setChecked(False)

    def _toggle_screenshare_mode(self, enabled: bool) -> None:
        self._set_mode("screen_share" if enabled else "normal")
        if enabled:
            self.compact_action.setChecked(False)

    def _ask_custom_seconds(self) -> None:
        value, ok = QInputDialog.getInt(
            None,
            "Custom duration (seconds)",
            "Seconds:",
            value=120,
            minValue=1,
            maxValue=3600,
        )
        if ok:
            self._set_duration_seconds(value)

    def _ask_custom_minutes(self) -> None:
        value, ok = QInputDialog.getInt(
            None,
            "Custom duration (minutes)",
            "Minutes:",
            value=2,
            minValue=1,
            maxValue=120,
        )
        if ok:
            self._set_duration_seconds(value * 60)
