# app/ui/main_window.py
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QMessageBox,
    QComboBox,
    QTextEdit,
    QProgressBar,
    QCheckBox,
)

from app.ui.image_viewer import ImageViewer
from app.ui.plot_widget import PlotWidget
from app.worker import AlgorithmWorker
from app.models.analysis_config import AnalysisConfig
from core.algorithms import ALGO_INTENSITY, ALGO_CONTRAST, ALGO_PROFILES
from core.io.image_loader import load_image
from core.roi import apply_roi, RectROI, CircleROI, PolygonROI
from core.profiles import LineSection, extract_line_profile
from core.export.csv_exporter import export_results_csv
from core.export.pdf_report import export_pdf_report
from datetime import datetime


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.logger = logging.getLogger(__name__)
        self.setWindowTitle("Photonics Lab Image Processor")
        self.resize(1400, 760)

        self.selected_images: List[Path] = []
        self.active_image: Optional[Path] = None

        self.thread: Optional[QThread] = None
        self.worker: Optional[AlgorithmWorker] = None

        self.roi_payload: Optional[dict] = None
        self.cross_sections_payload: List[dict] = []
        self.active_section_index: int = -1

        #check it
        self.last_saved_plot_path: Optional[Path] = None
        self.last_results: List[Dict[str, Any]] = []

        central = QWidget()
        central.setStyleSheet(
            """
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #d18cff,
                stop:1 #6c2bd1
            );
            """
        )
        main_layout = QHBoxLayout(central)

        # LEFT PANEL
        left = QVBoxLayout()

        self.btn_select = QPushButton("Choose images")

        self.combo_algo = QComboBox()
        self.combo_algo.addItem("Intensity metrics", userData=ALGO_INTENSITY)
        self.combo_algo.addItem("Contrast metrics", userData=ALGO_CONTRAST)
        self.combo_algo.addItem("Profiles", userData=ALGO_PROFILES)

        self.combo_tool = QComboBox()
        self.combo_tool.addItem("Tool: None", userData="none")
        self.combo_tool.addItem("Tool: Rectangle ROI", userData="rect")
        self.combo_tool.addItem("Tool: Circle ROI", userData="circle")
        self.combo_tool.addItem("Tool: Polygon ROI", userData="polygon")
        self.combo_tool.addItem("Tool: Cross-section", userData="cross")

        self.btn_clear_roi = QPushButton("Clear ROI")
        self.btn_clear_roi.setEnabled(False)
        self.label_roi = QLabel("ROI: none")

        # Cross-sections list
        self.list_sections = QListWidget()
        self.list_sections.setMinimumHeight(120)

        self.btn_remove_section = QPushButton("Remove selected section")
        self.btn_remove_section.setEnabled(False)

        self.btn_clear_cs = QPushButton("Clear cross-sections")
        self.btn_clear_cs.setEnabled(False)

        self.btn_plot_profiles = QPushButton("Plot profiles (active image)")
        self.btn_plot_profiles.setEnabled(False)

        self.btn_export_plot = QPushButton("Export plot to PNG")
        self.btn_export_plot.setEnabled(False)

        self.label_cs = QLabel("Cross-sections: 0 (right click removes last)")

        # Trend plot controls
        self.label_trend = QLabel("Trend plot (after run):")
        self.combo_x = QComboBox()
        self.combo_x.setEnabled(False)
        self.combo_y = QComboBox()
        self.combo_y.setEnabled(False)
        self.btn_plot_trend = QPushButton("Plot trend")
        self.btn_plot_trend.setEnabled(False)


        self.btn_export_csv = QPushButton("Export results CSV")
        self.btn_export_csv.setEnabled(False)

        self.btn_quicksave_plot = QPushButton("Quick-save plot PNG (results/plots)")
        self.btn_quicksave_plot.setEnabled(False)

        self.btn_export_pdf = QPushButton("Export PDF report")
        self.btn_export_pdf.setEnabled(False)

        self.chk_export_txt = QCheckBox("Export results to TXT (results/results.txt)")
        self.chk_export_txt.setChecked(True)

        self.list_files = QListWidget()
        self.list_files.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.btn_run = QPushButton("Run")
        self.btn_run.setEnabled(False)

        self.progress = QProgressBar()
        self.progress.setValue(0)

        self.label_status = QLabel("Status: ready")

        left.addWidget(self.btn_select)
        left.addWidget(self.combo_algo)
        left.addWidget(self.combo_tool)

        left.addWidget(self.btn_clear_roi)
        left.addWidget(self.label_roi)

        left.addWidget(QLabel("Cross-sections list:"))
        left.addWidget(self.list_sections, 1)
        left.addWidget(self.btn_remove_section)
        left.addWidget(self.btn_clear_cs)
        left.addWidget(self.btn_plot_profiles)
        left.addWidget(self.btn_export_plot)
        left.addWidget(self.label_cs)

        left.addWidget(self.label_trend)
        left.addWidget(QLabel("X (parameter from filename):"))
        left.addWidget(self.combo_x)
        left.addWidget(QLabel("Y (metric):"))
        left.addWidget(self.combo_y)
        left.addWidget(self.btn_plot_trend)

        left.addWidget(self.btn_export_csv)
        left.addWidget(self.btn_quicksave_plot)
        left.addWidget(self.btn_export_pdf)


        left.addWidget(self.chk_export_txt)
        left.addWidget(self.list_files, 2)
        left.addWidget(self.btn_run)
        left.addWidget(self.progress)
        left.addWidget(self.label_status)

        # RIGHT PANEL
        right = QVBoxLayout()
        self.image_viewer = ImageViewer()
        self.plot_widget = PlotWidget()
        self.text_result = QTextEdit()
        self.text_result.setReadOnly(True)
        self.text_result.setPlaceholderText("Results / logs")

        right.addWidget(self.image_viewer, 3)
        right.addWidget(self.plot_widget, 2)
        right.addWidget(self.text_result, 2)

        main_layout.addLayout(left, 1)
        main_layout.addLayout(right, 3)
        self.setCentralWidget(central)

        self.setStyleSheet(
            """
            QTextEdit, QListWidget, QComboBox {
                background-color: rgba(0, 0, 0, 120);
                color: #ffffff;
                border: 1px solid #ffffff;
            }
            QPushButton {
                background-color: #6c2bd1;
                color: white;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QPushButton:hover { background-color: #8e44ff; }
            QLabel, QCheckBox { color: #ffffff; }
            QProgressBar {
                background-color: rgba(0, 0, 0, 120);
                color: #ffffff;
                border: 1px solid #ffffff;
            }
            """
        )

        # signals
        self.btn_select.clicked.connect(self.on_select_files)
        self.btn_run.clicked.connect(self.on_run)

        self.combo_tool.currentIndexChanged.connect(self.on_tool_changed)
        self.btn_clear_roi.clicked.connect(self.on_clear_roi)

        self.list_sections.itemSelectionChanged.connect(self.on_section_selected)
        self.btn_remove_section.clicked.connect(self.on_remove_selected_section)
        self.btn_clear_cs.clicked.connect(self.on_clear_cs)
        self.btn_plot_profiles.clicked.connect(self.on_plot_profiles)
        self.btn_export_plot.clicked.connect(self.on_export_plot_png)

        self.btn_plot_trend.clicked.connect(self.on_plot_trend)

        self.image_viewer.roiChanged.connect(self.on_roi_changed)
        self.image_viewer.crossSectionsChanged.connect(self.on_cross_sections_changed)
        self.image_viewer.activeCrossSectionChanged.connect(self.on_active_section_changed_from_viewer)

        self.btn_export_csv.clicked.connect(self.on_export_csv)
        self.btn_quicksave_plot.clicked.connect(self.on_quicksave_plot_png)
        self.btn_export_pdf.clicked.connect(self.on_export_pdf)


        # init
        self.on_tool_changed()
        self._update_trend_controls()

    # ---------- file selection / preview ----------

    def on_select_files(self) -> None:
        dialog = QFileDialog(self, "Choose images to process")
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)

        #dialog.setNameFilters(["Pictures (*.png *.jpg *.jpeg *.tif *.tiff *.bmp)", "All files (*.*)"])

        dialog.setNameFilters(
            [
                "Pictures (*.png *.PNG *.jpg *.JPG *.jpeg *.JPEG *.tif *.TIF *.tiff *.TIFF *.bmp *.BMP)",
                "All files (*.*)",
            ]
        )

        if not dialog.exec():
            return

        self.selected_images = [Path(f) for f in dialog.selectedFiles()]
        self.list_files.clear()

        for p in self.selected_images:
            item = QListWidgetItem(p.name)
            item.setToolTip(str(p))
            item.setData(Qt.ItemDataRole.UserRole, str(p))
            self.list_files.addItem(item)

        try:
            self.list_files.itemClicked.disconnect(self.on_file_clicked)
        except TypeError:
            pass
        self.list_files.itemClicked.connect(self.on_file_clicked)

        self.btn_run.setEnabled(bool(self.selected_images))
        self.progress.setValue(0)
        self.label_status.setText(f"Number of files: {len(self.selected_images)}")

        if self.selected_images:
            self.active_image = self.selected_images[0]
            self.image_viewer.set_image(self.active_image)

        self._update_buttons()

    def on_file_clicked(self, item: QListWidgetItem) -> None:
        p = Path(item.data(Qt.ItemDataRole.UserRole))
        if p.exists():
            self.active_image = p
            self.image_viewer.set_image(p)
            self.label_status.setText(f"Preview: {p.name}")
            self._update_buttons()

    # ---------- tool / ROI ----------

    def on_tool_changed(self) -> None:
        tool = self.combo_tool.currentData()
        self.image_viewer.set_tool(tool)
        self._update_buttons()

    def on_clear_roi(self) -> None:
        self.image_viewer.clear_roi()

    def on_roi_changed(self, payload) -> None:
        self.roi_payload = payload if isinstance(payload, dict) else None
        self._update_roi_label()
        self._update_buttons()

    def _update_roi_label(self) -> None:
        if not self.roi_payload:
            self.label_roi.setText("ROI: none")
            return
        t = self.roi_payload.get("type")
        if t == "rect":
            r = self.roi_payload
            self.label_roi.setText(f"ROI: rect x={r.get('x')} y={r.get('y')} w={r.get('w')} h={r.get('h')}")
        elif t == "circle":
            r = self.roi_payload
            self.label_roi.setText(f"ROI: circle cx={r.get('cx')} cy={r.get('cy')} r={r.get('r')}")
        elif t == "polygon":
            pts = self.roi_payload.get("points", [])
            n = len(pts) if isinstance(pts, list) else 0
            self.label_roi.setText(f"ROI: polygon points={n}")
        else:
            self.label_roi.setText("ROI: (unknown)")

    def _roi_obj_from_payload(self):
        if not self.roi_payload:
            return None
        t = self.roi_payload.get("type")
        try:
            if t == "rect":
                return RectROI(int(self.roi_payload["x"]), int(self.roi_payload["y"]), int(self.roi_payload["w"]), int(self.roi_payload["h"]))
            if t == "circle":
                return CircleROI(int(self.roi_payload["cx"]), int(self.roi_payload["cy"]), int(self.roi_payload["r"]))
            if t == "polygon":
                pts = self.roi_payload.get("points", [])
                return PolygonROI(points=[(int(p[0]), int(p[1])) for p in pts])
        except Exception:
            return None
        return None

    # ---------- cross-sections list ----------

    def on_cross_sections_changed(self, payload) -> None:
        self.cross_sections_payload = payload if isinstance(payload, list) else []
        self.label_cs.setText(f"Cross-sections: {len(self.cross_sections_payload)} (right click removes last)")
        self._rebuild_sections_list()
        self._update_buttons()

    def on_active_section_changed_from_viewer(self, idx: int) -> None:
        self.active_section_index = idx
        if idx == -1:
            self.list_sections.clearSelection()
        else:
            if 0 <= idx < self.list_sections.count():
                self.list_sections.blockSignals(True)
                self.list_sections.setCurrentRow(idx)
                self.list_sections.blockSignals(False)
        self._update_buttons()

    def _rebuild_sections_list(self) -> None:
        self.list_sections.blockSignals(True)
        self.list_sections.clear()
        for idx, s in enumerate(self.cross_sections_payload, start=1):
            txt = f"Sec {idx}: ({int(s['x0'])},{int(s['y0'])}) → ({int(s['x1'])},{int(s['y1'])})"
            self.list_sections.addItem(txt)
        self.list_sections.blockSignals(False)

        if self.active_section_index != -1 and self.active_section_index < self.list_sections.count():
            self.list_sections.setCurrentRow(self.active_section_index)

    def on_section_selected(self) -> None:
        row = self.list_sections.currentRow()
        if row < 0:
            self.active_section_index = -1
            self.image_viewer.set_active_cross_section(-1, emit=False)
        else:
            self.active_section_index = row
            self.image_viewer.set_active_cross_section(row, emit=False)
        self._update_buttons()

    def on_remove_selected_section(self) -> None:
        row = self.list_sections.currentRow()
        if row < 0:
            return
        self.image_viewer.remove_cross_section(row)
        self.plot_widget.clear()
        self._update_buttons()

    def on_clear_cs(self) -> None:
        self.image_viewer.clear_cross_sections()
        self.plot_widget.clear()
        self._update_buttons()

    # ---------- profiles plot ----------

    def on_plot_profiles(self) -> None:
        if not self.active_image or not self.cross_sections_payload:
            return

        arr, _ = load_image(self.active_image)
        roi_obj = self._roi_obj_from_payload()
        arr_roi = apply_roi(arr, roi_obj)

        profiles_to_plot = []
        for idx, s in enumerate(self.cross_sections_payload, start=1):
            sec = LineSection(
                x0=float(s["x0"]), y0=float(s["y0"]),
                x1=float(s["x1"]), y1=float(s["y1"]),
                samples=200
            )
            t, y = extract_line_profile(arr_roi, sec)
            profiles_to_plot.append((t.tolist(), y.tolist(), f"Sec {idx}"))

        self.plot_widget.set_title("Intensity profiles")
        self.plot_widget.plot_profiles(profiles_to_plot)
        self.text_result.append(f"Plotted {len(profiles_to_plot)} profile(s) for {self.active_image.name}")
        self._update_buttons()

    def on_export_plot_png(self) -> None:
        if not self.plot_widget.has_content():
            QMessageBox.information(self, "No plot", "Plot something first.")
            return

        default_name = "plot.png"
        if self.active_image:
            default_name = f"{self.active_image.stem}_plot.png"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export plot to PNG",
            str(Path("results") / default_name),
            "PNG Image (*.png)",
        )
        if not file_path:
            return

        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            self.plot_widget.save_png(file_path, dpi=200)
            self.text_result.append(f"Saved plot: {file_path}")
            #check 2
            self.last_saved_plot_path = Path(file_path)

        except Exception as e:
            QMessageBox.critical(self, "Export error", str(e))

    # --------- Trend plot ----------

    def _update_trend_controls(self) -> None:
        has_results = len(self.last_results) > 0
        self.combo_x.setEnabled(has_results)
        self.combo_y.setEnabled(has_results)
        self.btn_plot_trend.setEnabled(has_results and self.combo_x.count() > 0 and self.combo_y.count() > 0)

    def _populate_trend_dropdowns(self) -> None:
        # collect param keys and metric keys from results (ignore errored)
        ok = [r for r in self.last_results if isinstance(r, dict) and "error" not in r]

        param_keys = set()
        metric_keys = set()
        for r in ok:
            params = r.get("params", {})
            if isinstance(params, dict):
                param_keys.update([k for k, v in params.items() if isinstance(v, (int, float))])

            # metrics: numeric top-level keys (excluding known non-metrics)
            for k, v in r.items():
                if k in ("filename", "path", "color_mode", "roi", "params", "summary", "profiles"):
                    continue
                if isinstance(v, (int, float)):
                    metric_keys.add(k)

        self.combo_x.blockSignals(True)
        self.combo_y.blockSignals(True)
        self.combo_x.clear()
        self.combo_y.clear()

        for k in sorted(param_keys):
            self.combo_x.addItem(k, userData=k)

        for k in sorted(metric_keys):
            self.combo_y.addItem(k, userData=k)

        self.combo_x.blockSignals(False)
        self.combo_y.blockSignals(False)

        self._update_trend_controls()

    def on_plot_trend(self) -> None:
        if not self.last_results:
            return
        xk = self.combo_x.currentData()
        yk = self.combo_y.currentData()
        if not xk or not yk:
            return

        points = []
        for r in self.last_results:
            if "error" in r:
                continue
            params = r.get("params", {})
            if not isinstance(params, dict):
                continue
            x = params.get(xk)
            y = r.get(yk)
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                points.append((float(x), float(y)))

        if not points:
            QMessageBox.information(self, "No data", f"No valid points for X='{xk}' and Y='{yk}'.")
            return

        if len(points) == 1:
            QMessageBox.information(self, "Only one point",
                                    "Trend plot has only 1 valid point. Add more images or vary the X parameter in filenames.")



        points.sort(key=lambda t: t[0])
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        self.plot_widget.set_title(f"Trend: {yk} vs {xk}")
        self.plot_widget.plot_xy(xs, ys, xlabel=xk, ylabel=yk)
        self.text_result.append(f"Trend plotted: {yk} vs {xk} ({len(points)} points)")
        self._update_buttons()

    # ---------- run batch ----------

    def on_run(self) -> None:
        if not self.selected_images:
            QMessageBox.warning(self, "No files", "Choose files first.")
            return

        algo = self.combo_algo.currentData()
        export_txt = self.chk_export_txt.isChecked()

        config = AnalysisConfig(
            algorithm=algo,
            export_txt=export_txt,
            roi=self.roi_payload,
            cross_sections=self.cross_sections_payload if self.cross_sections_payload else None,
            profile_samples=200,
        )

        if algo == ALGO_PROFILES and not self.cross_sections_payload:
            QMessageBox.warning(self, "No cross-sections", "Define at least one cross-section before running Profiles export.")
            return

        self.btn_run.setEnabled(False)
        self.progress.setValue(0)
        self.text_result.setPlainText("Running...\n")
        self.label_status.setText("Status: running...")

        self.thread = QThread()
        self.worker = AlgorithmWorker(self.selected_images, config)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)

        self.worker.progress.connect(self.on_progress)
        self.worker.log.connect(self.on_log)
        self.worker.resultsReady.connect(self.on_results_ready)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)

        # cleanup on finished
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_results_ready(self, results_obj) -> None:
        # results_obj should be list[dict]
        if isinstance(results_obj, list):
            self.last_results = results_obj
        else:
            self.last_results = []
        self._populate_trend_dropdowns()
        self._update_trend_controls()

    def on_progress(self, done: int, total: int) -> None:
        if total > 0:
            self.progress.setValue(int(done * 100 / total))
        self.label_status.setText(f"Status: running... {done}/{total}")

    def on_log(self, msg: str) -> None:
        self.text_result.append(msg)

    def on_finished(self, final_text: str) -> None:
        self.text_result.append("\n=== DONE ===\n")
        self.text_result.append(final_text)
        self.label_status.setText("Status: finished")
        self.btn_run.setEnabled(True)
        self._update_trend_controls()

    def on_error(self, msg: str) -> None:
        self.label_status.setText("Status: error")
        QMessageBox.critical(self, "Error", msg)
        self.btn_run.setEnabled(True)
        self._update_trend_controls()

    # ---------- misc ----------

    def _update_buttons(self) -> None:
        self.btn_clear_roi.setEnabled(bool(self.roi_payload))

        has_sections = len(self.cross_sections_payload) > 0
        self.btn_clear_cs.setEnabled(has_sections)
        self.btn_plot_profiles.setEnabled(self.active_image is not None and has_sections)
        self.btn_export_plot.setEnabled(self.plot_widget.has_content())

        self.btn_remove_section.setEnabled(self.list_sections.currentRow() >= 0)
        self._update_trend_controls()
        has_results = len(self.last_results) > 0
        self.btn_export_csv.setEnabled(has_results)
        self.btn_export_pdf.setEnabled(has_results)

        self.btn_quicksave_plot.setEnabled(self.plot_widget.has_content())


    def on_export_csv(self) -> None:
        if not self.last_results:
            QMessageBox.information(self, "No data", "Run a batch first.")
            return
        try:
            out_path = export_results_csv(self.last_results, out_dir=Path("results"))
            self.text_result.append(f"CSV exported: {out_path}")
        except Exception as e:
            QMessageBox.critical(self, "CSV export error", str(e))

    def on_quicksave_plot_png(self) -> None:
        if not self.plot_widget.has_content():
            QMessageBox.information(self, "No plot", "Plot something first.")
            return
        try:
            out_dir = Path("results") / "plots"
            out_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = out_dir / f"plot_{ts}.png"
            self.plot_widget.save_png(str(out_path), dpi=200)
            self.last_saved_plot_path = out_path
            self.text_result.append(f"Plot saved: {out_path}")
            self._update_buttons()
        except Exception as e:
            QMessageBox.critical(self, "Plot save error", str(e))

    def on_export_pdf(self) -> None:
        if not self.last_results:
            QMessageBox.information(self, "No data", "Run a batch first.")
            return
        try:
            pdf_path = export_pdf_report(
                self.last_results,
                out_dir=Path("results"),
                title="Photonics Lab Analysis Report",
                plot_png_path=self.last_saved_plot_path,
            )
            self.text_result.append(f"PDF exported: {pdf_path}")
        except Exception as e:
            QMessageBox.critical(self, "PDF export error", str(e))
