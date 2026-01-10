# core/analysis/intensity_metrics.py
from __future__ import annotations

from typing import Dict
import numpy as np


def compute_intensity_metrics_array(arr: np.ndarray) -> Dict[str, float]:
    """
    Computes:
      N = sum(I)
      D = sum(I^2)
      PR = (sum(I))^2 / sum(I^2)  (Participation Ratio style)
    Works for grayscale or RGB (RGB is converted to luminance first).
    """
    if arr.ndim == 3:
        # luminance
        arr = (0.2126 * arr[..., 0] + 0.7152 * arr[..., 1] + 0.0722 * arr[..., 2]).astype(np.float32)
    else:
        arr = arr.astype(np.float32)

    arr = np.clip(arr, 0, None)
    N = float(np.sum(arr))
    D = float(np.sum(arr * arr))
    PR = float((N * N) / D) if D > 0 else 0.0
    return {"N": N, "D": D, "PR": PR}
