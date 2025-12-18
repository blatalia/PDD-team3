# app/worker.py
from PyQt6.QtCore import QObject, pyqtSignal
from pathlib import Path
from typing import List
import logging
import os
import concurrent.futures as cf

from core.worker_tasks import process_one_image


class AlgorithmWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)   # done, total
    log = pyqtSignal(str)             # optional: stream messages

    def __init__(self, images: List[Path], algorithm: str, max_workers: int | None = None):
        super().__init__()
        self.images = images
        self.algorithm = algorithm
        self.logger = logging.getLogger("worker")
        self._cancel = False

        cpu = os.cpu_count() or 2
        # Good default for large images: leave 1 core for UI + avoid RAM spikes
        self.max_workers = max_workers or max(1, min(cpu - 1, 4))

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            total = len(self.images)
            self.logger.info("Process '%s' started for %d files", self.algorithm, total)
            self.log.emit(f"Starting {self.algorithm} on {total} file(s) with {self.max_workers} worker(s)")

            done = 0
            results: list[str] = []

            # Convert Paths to strings (pickle-safe)
            image_strs = [str(p) for p in self.images]

            with cf.ProcessPoolExecutor(max_workers=self.max_workers) as ex:
                futures = [ex.submit(process_one_image, self.algorithm, p) for p in image_strs]

                for fut in cf.as_completed(futures):
                    if self._cancel:
                        self.log.emit("Cancelled by user.")
                        # Cancel futures not yet started
                        for f in futures:
                            f.cancel()
                        break

                    # If one task crashes, .result() will raise
                    res = fut.result()
                    results.append(res)

                    done += 1
                    self.progress.emit(done, total)

            self.logger.info("Process '%s' finished", self.algorithm)

            if self._cancel:
                self.finished.emit("Cancelled.")
            else:
                # combine results; adapt formatting to your taste
                self.finished.emit("\n\n".join(results) if results else "No output.")

        except Exception as e:
            self.logger.exception("Worker error")
            self.error.emit(str(e))
