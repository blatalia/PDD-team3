# core/roi.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw


@dataclass(frozen=True)
class RectROI:
    x: int
    y: int
    w: int
    h: int


@dataclass(frozen=True)
class CircleROI:
    cx: int
    cy: int
    r: int


@dataclass(frozen=True)
class PolygonROI:
    points: List[Tuple[int, int]]  # (x,y) in image coords


ROI = Union[RectROI, CircleROI, PolygonROI]


def clamp_rect_roi(roi: RectROI, width: int, height: int) -> RectROI:
    x = max(0, min(int(roi.x), width - 1))
    y = max(0, min(int(roi.y), height - 1))
    w = max(1, int(roi.w))
    h = max(1, int(roi.h))

    if x + w > width:
        w = max(1, width - x)
    if y + h > height:
        h = max(1, height - y)

    return RectROI(x=x, y=y, w=w, h=h)


def apply_rect_roi(arr: np.ndarray, roi: Optional[RectROI]) -> np.ndarray:
    """
    Crops array to ROI.
    Supports grayscale (H,W) and RGB (H,W,3).
    """
    if roi is None:
        return arr

    h, w = arr.shape[:2]
    r = clamp_rect_roi(roi, width=w, height=h)
    x0, y0 = r.x, r.y
    x1, y1 = r.x + r.w, r.y + r.h
    return arr[y0:y1, x0:x1]


def _mask_from_circle(width: int, height: int, roi: CircleROI) -> np.ndarray:
    img = Image.new("L", (width, height), 0)
    d = ImageDraw.Draw(img)
    x0 = roi.cx - roi.r
    y0 = roi.cy - roi.r
    x1 = roi.cx + roi.r
    y1 = roi.cy + roi.r
    d.ellipse([x0, y0, x1, y1], fill=255)
    return np.array(img, dtype=np.uint8)


def _mask_from_polygon(width: int, height: int, roi: PolygonROI) -> np.ndarray:
    img = Image.new("L", (width, height), 0)
    d = ImageDraw.Draw(img)
    d.polygon(list(roi.points), fill=255)
    return np.array(img, dtype=np.uint8)


def apply_mask_roi(arr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Applies a binary mask (H,W) to grayscale or RGB array.
    Outside ROI becomes 0.
    """
    m = (mask.astype(np.float32) / 255.0)
    if arr.ndim == 2:
        return arr * m
    if arr.ndim == 3:
        return arr * m[..., None]
    return arr


def apply_circle_roi(arr: np.ndarray, roi: Optional[CircleROI]) -> np.ndarray:
    if roi is None:
        return arr
    h, w = arr.shape[:2]
    # clamp radius best-effort
    r = max(0, int(roi.r))
    r = min(r, roi.cx, roi.cy, w - 1 - roi.cx, h - 1 - roi.cy)
    if r <= 0:
        return np.zeros_like(arr)
    mask = _mask_from_circle(w, h, CircleROI(roi.cx, roi.cy, r))
    return apply_mask_roi(arr, mask)


def apply_polygon_roi(arr: np.ndarray, roi: Optional[PolygonROI]) -> np.ndarray:
    if roi is None:
        return arr
    h, w = arr.shape[:2]
    if len(roi.points) < 3:
        return np.zeros_like(arr)
    mask = _mask_from_polygon(w, h, roi)
    return apply_mask_roi(arr, mask)


def apply_roi(arr: np.ndarray, roi: Optional[ROI]) -> np.ndarray:
    """
    Unified ROI apply:
      - Rect -> crop
      - Circle/Polygon -> mask (keeps full size)
    """
    if roi is None:
        return arr
    if isinstance(roi, RectROI):
        return apply_rect_roi(arr, roi)
    if isinstance(roi, CircleROI):
        return apply_circle_roi(arr, roi)
    if isinstance(roi, PolygonROI):
        return apply_polygon_roi(arr, roi)
    return arr
