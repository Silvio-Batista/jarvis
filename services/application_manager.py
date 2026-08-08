from __future__ import annotations

import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Any


class ApplicationManager:
    def __init__(self, apps: list[dict[str, Any]]) -> None:
        self.apps = apps

    def list_apps(self) -> list[dict[str, Any]]:
        return list(self.apps)

    def launch(self, app: dict[str, Any]) -> tuple[bool, str]:
        command = str(app.get("command", "")).strip()
        name = app.get("name") or app.get("label") or command
        if not command:
            return False, f"Comando vazio para {name}"

        if command.startswith("http://") or command.startswith("https://"):
            webbrowser.open(command)
            return True, f"Opened {name}"

        # Caminhos conhecidos
        for path in self._candidates(command):
            if Path(path).exists():
                subprocess.Popen([path], shell=False)
                return True, f"Opened {name}"

        try:
            subprocess.Popen(["cmd", "/c", "start", "", command], shell=False)
            return True, f"Opened {name}"
        except OSError as error:
            return False, f"Failed to open {name}: {error}"

    def _candidates(self, command: str) -> list[str]:
        cmd = command.lower()
        mapping = {
            "code": [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            ],
            "msedge": [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            ],
            "spotify": [
                os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
            ],
            "discord": [
                os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe"),
            ],
            "docker desktop": [
                r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
            ],
        }
        return mapping.get(cmd, []) + [command, f"{command}.exe"]
