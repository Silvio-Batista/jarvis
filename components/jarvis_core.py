from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.theme import COLORS
from services.jarvis_service import JarvisState


class CoreOrb(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(260, 260)
        self._angle = 0.0
        self._state = JarvisState.ONLINE
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(33)

    def set_state(self, state: JarvisState | str) -> None:
        self._state = JarvisState(state) if isinstance(state, str) else state
        self.update()

    def _animate(self) -> None:
        speed = {
            JarvisState.IDLE: 1.2,
            JarvisState.ONLINE: 1.5,
            JarvisState.LISTENING: 3.5,
            JarvisState.THINKING: 5.0,
            JarvisState.EXECUTING: 4.0,
            JarvisState.SPEAKING: 2.8,
            JarvisState.ERROR: 0.6,
        }.get(self._state, 1.5)
        self._angle = (self._angle + speed) % 360
        self.update()

    def _state_color(self) -> QColor:
        mapping = {
            JarvisState.ONLINE: COLORS["cyan"],
            JarvisState.IDLE: COLORS["cyan_dim"],
            JarvisState.LISTENING: COLORS["green"],
            JarvisState.THINKING: COLORS["amber"],
            JarvisState.EXECUTING: COLORS["cyan_soft"],
            JarvisState.SPEAKING: COLORS["cyan"],
            JarvisState.ERROR: COLORS["red"],
        }
        return QColor(mapping.get(self._state, COLORS["cyan"]))

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        radius = min(self.width(), self.height()) * 0.36
        color = self._state_color()

        glow = QRadialGradient(QPointF(cx, cy), radius * 1.6)
        glow.setColorAt(0.0, QColor(color.red(), color.green(), color.blue(), 70))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), radius * 1.55, radius * 1.55)

        for i, scale in enumerate((1.0, 0.78, 0.55)):
            pen = QPen(QColor(color.red(), color.green(), color.blue(), 160 - i * 40))
            pen.setWidthF(1.2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), radius * scale, radius * scale)

        # linhas radiais
        pen = QPen(QColor(color.red(), color.green(), color.blue(), 90))
        pen.setWidthF(1.0)
        painter.setPen(pen)
        for i in range(12):
            ang = math.radians(self._angle + i * 30)
            x1 = cx + math.cos(ang) * radius * 0.6
            y1 = cy + math.sin(ang) * radius * 0.6
            x2 = cx + math.cos(ang) * radius * 0.95
            y2 = cy + math.sin(ang) * radius * 0.95
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # pontos orbitando
        for i in range(3):
            ang = math.radians(self._angle * (1.2 + i * 0.2) + i * 120)
            px = cx + math.cos(ang) * radius * 1.12
            py = cy + math.sin(ang) * radius * 1.12
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(px, py), 2.5, 2.5)

        # núcleo
        painter.setBrush(QColor(5, 10, 18, 220))
        painter.setPen(QPen(color, 1.5))
        painter.drawEllipse(QPointF(cx, cy), radius * 0.42, radius * 0.42)

        painter.setPen(color)
        font = QFont("Segoe UI", 28, QFont.Light)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "J")


class JarvisCorePanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        from components.widgets import panel

        frame, body = panel("JARVIS CORE")
        self.orb = CoreOrb()
        body.addWidget(self.orb, alignment=Qt.AlignCenter)

        self.name = QLabel("JARVIS")
        self.name.setAlignment(Qt.AlignCenter)
        self.name.setStyleSheet(f"color: {COLORS['cyan']}; letter-spacing: 4px; font-weight: 700;")
        self.status = QLabel("ONLINE")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet(f"color: {COLORS['green']}; letter-spacing: 3px; font-size: 12px;")

        self.meta = QLabel("CORE STABLE · VOICE READY · AI READY")
        self.meta.setAlignment(Qt.AlignCenter)
        self.meta.setObjectName("Muted")
        self.meta.setStyleSheet("color: #7a8fa3; font-size: 11px;")

        body.addWidget(self.name)
        body.addWidget(self.status)
        body.addWidget(self.meta)
        layout.addWidget(frame)

    def set_state(self, state: str) -> None:
        self.orb.set_state(state)
        display = "RESTING" if state == "IDLE" else state
        self.status.setText(display)
        color = COLORS["green"] if state in {"ONLINE", "LISTENING"} else COLORS["cyan"]
        if state == "IDLE":
            color = COLORS["amber"]
        if state == "ERROR":
            color = COLORS["red"]
        self.status.setStyleSheet(f"color: {color}; letter-spacing: 3px; font-size: 12px;")
