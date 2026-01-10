# core/export/profile_exporter.py
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple, List
import numpy as np


def export_profiles_txt(
    filename_stem: str,
    profiles: List[Tuple[np.ndarray, np.ndarray]],
    out_dir: Path = Path("results/profiles"),
) -> Path:
    """
    Saves profiles as multiple TXT files:
      <stem>__sec01.txt, <stem>__sec02.txt, ...
    Each file: two columns: t, intensity
    Returns the output directory.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    for idx, (t, y) in enumerate(profiles, start=1):
        out_path = out_dir / f"{filename_stem}__sec{idx:02d}.txt"
        lines = ["t\tintensity"]
        for ti, yi in zip(t.tolist(), y.tolist()):
            lines.append(f"{ti}\t{yi}")
        out_path.write_text("\n".join(lines), encoding="utf-8")

    return out_dir
