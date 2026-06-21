from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .settings import DEFAULT_SPEAKER_LABEL
from .timer import TalkDebtTimer, format_signed_mmss


class SpeakerSettingsDialog(QDialog):
    def __init__(self, speaker_names: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Manage speakers")
        self.resize(360, 280)

        title = QLabel("Enter one speaker name per line.")
        title.setStyleSheet("font-weight: 600;")

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Alex\nSam\nJordan")
        self.editor.setPlainText("\n".join(speaker_names))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(title)
        layout.addWidget(self.editor)
        layout.addWidget(buttons)

    def speaker_names(self) -> list[str]:
        names: list[str] = []
        seen: set[str] = set()
        for raw_line in self.editor.toPlainText().splitlines():
            name = raw_line.strip()
            if not name or name in seen:
                continue
            seen.add(name)
            names.append(name)
        return names


class TimerWindow(QWidget):
    start_pause_requested = Signal()
    reset_requested = Signal()
    next_speaker_requested = Signal()
    stats_requested = Signal()
    speaker_changed = Signal(str)
    manage_speakers_requested = Signal()

    def __init__(self, timer_model: TalkDebtTimer) -> None:
        super().__init__()
        self.timer_model = timer_model
        self._drag_offset: QPoint | None = None
        self._mode = "normal"
        self._always_on_top = True

        self.setWindowTitle("Talk Debt")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        # Keep this tool window visible even when Talk Debt is not the active app on macOS.
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)
        self.setStyleSheet("background: #1f1f1f; color: #f0f0f0; border-radius: 10px;")

        self.title_label = QLabel("Talk Debt")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.time_label = QLabel("02:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(QFont("Menlo", 34, QFont.Weight.Bold))

        self.speaker_label = QLabel("Speaker")
        self.speaker_combo = QComboBox()
        self.speaker_combo.currentTextChanged.connect(self.speaker_changed.emit)
        self.manage_speakers_button = QPushButton("Edit")
        self.manage_speakers_button.clicked.connect(self.manage_speakers_requested.emit)

        speaker_row = QHBoxLayout()
        speaker_row.addWidget(self.speaker_label)
        speaker_row.addWidget(self.speaker_combo, 1)
        speaker_row.addWidget(self.manage_speakers_button)
        speaker_widget = QWidget()
        speaker_widget.setLayout(speaker_row)
        self.speaker_widget = speaker_widget

        self.start_pause_button = QPushButton("Start")
        self.reset_button = QPushButton("Reset")
        self.next_button = QPushButton("Next")
        self.stats_button = QPushButton("Stats")
        self.start_pause_button.clicked.connect(self.start_pause_requested.emit)
        self.reset_button.clicked.connect(self.reset_requested.emit)
        self.next_button.clicked.connect(self.next_speaker_requested.emit)
        self.stats_button.clicked.connect(self.stats_requested.emit)

        buttons = QHBoxLayout()
        buttons.addWidget(self.start_pause_button)
        buttons.addWidget(self.reset_button)
        buttons.addWidget(self.next_button)
        buttons.addWidget(self.stats_button)
        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons)
        self.buttons_widget = buttons_widget

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(self.title_label)
        layout.addWidget(self.time_label)
        layout.addWidget(self.speaker_widget)
        layout.addWidget(self.buttons_widget)

        self._ticker = QTimer(self)
        self._ticker.setInterval(200)
        self._ticker.timeout.connect(self.refresh)
        self._ticker.start()
        self.apply_mode("normal")
        self.refresh()

    @property
    def always_on_top(self) -> bool:
        return self._always_on_top

    @property
    def mode(self) -> str:
        return self._mode

    def set_speakers(self, speaker_names: list[str], current_speaker: str) -> None:
        self.speaker_combo.blockSignals(True)
        self.speaker_combo.clear()
        if speaker_names:
            self.speaker_combo.addItems(speaker_names)
            index = self.speaker_combo.findText(current_speaker)
            if index < 0:
                index = 0
            self.speaker_combo.setEnabled(True)
            self.speaker_combo.setCurrentIndex(index)
        else:
            self.speaker_combo.addItem(DEFAULT_SPEAKER_LABEL)
            self.speaker_combo.setEnabled(False)
            self.speaker_combo.setCurrentIndex(0)
        self.speaker_combo.blockSignals(False)

    def set_always_on_top(self, enabled: bool) -> None:
        self._always_on_top = enabled
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()
        if enabled:
            self.raise_()

    def apply_mode(self, mode: str) -> None:
        self._mode = mode
        if mode == "compact":
            self.time_label.setFont(QFont("Menlo", 24, QFont.Weight.Bold))
            self.resize(290, 150)
            self.buttons_widget.hide()
        elif mode == "screen_share":
            self.time_label.setFont(QFont("Menlo", 50, QFont.Weight.Bold))
            self.resize(460, 250)
            self.buttons_widget.show()
        else:
            self.time_label.setFont(QFont("Menlo", 34, QFont.Weight.Bold))
            self.resize(360, 205)
            self.buttons_widget.show()
        self.speaker_widget.show()

    def refresh(self) -> None:
        remaining = self.timer_model.signed_remaining_seconds()
        self.time_label.setText(format_signed_mmss(remaining))
        in_debt = remaining < 0
        self.time_label.setStyleSheet("color: #ff4d4f;" if in_debt else "color: #f0f0f0;")
        self.title_label.setText("Debt" if in_debt else "Talk Debt")
        self.start_pause_button.setText("Stop" if self.timer_model.is_running else "Start")

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_offset = None
        super().mouseReleaseEvent(event)


class StatsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Talk Debt Statistics")
        self.resize(540, 420)

        title = QLabel("Session statistics (retention: last 7 days)")
        title.setStyleSheet("font-weight: 600;")

        self.report = QTextEdit()
        self.report.setReadOnly(True)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(title)
        layout.addWidget(self.report)
        layout.addWidget(close_button)

    def set_report(self, text: str, *, rich: bool = False) -> None:
        if rich:
            self.report.setHtml(text)
            return
        self.report.setPlainText(text)
