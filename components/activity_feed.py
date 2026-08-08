from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from app.theme import COLORS
from components.widgets import panel
from services.activity_manager import ActivityEvent


class ActivityFeedPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        frame, body = panel("ACTIVITY LOG")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch(1)
        scroll.setWidget(self.container)
        body.addWidget(scroll)
        outer.addWidget(frame)

    def set_events(self, events: list[ActivityEvent]) -> None:
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for event in events:
            self.list_layout.insertWidget(self.list_layout.count() - 1, self._row(event))

    def _row(self, event: ActivityEvent) -> QWidget:
        colors = {
            "jarvis": COLORS["cyan"],
            "user": COLORS["white"],
            "system": COLORS["green"],
            "warn": COLORS["amber"],
            "error": COLORS["red"],
            "success": COLORS["green"],
            "info": COLORS["muted"],
        }
        color = colors.get(event.level.lower(), COLORS["muted"])
        label = QLabel(
            f"<span style='color:{COLORS['cyan_dim']}; font-family:Consolas'>{event.time_str()}</span><br>"
            f"<span style='color:{color}; letter-spacing:1px'>{event.source}</span><br>"
            f"<span style='color:{COLORS['white']}'>{event.message}</span>"
        )
        label.setWordWrap(True)
        label.setStyleSheet(
            f"background:{COLORS['bg_card']}; border:1px solid {COLORS['border']};"
            "border-radius:4px; padding:8px;"
        )
        return label
