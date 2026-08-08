from __future__ import annotations

from datetime import datetime
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from app.theme import COLORS
from components.widgets import panel


class DailyOverviewPanel(QWidget):
    def __init__(self, user_name: str, mock: dict[str, Any], parent=None) -> None:
        super().__init__(parent)
        self.user_name = user_name
        self.mock = mock

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        frame, body = panel("DAILY OVERVIEW")

        self.greeting = QLabel("")
        self.greeting.setObjectName("Greeting")
        hint = QLabel("Here's what requires your attention today.")
        hint.setObjectName("Muted")
        body.addWidget(self.greeting)
        body.addWidget(hint)

        grid = QGridLayout()
        grid.setSpacing(10)

        self.schedule_card = self._card("SCHEDULE", "")
        self.tasks_card, self.tasks_bar, self.tasks_label = self._progress_card("TASKS")
        self.focus_card = self._card("CURRENT FOCUS", "")
        self.prod_card, self.prod_bar, self.prod_label = self._progress_card("PRODUCTIVITY")

        grid.addWidget(self.schedule_card, 0, 0)
        grid.addWidget(self.tasks_card, 0, 1)
        grid.addWidget(self.focus_card, 1, 0)
        grid.addWidget(self.prod_card, 1, 1)
        body.addLayout(grid)
        body.addStretch(1)
        outer.addWidget(frame)
        self.refresh()

    def _card(self, title: str, body_text: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        t = QLabel(title)
        t.setObjectName("SectionTitle")
        b = QLabel(body_text)
        b.setWordWrap(True)
        b.setStyleSheet(f"color: {COLORS['white']}; font-size: 13px;")
        layout.addWidget(t)
        layout.addWidget(b)
        card.body_label = b  # type: ignore[attr-defined]
        return card

    def _progress_card(self, title: str) -> tuple[QFrame, QProgressBar, QLabel]:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        t = QLabel(title)
        t.setObjectName("SectionTitle")
        value = QLabel("")
        value.setStyleSheet(f"color: {COLORS['cyan']}; font-size: 16px;")
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setTextVisible(False)
        bar.setFixedHeight(8)
        layout.addWidget(t)
        layout.addWidget(value)
        layout.addWidget(bar)
        return card, bar, value

    def refresh(self) -> None:
        hour = datetime.now().hour
        if hour < 12:
            greet = "GOOD MORNING"
        elif hour < 18:
            greet = "GOOD AFTERNOON"
        else:
            greet = "GOOD EVENING"
        self.greeting.setText(f"{greet}, {self.user_name.upper()}")

        schedule = self.mock.get("schedule") or []
        if schedule:
            item = schedule[0]
            text = f"{item.get('time', '--:--')}\n{item.get('title', '')}\n{item.get('subtitle', '')}"
        else:
            text = "No upcoming events"
        self.schedule_card.body_label.setText(text)  # type: ignore[attr-defined]

        total = int(self.mock.get("tasks_total", 0))
        done = int(self.mock.get("tasks_done", 0))
        pct = int((done / total) * 100) if total else 0
        self.tasks_label.setText(f"TODAY\n{total} TASKS · {done} DONE")
        self.tasks_bar.setValue(pct)

        self.focus_card.body_label.setText(str(self.mock.get("focus", "—")))  # type: ignore[attr-defined]

        prod = int(self.mock.get("productivity", 0))
        self.prod_label.setText(f"{prod}%")
        self.prod_bar.setValue(prod)
