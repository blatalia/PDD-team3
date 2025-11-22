# core/algorithms.py
from pathlib import Path
from typing import List
import logging

from core.filters import apply_red_filter
from core.intensity import compute_intensity_metrics

# algorithms list
ALGO_RED = "red" # mock algorithm
ALGO_INTENSITY = "intensity" # mock algorithm


def run_intensity_algorithm(image_paths: List[Path]) -> str:
    logger = logging.getLogger(__name__)

    lines = []
    for img in image_paths:
        try:
            N, D, PR = compute_intensity_metrics(img)
            line = f"{img.name}: PR={PR:.4f}, N={N:.2f}, D={D:.2f}"
            lines.append(line)
            logger.info("Intensity: %s -> %s", img, line)
        except Exception as e:
            logger.error("Intensity ERROR on %s: %s", img, e)
            lines.append(f"{img.name}: ERROR ({e})")

    if not lines:
        return "Intensity failed, could not resolve any file"

    return "Intensity:\n" + "\n".join(lines)


# main function, runs certain algotithm based on input
# TO DO dwa algorytmy i więcej na raz po sobie
def run_algorithm(algorithm: str, image_paths: List[Path]) -> str:
    if algorithm == ALGO_RED:
        return apply_red_filter(image_paths)
    elif algorithm == ALGO_INTENSITY:
        return run_intensity_algorithm(image_paths)
    else:
        logging.getLogger(__name__).error("Unknown algorithm: %s", algorithm)
        return f"Unknown algorithm: {algorithm}"
