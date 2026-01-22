# core/analysis/contrast_metrics.py
from __future__ import annotations

from typing import Dict
import numpy as np


def compute_contrast_metrics_array(gray: np.ndarray) -> Dict[str, float]:
    """
    Contrast metrics on grayscale array:
      - Michelson: (Imax - Imin) / (Imax + Imin)
      - RMS contrast: standard deviation of intensity (std)
      - Std/Mean: coefficient of variation (std / mean)
      - Histogram spread: (p95 - p5) / (p95 + p5)
    """
    g = gray.astype(np.float32)
    g = np.clip(g, 0, None)

    imin = float(np.min(g))
    imax = float(np.max(g))
    michelson = float((imax - imin) / (imax + imin)) if (imax + imin) > 0 else 0.0

    mean = float(np.mean(g))
    std = float(np.std(g))

    # RMS contrast = standard deviation
    rms = std

    # Relative contrast / speckle contrast
    std_mean = float(std / mean) if mean != 0 else 0.0

    p5 = float(np.percentile(g, 5))
    p95 = float(np.percentile(g, 95))
    hist_spread = float((p95 - p5) / (p95 + p5)) if (p95 + p5) > 0 else 0.0

    return {
        "michelson": michelson,
        "rms": rms,
        "hist_spread": hist_spread,
        "std_mean": std_mean,
    }

