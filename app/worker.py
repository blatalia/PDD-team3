# app/worker.py
from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal
from pathlib import Path
from typing import List
import logging
import os
import concurrent.futures as cf

from app.models.analysis_config import AnalysisConfig
from core.worker_tasks import process_one_image_task
from core.export.txt_exporter import export_results_txt
from core.export.profile_exporter import export_profiles_txt
from core.algorithms import ALGO_PROFILES


class AlgorithmWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)        # done, total
    log = pyqtSignal(str)
    resultsReady = pyqtSignal(object)      # list[dict] (pickle-safe in Qt)

    def __init__(self, images: List[Path], config: AnalysisConfig, max_workers: int | None = None):
        super().__init__()
        self.images = images
        self.config = config
        self.logger = logging.getLogger("worker")
        self._cancel = False

        cpu = os.cpu_count() or 2
        self.max_workers = max_workers or max(1, min(cpu - 1, 4))

    def cancel(self) -> None:
        self._cancel = True

    @staticmethod
    def _format_roi(roi: object) -> str:
        if not isinstance(roi, dict):
            return ""
        t = roi.get("type")
        if t == "rect":
            return f" ROI[x={roi.get('x')},y={roi.get('y')},w={roi.get('w')},h={roi.get('h')}]"
        if t == "circle":
            return f" ROI[cx={roi.get('cx')},cy={roi.get('cy')},r={roi.get('r')}]"
        if t == "polygon":
            pts = roi.get("points", [])
            n = len(pts) if isinstance(pts, list) else 0
            return f" ROI[polygon points={n}]"
        return " ROI[unknown]"

    def run(self) -> None:
        try:
            total = len(self.images)
            algo = self.config.algorithm
            roi_payload = self.config.roi
            cross_sections = self.config.cross_sections
            profile_samples = self.config.profile_samples

            self.logger.info("Batch '%s' started for %d files", algo, total)
            self.log.emit(f"Starting '{algo}' on {total} file(s)")
            self.log.emit(f"Workers: {self.max_workers}")

            done = 0
            results = []

            image_strs = [str(p) for p in self.images]

            with cf.ProcessPoolExecutor(max_workers=self.max_workers) as ex:
                futures = [
                    ex.submit(
                        process_one_image_task,
                        algo,
                        p,
                        roi_payload,
                        cross_sections,
                        profile_samples,
                    )
                    for p in image_strs
                ]

                for fut in cf.as_completed(futures):
                    if self._cancel:
                        self.log.emit("Cancelled by user.")
                        for f in futures:
                            f.cancel()
                        break

                    res = fut.result()
                    results.append(res)

                    done += 1
                    self.progress.emit(done, total)

            if self._cancel:
                self.finished.emit("Cancelled.")
                return

            results.sort(key=lambda d: d.get("filename", ""))

            # publish structured results to UI
            self.resultsReady.emit(results)

            if self.config.export_txt:
                out_path = export_results_txt(results)
                self.log.emit(f"Exported TXT: {out_path}")

            if algo == ALGO_PROFILES:
                exported_any = False
                for r in results:
                    if "error" in r:
                        continue
                    profs = r.get("profiles", [])
                    if not isinstance(profs, list) or not profs:
                        continue
                    np_profiles = []
                    import numpy as np
                    for p in profs:
                        t = p.get("t", [])
                        y = p.get("y", [])
                        np_profiles.append((np.array(t, dtype=float), np.array(y, dtype=float)))
                    stem = Path(r.get("filename", "image")).stem
                    export_profiles_txt(stem, np_profiles)
                    exported_any = True
                if exported_any:
                    self.log.emit("Exported profiles to: results/profiles/")

            lines = []
            for r in results:
                filename = r.get("filename", "?")
                if "error" in r:
                    lines.append(f"{filename}: ERROR ({r.get('error')})")
                    continue
                mode = r.get("color_mode", "?")
                roi_txt = self._format_roi(r.get("roi"))
                lines.append(f"{filename} [{mode}]{roi_txt} -> {r.get('summary','OK')}")

            self.finished.emit("\n".join(lines) if lines else "No output.")

        except Exception as e:
            self.logger.exception("Worker error")
            self.error.emit(str(e))
