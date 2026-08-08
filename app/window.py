from __future__ import annotations

import os
import subprocess
from typing import Any

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer
from PySide6.QtGui import QCloseEvent, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QGridLayout,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from app.config import apps_config, settings
from app.theme import COLORS, load_fonts, stylesheet
from components.activity_feed import ActivityFeedPanel
from components.applications import ApplicationsPanel
from components.daily_overview import DailyOverviewPanel
from components.header import HeaderBar
from components.jarvis_core import JarvisCorePanel
from components.quick_actions import QuickActionsPanel
from components.system_status import SystemStatusPanel
from components.voice_interface import VoiceInterfacePanel
from services.activity_manager import ActivityManager
from services.application_manager import ApplicationManager
from services.jarvis_service import JarvisService, JarvisState
from services.reminder_service import ReminderService
from services.system_monitor import SystemMonitor
from services.task_manager import TaskManager
from services.voice_runtime import VoiceRuntime


class GridBackground(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Root")

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(COLORS["bg"]))
        # grid bem sutil (clean)
        pen = QPen(QColor(16, 21, 31, 90))
        pen.setWidth(1)
        painter.setPen(pen)
        step = 64
        for x in range(0, self.width(), step):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), step):
            painter.drawLine(0, y, self.width(), y)

        accent = QPen(QColor(COLORS["red"]))
        accent.setWidth(1)
        painter.setPen(accent)
        m = 12
        length = 22
        painter.drawLine(m, m, m + length, m)
        painter.drawLine(m, m, m, m + length)
        painter.drawLine(self.width() - m, m, self.width() - m - length, m)
        painter.drawLine(self.width() - m, m, self.width() - m, m + length)
        painter.drawLine(m, self.height() - m, m + length, self.height() - m)
        painter.drawLine(m, self.height() - m, m, self.height() - m - length)
        painter.drawLine(
            self.width() - m, self.height() - m, self.width() - m - length, self.height() - m
        )
        painter.drawLine(
            self.width() - m, self.height() - m, self.width() - m, self.height() - m - length
        )


class JarvisWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.cfg = settings()
        load_fonts()
        self.setWindowTitle(self.cfg.get("window_title", "TowerHub JARVIS"))
        self.setMinimumSize(1280, 800)
        self.setStyleSheet(stylesheet())

        self.monitor = SystemMonitor()
        self.activity = ActivityManager()
        self.apps = ApplicationManager(apps_config())
        self.task_manager = TaskManager()
        self.reminders = ReminderService(self.task_manager)
        self.jarvis = JarvisService()
        self.voice = VoiceRuntime()

        self._build_ui()
        self._connect()
        self._bootstrap_logs()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh)
        self.refresh_timer.start(int(self.cfg.get("refresh_ms", 1000)))

        if self.cfg.get("start_maximized", True):
            self.showMaximized()

        self.setWindowOpacity(0.0)
        self._fade = QPropertyAnimation(self, b"windowOpacity")
        self._fade.setDuration(700)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)
        self._fade.start()

        self.jarvis.set_state(JarvisState.IDLE)
        self.reminders.start()
        QTimer.singleShot(400, self._start_voice)

    def _build_ui(self) -> None:
        root = GridBackground()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        self.header = HeaderBar()
        layout.addWidget(self.header)

        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 5)
        grid.setColumnStretch(2, 2)
        grid.setRowStretch(0, 1)

        user = self.cfg.get("user_name", "User")

        self.system_panel = SystemStatusPanel()
        self.daily_panel = DailyOverviewPanel(
            user,
            self.task_manager,
            on_toggle_task=self._on_task_toggle,
        )
        self.core_panel = JarvisCorePanel()
        self.apps_panel = ApplicationsPanel(self.apps.list_apps(), self._launch_app)
        self.activity_panel = ActivityFeedPanel()
        self.actions_panel = QuickActionsPanel(self._quick_action)
        self.voice_panel = VoiceInterfacePanel()

        # Esquerda
        left_col = QVBoxLayout()
        left_col.setSpacing(12)
        left_col.addWidget(self.system_panel, 2)
        left_col.addWidget(self.apps_panel, 2)
        left_wrap = QWidget()
        left_wrap.setLayout(left_col)

        # Centro — cerebro + voz
        center_col = QVBoxLayout()
        center_col.setSpacing(12)
        center_col.addWidget(self.core_panel, 3)
        center_col.addWidget(self.voice_panel, 2)
        center_wrap = QWidget()
        center_wrap.setLayout(center_col)

        # Direita — dia dinamico + activity/actions
        right_col = QVBoxLayout()
        right_col.setSpacing(12)
        right_col.addWidget(self.daily_panel, 4)
        right_col.addWidget(self.activity_panel, 2)
        right_col.addWidget(self.actions_panel, 2)
        right_wrap = QWidget()
        right_wrap.setLayout(right_col)

        grid.addWidget(left_wrap, 0, 0)
        grid.addWidget(center_wrap, 0, 1)
        grid.addWidget(right_wrap, 0, 2)
        layout.addLayout(grid, 1)

    def _connect(self) -> None:
        self.jarvis.state_changed.connect(self.core_panel.set_state)
        self.jarvis.state_changed.connect(self._on_state)
        self.jarvis.voice_prompt_changed.connect(self.voice_panel.set_prompt)

        self.voice.state_changed.connect(self._on_voice_state)
        self.voice.session_changed.connect(self._on_session_changed)
        self.voice.heard.connect(self._on_heard)
        self.voice.replied.connect(self._on_replied)
        self.voice.log.connect(self._on_voice_log)
        self.voice.ready.connect(self._on_voice_ready)
        self.voice.failed.connect(self._on_voice_failed)
        self.voice_panel.toggle_requested.connect(self.voice.toggle_session)

    def _bootstrap_logs(self) -> None:
        self.activity.add("JARVIS", "System monitoring initialized", "jarvis")
        self.activity.add("SYSTEM", "Network connection established", "system")
        self.activity.add("JARVIS", "Command center online", "success")
        self.activity.add("JARVIS", "Voice starts in RESTING mode", "jarvis")
        self.activity_panel.set_events(self.activity.all())

    def _start_voice(self) -> None:
        self.voice_panel.set_state_label("THINKING")
        self.voice_panel.set_prompt("Calibrando microfone...")
        self.voice_panel.set_session_active(False)
        self.voice.start()

    def _refresh(self) -> None:
        snap = self.monitor.snapshot()
        self.system_panel.update_stats(snap)
        self.header.update_mini_stats(snap.cpu, snap.memory, snap.net_down_mbs)
        self.daily_panel.refresh()

    def _on_state(self, state: str) -> None:
        self.voice_panel.set_listening(state == JarvisState.LISTENING.value)

    def _on_voice_state(self, state: str) -> None:
        self.jarvis.set_state(state)
        self.voice_panel.set_state_label(state)

    def _on_session_changed(self, active: bool) -> None:
        self.voice_panel.set_session_active(active)

    def _on_voice_ready(self) -> None:
        self.activity.add("JARVIS", "Voice ready — diga Jarvis para ativar", "success")
        self.activity_panel.set_events(self.activity.all())
        self.voice_panel.set_session_active(False)

    def _on_voice_failed(self, message: str) -> None:
        self.activity.add("JARVIS", f"Voice error: {message}", "error")
        self.activity_panel.set_events(self.activity.all())
        self.voice_panel.set_state_label("ERROR")
        self.voice_panel.set_prompt(message)

    def _on_heard(self, text: str) -> None:
        self.voice_panel.set_heard(text)

    def _on_replied(self, text: str) -> None:
        self.voice_panel.set_reply(text)

    def _on_voice_log(self, source: str, message: str, level: str) -> None:
        self.activity.add(source, message, level)
        self.activity_panel.set_events(self.activity.all())

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self.voice.stop()
        super().closeEvent(event)

    def _launch_app(self, app: dict[str, Any]) -> None:
        self.jarvis.set_state(JarvisState.EXECUTING)
        ok, message = self.apps.launch(app)
        level = "user" if ok else "error"
        self.activity.add("USER" if ok else "JARVIS", message, level)
        self.activity_panel.set_events(self.activity.all())
        # Volta para resting/active conforme sessao
        back = JarvisState.LISTENING if self.voice.is_active else JarvisState.IDLE
        QTimer.singleShot(600, lambda: self.jarvis.set_state(back))

    def _quick_action(self, key: str) -> None:
        mapping = {
            "open_vscode": {"name": "Visual Studio Code", "command": "code"},
            "open_terminal": {"name": "Windows Terminal", "command": "wt"},
            "open_browser": {"name": "Browser", "command": "msedge"},
            "open_spotify": {"name": "Spotify", "command": "spotify"},
        }
        if key in mapping:
            self._launch_app(mapping[key])
            return

        self.jarvis.set_state(JarvisState.EXECUTING)
        if key == "lock":
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=False)
            self.activity.add("JARVIS", "Computer locked", "jarvis")
        elif key == "restart":
            os.system("shutdown /r /t 30")
            self.activity.add("SYSTEM", "Restart scheduled (30s)", "warn")
        elif key == "shutdown":
            os.system("shutdown /s /t 30")
            self.activity.add("SYSTEM", "Shutdown scheduled (30s)", "warn")
        self.activity_panel.set_events(self.activity.all())
        back = JarvisState.LISTENING if self.voice.is_active else JarvisState.IDLE
        QTimer.singleShot(600, lambda: self.jarvis.set_state(back))
