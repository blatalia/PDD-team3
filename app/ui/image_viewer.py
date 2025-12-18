from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt6.QtGui import QPixmap, QPainter
from pathlib import Path
from PyQt6.QtCore import Qt, QRectF 


class ImageViewer(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._pixmap_item = None
        self._scale_factor = 1.0

        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

    def set_image(self, path: Path):
        pixmap = QPixmap(str(path))
        self._scene.clear()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        self.reset_transform()

    def reset_transform(self):
        self.resetTransform()
        self._scale_factor = 1.0

    def wheelEvent(self, event):
        if self._pixmap_item is None:
            return

        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        new_scale = self._scale_factor * zoom_factor
        if new_scale < 0.1 or new_scale > 10:
            return

        self._scale_factor = new_scale
        self.scale(zoom_factor, zoom_factor)
