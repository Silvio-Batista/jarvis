"""Toca musica de verdade no Spotify (busca + abre faixa/playlist)."""

from __future__ import annotations

import os
import re
import subprocess
import time
import urllib.parse
from functools import lru_cache

# Generos/moods: melhor pegar playlist e tocar a 1a faixa
MOODS = {
    "lofi",
    "lo-fi",
    "lo fi",
    "chill",
    "jazz",
    "focus",
    "foco",
    "sleep",
    "sleeping",
    "relax",
    "relaxar",
    "study",
    "estudo",
    "rap",
    "rock",
    "sertanejo",
    "funk",
    "pagode",
    "mpb",
    "eletronic",
    "eletronica",
    "party",
    "festa",
    "workout",
    "treino",
    "classical",
    "classica",
    "ambient",
    "beats",
    "radio",
}


def _tem_credenciais() -> bool:
    return bool(os.getenv("SPOTIFY_CLIENT_ID") and os.getenv("SPOTIFY_CLIENT_SECRET"))


@lru_cache(maxsize=1)
def _cliente_busca():
    """Client Credentials: busca no catalogo sem login do usuario."""
    from spotipy import Spotify
    from spotipy.oauth2 import SpotifyClientCredentials

    auth = SpotifyClientCredentials(
        client_id=os.environ["SPOTIFY_CLIENT_ID"],
        client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
    )
    return Spotify(auth_manager=auth)


def _cliente_usuario():
    """OAuth do usuario: permite start_playback (Premium)."""
    from spotipy import Spotify
    from spotipy.oauth2 import SpotifyOAuth

    redirect = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
    scope = "user-modify-playback-state user-read-playback-state user-read-currently-playing"
    auth = SpotifyOAuth(
        client_id=os.environ["SPOTIFY_CLIENT_ID"],
        client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=redirect,
        scope=scope,
        cache_path=os.path.join("temp", ".spotify_token_cache"),
        open_browser=True,
    )
    return Spotify(auth_manager=auth)


def _abrir_spotify_app() -> None:
    candidatos = [
        os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\Spotify.exe"),
    ]
    for caminho in candidatos:
        if os.path.exists(caminho):
            subprocess.Popen([caminho], shell=False)
            return
    subprocess.Popen(["cmd", "/c", "start", "", "spotify:"], shell=False)


def _abrir_uri(uri: str) -> None:
    subprocess.Popen(["cmd", "/c", "start", "", uri], shell=False)


def _parece_mood(termo: str) -> bool:
    t = termo.lower().strip()
    t = t.replace("musica ", "").replace("playlist ", "").strip()
    return t in MOODS or any(m in t for m in ("lofi", "lo-fi", "lo fi", "chill beats"))


def _escolher_uri(sp, termo: str) -> tuple[str, str]:
    """
    Retorna (uri, descricao).
    Moods -> playlist (e se possivel 1a faixa para comecar tocando).
    Senao -> faixa.
    """
    if _parece_mood(termo):
        playlists = sp.search(q=termo, type="playlist", limit=5)
        items = (playlists.get("playlists") or {}).get("items") or []
        items = [p for p in items if p]
        if items:
            playlist = items[0]
            nome = playlist.get("name", termo)
            pid = playlist["id"]
            # Tenta pegar a primeira faixa da playlist para JA comecar tocando
            try:
                tracks = sp.playlist_items(pid, limit=1, additional_types=["track"])
                t_items = tracks.get("items") or []
                if t_items and t_items[0].get("track") and t_items[0]["track"].get("uri"):
                    track = t_items[0]["track"]
                    track_name = track.get("name", "")
                    return track["uri"], f"{track_name} (playlist {nome})"
            except Exception:
                pass
            return playlist["uri"], f"playlist {nome}"

    tracks = sp.search(q=termo, type="track", limit=5)
    t_items = (tracks.get("tracks") or {}).get("items") or []
    t_items = [t for t in t_items if t]
    if t_items:
        track = t_items[0]
        artists = ", ".join(a["name"] for a in track.get("artists", []))
        return track["uri"], f"{track['name']} - {artists}"

    playlists = sp.search(q=termo, type="playlist", limit=1)
    items = (playlists.get("playlists") or {}).get("items") or []
    items = [p for p in items if p]
    if items:
        return items[0]["uri"], f"playlist {items[0].get('name', termo)}"

    raise RuntimeError(f"Nada encontrado no Spotify para: {termo}")


