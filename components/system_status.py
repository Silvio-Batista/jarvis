from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from components.widgets import metric_row, panel
from services.system_monitor import SystemSnapshot


class SystemStatusPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        frame, body = panel("SYSTEM STATUS")

        self.cpu_w, self.cpu_bar, self.cpu_val = metric_row("CPU")
        self.mem_w, self.mem_bar, self.mem_val = metric_row("MEMORY")
        self.gpu_w, self.gpu_bar, self.gpu_val = metric_row("GPU")
        self.disk_w, self.disk_bar, self.disk_val = metric_row("DISK")

        for w in (self.cpu_w, self.mem_w, self.gpu_w, self.disk_w):
            body.addWidget(w)

        self.net = QLabel("NETWORK\n↑ 0.0 MB/s\n↓ 0.0 MB/s")
        self.net.setObjectName("Muted")
        self.net.setStyleSheet("color: #7ef0ff; font-family: Consolas; font-size: 12px;")
        body.addWidget(self.net)
        body.addStretch(1)
        outer.addWidget(frame)

    def update_stats(self, snap: SystemSnapshot) -> None:
        self.cpu_bar.setValue(int(snap.cpu))
        self.cpu_val.setText(f"{snap.cpu:0.0f}%")
        self.mem_bar.setValue(int(snap.memory))
        self.mem_val.setText(f"{snap.memory:0.0f}%")
        if snap.gpu is None:
            self.gpu_bar.setValue(0)
            self.gpu_val.setText("N/A")
        else:
            self.gpu_bar.setValue(int(snap.gpu))
            self.gpu_val.setText(f"{snap.gpu:0.0f}%")
        self.disk_bar.setValue(int(snap.disk))
        self.disk_val.setText(f"{snap.disk:0.0f}%")
        self.net.setText(
            f"NETWORK\n↑ {snap.net_up_mbs:0.1f} MB/s\n↓ {snap.net_down_mbs:0.1f} MB/s"
        )
