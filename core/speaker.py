import asyncio
import ctypes
import hashlib
import os
import tempfile
import time
from pathlib import Path

import edge_tts
import requests

CACHE_DIR = Path(__file__).resolve().parent.parent / "temp" / "tts_cache"


VOICE_PRESETS: dict[str, dict[str, str]] = {
    "julio": {
        "voice": "pt-BR-JulioNeural",
        "rate": "+10%",
        "pitch": "+0Hz",
        "engine": "azure",
        "descricao": "Masculina PT-BR Julio (Azure Speech - recomendado)",
    },
    "jarvis_robot": {
        "voice": "pt-BR-AntonioNeural",
        "rate": "+40%",
        "pitch": "-35Hz",
        "engine": "edge",
        "descricao": "Masculina PT Antonio, grave/robotica e rapida (Edge gratuito)",
    },
    "antonio": {
        "voice": "pt-BR-AntonioNeural",
        "rate": "+25%",
        "pitch": "+0Hz",
        "engine": "edge",
        "descricao": "Masculina PT natural (Edge)",
    },
    "francisca": {
        "voice": "pt-BR-FranciscaNeural",
        "rate": "+20%",
        "pitch": "+0Hz",
        "engine": "edge",
        "descricao": "Feminina PT natural (Edge)",
    },
    "thalita": {
        "voice": "pt-BR-ThalitaMultilingualNeural",
        "rate": "+15%",
        "pitch": "-10Hz",
        "engine": "edge",
        "descricao": "Feminina PT multilingue (Edge)",
    },
    "ryan_deep": {
        "voice": "en-GB-RyanNeural",
        "rate": "+5%",
        "pitch": "-25Hz",
        "engine": "edge",
        "descricao": "Masculina EN-GB grave (Edge)",
    },
    "guy_robot": {
        "voice": "en-US-GuyNeural",
        "rate": "+0%",
        "pitch": "-40Hz",
        "engine": "edge",
        "descricao": "Masculina EN-US robotica (Edge)",
    },
}


class Speaker:
    """TTS com Edge (gratis) ou Azure Speech (Julio e outras vozes)."""

    def __init__(
        self,
        voice: str = "pt-BR-JulioNeural",
        rate: str = "+10%",
        pitch: str = "+0Hz",
        preset: str | None = None,
        custom_presets: dict | None = None,
        engine: str | None = None,
    ) -> None:
        presets = {**VOICE_PRESETS, **(custom_presets or {})}
        if preset and preset in presets:
            escolha = presets[preset]
            self.voice = escolha["voice"]
            self.rate = escolha.get("rate", "+10%")
            self.pitch = escolha.get("pitch", "+0Hz")
            self.engine = (engine or escolha.get("engine") or "edge").lower()
            print(f"Voz: preset '{preset}' -> {self.voice} [{self.engine}]")
        else:
            self.voice = voice
            self.rate = rate
            self.pitch = pitch
            # Julio e outras vozes Azure-only
            default_engine = "azure" if "Julio" in voice or engine == "azure" else "edge"
            self.engine = (engine or default_engine).lower()
            print(f"Voz: {self.voice} [{self.engine}] (rate={self.rate}, pitch={self.pitch})")

        self.azure_key = os.getenv("AZURE_SPEECH_KEY", "").strip()
        self.azure_region = os.getenv("AZURE_SPEECH_REGION", "brazilsouth").strip()
        self._winmm = ctypes.windll.winmm
        self._avisou_azure = False
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        if self.engine == "azure" and not self.azure_key:
            print(
                "\n[!] Voz Julio precisa de Azure Speech (gratis).\n"
                "    1) Crie recurso Speech em https://portal.azure.com\n"
                "    2) Copie Key + Region para o arquivo .env\n"
                "    Exemplo: .env.example\n"
            )

    def _cache_path(self, text: str) -> Path:
        chave = f"{self.engine}|{self.voice}|{self.rate}|{self.pitch}|{text}"
        digest = hashlib.sha1(chave.encode("utf-8")).hexdigest()
        return CACHE_DIR / f"{digest}.mp3"

    def _rate_to_azure_percent(self) -> str:
        # Edge usa +10%; Azure SSML prosody rate aceita +10% tambem
        return self.rate

    def _pitch_to_azure(self) -> str:
        return self.pitch

    async def _gerar_edge(self, text: str, output: Path) -> None:
        communicate = edge_tts.Communicate(
            text,
            self.voice,
            rate=self.rate,
            pitch=self.pitch,
        )
        await communicate.save(str(output))

    def _gerar_azure(self, text: str, output: Path) -> None:
        if not self.azure_key:
            raise RuntimeError(
                "AZURE_SPEECH_KEY ausente. Configure o arquivo .env para usar a voz do Julio."
            )

        url = f"https://{self.azure_region}.tts.speech.microsoft.com/cognitiveservices/v1"
        ssml = f"""
<speak version='1.0' xml:lang='pt-BR'>
  <voice name='{self.voice}'>
    <prosody rate='{self._rate_to_azure_percent()}' pitch='{self._pitch_to_azure()}'>
      {text}
    </prosody>
  </voice>
</speak>
""".strip()

        headers = {
            "Ocp-Apim-Subscription-Key": self.azure_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
            "User-Agent": "jarvis-assistant",
        }
        response = requests.post(url, headers=headers, data=ssml.encode("utf-8"), timeout=30)
        if response.status_code != 200:
            raise RuntimeError(
                f"Azure TTS falhou ({response.status_code}): {response.text[:200]}"
            )
        output.write_bytes(response.content)

    def _gerar(self, text: str, output: Path) -> None:
        if self.engine == "azure":
            self._gerar_azure(text, output)
            return
        try:
            asyncio.run(self._gerar_edge(text, output))
        except Exception:
            # Se Edge falhar em voz Azure-only, tenta Azure automaticamente
            if self.azure_key:
                self._gerar_azure(text, output)
            else:
                raise

    def _mci(self, comando: str) -> None:
        resultado = self._winmm.mciSendStringW(comando, None, 0, None)
        if resultado != 0:
            raise RuntimeError(f"Falha MCI ({resultado}): {comando}")

    def _tocar_mp3(self, caminho: Path) -> None:
        path = str(caminho.resolve())
        alias = "jarvis_voice"
        try:
            self._mci(f"close {alias}")
        except RuntimeError:
            pass

        self._mci(f'open "{path}" type mpegvideo alias {alias}')
        try:
            self._mci(f"play {alias} wait")
        finally:
            try:
                self._mci(f"close {alias}")
            except RuntimeError:
                pass

    def say(self, text: str) -> None:
        if not text.strip():
            return

        print(f"Jarvis: {text}")
        cached = self._cache_path(text)

        try:
            if not cached.exists():
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    temp_path = Path(tmp.name)
                try:
                    self._gerar(text, temp_path)
                    time.sleep(0.03)
                    temp_path.replace(cached)
                finally:
                    temp_path.unlink(missing_ok=True)

            self._tocar_mp3(cached)
        except Exception as error:
            print(f"(TTS falhou: {error})")
            if self.engine == "azure" and not self.azure_key and not self._avisou_azure:
                self._avisou_azure = True
                print("Configure AZURE_SPEECH_KEY no .env para liberar a voz do Julio.")


