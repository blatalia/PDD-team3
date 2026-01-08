# core/contrasts.py
import numpy as np
from typing import Tuple


def compute_contrast(array: np.ndarray) -> Tuple[float, float, float, float]:
    """
    Compute contrast metrics from a grayscale numpy array.

    Returns:
    michelson_contrast, rms_contrast, histogram_spread_contrast, std_mean_contrast
    """
    array_grey = np.asarray(array).astype(float)

    I_max = array_grey.max()
    I_min = array_grey.min()

    michelson_contrast = (I_max - I_min) / (I_max + I_min) if (I_max + I_min) != 0 else float("inf")

    mean_intensity = np.mean(array_grey)
    rms_contrast = np.sqrt(np.mean((array_grey - mean_intensity) ** 2))

    q1 = np.percentile(array_grey, 25)
    q3 = np.percentile(array_grey, 75)
    histogram_spread_contrast = (q3 - q1) / (I_max - I_min) if (I_max - I_min) != 0 else 0.0

    mean_I = array_grey.mean()
    std_I = array_grey.std()
    std_mean_contrast = std_I / mean_I if mean_I != 0 else float("inf")

    return michelson_contrast, rms_contrast, histogram_spread_contrast, std_mean_contrast
