# core/export/txt_exporter.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def export_results_txt(results: List[Dict[str, Any]], out_dir: Path = Path("results")) -> Path:
    """
    Export results to TXT using RAW pixel-domain intensity values.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.txt"

    # Collect keys in a stable order
    all_keys = set()
    for r in results:
        if isinstance(r, dict):
            all_keys.update(r.keys())

    # Preferred order for TXT (scientific, pixel-domain first)
    preferred = [
        "filename",
        "color_mode",

        # --- RAW pixel-domain intensity metrics ---
        "N_px",        # number of pixels
        "D_px",        # total intensity (pixel sum)
        "mean_px",     # mean intensity per pixel

        # --- contrast metrics ---
        "michelson",
        "rms",
        "hist_spread",
        "std_mean",

        # --- status / meta ---
        "error",
        "summary",
        "path",
    ]

    # Build final key list
    keys = [k for k in preferred if k in all_keys] + sorted(
        [k for k in all_keys if k not in preferred]
    )

    lines = []
    lines.append("\t".join(keys))

    for r in results:
        row = []
        for k in keys:
            v = r.get(k, "")
            if isinstance(v, float):
                row.append(f"{v:.6g}")
            else:
                row.append(str(v))
        lines.append("\t".join(row))

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
