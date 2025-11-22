# core/intensity.py
from pathlib import Path
from typing import Tuple

from PIL import Image
import numpy as np


def compute_intensity_metrics(image_path: Path) -> Tuple[float, float, float]:
    image = Image.open(image_path)

    grey_scale = image.convert("L")
    array_grey = np.array(grey_scale).astype(float)

    sum_I = array_grey.sum()
    sum_I_sq = (array_grey ** 2).sum()

    numerator = sum_I ** 2
    denominator = sum_I_sq

    PR = numerator / denominator if denominator != 0 else float("inf")

    return numerator, denominator, PR
