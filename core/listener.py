import re
import time

import numpy as np
import sounddevice as sd
import speech_recognition as sr

from core.audio_devices import resolver_microfone


class Listener:
    """Captura áudio com detecção de voz (VAD) e converte em texto."""

    def __init__(
        self,
        idioma: str = "pt-BR",
        taxa_amostragem: int | None = None,
        limiar_silencio: float = 0.0008,
        microfone: str | int | None = "fifine",
        chunk_ms: int = 80,
        silencio_para_parar: float = 0.55,
        max_segundos: float = 4.5,
        espera_fala: float = 3.0,
    ) -> None:
        self.idioma = idioma
        self.limiar_silencio = limiar_silencio
        self.chunk_ms = chunk_ms
        self.silencio_para_parar = silencio_para_parar
        self.max_segundos = max_segundos
        self.espera_fala = espera_fala
        self.device_index, info = resolver_microfone(microfone)
        self.channels = 1
        self.taxa_amostragem = int(taxa_amostragem or info["default_samplerate"])
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 200
        self.recognizer.dynamic_energy_threshold = False

        print(
            f"Microfone: [{self.device_index}] {info['name']} "
            f"@ {self.taxa_amostragem} Hz"
        )
        self._calibrar()

    def _calibrar(self) -> None:
        """Ajusta limiar com base no ruído ambiente."""
        print("Calibrando microfone (fique em silêncio)...")
        frames = int(0.8 * self.taxa_amostragem)
        audio = sd.rec(
            frames,
            samplerate=self.taxa_amostragem,
            channels=self.channels,
            dtype="float32",
            device=self.device_index,
        )
        sd.wait()
        ruido = float(np.abs(audio).mean())
        # Limiar um pouco acima do ruído, com piso mínimo
        self.limiar_silencio = max(0.0004, ruido * 3.5)
        print(f"Ruído ambiente={ruido:.5f} | limiar={self.limiar_silencio:.5f}")

    def _nivel(self, audio: np.ndarray) -> float:
        if audio.size == 0:
            return 0.0
        if np.issubdtype(audio.dtype, np.integer):
            normalizado = audio.astype(np.float32) / 32768.0
        else:
            normalizado = audio.astype(np.float32)
        return float(np.abs(normalizado).mean())

    def _gravar_vad(self) -> np.ndarray | None:
        """Grava só enquanto houver fala; para no silêncio."""
        chunk = int(self.taxa_amostragem * self.chunk_ms / 1000)
        print("Ouvindo...")

        falando = False
        buffer: list[np.ndarray] = []
        silencio_atual = 0.0
        inicio = time.monotonic()
        inicio_fala = None

        with sd.InputStream(
            samplerate=self.taxa_amostragem,
            channels=self.channels,
            dtype="int16",
            device=self.device_index,
            blocksize=chunk,
        ) as stream:
            while True:
                data, _overflowed = stream.read(chunk)
                mono = data.reshape(-1, self.channels)[:, 0].copy()
                nivel = self._nivel(mono)
                agora = time.monotonic()

                if not falando:
                    if nivel >= self.limiar_silencio:
                        falando = True
                        inicio_fala = agora
                        # Mantém um pedacinho anterior implícito pelo chunk atual
                        buffer.append(mono)
                    elif agora - inicio >= self.espera_fala:
                        return None
                    continue

                buffer.append(mono)

                if nivel < self.limiar_silencio:
                    silencio_atual += self.chunk_ms / 1000
                else:
                    silencio_atual = 0.0

                duracao = agora - (inicio_fala or agora)
                if silencio_atual >= self.silencio_para_parar:
                    break
                if duracao >= self.max_segundos:
                    break

        if not buffer:
            return None
        return np.concatenate(buffer)

    def ouvir(self, segundos: float | None = None) -> str | None:
        if segundos is not None:
            self.max_segundos = segundos

        audio = self._gravar_vad()
        if audio is None:
            return None

        nivel = self._nivel(audio)
        print(f"Nível de áudio: {nivel:.5f}")
        audio_data = sr.AudioData(audio.tobytes(), self.taxa_amostragem, 2)
        try:
            texto = self.recognizer.recognize_google(audio_data, language=self.idioma)
            print(f"Você: {texto}")
            return texto.lower().strip()
        except sr.UnknownValueError:
            print("Não entendi o áudio.")
            return None
        except sr.RequestError as error:
            print(f"Erro no reconhecimento de fala: {error}")
            return None


def extrair_comando(texto: str, wake_words: list[str]) -> str | None:
    """Retorna o comando após a wake word, ou None se ela não aparecer."""
    normalizado = texto.lower().strip()
    for wake in wake_words:
        padrao = rf"\b{re.escape(wake.lower())}\b[,:]?\s*(.*)"
        match = re.search(padrao, normalizado)
        if match:
            return match.group(1).strip()
    return None


def parece_comando(texto: str) -> bool:
    """Heurística para aceitar frases de ação."""
    gatilhos = (
        "abrir",
        "abra",
        "abre",
        "iniciar",
        "inicia",
        "executar",
        "pesquisar",
        "pesquisa",
        "buscar",
        "google",
        "youtube",
        "wikipedia",
        "wiki",
        "que horas",
        "que dia",
        "volume",
        "bloquear",
        "desligar",
        "reiniciar",
        "cancelar",
        "mudo",
        "silenciar",
        "tchau",
        "encerrar",
        "print",
        "screenshot",
        "minimizar",
        "suspender",
        "dormir",
        "o que",
        "quem",
        "qual",
        "como",
        "quando",
        "onde",
        "por que",
        "porque",
        "quanto",
        "me diga",
        "explica",
        "toca",
        "toque",
        "tocar",
        "pausar",
        "play",
        "spotify",
        "ouvir",
        "coloca",
        "ponha",
        "bota",
    )
    t = texto.lower().strip()
    if t.endswith("?"):
        return True
    return any(g in t for g in gatilhos)


def parece_conversa(texto: str) -> bool:
    """Saudacoes e papo curto — sem precisar de wake word."""
    t = texto.lower().strip()
    if not t:
        return False
    gatilhos = (
        "oi",
        "ola",
        "olá",
        "eai",
        "e ai",
        "bom dia",
        "boa tarde",
        "boa noite",
        "tudo bem",
        "tudo bom",
        "como vai",
        "como voce",
        "como você",
        "obrigado",
        "obrigada",
        "valeu",
        "quem e voce",
        "quem é você",
        "qual seu nome",
        "me ajuda",
        "esta ai",
        "está ai",
        "ainda ai",
        "me ouve",
        "me escuta",
        "beleza",
        "valeu",
        "thanks",
        "jarvis",
    )
    if t in {"ok", "okay", "certo", "entendi", "blz", "show", "massa", "fala", "iae", "hey"}:
        return True
    return any(g in t for g in gatilhos)
