from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QObject, Signal


class JarvisState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    EXECUTING = "EXECUTING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"
    ONLINE = "ONLINE"


class JarvisService(QObject):
    """Estado do núcleo JARVIS — pronto para voz/LLM no futuro."""

    state_changed = Signal(str)
    voice_prompt_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._state = JarvisState.ONLINE
        self._voice_prompt = "Say something..."

    @property
    def state(self) -> JarvisState:
        return self._state

    def set_state(self, state: JarvisState | str) -> None:
        value = JarvisState(state) if isinstance(state, str) else state
        self._state = value
        self.state_changed.emit(value.value)

    def set_voice_prompt(self, text: str) -> None:
        self._voice_prompt = text
        self.voice_prompt_changed.emit(text)

    @property
    def voice_prompt(self) -> str:
        return self._voice_prompt
