from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QMessageBox, QPushButton, QVBoxLayout, QWidget

from components.widgets import panel


class QuickActionsPanel(QWidget):
    def __init__(self, on_action: Callable[[str], None], parent=None) -> None:
        super().__init__(parent)
        self.on_action = on_action
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        frame, body = panel("QUICK ACTIONS")

        actions = [
            ("OPEN VS CODE", "open_vscode", False),
            ("OPEN TERMINAL", "open_terminal", False),
            ("OPEN BROWSER", "open_browser", False),
            ("OPEN SPOTIFY", "open_spotify", False),
            ("LOCK COMPUTER", "lock", False),
            ("RESTART", "restart", True),
            ("SHUTDOWN", "shutdown", True),
        ]
        for label, key, danger in actions:
            btn = QPushButton(label)
            btn.setObjectName("DangerBtn" if danger else "ActionBtn")
            btn.clicked.connect(lambda checked=False, k=key, d=danger, l=label: self._click(k, d, l))
            body.addWidget(btn)

        body.addStretch(1)
        outer.addWidget(frame)

    def _click(self, key: str, danger: bool, label: str) -> None:
        if danger:
            reply = QMessageBox.question(
                self,
                "Confirm",
                f"Execute {label}?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        self.on_action(key)
