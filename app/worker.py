# app/worker.py
from PyQt6.QtCore import QObject, pyqtSignal
from pathlib import Path
from typing import List
import logging

from core.algorithms import run_algorithm


class AlgorithmWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, images: List[Path], algorithm: str):
        super().__init__()
        self.images = images
        self.algorithm = algorithm
        self.logger = logging.getLogger("worker")

    def run(self):
        try:
            self.logger.info(
                "Process '%s' started for %d files",
                self.algorithm,
                len(self.images),
            )
            result = run_algorithm(self.algorithm, self.images)
            self.logger.info("Process '%s' finished", self.algorithm)
            self.finished.emit(result)
        except Exception as e:
            self.logger.exception("Worker error")
            self.error.emit(str(e))
