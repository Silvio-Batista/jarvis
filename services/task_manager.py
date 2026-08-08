from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TASKS_PATH = ROOT / "config" / "tasks.json"
STATE_PATH = ROOT / "temp" / "tasks_state.json"

WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


@dataclass
class TaskItem:
    id: str
    title: str
    remind_at: str | None
    done: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskItem":
        return cls(
            id=str(data.get("id") or data.get("title")),
            title=str(data.get("title", "Tarefa")),
            remind_at=data.get("remind_at"),
            done=bool(data.get("done", False)),
        )


@dataclass
class DayPlan:
    date_key: str
    weekday: str
    focus: str
    schedule: list[dict[str, Any]]
    tasks: list[TaskItem]

    @property
    def done_count(self) -> int:
        return sum(1 for t in self.tasks if t.done)

    @property
    def total(self) -> int:
        return len(self.tasks)

    @property
    def progress(self) -> int:
        if not self.tasks:
            return 0
        return int((self.done_count / self.total) * 100)

    def next_schedule(self) -> dict[str, Any] | None:
        now = datetime.now().strftime("%H:%M")
        upcoming = [s for s in self.schedule if str(s.get("time", "99:99")) >= now]
        if upcoming:
            return upcoming[0]
        return self.schedule[0] if self.schedule else None


class TaskManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or TASKS_PATH
        self._raw = self._load_raw()
        self._state = self._load_state()

    def _load_raw(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"recurring": {}, "dates": {}, "defaults": {}}
        with self.path.open(encoding="utf-8") as file:
            return json.load(file)

    def _load_state(self) -> dict[str, Any]:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not STATE_PATH.exists():
            return {"done": {}, "notified": {}}
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"done": {}, "notified": {}}

    def _save_state(self) -> None:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(
            json.dumps(self._state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def reload(self) -> None:
        self._raw = self._load_raw()

    def plan_for(self, when: datetime | None = None) -> DayPlan:
        when = when or datetime.now()
        date_key = when.strftime("%Y-%m-%d")
        weekday = WEEKDAYS[when.weekday()]
        defaults = self._raw.get("defaults") or {}

        base = deepcopy(self._raw.get("recurring", {}).get(weekday) or {})
        override = deepcopy(self._raw.get("dates", {}).get(date_key) or {})

        focus = override.get("focus") or base.get("focus") or defaults.get("focus") or "Focus"
        schedule = override.get("schedule") or base.get("schedule") or []
        tasks_raw = override.get("tasks") or base.get("tasks") or []

        done_map = self._state.get("done", {}).get(date_key, {})
        tasks: list[TaskItem] = []
        for item in tasks_raw:
            task = TaskItem.from_dict(item)
            if task.id in done_map:
                task.done = bool(done_map[task.id])
            tasks.append(task)

        return DayPlan(
            date_key=date_key,
            weekday=weekday,
            focus=focus,
            schedule=schedule,
            tasks=tasks,
        )

    def mark_done(self, task_id: str, done: bool = True, when: datetime | None = None) -> None:
        when = when or datetime.now()
        date_key = when.strftime("%Y-%m-%d")
        self._state.setdefault("done", {}).setdefault(date_key, {})[task_id] = done
        self._save_state()

    def due_reminders(self, when: datetime | None = None) -> list[TaskItem]:
        when = when or datetime.now()
        plan = self.plan_for(when)
        now_hm = when.strftime("%H:%M")
        notified = self._state.setdefault("notified", {}).setdefault(plan.date_key, [])
        due: list[TaskItem] = []
        for task in plan.tasks:
            if task.done or not task.remind_at:
                continue
            if task.remind_at <= now_hm and task.id not in notified:
                due.append(task)
        return due

    def mark_notified(self, task_id: str, when: datetime | None = None) -> None:
        when = when or datetime.now()
        date_key = when.strftime("%Y-%m-%d")
        bucket = self._state.setdefault("notified", {}).setdefault(date_key, [])
        if task_id not in bucket:
            bucket.append(task_id)
            self._save_state()
