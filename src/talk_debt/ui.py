from __future__ import annotations

from PySide6.QtCore import QPoint, QTimer, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .timer import TalkDebtTimer, format_signed_mmss


class TimerWindow(QWidget):
    start_pause_requested = Signal()
    reset_requested = Signal()
    next_speaker_requested = Signal()

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
        self.setStyleSheet("background: #1f1f1f; color: #f0f0f0; border-radius: 10px;")

        self.title_label = QLabel("Talk Debt")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.time_label = QLabel("02:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(QFont("Menlo", 34, QFont.Weight.Bold))

        self.start_pause_button = QPushButton("Start")
        self.reset_button = QPushButton("Reset")
        self.next_button = QPushButton("Next")
        self.start_pause_button.clicked.connect(self.start_pause_requested.emit)
        self.reset_button.clicked.connect(self.reset_requested.emit)
        self.next_button.clicked.connect(self.next_speaker_requested.emit)

        buttons = QHBoxLayout()
        buttons.addWidget(self.start_pause_button)
        buttons.addWidget(self.reset_button)
        buttons.addWidget(self.next_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(self.title_label)
        layout.addWidget(self.time_label)
        layout.addLayout(buttons)

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

    def set_always_on_top(self, enabled: bool) -> None:
        self._always_on_top = enabled
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def set_click_through(self, enabled: bool) -> None:
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, enabled)

    def apply_mode(self, mode: str) -> None:
        self._mode = mode
        if mode == "compact":
            self.time_label.setFont(QFont("Menlo", 24, QFont.Weight.Bold))
            self.resize(230, 115)
            self.start_pause_button.hide()
            self.reset_button.hide()
            self.next_button.hide()
        elif mode == "screen_share":
            self.time_label.setFont(QFont("Menlo", 50, QFont.Weight.Bold))
            self.resize(420, 220)
            self.start_pause_button.show()
            self.reset_button.show()
            self.next_button.show()
        else:
            self.time_label.setFont(QFont("Menlo", 34, QFont.Weight.Bold))
            self.resize(320, 165)
            self.start_pause_button.show()
            self.reset_button.show()
            self.next_button.show()

    def refresh(self) -> None:
        remaining = self.timer_model.signed_remaining_seconds()
        self.time_label.setText(format_signed_mmss(remaining))
        in_debt = remaining < 0
        self.time_label.setStyleSheet("color: #ff4d4f;" if in_debt else "color: #f0f0f0;")
        self.title_label.setText("Debt" if in_debt else "Talk Debt")
        self.start_pause_button.setText("Pause" if self.timer_model.is_running else "Start")

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_offset = None
        super().mouseReleaseEvent(event)
