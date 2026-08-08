from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

from services.task_manager import TaskManager, TaskItem

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "assets" / "logo" / "Logo I.A TowerHub.png"


class ReminderService(QObject):
    """Dispara notificacoes nativas do Windows para tarefas do dia."""

    reminded = Signal(str)

    def __init__(self, tasks: TaskManager, parent=None) -> None:
        super().__init__(parent)
        self.tasks = tasks
        self._timer = QTimer(self)
        self._timer.setInterval(20_000)  # 20s
        self._timer.timeout.connect(self.check)

    def start(self) -> None:
        self._timer.start()
        # checa logo ao iniciar (tarefas ja no horario)
        QTimer.singleShot(1500, self.check)

    def stop(self) -> None:
        self._timer.stop()

    def check(self) -> None:
        for task in self.tasks.due_reminders():
            ok = self._notify(task)
            self.tasks.mark_notified(task.id)
            if ok:
                self.reminded.emit(task.title)

    def _notify(self, task: TaskItem) -> bool:
        title = "JARVIS · Lembrete"
        message = task.title
        if task.remind_at:
            message = f"{task.remind_at} — {task.title}"

        try:
            from winotify import Notification, audio

            toast = Notification(
                app_id="TowerHub JARVIS",
                title=title,
                msg=message,
                icon=str(LOGO) if LOGO.exists() else "",
                duration="short",
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
            return True
        except Exception:
            # Fallback PowerShell toast-like balloon via msg (simples)
            try:
                import subprocess

                subprocess.Popen(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        (
                            "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
                            "ContentType = WindowsRuntime] > $null; "
                            f"$xml = New-Object Windows.Data.Xml.Dom.XmlDocument; "
                        ),
                    ],
                    shell=False,
                )
            except Exception:
                pass
            return False

    def notify_custom(self, title: str, message: str) -> None:
        try:
            from winotify import Notification, audio

            toast = Notification(
                app_id="TowerHub JARVIS",
                title=title,
                msg=message,
                icon=str(LOGO) if LOGO.exists() else "",
                duration="short",
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
        except Exception:
            pass
