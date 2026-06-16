from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

_BG_COLOR = QColor("#1e120d")
_CLOCK_COLOR = QColor("#7b432b")


def _draw_icon(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    margin = size * 0.08
    base_rect = QRectF(margin, margin, size - (2 * margin), size - (2 * margin))

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_BG_COLOR)
    painter.drawRoundedRect(base_rect, size * 0.2, size * 0.2)

    center = QPointF(size / 2, size / 2)
    radius = size * 0.29

    ring_pen = QPen(_CLOCK_COLOR)
    ring_pen.setWidthF(max(2.0, size * 0.065))
    painter.setPen(ring_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(center, radius, radius)

    hand_pen = QPen(_CLOCK_COLOR)
    hand_pen.setWidthF(max(2.0, size * 0.055))
    hand_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(hand_pen)
    painter.drawLine(center, QPointF(center.x(), center.y() - (radius * 0.52)))
    painter.drawLine(center, QPointF(center.x() + (radius * 0.42), center.y() - (radius * 0.08)))

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_CLOCK_COLOR)
    painter.drawEllipse(center, size * 0.03, size * 0.03)

    painter.end()
    return pixmap


def create_app_icon() -> QIcon:
    icon = QIcon()
    for size in (16, 18, 20, 22, 24, 32, 40, 48, 64, 128, 256, 512):
        icon.addPixmap(_draw_icon(size))
    return icon
