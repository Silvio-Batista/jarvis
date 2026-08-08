from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.theme import COLORS, LOGO_PATH


class HeaderBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QHBoxLayout(self)
        root.setContentsMargins(4, 2, 4, 2)
        root.setSpacing(16)

        left = QHBoxLayout()
        left.setSpacing(12)
        left.setAlignment(Qt.AlignVCenter)

        self.logo = QLabel()
        self.logo.setFixedSize(48, 48)
        self.logo.setScaledContents(True)
        if Path(LOGO_PATH).exists():
            pix = QPixmap(str(LOGO_PATH))
            self.logo.setPixmap(
                pix.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        left.addWidget(self.logo)

        brand = QVBoxLayout()
        brand.setSpacing(1)
        tower = QLabel("TOWERHUB")
        tower.setObjectName("Brand")
        title = QLabel("JARVIS")
        title.setObjectName("Title")
        subtitle = QLabel("PERSONAL AI COMMAND CENTER")
        subtitle.setObjectName("Subtitle")
        brand.addWidget(tower)
        brand.addWidget(title)
        brand.addWidget(subtitle)
        left.addLayout(brand)

        center = QVBoxLayout()
        center.setAlignment(Qt.AlignCenter)
        self.clock = QLabel("--:--:--")
        self.clock.setObjectName("BigTime")
        self.clock.setAlignment(Qt.AlignCenter)
        self.date = QLabel("")
        self.date.setObjectName("Muted")
        self.date.setAlignment(Qt.AlignCenter)
        center.addWidget(self.clock)
        center.addWidget(self.date)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.online = QLabel("● SYSTEM ONLINE")
        self.online.setObjectName("StatusOnline")
        self.online.setAlignment(Qt.AlignRight)
        self.mini = QLabel("CPU --%   MEM --%   NET --")
        self.mini.setObjectName("Muted")
        self.mini.setAlignment(Qt.AlignRight)
        right.addWidget(self.online)
        right.addWidget(self.mini)

        root.addLayout(left, 3)
        root.addLayout(center, 3)
        root.addLayout(right, 2)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._tick()

    def _tick(self) -> None:
        now = datetime.now()
        self.clock.setText(now.strftime("%H:%M:%S"))
        # PT-BR amigavel
        dias = [
            "SEGUNDA",
            "TERÇA",
            "QUARTA",
            "QUINTA",
            "SEXTA",
            "SÁBADO",
            "DOMINGO",
        ]
        meses = [
            "JAN",
            "FEV",
            "MAR",
            "ABR",
            "MAI",
            "JUN",
            "JUL",
            "AGO",
            "SET",
            "OUT",
            "NOV",
            "DEZ",
        ]
        self.date.setText(
            f"{dias[now.weekday()]} · {now.day:02d} {meses[now.month - 1]} {now.year}"
        )

    def update_mini_stats(self, cpu: float, mem: float, net_down: float) -> None:
        self.mini.setText(f"CPU {cpu:0.0f}%   MEM {mem:0.0f}%   NET {net_down:0.1f} MB/s")
