# core/export/csv_exporter.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Set
import csv
from datetime import datetime


def export_results_csv(results: List[Dict[str, Any]], out_dir: Path = Path("results")) -> Path:
    """
    Exports a flat CSV:
      filename, <params.*>, <metric columns...>

    Notes:
    - params are expanded into columns like "param.T", "param.I"
    - nested non-numeric fields are skipped (roi, profiles)
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"results_{ts}.csv"

    ok = [r for r in results if isinstance(r, dict)]

    # Collect param keys
    param_keys: Set[str] = set()
    metric_keys: Set[str] = set()

    for r in ok:
        params = r.get("params", {})
        if isinstance(params, dict):
            for k, v in params.items():
                if isinstance(v, (int, float)):
                    param_keys.add(k)

        # metrics = numeric top-level keys excluding known non-metrics
        for k, v in r.items():
            if k in ("filename", "path", "color_mode", "roi", "params", "summary", "profiles", "error"):
                continue
            if isinstance(v, (int, float)):
                metric_keys.add(k)

    param_keys = set(sorted(param_keys))
    metric_keys = set(sorted(metric_keys))

    fieldnames = ["filename"] + [f"param.{k}" for k in sorted(param_keys)] + sorted(metric_keys) + ["error"]

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()

        for r in ok:
            row: Dict[str, Any] = {k: "" for k in fieldnames}
            row["filename"] = r.get("filename", "")

            params = r.get("params", {})
            if isinstance(params, dict):
                for k in param_keys:
                    v = params.get(k)
                    if isinstance(v, (int, float)):
                        row[f"param.{k}"] = v

            for k in metric_keys:
                v = r.get(k)
                if isinstance(v, (int, float)):
                    row[k] = v

            if "error" in r:
                row["error"] = r.get("error", "")

            w.writerow(row)

    return out_path
