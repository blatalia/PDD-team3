# core/export/txt_exporter.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def export_results_txt(results: List[Dict[str, Any]], out_dir: Path = Path("results")) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.txt"

    # Collect keys in a stable order
    # Always include filename first
    all_keys = set()
    for r in results:
        all_keys.update(r.keys())
    # prefer common fields
    preferred = ["filename", "color_mode", "summary", "N", "D", "PR", "michelson", "rms", "hist_spread", "std_mean", "error", "path"]
    keys = [k for k in preferred if k in all_keys] + sorted([k for k in all_keys if k not in preferred])

    lines = []
    lines.append("\t".join(keys))
    for r in results:
        row = []
        for k in keys:
            v = r.get(k, "")
            row.append(str(v))
        lines.append("\t".join(row))

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
