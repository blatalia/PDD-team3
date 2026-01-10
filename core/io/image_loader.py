# core/io/image_loader.py
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}


def load_image(path: Path) -> Tuple[np.ndarray, str]:
    """
    Loads JPG/PNG/TIFF/BMP using Pillow.
    Returns: (numpy array, color_mode)
      - color_mode: "grayscale" or "rgb"
    """
    if path.suffix.lower() not in SUPPORTED_EXTS:
        raise ValueError(f"Unsupported extension: {path.suffix}")

    img = Image.open(path)

    # If grayscale-ish modes (including 16-bit), convert to 8-bit L for analysis consistency
    if img.mode in ("L", "I;16", "I", "F"):
        arr = np.array(img.convert("L"), dtype=np.float32)
        return arr, "grayscale"

    # everything else -> RGB
    img_rgb = img.convert("RGB")
    arr = np.array(img_rgb, dtype=np.float32)
    return arr, "rgb"