def _tentar_playback_api(uri: str) -> bool:
    """Usa API oficial para dar play (precisa Premium + dispositivo ativo)."""
    try:
        sp = _cliente_usuario()
        devices = sp.devices().get("devices") or []
        device_id = None
        if devices:
            active = next((d for d in devices if d.get("is_active")), devices[0])
            device_id = active.get("id")

        if uri.startswith("spotify:track:"):
            sp.start_playback(device_id=device_id, uris=[uri])
        else:
            sp.start_playback(device_id=device_id, context_uri=uri)
        return True
    except Exception:
        return False


def _focar_spotify() -> bool:
    try:
        import win32con
        import win32gui
    except ImportError:
        return False

    def _enum(hwnd, acc):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if re.search(r"spotify", title, re.I):
                acc.append(hwnd)

    janelas: list[int] = []
    win32gui.EnumWindows(_enum, janelas)
    if not janelas:
        return False
    hwnd = janelas[0]
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    time.sleep(0.25)
    return True


def _automation_busca_e_enter(termo: str) -> None:
    """Fallback: abre busca e confirma o Top result para comecar a tocar."""
    try:
        import win32com.client
    except ImportError:
        query = urllib.parse.quote(termo)
        _abrir_uri(f"spotify:search:{query}")
        return

    _abrir_spotify_app()
    time.sleep(2.0)
    query = urllib.parse.quote(termo)
    _abrir_uri(f"spotify:search:{query}")
    time.sleep(2.5)
    _focar_spotify()

    shell = win32com.client.Dispatch("WScript.Shell")
    # No Spotify, Enter no resultado do topo costuma iniciar a faixa
    shell.SendKeys("{ENTER}")
    time.sleep(1.0)
    shell.SendKeys("{ENTER}")
    time.sleep(0.6)
    shell.SendKeys(" ")
    time.sleep(0.3)
    # Tecla de midia play/pause como reforco (se estiver pausado, toca)
    try:
        import ctypes

        VK_MEDIA_PLAY_PAUSE = 0xB3
        ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)
    except Exception:
        pass


def tocar(termo: str) -> str:
    """
    Resolve o termo e manda tocar no Spotify Desktop.
    1) API de busca + URI da faixa (melhor)
    2) start_playback se Premium/autorizado
    3) automacao de teclado
    """
    termo = termo.strip()
    if not termo:
        return "Qual musica voce quer no Spotify?"

    _abrir_spotify_app()
    time.sleep(1.0)

    if not _tem_credenciais():
        _automation_busca_e_enter(termo)
        return (
            f"Tentei tocar {termo} no Spotify. "
            "Para acertar sempre, configure SPOTIFY_CLIENT_ID e "
            "SPOTIFY_CLIENT_SECRET no .env (developer.spotify.com)."
        )

    try:
        sp = _cliente_busca()
        uri, descricao = _escolher_uri(sp, termo)
    except Exception as error:
        _automation_busca_e_enter(termo)
        return f"Busca falhou ({error}). Tentei pelo app."

    # Preferencia: playback API (Premium). Senao abre a URI da faixa (costuma autoplay).
    if os.getenv("SPOTIFY_USER_AUTH", "").lower() in {"1", "true", "yes"}:
        if _tentar_playback_api(uri):
            return f"Tocando {descricao}."

    _abrir_uri(uri)
    time.sleep(1.8)
    _focar_spotify()
    try:
        _automation_play_apenas()
    except Exception:
        pass

    # Se ainda for playlist (sem faixa resolvida), Enter ajuda a iniciar
    if uri.startswith("spotify:playlist:"):
        try:
            import win32com.client

            shell = win32com.client.Dispatch("WScript.Shell")
            shell.SendKeys("{ENTER}")
            time.sleep(0.5)
            shell.SendKeys(" ")
        except Exception:
            pass

    return f"Tocando {descricao}."


def _automation_play_apenas() -> None:
    import win32com.client
    import win32con
    import win32gui

    def _enum(hwnd, acc):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if re.search(r"spotify", title, re.I):
                acc.append(hwnd)

    janelas: list[int] = []
    win32gui.EnumWindows(_enum, janelas)
    if not janelas:
        return
    win32gui.ShowWindow(janelas[0], win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(janelas[0])
    time.sleep(0.2)
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys(" ")
