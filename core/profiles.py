# core/profiles.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
import numpy as np


@dataclass(frozen=True)
class LineSection:
    x0: float
    y0: float
    x1: float
    y1: float
    samples: int = 200


def _to_grayscale(arr: np.ndarray) -> np.ndarray:
    if arr.ndim == 2:
        return arr.astype(np.float32)
    if arr.ndim == 3:
        return (0.2126 * arr[..., 0] + 0.7152 * arr[..., 1] + 0.0722 * arr[..., 2]).astype(np.float32)
    raise ValueError("Unsupported image array shape.")


def extract_line_profile(arr: np.ndarray, line: LineSection) -> Tuple[np.ndarray, np.ndarray]:
    """
    Bilinear sampled profile along a line.
    Returns (t, intensity) where t is in [0,1].
    """
    gray = _to_grayscale(arr)
    h, w = gray.shape[:2]

    n = int(line.samples)
    n = max(2, min(n, 5000))  # sanity

    t = np.linspace(0.0, 1.0, n, dtype=np.float32)
    xs = line.x0 + (line.x1 - line.x0) * t
    ys = line.y0 + (line.y1 - line.y0) * t

    xs = np.clip(xs, 0, w - 1)
    ys = np.clip(ys, 0, h - 1)

    x0 = np.floor(xs).astype(int)
    y0 = np.floor(ys).astype(int)
    x1 = np.clip(x0 + 1, 0, w - 1)
    y1 = np.clip(y0 + 1, 0, h - 1)

    dx = xs - x0
    dy = ys - y0

    Ia = gray[y0, x0]
    Ib = gray[y0, x1]
    Ic = gray[y1, x0]
    Id = gray[y1, x1]

    intens = (
        Ia * (1 - dx) * (1 - dy)
        + Ib * dx * (1 - dy)
        + Ic * (1 - dx) * dy
        + Id * dx * dy
    ).astype(np.float32)

    return t, intens
