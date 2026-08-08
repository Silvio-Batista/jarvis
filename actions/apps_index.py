"""Índice de apps do menu Iniciar do Windows para abrir qualquer programa."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

CACHE_PATH = Path(__file__).resolve().parent.parent / "temp" / "apps_index.json"
CACHE_TTL_SECONDS = 60 * 60 * 12  # 12h


def _normalizar(texto: str) -> str:
    tabela = str.maketrans(
        "áàãâäéèêëíìîïóòõôöúùûüçñ",
        "aaaaaeeeeiiiiooooouuuucn",
    )
    return texto.lower().translate(tabela).strip()


def _carregar_do_windows() -> dict[str, str]:
    """Usa PowerShell Get-StartApps: nome -> AppID."""
    script = (
        "Get-StartApps | Select-Object Name, AppID | "
        "ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return {}

    data = json.loads(result.stdout)
    if isinstance(data, dict):
        data = [data]

    apps: dict[str, str] = {}
    for item in data:
        nome = str(item.get("Name", "")).strip()
        app_id = str(item.get("AppID", "")).strip()
        if nome and app_id:
            apps[_normalizar(nome)] = app_id
    return apps


def carregar_apps(forcar: bool = False) -> dict[str, str]:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not forcar and CACHE_PATH.exists():
        idade = time.time() - CACHE_PATH.stat().st_mtime
        if idade < CACHE_TTL_SECONDS:
            try:
                return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

    print("Indexando aplicativos do Windows (uma vez)...")
    apps = _carregar_do_windows()
    if apps:
        CACHE_PATH.write_text(json.dumps(apps, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{len(apps)} apps indexados.")
    else:
        print("Nao foi possivel indexar apps do menu Iniciar.")
    return apps


def encontrar_app(consulta: str, apps: dict[str, str]) -> tuple[str, str] | None:
    """Retorna (nome_normalizado, app_id) pelo melhor match."""
    q = _normalizar(consulta)
    if not q:
        return None

    if q in apps:
        return q, apps[q]

    # Match por contenção (mais específico primeiro)
    candidatos = [(nome, app_id) for nome, app_id in apps.items() if q in nome or nome in q]
    if not candidatos:
        # tokens: "discord canary" -> tenta por palavras
        tokens = [t for t in q.split() if len(t) > 2]
        if tokens:
            candidatos = [
                (nome, app_id)
                for nome, app_id in apps.items()
                if all(t in nome for t in tokens)
            ]

    if not candidatos:
        return None

    candidatos.sort(key=lambda item: len(item[0]))
    return candidatos[0]
