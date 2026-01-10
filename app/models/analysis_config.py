# app/models/analysis_config.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass(frozen=True)
class AnalysisConfig:
    algorithm: str
    export_txt: bool = True

    # ROI payload is a simple dict so it's ProcessPool-safe.
    roi: Optional[Dict[str, Any]] = None

    # Cross-sections payload: list of lines in IMAGE coords:
    # [{"x0":..,"y0":..,"x1":..,"y1":..}, ...]
    cross_sections: Optional[List[Dict[str, float]]] = None
    profile_samples: int = 200
