# core/worker_tasks.py
from pathlib import Path
from core.algorithms import run_algorithm


def process_one_image(algorithm: str, image_path_str: str) -> str:
    """
    Runs the selected algorithm for exactly one image.
    Returns a short text result (string).
    """
    p = Path(image_path_str)
    return run_algorithm(algorithm, [p])
