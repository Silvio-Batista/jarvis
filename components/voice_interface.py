from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.theme import COLORS
from components.widgets import panel


class WaveWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(42)
        self._phase = 0
        self._active = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    def set_active(self, active: bool) -> None:
        self._active = active
        self.update()

    def _tick(self) -> None:
        if self._active:
            self._phase = (self._phase + 1) % 200
            self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor(COLORS["green"] if self._active else COLORS["cyan_dim"])
        pen = QPen(color, 2)
        painter.setPen(pen)
        w, h = self.width(), self.height()
        mid = h / 2
        bars = 24
        for i in range(bars):
            x = 8 + i * ((w - 16) / bars)
            if self._active:
                amp = 6 + 12 * abs((i + self._phase // 3) % 8 - 4) / 4
            else:
                amp = 3
            painter.drawLine(int(x), int(mid - amp), int(x), int(mid + amp))


class VoiceInterfacePanel(QWidget):
    toggle_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        frame, body = panel("VOICE INTERFACE")

        self.session = QLabel("SESSION: RESTING")
        self.session.setAlignment(Qt.AlignCenter)
        self.session.setStyleSheet(
            f"color: {COLORS['amber']}; letter-spacing: 2px; font-size: 11px; font-weight: 700;"
        )

        self.status = QLabel("● STARTING")
        self.status.setStyleSheet(f"color: {COLORS['amber']}; letter-spacing: 2px;")
        self.prompt = QLabel('"Initializing microphone..."')
        self.prompt.setObjectName("Muted")
        self.prompt.setAlignment(Qt.AlignCenter)
        self.prompt.setWordWrap(True)
        self.heard = QLabel("")
        self.heard.setAlignment(Qt.AlignCenter)
        self.heard.setWordWrap(True)
        self.heard.setStyleSheet(f"color: {COLORS['cyan_soft']}; font-size: 11px;")
        self.waves = WaveWidget()

        self.toggle_btn = QPushButton("ACTIVATE JARVIS")
        self.toggle_btn.setObjectName("ActionBtn")
        self.toggle_btn.clicked.connect(self.toggle_requested.emit)

        body.addWidget(self.session)
        body.addWidget(self.status)
        body.addWidget(self.waves)
        body.addWidget(self.prompt)
        body.addWidget(self.heard)
        body.addWidget(self.toggle_btn)
        body.addStretch(1)
        outer.addWidget(frame)
        self._session_active = False

    def set_session_active(self, active: bool) -> None:
        self._session_active = active
        if active:
            self.session.setText("SESSION: ACTIVE")
            self.session.setStyleSheet(
                f"color: {COLORS['green']}; letter-spacing: 2px; font-size: 11px; font-weight: 700;"
            )
            self.toggle_btn.setText("DEACTIVATE / REST")
            self.toggle_btn.setObjectName("DangerBtn")
            self.toggle_btn.setStyle(self.toggle_btn.style())
        else:
            self.session.setText("SESSION: RESTING")
            self.session.setStyleSheet(
                f"color: {COLORS['amber']}; letter-spacing: 2px; font-size: 11px; font-weight: 700;"
            )
            self.toggle_btn.setText("ACTIVATE JARVIS")
            self.toggle_btn.setObjectName("ActionBtn")
            self.toggle_btn.setStyle(self.toggle_btn.style())
            self.prompt.setText('"Diga Jarvis para ativar"')
            self.waves.set_active(False)

    def set_listening(self, listening: bool) -> None:
        self.waves.set_active(listening)

    def set_state_label(self, state: str) -> None:
        colors = {
            "LISTENING": COLORS["green"],
            "THINKING": COLORS["amber"],
            "EXECUTING": COLORS["cyan_soft"],
            "SPEAKING": COLORS["cyan"],
            "ONLINE": COLORS["green"],
            "IDLE": COLORS["amber"],
            "ERROR": COLORS["red"],
        }
        color = colors.get(state, COLORS["cyan"])
        label = state
        if state == "IDLE" and not self._session_active:
            label = "RESTING"
        self.status.setText(f"● {label}")
        self.status.setStyleSheet(f"color: {color}; letter-spacing: 2px;")

        # Em resting ainda escuta wake word — ondas suaves
        resting_listen = state == "IDLE" and not self._session_active
        self.waves.set_active(state == "LISTENING" or resting_listen)

        if state == "LISTENING":
            self.prompt.setText('"Ouvindo — pode falar direto"')
        elif state == "IDLE" and not self._session_active:
            self.prompt.setText('"Diga Jarvis para ativar"')
        elif state == "THINKING":
            self.prompt.setText('"Processando..."')
        elif state == "SPEAKING":
            self.prompt.setText('"Respondendo..."')
        elif state == "ERROR":
            self.prompt.setText('"Falha no microfone/voz"')

    def set_prompt(self, text: str) -> None:
        self.prompt.setText(f'"{text}"')

    def set_heard(self, text: str) -> None:
        self.heard.setText(f"YOU: {text}")

    def set_reply(self, text: str) -> None:
        self.prompt.setText(f'"{text}"')
