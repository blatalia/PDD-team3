# app/ui/image_viewer.py
from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Tuple

from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QPen, QPolygon, QColor
from PyQt6.QtWidgets import QWidget

SECTION_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]

class ImageViewer(QWidget):
    """
    Tools:
      - none
      - rect ROI
      - circle ROI
      - polygon ROI
      - cross-section (line): click+drag to add line, right click removes last
    ROI + sections are stored in IMAGE pixel coordinates.
    """

    roiChanged = pyqtSignal(object)            # payload dict or None
    crossSectionsChanged = pyqtSignal(object)  # list payload
    activeCrossSectionChanged = pyqtSignal(int)  # active index (-1 if none)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.setMouseTracking(True)

        self._pixmap_original: Optional[QPixmap] = None
        self._pixmap_scaled: Optional[QPixmap] = None
        self._target_rect: Optional[QRect] = None

        self._tool: str = "none"

        self._drawing: bool = False
        self._start_pt: Optional[QPoint] = None
        self._current_pt: Optional[QPoint] = None

        self._rect_image: Optional[QRect] = None
        self._circle_image: Optional[Tuple[int, int, int]] = None
        self._poly_image: Optional[List[Tuple[int, int]]] = None

        self._poly_points_widget: List[QPoint] = []
        self._poly_preview_pt: Optional[QPoint] = None
        self._poly_is_drawing: bool = False

        self._sections_image: List[Tuple[int, int, int, int]] = []
        self._active_section_index: int = -1


    def set_tool(self, tool: str) -> None:
        if tool not in ("none", "rect", "circle", "polygon", "cross"):
            tool = "none"
        self._tool = tool

        self._drawing = False
        self._start_pt = None
        self._current_pt = None

        self._poly_points_widget = []
        self._poly_preview_pt = None
        self._poly_is_drawing = False

        self.update()

    def clear_roi(self) -> None:
        self._rect_image = None
        self._circle_image = None
        self._poly_image = None
        self._poly_points_widget = []
        self._poly_preview_pt = None
        self._poly_is_drawing = False
        self.roiChanged.emit(None)
        self.update()

    def clear_cross_sections(self) -> None:
        self._sections_image = []
        self.set_active_cross_section(-1, emit=True)
        self.crossSectionsChanged.emit([])
        self.update()

    def set_active_cross_section(self, index: int, emit: bool = False) -> None:
        if index < -1:
            index = -1
        if index >= len(self._sections_image):
            index = -1
        changed = index != self._active_section_index
        self._active_section_index = index
        if emit and changed:
            self.activeCrossSectionChanged.emit(self._active_section_index)
        self.update()

    def remove_cross_section(self, index: int) -> None:
        if index < 0 or index >= len(self._sections_image):
            return
        self._sections_image.pop(index)

        if not self._sections_image:
            self._active_section_index = -1
        else:
            if self._active_section_index == index:
                self._active_section_index = min(index, len(self._sections_image) - 1)
            elif self._active_section_index > index:
                self._active_section_index -= 1

        self.crossSectionsChanged.emit(self.get_cross_sections_payload())
        self.activeCrossSectionChanged.emit(self._active_section_index)
        self.update()

    def get_cross_sections_payload(self) -> List[dict]:
        payload = []
        for (x0, y0, x1, y1) in self._sections_image:
            payload.append({"x0": float(x0), "y0": float(y0), "x1": float(x1), "y1": float(y1)})
        return payload

    def set_image(self, path: Path) -> None:
        pm = QPixmap(str(path))
        if pm.isNull():
            self._pixmap_original = None
            self._pixmap_scaled = None
            self._target_rect = None
            self.clear_roi()
            self.clear_cross_sections()
            self.update()
            return

        self._pixmap_original = pm
        self._update_scaled_pixmap()
        self.update()


    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_scaled_pixmap()
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)

        if self._pixmap_scaled and self._target_rect:
            painter.drawPixmap(self._target_rect, self._pixmap_scaled)

        if self._sections_image:
            for idx, (x0, y0, x1, y1) in enumerate(self._sections_image):
                color = QColor(SECTION_COLORS[idx % len(SECTION_COLORS)])
                pen_cs = QPen(color)
                pen_cs.setWidth(4 if idx == self._active_section_index else 2)
                painter.setPen(pen_cs)

                p0 = self._image_point_to_widget_point(x0, y0)
                p1 = self._image_point_to_widget_point(x1, y1)
                if p0 and p1:
                    painter.drawLine(p0, p1)
                painter.setPen(pen_cs)

                p0 = self._image_point_to_widget_point(x0, y0)
                p1 = self._image_point_to_widget_point(x1, y1)
                if p0 and p1:
                    painter.drawLine(p0, p1)

        if self._tool == "cross" and self._drawing and self._start_pt and self._current_pt:
            next_idx = len(self._sections_image) if self._sections_image else 0
            pen_cs = QPen(QColor(SECTION_COLORS[next_idx % len(SECTION_COLORS)]))
            pen_cs.setWidth(2)
            painter.setPen(pen_cs)
            painter.drawLine(self._start_pt, self._current_pt)

        pen = QPen(Qt.GlobalColor.green)
        pen.setWidth(2)
        painter.setPen(pen)

        if self._tool == "rect":
            rect_widget = None
            if self._drawing and self._start_pt and self._current_pt:
                rect_widget = QRect(self._start_pt, self._current_pt).normalized()
                if self._target_rect:
                    rect_widget = rect_widget.intersected(self._target_rect)
            elif self._rect_image is not None:
                rect_widget = self._image_rect_to_widget_rect(self._rect_image)

            if rect_widget is not None:
                painter.drawRect(rect_widget)

        elif self._tool == "circle":
            circle_widget = None
            if self._drawing and self._start_pt and self._current_pt:
                circle_widget = self._circle_widget_rect_from_drag(self._start_pt, self._current_pt)
            elif self._circle_image is not None:
                circle_widget = self._circle_image_to_widget_rect(self._circle_image)

            if circle_widget is not None:
                painter.drawEllipse(circle_widget)

        elif self._tool == "polygon":
            if self._poly_is_drawing and self._poly_points_widget:
                poly = QPolygon(self._poly_points_widget)
                painter.drawPolyline(poly)
                if self._poly_preview_pt is not None:
                    painter.drawLine(self._poly_points_widget[-1], self._poly_preview_pt)
                for pt in self._poly_points_widget:
                    painter.drawEllipse(pt, 3, 3)
            elif self._poly_image is not None:
                poly_w = self._poly_image_to_widget_poly(self._poly_image)
                if poly_w is not None:
                    painter.drawPolygon(poly_w)
                    for i in range(poly_w.count()):
                        pt = poly_w.point(i)
                        painter.drawEllipse(pt, 3, 3)

    def mousePressEvent(self, event) -> None:
        if self._tool == "none":
            return
        if not self._target_rect or not self._pixmap_original:
            return
        if not self._target_rect.contains(event.pos()):
            return

        # right click removes last cross-section
        if self._tool == "cross" and event.button() == Qt.MouseButton.RightButton:
            if self._sections_image:
                self._sections_image.pop()
                if self._active_section_index >= len(self._sections_image):
                    self._active_section_index = len(self._sections_image) - 1
                if not self._sections_image:
                    self._active_section_index = -1

                self.crossSectionsChanged.emit(self.get_cross_sections_payload())
                self.activeCrossSectionChanged.emit(self._active_section_index)
                self.update()
            return

        if self._tool in ("rect", "circle", "cross"):
            if event.button() != Qt.MouseButton.LeftButton:
                return
            self._drawing = True
            self._start_pt = event.pos()
            self._current_pt = event.pos()
            self.update()
            return

        if self._tool == "polygon":
            # right click removes last point
            if event.button() == Qt.MouseButton.RightButton:
                if self._poly_is_drawing and self._poly_points_widget:
                    self._poly_points_widget.pop()
                    self.update()
                return

            if event.button() != Qt.MouseButton.LeftButton:
                return

            if not self._poly_is_drawing:
                self._poly_is_drawing = True
                self._poly_points_widget = []
                self._poly_preview_pt = None

            self._poly_points_widget.append(event.pos())
            self.update()
            return

    def mouseMoveEvent(self, event) -> None:
        if self._tool == "none":
            return
        if not self._target_rect:
            return

        if self._tool in ("rect", "circle", "cross"):
            if not self._drawing:
                return
            self._current_pt = event.pos()
            self.update()
            return

        if self._tool == "polygon":
            if not self._poly_is_drawing:
                return
            self._poly_preview_pt = event.pos()
            self.update()
            return

    def mouseReleaseEvent(self, event) -> None:
        if self._tool == "none":
            return
        if not self._target_rect or not self._pixmap_original:
            return

        if self._tool == "rect":
            if event.button() != Qt.MouseButton.LeftButton:
                return
            if not self._drawing or not self._start_pt or not self._current_pt:
                return
            self._drawing = False

            rect_widget = QRect(self._start_pt, self._current_pt).normalized()
            rect_widget = rect_widget.intersected(self._target_rect)

            rect_image = self._widget_rect_to_image_rect(rect_widget)
            if rect_image is None or rect_image.width() < 2 or rect_image.height() < 2:
                self._rect_image = None
                self.roiChanged.emit(None)
                self.update()
                return

            self._rect_image = rect_image
            self._circle_image = None
            self._poly_image = None

            payload = {
                "type": "rect",
                "x": rect_image.x(),
                "y": rect_image.y(),
                "w": rect_image.width(),
                "h": rect_image.height(),
            }
            self.roiChanged.emit(payload)
            self.update()
            return

        if self._tool == "circle":
            if event.button() != Qt.MouseButton.LeftButton:
                return
            if not self._drawing or not self._start_pt or not self._current_pt:
                return
            self._drawing = False

            c = self._circle_from_drag_widget_to_image(self._start_pt, self._current_pt)
            if c is None:
                self._circle_image = None
                self.roiChanged.emit(None)
                self.update()
                return

            cx, cy, r = c
            if r < 2:
                self._circle_image = None
                self.roiChanged.emit(None)
                self.update()
                return

            self._circle_image = (cx, cy, r)
            self._rect_image = None
            self._poly_image = None

            payload = {"type": "circle", "cx": cx, "cy": cy, "r": r}
            self.roiChanged.emit(payload)
            self.update()
            return

        if self._tool == "cross":
            if event.button() != Qt.MouseButton.LeftButton:
                return
            if not self._drawing or not self._start_pt or not self._current_pt:
                return
            self._drawing = False

            p0 = self._widget_point_to_image_point(self._start_pt)
            p1 = self._widget_point_to_image_point(self._current_pt)
            if p0 is None or p1 is None:
                self.update()
                return

            x0, y0 = p0
            x1, y1 = p1
            if abs(x1 - x0) + abs(y1 - y0) < 2:
                self.update()
                return

            self._sections_image.append((x0, y0, x1, y1))
            self._active_section_index = len(self._sections_image) - 1  # new one becomes active

            self.crossSectionsChanged.emit(self.get_cross_sections_payload())
            self.activeCrossSectionChanged.emit(self._active_section_index)
            self.update()
            return

    def mouseDoubleClickEvent(self, event) -> None:
        if self._tool != "polygon":
            return
        if not self._target_rect or not self._pixmap_original:
            return
        if not self._poly_is_drawing:
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return

        if len(self._poly_points_widget) < 3:
            self._poly_is_drawing = False
            self._poly_points_widget = []
            self._poly_preview_pt = None
            self._poly_image = None
            self.roiChanged.emit(None)
            self.update()
            return

        pts_img = []
        for ptw in self._poly_points_widget:
            p = self._widget_point_to_image_point(ptw)
            if p is not None:
                pts_img.append(p)

        if len(pts_img) < 3:
            self._poly_is_drawing = False
            self._poly_points_widget = []
            self._poly_preview_pt = None
            self._poly_image = None
            self.roiChanged.emit(None)
            self.update()
            return

        self._poly_image = pts_img
        self._rect_image = None
        self._circle_image = None

        self._poly_is_drawing = False
        self._poly_points_widget = []
        self._poly_preview_pt = None

        payload = {"type": "polygon", "points": [[x, y] for (x, y) in pts_img]}
        self.roiChanged.emit(payload)
        self.update()

    # ---------- conversions ----------
    def _update_scaled_pixmap(self) -> None:
        if not self._pixmap_original:
            self._pixmap_scaled = None
            self._target_rect = None
            return

        scaled = self._pixmap_original.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._pixmap_scaled = scaled

        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        self._target_rect = QRect(x, y, scaled.width(), scaled.height())

    def _widget_rect_to_image_rect(self, r: QRect) -> Optional[QRect]:
        if not self._pixmap_original or not self._pixmap_scaled or not self._target_rect:
            return None

        iw, ih = self._pixmap_original.width(), self._pixmap_original.height()
        sw, sh = self._target_rect.width(), self._target_rect.height()

        rx = r.x() - self._target_rect.x()
        ry = r.y() - self._target_rect.y()

        scale_x = iw / sw
        scale_y = ih / sh

        x = int(round(rx * scale_x))
        y = int(round(ry * scale_y))
        w = int(round(r.width() * scale_x))
        h = int(round(r.height() * scale_y))

        x = max(0, min(x, iw - 1))
        y = max(0, min(y, ih - 1))
        w = max(1, min(w, iw - x))
        h = max(1, min(h, ih - y))

        return QRect(x, y, w, h)

    def _image_rect_to_widget_rect(self, r: QRect) -> Optional[QRect]:
        if not self._pixmap_original or not self._pixmap_scaled or not self._target_rect:
            return None

        iw, ih = self._pixmap_original.width(), self._pixmap_original.height()
        sw, sh = self._target_rect.width(), self._target_rect.height()

        scale_x = sw / iw
        scale_y = sh / ih

        x = int(round(r.x() * scale_x)) + self._target_rect.x()
        y = int(round(r.y() * scale_y)) + self._target_rect.y()
        w = int(round(r.width() * scale_x))
        h = int(round(r.height() * scale_y))
        return QRect(x, y, w, h)

    def _widget_point_to_image_point(self, ptw: QPoint) -> Optional[Tuple[int, int]]:
        if not self._pixmap_original or not self._pixmap_scaled or not self._target_rect:
            return None
        if not self._target_rect.contains(ptw):
            return None

        iw, ih = self._pixmap_original.width(), self._pixmap_original.height()
        sw, sh = self._target_rect.width(), self._target_rect.height()
        scale_x = iw / sw
        scale_y = ih / sh

        rx = ptw.x() - self._target_rect.x()
        ry = ptw.y() - self._target_rect.y()

        x = int(round(rx * scale_x))
        y = int(round(ry * scale_y))
        x = max(0, min(x, iw - 1))
        y = max(0, min(y, ih - 1))
        return (x, y)

    def _image_point_to_widget_point(self, x: int, y: int) -> Optional[QPoint]:
        if not self._pixmap_original or not self._pixmap_scaled or not self._target_rect:
            return None
        iw, ih = self._pixmap_original.width(), self._pixmap_original.height()
        sw, sh = self._target_rect.width(), self._target_rect.height()
        scale_x = sw / iw
        scale_y = sh / ih

        wx = int(round(x * scale_x)) + self._target_rect.x()
        wy = int(round(y * scale_y)) + self._target_rect.y()
        return QPoint(wx, wy)

    # ---------- circle helpers ----------
    def _circle_widget_rect_from_drag(self, start: QPoint, end: QPoint) -> Optional[QRect]:
        if not self._target_rect:
            return None
        end_clamped = QPoint(
            max(self._target_rect.left(), min(end.x(), self._target_rect.right())),
            max(self._target_rect.top(), min(end.y(), self._target_rect.bottom())),
        )
        dx = end_clamped.x() - start.x()
        dy = end_clamped.y() - start.y()
        r = int((dx * dx + dy * dy) ** 0.5)
        return QRect(start.x() - r, start.y() - r, 2 * r, 2 * r)

    def _circle_from_drag_widget_to_image(self, start: QPoint, end: QPoint) -> Optional[Tuple[int, int, int]]:
        if not self._target_rect or not self._pixmap_original:
            return None

        c_img = self._widget_point_to_image_point(start)
        if c_img is None:
            return None

        end_img = self._widget_point_to_image_point(end)
        if end_img is None:
            end = QPoint(
                max(self._target_rect.left(), min(end.x(), self._target_rect.right())),
                max(self._target_rect.top(), min(end.y(), self._target_rect.bottom())),
            )
            end_img = self._widget_point_to_image_point(end)
            if end_img is None:
                return None

        cx, cy = c_img
        ex, ey = end_img
        dx = ex - cx
        dy = ey - cy
        r = int((dx * dx + dy * dy) ** 0.5)

        iw, ih = self._pixmap_original.width(), self._pixmap_original.height()
        r = min(r, cx, cy, iw - 1 - cx, ih - 1 - cy)
        r = max(0, r)
        return (cx, cy, r)

    def _circle_image_to_widget_rect(self, c: Tuple[int, int, int]) -> Optional[QRect]:
        if not self._pixmap_original or not self._pixmap_scaled or not self._target_rect:
            return None
        cx, cy, r = c

        iw, ih = self._pixmap_original.width(), self._pixmap_original.height()
        sw, sh = self._target_rect.width(), self._target_rect.height()
        scale_x = sw / iw
        scale_y = sh / ih

        wx = int(round(cx * scale_x)) + self._target_rect.x()
        wy = int(round(cy * scale_y)) + self._target_rect.y()
        wrx = int(round(r * scale_x))
        wry = int(round(r * scale_y))

        return QRect(wx - wrx, wy - wry, 2 * wrx, 2 * wry)

    def _poly_image_to_widget_poly(self, pts_img: List[Tuple[int, int]]) -> Optional[QPolygon]:
        if not self._pixmap_original or not self._pixmap_scaled or not self._target_rect:
            return None
        iw, ih = self._pixmap_original.width(), self._pixmap_original.height()
        sw, sh = self._target_rect.width(), self._target_rect.height()
        scale_x = sw / iw
        scale_y = sh / ih

        pts = []
        for (x, y) in pts_img:
            wx = int(round(x * scale_x)) + self._target_rect.x()
            wy = int(round(y * scale_y)) + self._target_rect.y()
            pts.append(QPoint(wx, wy))
        return QPolygon(pts)
