# core/algorithms.py
from pathlib import Path
from typing import List
import logging

from core.filters import apply_red_filter
from core.intensity import compute_intensity_metrics
import numpy as np
from PIL import Image
from core.contrasts import compute_contrast


# algorithms list
ALGO_RED = "red" # mock algorithm
ALGO_INTENSITY = "intensity" # mock algorithm
ALGO_SAVE_INTO_FILE = "save-into-file"
ALGO_CONTRAST = "contrast"


def run_contrast_single(image_path: Path) -> str:
    img = Image.open(image_path).convert("L")
    arr = np.array(img)

    michelson, rms, hist_spread, std_mean = compute_contrast(arr)

    return (
        f"{image_path.name}\n"
        f"Michelson Contrast: {michelson:.6f}\n"
        f"RMS Contrast: {rms:.6f}\n"
        f"Histogram Spread Contrast: {hist_spread:.6f}\n"
        f"Std/Mean Contrast: {std_mean:.6f}"
    )



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



import sys
import subprocess
import shutil
from pathlib import Path

SUPPORTED_EXTS = (".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp")


def _sync_input_folder_to_laser_photos(src_folder: Path, dst_folder: Path) -> int:
    """
    Copy supported image files from src_folder to dst_folder (non-recursive).
    Returns number of copied files.
    """
    dst_folder.mkdir(parents=True, exist_ok=True)

    # Clear destination folder to avoid mixing old data with new run
    for p in dst_folder.iterdir():
        if p.is_file():
            p.unlink()

    copied = 0
    for p in src_folder.iterdir():
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            shutil.copy2(p, dst_folder / p.name)
            copied += 1

    return copied


def run_stakeholder_analysis(input_folder: Path) -> str:
    """
    Runs script as a black-box subprocess.
    - Copies user's input images into save-into"/Laser photos/
    - Runs save-into"/save_file_into.py with cwd=ssave-into"
    - Reads save-into"/results/results.txt and returns it to GUI
    """
    logger = logging.getLogger(__name__)

    script_dir = Path(__file__).resolve().parents[1] / "save-into"
    script_path = script_dir / "save_into_file.py"
    laser_photos_dir = script_dir / "Laser photos"
    results_txt = script_dir / "results" / "results.txt"

    if not script_path.exists():
        return f"script not found: {script_path}"

    if not input_folder.exists() or not input_folder.is_dir():
        return f"Input folder is invalid: {input_folder}"

    copied = _sync_input_folder_to_laser_photos(input_folder, laser_photos_dir)
    if copied == 0:
        return (
            f"No supported images found in: {input_folder}\n"
            f"Supported extensions: {', '.join(SUPPORTED_EXTS)}"
        )

    logger.info("copied %d image(s) into %s", copied, laser_photos_dir)

    # Run script with working directory set to script_dir.
    cmd = [sys.executable, str(script_path)]
    logger.info("running subprocess: %s (cwd=%s)", cmd, script_dir)

    proc = subprocess.run(
        cmd,
        cwd=str(script_dir),
        capture_output=True,
        text=True,
    )

    # Prepare a readable report to show in GUI
    report_parts = []
    report_parts.append(f"subprocess exit code: {proc.returncode}")
    if proc.stdout.strip():
        report_parts.append("\n--- STDOUT ---\n" + proc.stdout.strip())
    if proc.stderr.strip():
        report_parts.append("\n--- STDERR ---\n" + proc.stderr.strip())

    if results_txt.exists():
        try:
            content = results_txt.read_text(encoding="utf-8", errors="replace")
            report_parts.append("\n--- results/results.txt ---\n" + content)
        except Exception as e:
            report_parts.append(f"\nCould not read results file: {results_txt}\nError: {e}")
    else:
        report_parts.append(f"\nResults file not found: {results_txt}")

    return "\n".join(report_parts)




# main function, runs certain algotithm based on input
# TO DO dwa algorytmy i więcej na raz po sobie
# def run_algorithm(algorithm: str, image_paths: List[Path]) -> str:
#     if algorithm == ALGO_RED:
#         return apply_red_filter(image_paths)
#     elif algorithm == ALGO_INTENSITY:
#         return run_intensity_algorithm(image_paths)
#     else:
#         logging.getLogger(__name__).error("Unknown algorithm: %s", algorithm)
#         return f"Unknown algorithm: {algorithm}"

def run_algorithm(algorithm: str, image_paths: List[Path], input_folder: Path | None = None) -> str:
    if algorithm == ALGO_RED:
        return apply_red_filter(image_paths)
    elif algorithm == ALGO_INTENSITY:
        return run_intensity_algorithm(image_paths)
    elif algorithm == ALGO_SAVE_INTO_FILE:
        if input_folder is None:
            return "analysis requires an input folder."
        return run_stakeholder_analysis(input_folder)
    elif algorithm == ALGO_CONTRAST:
        if not image_paths:
            return "Contrast: no image selected."
        return run_contrast_single(image_paths[0])

    else:
        logging.getLogger(__name__).error("Nieznany algorytm: %s", algorithm)
        return f"Nieznany algorytm: {algorithm}"

