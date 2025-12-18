# core/worker_tasks.py
from pathlib import Path
from core.algorithms import run_algorithm

def process_one_image(algorithm: str, image_path_str: str) -> str:
    """
    Runs the algorithm for exactly one image.
    Return a small string (status/path), not big arrays.
    """
    p = Path(image_path_str)
    # reuse your existing entrypoint, but for a single file
    return run_algorithm(algorithm, [p])