def imprimir_vozes() -> None:
    print("Presets (config.yaml -> voz_preset):\n")
    for nome, dados in VOICE_PRESETS.items():
        eng = dados.get("engine", "edge")
        print(f"  {nome:14} {dados['voice']}  [{eng}]")
        print(f"                 {dados['descricao']}")
        print(f"                 rate={dados['rate']}  pitch={dados['pitch']}\n")

    print("Julio (pt-BR-JulioNeural) NÃO está mais no Edge gratis.")
    print("Use Azure Speech free: https://portal.azure.com -> create Speech resource")
    print("Depois preencha o arquivo .env (veja .env.example)")
    print()
    print("Pesquisar outras vozes Edge: py main.py --voices-all pt")
    print("Testar: py main.py --preview-voice pt-BR-AntonioNeural")


async def listar_vozes_edge(filtro: str | None = None) -> None:
    vozes = await edge_tts.list_voices()
    filtro_l = (filtro or "").lower().strip()

    print("Vozes Edge TTS", end="")
    print(f" (filtro: {filtro})" if filtro_l else "", end=":\n\n")

    total = 0
    for voz in sorted(vozes, key=lambda v: v["ShortName"]):
        short = voz["ShortName"]
        locale = voz["Locale"]
        gender = voz.get("Gender", "")
        friendly = voz.get("FriendlyName", "")
        short_l = short.lower()
        locale_l = locale.lower()
        gender_l = gender.lower()
        friendly_l = friendly.lower()

        if filtro_l:
            if filtro_l in {"male", "female"}:
                if gender_l != filtro_l:
                    continue
            elif len(filtro_l) <= 5 and "-" not in filtro_l:
                if not (
                    locale_l.startswith(filtro_l)
                    or short_l.startswith(filtro_l)
                    or f"-{filtro_l}-" in f"-{short_l}-"
                    or f"-{filtro_l}" in short_l
                ):
                    continue
            elif filtro_l not in f"{short_l} {locale_l} {friendly_l}":
                continue

        total += 1
        print(f"  {short:42} {gender:8} {locale}")

    print(f"\n{total} voz(es). Julio e outras Azure: use voz_preset: julio + .env")
    print("Galeria: https://speech.microsoft.com/portal/voicegallery")


def preview_voz(voice: str, rate: str = "+10%", pitch: str = "+0Hz") -> None:
    engine = "azure" if "Julio" in voice else None
    print(f"Testando voz: {voice}")
    speaker = Speaker(voice=voice, rate=rate, pitch=pitch, preset=None, engine=engine)
    speaker.say("Jarvis online. Sistemas prontos.")
