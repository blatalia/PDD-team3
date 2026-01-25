# app/ui/plot_widget.py
from __future__ import annotations

from typing import List, Tuple, Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


class PlotWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._title = QLabel("Plot")
        self._title.setStyleSheet("color: white;")

        self._fig = Figure()
        self._canvas = FigureCanvas(self._fig)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addWidget(self._canvas, 1)

        self._fig.patch.set_alpha(0.0)
        self._has_content: bool = False

    def set_title(self, title: str) -> None:
        self._title.setText(title)

    def clear(self) -> None:
        self._fig.clear()
        self._has_content = False
        self._canvas.draw_idle()

    def plot_profiles(self, profiles: List[Tuple[List[float], List[float], str]]) -> None:
        self._fig.clear()
        ax = self._fig.add_subplot(111)
        ax.grid(True)

        for item in profiles:
            if len(item) == 3:
                x, y, label = item
                color = None
            else:
                x, y, label, color = item

            ax.plot(x, y, label=label, color=color)

        if len(profiles) > 1:
            ax.legend()

        ax.set_xlabel("Normalized position (0..1)")
        ax.set_ylabel("Intensity (a.u.)")

        self._has_content = len(profiles) > 0
        self._canvas.draw_idle()

    def plot_xy(self, x: List[float], y: List[float], xlabel: str, ylabel: str) -> None:
        self._fig.clear()
        ax = self._fig.add_subplot(111)
        ax.grid(True)

        ax.scatter(x, y)

        # only draw connecting line when we have at least 2 points
        if len(x) >= 2:
            ax.plot(x, y)

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        self._has_content = len(x) > 0 and len(y) > 0
        self._canvas.draw_idle()


    def has_content(self) -> bool:
        return self._has_content

    def save_png(self, filepath: str, dpi: int = 200) -> None:
        self._fig.savefig(filepath, dpi=dpi, bbox_inches="tight")
