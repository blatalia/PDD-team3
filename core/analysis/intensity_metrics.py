# core/analysis/intensity_metrics.py
from __future__ import annotations

from typing import Dict
import numpy as np


def compute_intensity_metrics_array(arr: np.ndarray) -> dict:
    """
    Intensity metrics
    """
    if arr.ndim == 3:
        arr_gray = (
            0.2126 * arr[..., 0]
            + 0.7152 * arr[..., 1]
            + 0.0722 * arr[..., 2]
        ).astype(np.float64)
    else:
        arr_gray = arr.astype(np.float64)

    valid = np.isfinite(arr_gray)
    pixels = arr_gray[valid]

    if pixels.size == 0:
        return {
            "D_px": 0.0,
            "N_px": 0,
            "mean_px": 0.0,
            "PR": 0.0,
        }

    D_px = float(pixels.sum())
    N_px = int(pixels.size)
    mean_px = float(D_px / N_px)

    return {
        "D_px": D_px,
        "N_px": N_px,
        "mean_px": mean_px,
        "PR": mean_px,
    }
