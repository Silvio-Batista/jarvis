from __future__ import annotations

from datetime import datetime
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.theme import COLORS
from components.widgets import panel
from services.task_manager import DayPlan, TaskManager


class DailyOverviewPanel(QWidget):
    def __init__(
        self,
        user_name: str,
        tasks: TaskManager,
        on_toggle_task: Callable[[str, bool], None] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.user_name = user_name
        self.tasks = tasks
        self.on_toggle_task = on_toggle_task

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        frame, body = panel("HOJE")

        self.greeting = QLabel("")
        self.greeting.setObjectName("Greeting")
        self.subtitle = QLabel("")
        self.subtitle.setObjectName("Muted")
        body.addWidget(self.greeting)
        body.addWidget(self.subtitle)

        # Agenda + foco
        top = QHBoxLayout()
        top.setSpacing(10)
        self.schedule_card = self._info_card("PRÓXIMO")
        self.focus_card = self._info_card("FOCO")
        top.addWidget(self.schedule_card, 1)
        top.addWidget(self.focus_card, 1)
        body.addLayout(top)

        # Progresso
        prog_wrap = QFrame()
        prog_wrap.setObjectName("Card")
        prog_l = QVBoxLayout(prog_wrap)
        prog_l.setContentsMargins(12, 10, 12, 10)
        prog_l.setSpacing(6)
        head = QHBoxLayout()
        t = QLabel("TAREFAS DO DIA")
        t.setObjectName("SectionTitle")
        self.tasks_count = QLabel("")
        self.tasks_count.setStyleSheet(f"color: {COLORS['cyan_soft']}; font-size: 12px;")
        head.addWidget(t)
        head.addStretch(1)
        head.addWidget(self.tasks_count)
        self.tasks_bar = QProgressBar()
        self.tasks_bar.setRange(0, 100)
        self.tasks_bar.setTextVisible(False)
        self.tasks_bar.setFixedHeight(6)
        prog_l.addLayout(head)
        prog_l.addWidget(self.tasks_bar)
        body.addWidget(prog_wrap)

        # Lista de tarefas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tasks_host = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_host)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(6)
        self.tasks_layout.addStretch(1)
        scroll.setWidget(self.tasks_host)
        scroll.setMinimumHeight(120)
        body.addWidget(scroll, 1)

        hint = QLabel("Clique na tarefa para marcar como feita · lembretes no Windows")
        hint.setObjectName("Muted")
        hint.setStyleSheet("color: #6b7c90; font-size: 10px;")
        body.addWidget(hint)

        outer.addWidget(frame)
        self.refresh()

    def _info_card(self, title: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        t = QLabel(title)
        t.setObjectName("SectionTitle")
        b = QLabel("—")
        b.setWordWrap(True)
        b.setStyleSheet(f"color: {COLORS['white']}; font-size: 13px; font-weight: 500;")
        layout.addWidget(t)
        layout.addWidget(b)
        card.body_label = b  # type: ignore[attr-defined]
        return card

    def refresh(self) -> None:
        plan = self.tasks.plan_for()
        hour = datetime.now().hour
        if hour < 12:
            greet = "Bom dia"
        elif hour < 18:
            greet = "Boa tarde"
        else:
            greet = "Boa noite"
        self.greeting.setText(f"{greet}, {self.user_name}")
        self.subtitle.setText(
            f"{plan.weekday.capitalize()} · {plan.date_key} · {plan.total} tarefas"
        )

        nxt = plan.next_schedule()
        if nxt:
            self.schedule_card.body_label.setText(  # type: ignore[attr-defined]
                f"{nxt.get('time', '--:--')}\n{nxt.get('title', '')}\n{nxt.get('subtitle', '')}"
            )
        else:
            self.schedule_card.body_label.setText("Sem compromissos")  # type: ignore[attr-defined]

        self.focus_card.body_label.setText(plan.focus)  # type: ignore[attr-defined]
        self.tasks_count.setText(f"{plan.done_count}/{plan.total}")
        self.tasks_bar.setValue(plan.progress)
        self._render_tasks(plan)

    def _render_tasks(self, plan: DayPlan) -> None:
        while self.tasks_layout.count() > 1:
            item = self.tasks_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not plan.tasks:
            empty = QLabel("Nenhuma tarefa para hoje. Edite config/tasks.json")
            empty.setObjectName("Muted")
            self.tasks_layout.insertWidget(0, empty)
            return

        for task in plan.tasks:
            mark = "✓" if task.done else "○"
            remind = f"  ·  {task.remind_at}" if task.remind_at else ""
            btn = QPushButton(f"{mark}  {task.title}{remind}")
            btn.setObjectName("TaskBtnDone" if task.done else "TaskBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(
                lambda checked=False, tid=task.id, done=task.done: self._toggle(tid, not done)
            )
            # re-apply style for objectName swap
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, btn)

    def _toggle(self, task_id: str, done: bool) -> None:
        self.tasks.mark_done(task_id, done=done)
        if self.on_toggle_task:
            self.on_toggle_task(task_id, done)
        self.refresh()
