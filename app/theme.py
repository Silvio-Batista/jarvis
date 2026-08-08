"""Identidade visual clean — TowerHub + JARVIS."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QFontDatabase

ROOT = Path(__file__).resolve().parent.parent
FONT_PATH = ROOT / "assets" / "fonts" / "Outfit.ttf"
LOGO_PATH = ROOT / "assets" / "logo" / "Logo I.A TowerHub.png"

COLORS = {
    "bg": "#07090d",
    "bg_panel": "#0c1018",
    "bg_card": "#111722",
    "bg_hover": "#182032",
    "border": "#243044",
    "border_soft": "#1a2230",
    "cyan": "#5ad7ff",
    "cyan_dim": "#3a8eaa",
    "cyan_soft": "#a8ecff",
    "white": "#f2f6fb",
    "muted": "#8b9bb0",
    "green": "#4dffb5",
    "red": "#e10600",  # TowerHub red
    "red_soft": "#ff4d4d",
    "amber": "#ffc857",
    "grid": "#10151f",
}

FONTS = {
    "display": "Outfit",
    "fallback": "Segoe UI",
    "mono": "Cascadia Mono, Consolas, monospace",
}

_FONT_FAMILY = FONTS["fallback"]


def load_fonts() -> str:
    """Carrega Outfit se existir; retorna familia efetiva."""
    global _FONT_FAMILY
    if FONT_PATH.exists():
        font_id = QFontDatabase.addApplicationFont(str(FONT_PATH))
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            _FONT_FAMILY = families[0]
            return _FONT_FAMILY
    _FONT_FAMILY = FONTS["fallback"]
    return _FONT_FAMILY


def font_family() -> str:
    return _FONT_FAMILY


def stylesheet() -> str:
    c = COLORS
    f = _FONT_FAMILY
    return f"""
    QMainWindow, QWidget#Root {{
        background-color: {c['bg']};
        color: {c['white']};
        font-family: "{f}";
        font-size: 13px;
    }}
    QLabel {{
        color: {c['white']};
        background: transparent;
        font-family: "{f}";
    }}
    QLabel#Title {{
        color: {c['white']};
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 3px;
    }}
    QLabel#Subtitle {{
        color: {c['muted']};
        font-size: 10px;
        letter-spacing: 1.5px;
        font-weight: 500;
    }}
    QLabel#Brand {{
        color: {c['red']};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 3px;
    }}
    QLabel#SectionTitle {{
        color: {c['muted']};
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 2px;
    }}
    QLabel#Muted {{
        color: {c['muted']};
        font-size: 12px;
    }}
    QLabel#BigTime {{
        color: {c['white']};
        font-size: 36px;
        font-weight: 300;
        letter-spacing: 1px;
    }}
    QLabel#Greeting {{
        color: {c['white']};
        font-size: 22px;
        font-weight: 500;
        letter-spacing: 0.5px;
    }}
    QLabel#StatusOnline {{
        color: {c['green']};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1.5px;
    }}
    QFrame#Panel {{
        background-color: {c['bg_panel']};
        border: 1px solid {c['border_soft']};
        border-radius: 14px;
    }}
    QFrame#Card {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border_soft']};
        border-radius: 10px;
    }}
    QPushButton {{
        font-family: "{f}";
    }}
    QPushButton#ActionBtn {{
        background-color: {c['bg_card']};
        color: {c['cyan_soft']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        padding: 11px 14px;
        text-align: left;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.8px;
    }}
    QPushButton#ActionBtn:hover {{
        background-color: {c['bg_hover']};
        border: 1px solid {c['cyan_dim']};
        color: {c['white']};
    }}
    QPushButton#DangerBtn {{
        background-color: #160b0b;
        color: {c['red_soft']};
        border: 1px solid #4a1a1a;
        border-radius: 10px;
        padding: 11px 14px;
        text-align: left;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.8px;
    }}
    QPushButton#DangerBtn:hover {{
        background-color: #241010;
        border: 1px solid {c['red']};
    }}
    QPushButton#AppBtn {{
        background-color: {c['bg_card']};
        color: {c['white']};
        border: 1px solid {c['border_soft']};
        border-radius: 10px;
        padding: 12px 14px;
        text-align: left;
        font-weight: 500;
    }}
    QPushButton#AppBtn:hover {{
        background-color: {c['bg_hover']};
        border: 1px solid {c['red']};
    }}
    QPushButton#TaskBtn {{
        background-color: transparent;
        color: {c['white']};
        border: 1px solid {c['border_soft']};
        border-radius: 8px;
        padding: 8px 10px;
        text-align: left;
        font-size: 12px;
    }}
    QPushButton#TaskBtn:hover {{
        border: 1px solid {c['cyan_dim']};
        background-color: {c['bg_hover']};
    }}
    QPushButton#TaskBtnDone {{
        background-color: transparent;
        color: {c['muted']};
        border: 1px solid {c['border_soft']};
        border-radius: 8px;
        padding: 8px 10px;
        text-align: left;
        font-size: 12px;
        text-decoration: line-through;
    }}
    QProgressBar {{
        background-color: #0a0e14;
        border: none;
        border-radius: 4px;
        height: 6px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background-color: {c['red']};
        border-radius: 4px;
    }}
    QLineEdit#CleanInput {{
        background-color: {c['bg_card']};
        color: {c['white']};
        border: 1px solid {c['border_soft']};
        border-radius: 8px;
        padding: 8px 10px;
        selection-background-color: {c['red']};
    }}
    QLineEdit#CleanInput:focus {{
        border: 1px solid {c['red']};
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 5px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {c['border']};
        border-radius: 3px;
        min-height: 24px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    """
