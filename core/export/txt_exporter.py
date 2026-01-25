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

    all_keys = set()
    for r in results:
        if isinstance(r, dict):
            all_keys.update(r.keys())

    preferred = [
        "filename",
        "color_mode",

        "N_px",
        "D_px",
        "mean_px",

        "michelson",
        "rms",
        "hist_spread",
        "std_mean",

        "error",
        "summary",
        "path",
    ]

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
