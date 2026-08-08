from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any

from services.database import db_cursor

WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def _fmt_time(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, timedelta):
        total = int(value.total_seconds())
        hours, rem = divmod(total, 3600)
        minutes, _ = divmod(rem, 60)
        return f"{hours:02d}:{minutes:02d}"
    if isinstance(value, time):
        return value.strftime("%H:%M")
    text = str(value)
    return text[:5] if len(text) >= 5 else text


@dataclass
class TaskItem:
    id: str
    title: str
    remind_at: str | None
    done: bool = False


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
    """Tarefas e agenda dinamicas via MySQL (banco `jarvis`)."""

    def ensure_day(self, when: datetime | None = None) -> date:
        """Materializa o dia a partir do template recorrente, se ainda nao existir."""
        when = when or datetime.now()
        plan_date = when.date()
        weekday = when.weekday()  # 0=monday

        with db_cursor() as cur:
            cur.execute("SELECT id, focus FROM day_plans WHERE plan_date=%s", (plan_date,))
            day = cur.fetchone()
            if day:
                return plan_date

            cur.execute(
                "SELECT focus FROM recurring_plans WHERE weekday=%s",
                (weekday,),
            )
            rec = cur.fetchone()
            focus = rec["focus"] if rec else "Focus"
            cur.execute(
                "INSERT INTO day_plans (plan_date, focus) VALUES (%s, %s)",
                (plan_date, focus),
            )

            cur.execute(
                "SELECT time_at, title, subtitle FROM recurring_schedule WHERE weekday=%s",
                (weekday,),
            )
            for item in cur.fetchall():
                cur.execute(
                    "INSERT INTO day_schedule (plan_date, time_at, title, subtitle) "
                    "VALUES (%s, %s, %s, %s)",
                    (plan_date, item["time_at"], item["title"], item["subtitle"]),
                )

            cur.execute(
                "SELECT title, remind_at, sort_order FROM recurring_tasks "
                "WHERE weekday=%s ORDER BY sort_order, id",
                (weekday,),
            )
            for item in cur.fetchall():
                cur.execute(
                    "INSERT INTO tasks (plan_date, title, remind_at, sort_order) "
                    "VALUES (%s, %s, %s, %s)",
                    (plan_date, item["title"], item["remind_at"], item["sort_order"]),
                )
        return plan_date

    def plan_for(self, when: datetime | None = None) -> DayPlan:
        when = when or datetime.now()
        plan_date = self.ensure_day(when)
        weekday = WEEKDAYS[when.weekday()]

        with db_cursor() as cur:
            cur.execute(
                "SELECT focus FROM day_plans WHERE plan_date=%s",
                (plan_date,),
            )
            day = cur.fetchone()
            focus = day["focus"] if day else "Focus"

            cur.execute(
                "SELECT time_at, title, subtitle FROM day_schedule "
                "WHERE plan_date=%s ORDER BY time_at, id",
                (plan_date,),
            )
            schedule = [
                {
                    "time": _fmt_time(row["time_at"]) or "--:--",
                    "title": row["title"],
                    "subtitle": row.get("subtitle") or "",
                }
                for row in cur.fetchall()
            ]

            cur.execute(
                "SELECT id, title, remind_at, done FROM tasks "
                "WHERE plan_date=%s ORDER BY sort_order, id",
                (plan_date,),
            )
            tasks = [
                TaskItem(
                    id=str(row["id"]),
                    title=row["title"],
                    remind_at=_fmt_time(row["remind_at"]),
                    done=bool(row["done"]),
                )
                for row in cur.fetchall()
            ]

        return DayPlan(
            date_key=plan_date.isoformat(),
            weekday=weekday,
            focus=focus,
            schedule=schedule,
            tasks=tasks,
        )

    def mark_done(self, task_id: str, done: bool = True, when: datetime | None = None) -> None:
        with db_cursor() as cur:
            cur.execute(
                "UPDATE tasks SET done=%s WHERE id=%s",
                (1 if done else 0, int(task_id)),
            )

    def add_task(
        self,
        title: str,
        remind_at: str | None = None,
        when: datetime | None = None,
    ) -> int:
        when = when or datetime.now()
        plan_date = self.ensure_day(when)
        remind_value = None
        if remind_at:
            parts = remind_at.split(":")
            remind_value = time(int(parts[0]), int(parts[1]))

        with db_cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(sort_order), -1) + 1 AS next_order "
                "FROM tasks WHERE plan_date=%s",
                (plan_date,),
            )
            order = cur.fetchone()["next_order"]
            cur.execute(
                "INSERT INTO tasks (plan_date, title, remind_at, sort_order) "
                "VALUES (%s, %s, %s, %s)",
                (plan_date, title, remind_value, order),
            )
            return int(cur.lastrowid)

    def delete_task(self, task_id: str) -> None:
        with db_cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id=%s", (int(task_id),))

    def set_focus(self, focus: str, when: datetime | None = None) -> None:
        when = when or datetime.now()
        plan_date = self.ensure_day(when)
        with db_cursor() as cur:
            cur.execute(
                "UPDATE day_plans SET focus=%s WHERE plan_date=%s",
                (focus, plan_date),
            )

    def due_reminders(self, when: datetime | None = None) -> list[TaskItem]:
        when = when or datetime.now()
        plan_date = self.ensure_day(when)
        now_time = when.time().replace(second=0, microsecond=0)

        with db_cursor() as cur:
            cur.execute(
                "SELECT id, title, remind_at, done FROM tasks "
                "WHERE plan_date=%s AND done=0 AND notified=0 AND remind_at IS NOT NULL "
                "AND remind_at <= %s ORDER BY remind_at, id",
                (plan_date, now_time),
            )
            return [
                TaskItem(
                    id=str(row["id"]),
                    title=row["title"],
                    remind_at=_fmt_time(row["remind_at"]),
                    done=False,
                )
                for row in cur.fetchall()
            ]

    def mark_notified(self, task_id: str, when: datetime | None = None) -> None:
        with db_cursor() as cur:
            cur.execute(
                "UPDATE tasks SET notified=1 WHERE id=%s",
                (int(task_id),),
            )

    def reload(self) -> None:
        """Compat: nada a cachear — sempre le do MySQL."""
        return None
