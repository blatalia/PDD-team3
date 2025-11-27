# app/ui/main_window.py
from pathlib import Path
from typing import List, Optional
import logging

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
from core.algorithms import ALGO_RED, ALGO_INTENSITY


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

        self.image_label = QLabel("Preview:")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(300, 300)

        self.text_result = QTextEdit()
        self.text_result.setReadOnly(True)
        self.text_result.setPlaceholderText("Results:")

        right_layout.addWidget(self.image_label, 2)
        right_layout.addWidget(self.text_result, 1)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)

        self.setCentralWidget(central)


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
                "Pictures (*.png *.jpg *.jpeg *.tif *.tiff *.bmp)",
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

            logging.getLogger(__name__).info(
                "Number of files %d", len(self.selected_images)
            )
            self.btn_run.setEnabled(bool(self.selected_images))
            self.label_status.setText(
                f"Number of files {len(self.selected_images)}"
            )

    def on_run_algorithm(self):
        if not self.selected_images:
            QMessageBox.warning(
                self,
                "No files",
                "Choose files.",
            )
            return

        algo_code = self.combo_algo.currentData()
        self.current_algo = algo_code
        logging.getLogger(__name__).info(
            "Running process(es) '%s' for %d file(s)",
            algo_code,
            len(self.selected_images),
        )

        self.btn_run.setEnabled(False)
        self.label_status.setText("Status: running...")
        self.text_result.setPlainText("running in progress...")

        self.thread = QThread()
        self.worker = AlgorithmWorker(self.selected_images, algo_code)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_algorithm_finished)
        self.worker.error.connect(self.on_algorithm_error)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_algorithm_finished(self, result: str):
        logging.getLogger(__name__).info("Algorytm finished (OK)")
        self.label_status.setText("Status: finished")
        self.text_result.setPlainText(result)
        self.btn_run.setEnabled(True)

        if self.current_algo == ALGO_RED and self.selected_images:
            first_src = self.selected_images[0]
            result_path = Path("results") / first_src.name

            if result_path.exists():
                pixmap = QPixmap(str(result_path))
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(
                        self.image_label.width(),
                        self.image_label.height(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    self.image_label.setPixmap(pixmap)
                else:
                    self.image_label.setText("Preview: failed to load image")
            else:
                self.image_label.setText("Preview: result image not found")


    def on_algorithm_error(self, msg: str):
        logging.getLogger(__name__).error("Algorithm failed: %s", msg)
        self.label_status.setText("Status: Error")
        QMessageBox.critical(self, "Error", msg)
        self.btn_run.setEnabled(True)
