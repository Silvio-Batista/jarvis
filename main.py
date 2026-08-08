"""
JARVIS — Just A Rather Very Intelligent System

Uso:
  py main.py                 # painel desktop (Command Center)
  py main.py --voice         # assistente de voz (CLI)
  py main.py --text          # voz via teclado
  py main.py --devices
  py main.py --voices
  py main.py --voices-all [filtro]
  py main.py --preview-voice NOME
  py main.py --reindex-apps
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def run_gui() -> int:
    from PySide6.QtWidgets import QApplication

    from app.window import JarvisWindow

    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS")
    window = JarvisWindow()
    window.show()
    return app.exec()


def run_voice_cli(args: argparse.Namespace) -> int:
    from actions.apps_index import carregar_apps
    from actions.computer import ComputerActions
    from core.audio_devices import imprimir_dispositivos
    from core.brain import Brain
    from core.config import load_config
    from core.listener import Listener, extrair_comando, parece_comando, parece_conversa
    from core.speaker import Speaker, imprimir_vozes, listar_vozes_edge, preview_voz

    def criar_assistente():
        config = load_config()
        assistente = config["assistente"]
        apps = config.get("acoes", {}).get("apps", {})
        custom = config.get("vozes_custom") or {}

        listener = Listener(
            idioma=assistente.get("idioma_stt", "pt-BR"),
            taxa_amostragem=assistente.get("taxa_amostragem"),
            microfone=assistente.get("microfone", "fifine"),
            silencio_para_parar=assistente.get("silencio_para_parar", 0.5),
            max_segundos=assistente.get("max_segundos_fala", 4.0),
            espera_fala=assistente.get("espera_fala", 2.5),
        )
        preset = assistente.get("voz_preset")
        speaker = Speaker(
            voice=assistente.get("voz_tts", "pt-BR-AntonioNeural"),
            rate=assistente.get("velocidade_tts", "+40%"),
            pitch=assistente.get("tom_tts", "-35Hz"),
            preset=preset,
            custom_presets=custom,
            engine=assistente.get("tts_engine"),
        )
        if assistente.get("velocidade_tts"):
            speaker.rate = assistente["velocidade_tts"]
        if assistente.get("tom_tts"):
            speaker.pitch = assistente["tom_tts"]

        brain = Brain(
            ComputerActions(apps=apps),
            nome=assistente.get("nome", "Jarvis"),
        )
        return assistente, listener, speaker, brain

    def deve_processar(texto: str, wake_words: list[str], exigir_wake: bool) -> str | None:
        com_wake = extrair_comando(texto, wake_words)
        if com_wake is not None:
            return com_wake
        if exigir_wake:
            return None
        if parece_conversa(texto) or parece_comando(texto):
            return texto
        return None

    def encerrar(comando: str) -> bool:
        t = comando.lower()
        return any(
            p in t
            for p in (
                "desligar assistente",
                "encerrar assistente",
                "tchau jarvis",
                "ate logo jarvis",
                "dormir assistente",
            )
        ) or t.strip() in {"tchau", "ate logo", "adeus"}

    if args.devices:
        imprimir_dispositivos()
        return 0
    if args.voices:
        imprimir_vozes()
        return 0
    if args.voices_all is not None:
        asyncio.run(listar_vozes_edge(args.voices_all or None))
        return 0
    if args.preview_voice:
        preview_voz(args.preview_voice, rate=args.rate, pitch=args.pitch)
        return 0
    if args.reindex_apps:
        apps = carregar_apps(forcar=True)
        print(f"Pronto: {len(apps)} apps.")
        return 0

    assistente, listener, speaker, brain = criar_assistente()
    wake_words = assistente.get("wake_words", ["jarvis"])
    exigir_wake = bool(assistente.get("exigir_wake_word", False))
    nome = assistente.get("nome", "Jarvis")

    if args.text:
        print(f"{nome} em modo texto. Digite 'sair' para encerrar.")
        while True:
            try:
                linha = input("Voce: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not linha:
                continue
            if linha.lower() in {"sair", "exit", "quit"} or encerrar(linha):
                speaker.say("Ate logo. Estarei por aqui.")
                break
            if deve_processar(linha, wake_words, exigir_wake) is None:
                print("(Nao pareceu conversa nem comando)")
                continue
            speaker.say(brain.pensar(linha, wake_words=wake_words))
        return 0

    # --voice
    speaker.say(f"{nome} online. Pode falar comigo normalmente.")
    print("Modo voz CLI. Ctrl+C para encerrar.\n")
    while True:
        try:
            texto = listener.ouvir()
        except KeyboardInterrupt:
            print()
            speaker.say("Encerrando. Ate logo.")
            break
        if not texto:
            continue
        if deve_processar(texto, wake_words, exigir_wake) is None:
            print("(Ignorado)")
            continue
        if encerrar(texto):
            speaker.say("Ate logo. Estarei por aqui.")
            break
        speaker.say(brain.pensar(texto, wake_words=wake_words))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="JARVIS Command Center")
    parser.add_argument("--voice", action="store_true", help="Assistente de voz (CLI)")
    parser.add_argument("--text", action="store_true", help="Assistente via teclado")
    parser.add_argument("--devices", action="store_true", help="Lista microfones")
    parser.add_argument("--voices", action="store_true", help="Lista presets de voz")
    parser.add_argument(
        "--voices-all",
        nargs="?",
        const="",
        default=None,
        help="Lista/pesquisa vozes Edge TTS",
    )
    parser.add_argument("--preview-voice", metavar="NOME", help="Testa uma voz")
    parser.add_argument("--reindex-apps", action="store_true", help="Reindexa apps")
    parser.add_argument("--rate", default="+10%", help="Rate no preview")
    parser.add_argument("--pitch", default="-20Hz", help="Pitch no preview")
    args = parser.parse_args()

    voice_mode = any(
        [
            args.voice,
            args.text,
            args.devices,
            args.voices,
            args.voices_all is not None,
            args.preview_voice,
            args.reindex_apps,
        ]
    )
    if voice_mode:
        return run_voice_cli(args)
    return run_gui()


if __name__ == "__main__":
    sys.exit(main())
