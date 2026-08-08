from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


def panel(title: str | None = None) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("Panel")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(12)
    if title:
        label = QLabel(title)
        label.setObjectName("SectionTitle")
        layout.addWidget(label)
    return frame, layout


def metric_row(name: str) -> tuple[QWidget, QProgressBar, QLabel]:
    wrap = QWidget()
    layout = QVBoxLayout(wrap)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    top = QHBoxLayout()
    title = QLabel(name)
    title.setObjectName("Muted")
    value = QLabel("0%")
    value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    value.setStyleSheet("color: #3de7ff; font-family: Consolas; font-size: 12px;")
    top.addWidget(title)
    top.addWidget(value)

    bar = QProgressBar()
    bar.setRange(0, 100)
    bar.setValue(0)
    bar.setTextVisible(False)
    bar.setFixedHeight(8)

    layout.addLayout(top)
    layout.addWidget(bar)
    return wrap, bar, value
