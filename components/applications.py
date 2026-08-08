from __future__ import annotations

from typing import Any, Callable

from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from components.widgets import panel


class ApplicationsPanel(QWidget):
    def __init__(
        self,
        apps: list[dict[str, Any]],
        on_launch: Callable[[dict[str, Any]], None],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.on_launch = on_launch
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        frame, body = panel("PRIMARY APPLICATIONS")

        for app in apps:
            label = app.get("label") or app.get("name") or "APP"
            category = str(app.get("category", "app")).upper()
            btn = QPushButton(f"{label}\n{category}")
            btn.setObjectName("AppBtn")
            btn.setMinimumHeight(52)
            btn.clicked.connect(lambda checked=False, a=app: self.on_launch(a))
            body.addWidget(btn)

        body.addStretch(1)
        outer.addWidget(frame)
