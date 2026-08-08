import os
import re
import shutil
import subprocess
import urllib.parse
import webbrowser
from datetime import datetime
from pathlib import Path

from actions.apps_index import carregar_apps, encontrar_app

CORTESIA = re.compile(
    r"\b(por favor|pra mim|para mim|ai|obrigado|obrigada|pode|consegue|"
    r"quero que|voce pode|voce consegue|me faz|faz ai)\b",
    re.IGNORECASE,
)

ARTIGOS = re.compile(r"\b(o|a|os|as|um|uma|meu|minha|no|na|do|da|dos|das)\b", re.IGNORECASE)

PERGUNTA = re.compile(
    r"^(o que|oque|quem|qual|quais|como|quando|onde|porque|por que|porquê|"
    r"quanto|quanta|quantos|quantas|me diga|me explica|explica|define|"
    r"o que e|oque e|pra que|para que|existe|tem como)\b",
    re.IGNORECASE,
)


class ComputerActions:
    """Ações do computador: apps, sistema, pesquisa e perguntas."""

    def __init__(self, apps: dict[str, str] | None = None) -> None:
        base = {
            "chrome": "chrome",
            "google chrome": "chrome",
            "navegador": "chrome",
            "edge": "msedge",
            "spotify": "spotify",
            "bloco de notas": "notepad",
            "notepad": "notepad",
            "calculadora": "calc",
            "calc": "calc",
            "explorador": "explorer",
            "explorer": "explorer",
            "arquivos": "explorer",
            "discord": "discord",
            "vscode": "code",
            "visual studio code": "code",
            "codigo": "code",
            "terminal": "wt",
            "cmd": "cmd",
            "powershell": "powershell",
            "paint": "mspaint",
            "word": "winword",
            "excel": "excel",
            "gerenciador de tarefas": "taskmgr",
            "task manager": "taskmgr",
            "configuracoes": "ms-settings:",
            "configuracoes do windows": "ms-settings:",
            "configuracao": "ms-settings:",
        }
        self.apps_alias = {**base, **(apps or {})}
        self.apps_menu = carregar_apps()

    def executar(self, comando: str) -> str:
        texto = self._normalizar(comando)
        if not texto:
            return "Pois nao?"

        # --- sistema / info ---
        if any(p in texto for p in ("que horas", "horas sao", "que hora")):
            return f"Sao {datetime.now().strftime('%H:%M')}."

        if any(p in texto for p in ("que dia", "data de hoje", "qual a data")):
            return f"Hoje e {datetime.now().strftime('%d/%m/%Y')}."

        # --- encerrar assistente (tratado também no main) ---
        if any(p in texto for p in ("desligar assistente", "encerrar assistente", "tchau")):
            return "Ate logo."

        # --- power ---
        if any(p in texto for p in ("reiniciar o pc", "reiniciar computador", "restart")):
            os.system("shutdown /r /t 60")
            return "Reiniciando em 60 segundos. Diga cancelar desligamento para abortar."

        if any(p in texto for p in ("desligar o pc", "desligar computador", "shutdown")):
            os.system("shutdown /s /t 60")
            return "Desligando em 60 segundos. Diga cancelar desligamento para abortar."

        if "cancelar desligamento" in texto or "cancelar reinicio" in texto:
            os.system("shutdown /a")
            return "Cancelado."

        if any(p in texto for p in ("bloquear", "lock", "trava a tela", "travar tela", "travar")):
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=False)
            return "Tela bloqueada."

        if any(p in texto for p in ("suspender", "dormir", "sleep")):
            subprocess.run(
                ["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"],
                check=False,
            )
            return "Suspendendo."

        # --- volume / midia ---
        if "volume" in texto and any(p in texto for p in ("aumentar", "mais", "alto", "sobe")):
            self._tecla_volume(n=5, subir=True)
            return "Volume aumentado."

        if "volume" in texto and any(p in texto for p in ("diminuir", "menos", "baixo", "desce")):
            self._tecla_volume(n=5, subir=False)
            return "Volume diminuido."

        if any(p in texto for p in ("mute", "mudo", "silenciar", "tirar o mudo")):
            self._enviar_tecla_virtual(0xAD)
            return "Mudo alternado."

        # --- musica no Spotify (antes de play/pause generico) ---
        spotify = self._extrair_musica_spotify(texto)
        if spotify:
            return self._tocar_spotify(spotify)

        if any(p in texto for p in ("proximo", "proxima musica", "proxima faixa", "skip")):
            self._enviar_tecla_virtual(0xB0)
            return "Proxima faixa."

        if any(p in texto for p in ("anterior", "musica anterior", "faixa anterior")):
            self._enviar_tecla_virtual(0xB1)
            return "Faixa anterior."

        if texto in {"pausar", "play", "pause", "continuar", "continuar musica", "tocar musica", "pause play"}:
            self._enviar_tecla_virtual(0xB3)
            return "Play pause."

        # --- captura / janelas ---
        if any(p in texto for p in ("print", "screenshot", "captura de tela", "tirar print")):
            self._atalho("print_screen")
            return "Print capturado."

        if any(p in texto for p in ("minimizar tudo", "mostrar area de trabalho", "area de trabalho")):
            self._atalho("win+d")
            return "Area de trabalho."

        if "alt tab" in texto or "trocar janela" in texto or "proxima janela" in texto:
            self._atalho("alt+tab")
            return "Trocando janela."

        # --- pastas / urls uteis ---
        if any(p in texto for p in ("abrir downloads", "pasta downloads", "meus downloads")):
            pasta = Path.home() / "Downloads"
            subprocess.Popen(["explorer", str(pasta)])
            return "Abrindo Downloads."

        if any(p in texto for p in ("abrir documentos", "pasta documentos", "meus documentos")):
            pasta = Path.home() / "Documents"
            subprocess.Popen(["explorer", str(pasta)])
            return "Abrindo Documentos."

        if "lixeira" in texto and any(p in texto for p in ("abrir", "abra", "abre")):
            subprocess.Popen(["explorer", "shell:RecycleBinFolder"])
            return "Abrindo lixeira."

        # --- youtube / wikipedia / google explicito ---
        yt = re.search(r"\b(?:youtube|no youtube)\s+(.+)", texto)
        toque_livre = re.search(
            r"\b(?:toque|toca|tocar|play|ponha|coloca)\s+(.+)",
            texto,
        )
        if yt:
            termo = yt.group(1).strip()
            self._abrir_url(
                "https://www.youtube.com/results?search_query=" + urllib.parse.quote(termo)
            )
            return f"Buscando no YouTube: {termo}."
        if toque_livre and "spotify" not in texto:
            termo = toque_livre.group(1).strip()
            termo = re.sub(r"\s+no\s+youtube$", "", termo).strip()
            self._abrir_url(
                "https://www.youtube.com/results?search_query=" + urllib.parse.quote(termo)
            )
            return f"Buscando no YouTube: {termo}."

        wiki = re.search(r"\b(?:wikipedia|wiki)\s+(.+)", texto)
        if wiki:
            termo = wiki.group(1).strip()
            self._abrir_url(
                "https://pt.wikipedia.org/wiki/Special:Search?search="
                + urllib.parse.quote(termo)
            )
            return f"Wikipedia: {termo}."

        pesquisa = re.search(
            r"\b(?:pesquisar|pesquisa|busca|buscar|google|procura|procurar)\s+(.+)",
            texto,
        )
        if pesquisa:
            termo = pesquisa.group(1).strip()
            self._google(termo)
            return f"Pesquisando {termo}."

        # --- abrir apps / sites ---
        abrir = re.search(
            r"\b(?:abrir|abra|abre|iniciar|inicia|executar|roda|rode|lancar)\s+(.+)",
            texto,
        )
        if abrir:
            return self._abrir(abrir.group(1).strip())

        # atalho: só o nome do app conhecido
        for nome in sorted(self.apps_alias.keys(), key=len, reverse=True):
            if texto == nome or texto == f"abrir {nome}":
                return self._abrir(nome)

        # --- perguntas -> Google ---
        if PERGUNTA.search(texto) or texto.endswith("?"):
            self._google(comando.strip().rstrip("?"))
            return "Pesquisei no Google."

        # fallback: app curto; senão avisa (nao pesquisa web em tudo)
        if len(texto.split()) <= 3 and encontrar_app(texto, self.apps_menu):
            return self._abrir(texto)

        return (
            "Nao entendi. Exemplos: abrir discord, toque lo-fi no spotify, "
            "o que e python, que horas sao."
        )

    def _google(self, termo: str) -> None:
        self._abrir_url("https://www.google.com/search?q=" + urllib.parse.quote(termo))

    def _abrir_url(self, url: str) -> None:
        webbrowser.open(url)

    def _extrair_musica_spotify(self, texto: str) -> str | None:
        """Extrai o termo musical quando o usuario pede Spotify."""
        if "spotify" not in texto:
            return None

        padroes = [
            r"\b(?:toque|toca|tocar|play|ponha|coloca|ouvir|ouve|bota)\s+(.+?)\s+no\s+spotify\b",
            r"\bno\s+spotify\s+(?:toque|toca|tocar|play)?\s*(.+)$",
            r"\bspotify\s+(?:toque|toca|tocar|play|pesquisa|pesquisar|busca)?\s*(.+)$",
            r"\b(?:toque|toca|tocar|play)\s+spotify\s+(.+)$",
        ]
        for padrao in padroes:
            match = re.search(padrao, texto)
            if match:
                termo = match.group(1).strip(" .,!?")
                termo = ARTIGOS.sub(" ", termo)
                termo = re.sub(r"\s+", " ", termo).strip()
                if termo and termo != "spotify":
                    return termo

        # "abrir spotify" nao e musica — deixa para o fluxo de apps
        if re.search(r"\b(?:abrir|abra|abre|iniciar)\s+spotify\b", texto):
            return None
        return None

    def _tocar_spotify(self, termo: str) -> str:
        """Busca a musica/playlist e inicia a reproducao no Spotify."""
        from actions.spotify_player import tocar

        return tocar(termo)

    def _normalizar(self, comando: str) -> str:
        texto = comando.lower().strip()
        texto = (
            texto.replace("ã", "a")
            .replace("á", "a")
            .replace("à", "a")
            .replace("â", "a")
            .replace("é", "e")
            .replace("ê", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ô", "o")
            .replace("õ", "o")
            .replace("ú", "u")
            .replace("ç", "c")
        )
        texto = CORTESIA.sub(" ", texto)
        texto = re.sub(r"\s+", " ", texto).strip(" .,!")
        return texto

    def _abrir(self, alvo: str) -> str:
        alvo_limpo = ARTIGOS.sub(" ", alvo)
        alvo_limpo = CORTESIA.sub(" ", alvo_limpo)
        alvo_limpo = re.sub(r"\s+", " ", alvo_limpo).strip(" .,!?")

        if alvo_limpo.startswith("http://") or alvo_limpo.startswith("https://"):
            self._abrir_url(alvo_limpo)
            return "Abrindo link."

        # site curto: abrir youtube.com / github.com
        if re.fullmatch(r"[\w\-]+(\.[\w\-]+)+", alvo_limpo):
            self._abrir_url("https://" + alvo_limpo)
            return f"Abrindo {alvo_limpo}."

        # aliases do config
        for nome in sorted(self.apps_alias.keys(), key=len, reverse=True):
            if nome in alvo_limpo or alvo_limpo in nome:
                app = self.apps_alias[nome]
                if self._lancar(app):
                    return f"Abrindo {nome}."

        # menu Iniciar (qualquer app instalado)
        match = encontrar_app(alvo_limpo, self.apps_menu)
        if match:
            nome, app_id = match
            if self._lancar_appid(app_id) or self._lancar(app_id):
                return f"Abrindo {nome}."

        # tentativa genérica
        if self._lancar(alvo_limpo):
            return f"Abrindo {alvo_limpo}."

        # última chance: pesquisa o app no Google / Store vibe — melhor abrir busca no Windows
        if self._buscar_no_windows(alvo_limpo):
            return f"Busquei {alvo_limpo} no Windows."

        return f"Nao achei o app {alvo_limpo}."

    def _lancar_appid(self, app_id: str) -> bool:
        try:
            # AppX / StartApps: shell:AppsFolder\AppID
            if "\\" in app_id or "!" in app_id:
                subprocess.Popen(
                    ["explorer.exe", f"shell:AppsFolder\\{app_id}"],
                    shell=False,
                )
                return True
            subprocess.Popen(["cmd", "/c", "start", "", app_id], shell=False)
            return True
        except OSError:
            return False

    def _buscar_no_windows(self, termo: str) -> bool:
        try:
            # Abre a busca do Windows com o termo
            subprocess.Popen(
                ["cmd", "/c", "start", "", f"ms-search:query={termo}"],
                shell=False,
            )
            return True
        except OSError:
            return False

    def _lancar(self, app: str) -> bool:
        if app.startswith("ms-settings"):
            try:
                subprocess.Popen(["cmd", "/c", "start", "", app], shell=False)
                return True
            except OSError:
                return False

        for comando in self._candidatos(app):
            try:
                if Path(comando).exists():
                    subprocess.Popen([comando], shell=False)
                    return True
                if shutil.which(comando):
                    subprocess.Popen([comando], shell=False)
                    return True
            except OSError:
                continue

        try:
            subprocess.Popen(["cmd", "/c", "start", "", app], shell=False)
            return True
        except OSError:
            return False

    def _candidatos(self, app: str) -> list[str]:
        app_l = app.lower().strip()
        locais = {
            "chrome": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            ],
            "msedge": [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            ],
            "spotify": [
                os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
                os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\Spotify.exe"),
            ],
            "discord": [
                os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe"),
            ],
            "code": [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            ],
        }
        extras = locais.get(app_l, [])
        if app_l == "discord" and extras:
            # Discord costuma precisar de --processStart
            return extras
        return [*extras, app, f"{app}.exe"]

    def _tecla_volume(self, n: int = 5, subir: bool = True) -> None:
        codigo = 0xAF if subir else 0xAE
        for _ in range(n):
            self._enviar_tecla_virtual(codigo)

    def _enviar_tecla_virtual(self, codigo: int) -> None:
        import ctypes

        ctypes.windll.user32.keybd_event(codigo, 0, 0, 0)
        ctypes.windll.user32.keybd_event(codigo, 0, 2, 0)

    def _atalho(self, nome: str) -> None:
        import ctypes

        user32 = ctypes.windll.user32
        keybd = user32.keybd_event
        KEYEVENTF_KEYUP = 2
        VK = {
            "win": 0x5B,
            "d": 0x44,
            "alt": 0x12,
            "tab": 0x09,
            "print_screen": 0x2C,
        }

        if nome == "print_screen":
            keybd(VK["print_screen"], 0, 0, 0)
            keybd(VK["print_screen"], 0, KEYEVENTF_KEYUP, 0)
            return

        if nome == "win+d":
            keybd(VK["win"], 0, 0, 0)
            keybd(VK["d"], 0, 0, 0)
            keybd(VK["d"], 0, KEYEVENTF_KEYUP, 0)
            keybd(VK["win"], 0, KEYEVENTF_KEYUP, 0)
            return

        if nome == "alt+tab":
            keybd(VK["alt"], 0, 0, 0)
            keybd(VK["tab"], 0, 0, 0)
            keybd(VK["tab"], 0, KEYEVENTF_KEYUP, 0)
            keybd(VK["alt"], 0, KEYEVENTF_KEYUP, 0)
