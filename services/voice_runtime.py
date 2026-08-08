"""Runtime de voz: RESTING (so wake word) <-> ACTIVE (ouve continuo)."""

from __future__ import annotations

import re
import threading
import time
from typing import Any

from PySide6.QtCore import QObject, Signal

from actions.computer import ComputerActions
from core.brain import Brain
from core.config import load_config
from core.listener import Listener, extrair_comando, parece_comando, parece_conversa
from core.speaker import Speaker
from services.jarvis_service import JarvisState

REST_PATTERNS = (
    r"\bdescanse\b",
    r"\bdescansar\b",
    r"\bdescansa\b",
    r"\bpode descansar\b",
    r"\bstand ?by\b",
    r"\bdormir assistente\b",
    r"\bdesligar assistente\b",
    r"\bencerrar assistente\b",
)


class VoiceRuntime(QObject):
    state_changed = Signal(str)
    session_changed = Signal(bool)  # True = ACTIVE, False = RESTING
    heard = Signal(str)
    replied = Signal(str)
    log = Signal(str, str, str)
    ready = Signal()
    failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._listener: Listener | None = None
        self._speaker: Speaker | None = None
        self._brain: Brain | None = None
        self._wake_words: list[str] = ["jarvis", "jávis", "javis"]
        self._last_reply = ""
        self._active = False  # comeca em descanso
        self._lock = threading.Lock()

    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._active

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="jarvis-voice", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def activate(self, announce: bool = True) -> None:
        with self._lock:
            self._active = True
        self.session_changed.emit(True)
        self.log.emit("JARVIS", "Session ACTIVE", "success")
        if announce and self._speaker:
            self._emit_state(JarvisState.SPEAKING)
            self._speaker.say("Online. Estou ouvindo.")
            self._last_reply = "Online. Estou ouvindo."
            self.replied.emit(self._last_reply)

    def deactivate(self, announce: bool = True) -> None:
        with self._lock:
            self._active = False
        self.session_changed.emit(False)
        self.log.emit("JARVIS", "Session RESTING — diga Jarvis para ativar", "jarvis")
        if announce and self._speaker:
            self._emit_state(JarvisState.SPEAKING)
            self._speaker.say("Descansando. Diga Jarvis quando precisar.")
            self._last_reply = "Descansando. Diga Jarvis quando precisar."
            self.replied.emit(self._last_reply)
        self._emit_state(JarvisState.IDLE)

    def toggle_session(self) -> None:
        if self.is_active:
            self.deactivate(announce=True)
        else:
            self.activate(announce=True)

    def _emit_state(self, state: JarvisState) -> None:
        self.state_changed.emit(state.value)

    def _is_rest_command(self, texto: str) -> bool:
        t = texto.lower()
        return any(re.search(p, t) for p in REST_PATTERNS)

    def _has_wake(self, texto: str) -> bool:
        return extrair_comando(texto, self._wake_words) is not None

    def _init_stack(self) -> None:
        config = load_config()
        assistente: dict[str, Any] = config.get("assistente", {})
        apps = config.get("acoes", {}).get("apps", {})
        custom = config.get("vozes_custom") or {}

        self._wake_words = assistente.get(
            "wake_words",
            ["jarvis", "jávis", "javis"],
        )

        self._listener = Listener(
            idioma=assistente.get("idioma_stt", "pt-BR"),
            taxa_amostragem=assistente.get("taxa_amostragem"),
            microfone=assistente.get("microfone", "fifine"),
            silencio_para_parar=assistente.get("silencio_para_parar", 0.5),
            max_segundos=assistente.get("max_segundos_fala", 4.0),
            espera_fala=assistente.get("espera_fala", 2.5),
        )
        self._speaker = Speaker(
            voice=assistente.get("voz_tts", "pt-BR-AntonioNeural"),
            rate=assistente.get("velocidade_tts", "+40%"),
            pitch=assistente.get("tom_tts", "-35Hz"),
            preset=assistente.get("voz_preset"),
            custom_presets=custom,
            engine=assistente.get("tts_engine"),
        )
        if assistente.get("velocidade_tts"):
            self._speaker.rate = assistente["velocidade_tts"]
        if assistente.get("tom_tts"):
            self._speaker.pitch = assistente["tom_tts"]

        self._brain = Brain(
            ComputerActions(apps=apps),
            nome=assistente.get("nome", "Jarvis"),
        )

    def _run(self) -> None:
        try:
            self._emit_state(JarvisState.THINKING)
            self.log.emit("JARVIS", "Initializing voice core...", "jarvis")
            self._init_stack()
            assert self._listener and self._speaker and self._brain
            self.ready.emit()
            with self._lock:
                self._active = False
            self.session_changed.emit(False)
            self.log.emit(
                "JARVIS",
                "Em espera. Diga Jarvis para ativar.",
                "jarvis",
            )
            self._emit_state(JarvisState.SPEAKING)
            self._speaker.say("Em espera. Diga Jarvis para ativar.")
            self._last_reply = "Em espera. Diga Jarvis para ativar."
            self.replied.emit(self._last_reply)
            self._emit_state(JarvisState.IDLE)
        except Exception as error:
            self.failed.emit(str(error))
            self.log.emit("JARVIS", f"Voice failed: {error}", "error")
            self._emit_state(JarvisState.ERROR)
            return

        while not self._stop.is_set():
            try:
                active = self.is_active
                self._emit_state(
                    JarvisState.LISTENING if active else JarvisState.IDLE
                )
                # IDLE visual = resting, mas ainda escuta wake word
                if not active:
                    # marca resting na UI via state IDLE; prompt externo
                    pass

                texto = self._listener.ouvir()
                if self._stop.is_set():
                    break
                if not texto:
                    continue

                if self._last_reply and texto.lower() in self._last_reply.lower():
                    continue

                active = self.is_active

                # --- RESTING: so aceita wake word ---
                if not active:
                    if not self._has_wake(texto):
                        continue

                    self.heard.emit(texto)
                    self.log.emit("USER", texto, "user")

                    # Ativa sessao
                    with self._lock:
                        self._active = True
                    self.session_changed.emit(True)
                    self.log.emit("JARVIS", "Session ACTIVE", "success")

                    comando = extrair_comando(texto, self._wake_words) or ""
                    # "jarvis descanse" logo ao acordar
                    if comando and self._is_rest_command(comando):
                        self.deactivate(announce=True)
                        continue
                    if self._is_rest_command(texto) and not comando:
                        self.deactivate(announce=True)
                        continue

                    if not comando.strip():
                        resposta = "Online. Em que posso ajudar?"
                        self._emit_state(JarvisState.SPEAKING)
                        self._speaker.say(resposta)
                        self._last_reply = resposta
                        self.replied.emit(resposta)
                        self.log.emit("JARVIS", resposta, "jarvis")
                        time.sleep(0.35)
                        continue

                    # "Jarvis abre o chrome"
                    self._emit_state(JarvisState.THINKING)
                    resposta = self._brain.pensar(comando, wake_words=self._wake_words)
                    self._emit_state(JarvisState.EXECUTING)
                    self._emit_state(JarvisState.SPEAKING)
                    self._speaker.say(resposta)
                    self._last_reply = resposta
                    self.replied.emit(resposta)
                    self.log.emit("JARVIS", resposta, "jarvis")
                    time.sleep(0.35)
                    continue

                # --- ACTIVE: ouve continuo ---
                # Descanso (com ou sem dizer jarvis)
                if self._is_rest_command(texto):
                    self.heard.emit(texto)
                    self.log.emit("USER", texto, "user")
                    self.deactivate(announce=True)
                    time.sleep(0.35)
                    continue

                # Sem wake word: so se parecer comando/conversa
                com_wake = extrair_comando(texto, self._wake_words)
                if com_wake is not None:
                    pedido = com_wake
                    if not pedido:
                        self.heard.emit(texto)
                        resposta = "Pode falar."
                        self._emit_state(JarvisState.SPEAKING)
                        self._speaker.say(resposta)
                        self._last_reply = resposta
                        self.replied.emit(resposta)
                        continue
                else:
                    if not (parece_comando(texto) or parece_conversa(texto)):
                        continue
                    pedido = texto

                self.heard.emit(texto)
                self.log.emit("USER", texto, "user")

                if self._is_rest_command(pedido):
                    self.deactivate(announce=True)
                    time.sleep(0.35)
                    continue

                self._emit_state(JarvisState.THINKING)
                resposta = self._brain.pensar(pedido, wake_words=self._wake_words)
                self._emit_state(JarvisState.EXECUTING)
                self._emit_state(JarvisState.SPEAKING)
                self._speaker.say(resposta)
                self._last_reply = resposta
                self.replied.emit(resposta)
                self.log.emit("JARVIS", resposta, "jarvis")
                time.sleep(0.35)
            except Exception as error:
                self.log.emit("JARVIS", f"Voice loop error: {error}", "error")
                self._emit_state(JarvisState.ERROR)
                time.sleep(1.0)

        self._emit_state(JarvisState.ONLINE)
