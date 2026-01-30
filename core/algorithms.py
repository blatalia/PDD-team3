# core/algorithms.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, List
import numpy as np

from core.io.image_loader import load_image
from core.analysis.intensity_metrics import compute_intensity_metrics_array
from core.analysis.contrast_metrics import compute_contrast_metrics_array
from core.roi import RectROI, CircleROI, PolygonROI, apply_roi
from core.profiles import LineSection, extract_line_profile
from core.io.filename_parser import parse_parameters_from_filename

ALGO_INTENSITY = "intensity"
ALGO_CONTRAST = "contrast"
ALGO_PROFILES = "profiles"


def _roi_from_payload(roi_payload: Optional[Dict[str, Any]]):
    if not roi_payload:
        return None

    t = roi_payload.get("type")
    try:
        if t == "rect":
            return RectROI(
                x=int(roi_payload["x"]),
                y=int(roi_payload["y"]),
                w=int(roi_payload["w"]),
                h=int(roi_payload["h"]),
            )
        if t == "circle":
            return CircleROI(
                cx=int(roi_payload["cx"]),
                cy=int(roi_payload["cy"]),
                r=int(roi_payload["r"]),
            )
        if t == "polygon":
            pts = roi_payload.get("points", [])
            points = [(int(p[0]), int(p[1])) for p in pts]
            return PolygonROI(points=points)
    except Exception:
        return None

    return None


def _sections_from_payload(sections_payload: Optional[List[Dict[str, float]]], samples: int) -> List[LineSection]:
    if not sections_payload:
        return []
    out: List[LineSection] = []
    for s in sections_payload:
        try:
            out.append(
                LineSection(
                    x0=float(s["x0"]),
                    y0=float(s["y0"]),
                    x1=float(s["x1"]),
                    y1=float(s["y1"]),
                    samples=int(samples),
                )
            )
        except Exception:
            continue
    return out


def run_algorithm_on_path(
    algorithm: str,
    image_path: Path,
    roi_payload: Optional[Dict[str, Any]] = None,
    cross_sections: Optional[List[Dict[str, float]]] = None,
    profile_samples: int = 200,
) -> Dict[str, Any]:
    arr, color_mode = load_image(image_path)

    roi_obj = _roi_from_payload(roi_payload)
    arr_roi = apply_roi(arr, roi_obj)

    roi_info = roi_payload if roi_payload else None
    params = parse_parameters_from_filename(image_path.name)

    if algorithm == ALGO_INTENSITY:
        metrics = compute_intensity_metrics_array(arr_roi)

        n_px = int(metrics.get("N_px", 0))
        d_px = float(metrics.get("D_px", 0.0))
        mean_px = float(metrics.get("mean_px", 0.0))

        metrics["N"] = float(n_px)
        metrics["D"] = float(d_px)
        metrics["PR"] = float(mean_px)
        return {
            "filename": image_path.name,
            "path": str(image_path),
            "color_mode": color_mode,
            "roi": roi_info,
            "params": params,
            **metrics,
            "summary": f"mean_px={mean_px:.4f}, N_px={n_px}, D_px={d_px:.2f}",
        }



    if algorithm == ALGO_CONTRAST:
        if arr_roi.ndim == 3:
            arr_gray = (0.2126 * arr_roi[..., 0] + 0.7152 * arr_roi[..., 1] + 0.0722 * arr_roi[..., 2]).astype(np.float32)
        else:
            arr_gray = arr_roi.astype(np.float32)

        metrics = compute_contrast_metrics_array(arr_gray)
        return {
            "filename": image_path.name,
            "path": str(image_path),
            "color_mode": color_mode,
            "roi": roi_info,
            "params": params,
            **metrics,
            "summary": f"Michelson={metrics['michelson']:.6f}, RMS={metrics['rms']:.6f}",
        }

    if algorithm == ALGO_PROFILES:
        sections = _sections_from_payload(cross_sections, profile_samples)
        profiles = []
        for sec in sections:
            t, y = extract_line_profile(arr_roi, sec)
            profiles.append({"t": t.tolist(), "y": y.tolist()})

        return {
            "filename": image_path.name,
            "path": str(image_path),
            "color_mode": color_mode,
            "roi": roi_info,
            "params": params,
            "profiles": profiles,
            "summary": f"profiles={len(profiles)}",
        }

    raise ValueError(f"Unknown algorithm: {algorithm}")
