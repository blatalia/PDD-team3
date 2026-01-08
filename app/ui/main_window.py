# app/ui/main_window.py
from pathlib import Path
from typing import List, Optional
import logging
from app.ui.image_viewer import ImageViewer

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
)
from PyQt6.QtGui import QPixmap

from PyQt6.QtCore import Qt, QThread

from app.worker import AlgorithmWorker
from core.algorithms import ALGO_RED, ALGO_INTENSITY, ALGO_CONTRAST



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Photonics Lab Image Processor")
        self.resize(1000, 600)

        self.selected_images: List[Path] = []
        self.thread: Optional[QThread] = None
        self.worker: Optional[AlgorithmWorker] = None
        self.current_algo: Optional[str] = None

        central = QWidget()
        central.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #d18cff,
                stop:1 #6c2bd1
            );
        """)

        central.setObjectName("centralWidget")

        main_layout = QHBoxLayout(central)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        self.btn_select = QPushButton("Choose images")

        self.combo_algo = QComboBox()
        self.combo_algo.addItem("Filter", userData=ALGO_RED)
        self.combo_algo.addItem("Intensity", userData=ALGO_INTENSITY)
        self.combo_algo.addItem("Contrast metrics (single image)", userData=ALGO_CONTRAST)


        self.list_files = QListWidget()
        self.list_files.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.btn_run = QPushButton("Run")
        self.btn_run.setEnabled(False)

        self.label_status = QLabel("Status: ready")

        left_layout.addWidget(self.btn_select)
        left_layout.addWidget(self.combo_algo)
        left_layout.addWidget(self.list_files)
        left_layout.addWidget(self.btn_run)
        left_layout.addWidget(self.label_status)

        self.image_viewer = ImageViewer()
        self.image_viewer.setMinimumSize(300, 300)

        self.text_result = QTextEdit()
        self.text_result.setReadOnly(True)
        self.text_result.setPlaceholderText("Results")

        right_layout.addWidget(self.image_viewer, 2)
        right_layout.addWidget(self.text_result, 1)


        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)

        self.setCentralWidget(central)
        self.active_image: Path | None = None


        # signals
        self.btn_select.clicked.connect(self.on_select_files)
        self.btn_run.clicked.connect(self.on_run_algorithm)
        
        self.setStyleSheet("""
        QTextEdit, QListWidget, QComboBox {
            background-color: rgba(0, 0, 0, 120);  /* półprzezroczyste czarne */
            color: #ffffff;
            border: 1px solid #ffffff;
        }

        QPushButton {
            background-color: #6c2bd1;
            color: white;
            border-radius: 6px;
            padding: 6px 10px;
        }
        QPushButton:hover {
            background-color: #8e44ff;
        }

        QLabel {
            color: #ffffff;
        }
        """)



    def on_select_files(self):
        dialog = QFileDialog(self, "Choose images to process")
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dialog.setNameFilters(
            [
                "Pictures (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.JPG)",
                "All files (*.*)",
            ]
        )

        if dialog.exec():
            files = dialog.selectedFiles()
            self.selected_images = [Path(f) for f in files]
            self.list_files.clear()

            for p in self.selected_images:
                item = QListWidgetItem(p.name)
                item.setToolTip(str(p))
                item.setData(Qt.ItemDataRole.UserRole, str(p))
                self.list_files.addItem(item)

            # connect ONCE (not once per item)
            try:
                self.list_files.itemClicked.disconnect(self.on_file_clicked)
            except TypeError:
                pass
            self.list_files.itemClicked.connect(self.on_file_clicked)

            logging.getLogger(__name__).info("Number of files %d", len(self.selected_images))
            self.btn_run.setEnabled(bool(self.selected_images))
            self.label_status.setText(f"Number of files {len(self.selected_images)}")


    def on_run_algorithm(self):
        algo_code = self.combo_algo.currentData()
        self.current_algo = algo_code

        if not self.selected_images:
            QMessageBox.warning(self, "No files", "Choose files.")
            return

        # Contrast runs on ALL selected images
        images_for_run = self.selected_images

        logging.getLogger(__name__).info(
            "Running process(es) '%s' for %d file(s)",
            algo_code,
            len(images_for_run),
        )

        self.btn_run.setEnabled(False)
        self.label_status.setText("Status: running...")
        self.text_result.setPlainText("running in progress...")

        self.thread = QThread()
        self.worker = AlgorithmWorker(images_for_run, algo_code)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_algorithm_finished)
        self.worker.error.connect(self.on_algorithm_error)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # progress/log signals (you already have these)
        self.worker.progress.connect(self.on_progress)
        self.worker.log.connect(self.on_worker_log)

        self.thread.start()



        self.thread.start()

    def on_algorithm_finished(self, result: str):
        logging.getLogger(__name__).info("Algorytm finished (OK)")
        self.label_status.setText("Status: zakończono")
        self.text_result.setPlainText(result)
        self.btn_run.setEnabled(True)

        if self.current_algo == ALGO_RED and self.selected_images:
            first_src = self.selected_images[0]
            result_path = Path("results") / first_src.name

            if result_path.exists():
                self.image_viewer.set_image(result_path)
                self.label_status.setText(
                    f"Status: previewing processed {first_src.name}"
                )
            else:
                self.label_status.setText("Status: processed image not found")



    def on_algorithm_error(self, msg: str):
        logging.getLogger(__name__).error("Algorithm failed: %s", msg)
        self.label_status.setText("Status: Error")
        QMessageBox.critical(self, "Error", msg)
        self.btn_run.setEnabled(True)

    def on_file_clicked(self, item: QListWidgetItem):
        from PyQt6.QtCore import Qt
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        path = Path(data)
        if path.exists():
            self.active_image = path
            self.image_viewer.set_image(path)
            self.label_status.setText(f"Status: previewing {path.name}")
            


    def on_progress(self, done: int, total: int):
        self.label_status.setText(f"Status: running... {done}/{total}")

    def on_worker_log(self, msg: str):
        # optional: append log lines
        self.text_result.append(msg)
