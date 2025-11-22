# core/filters.py
from pathlib import Path
from typing import List
import logging

from PIL import Image


def apply_red_filter(image_paths: List[Path]) -> str:
    logger = logging.getLogger(__name__)

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    processed_files = []

    for src_path in image_paths:
        try:
            logger.info("Red filter processing %s", src_path)

            img = Image.open(src_path).convert("RGB")

            r, g, b = img.split()
            zero_channel = Image.new("L", img.size, 0)
            red_img = Image.merge("RGB", (r, zero_channel, zero_channel))

            dst_path = results_dir / src_path.name
            red_img.save(dst_path)

            processed_files.append(dst_path)
            logger.info("Red filter: saved %s", dst_path)
        except Exception as e:
            logger.error("Red filter: error during %s: %s", src_path, e)

    if not processed_files:
        return "Filtering: failed to process any file"

    return (
        f"Red Filter: processed {len(processed_files)} file(s).\n"
        f"Results saved in: {results_dir.resolve()}"
    )
