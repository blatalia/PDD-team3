# core/worker_tasks.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, List

from core.algorithms import run_algorithm_on_path


def process_one_image_task(
    algorithm: str,
    image_path_str: str,
    roi_payload: Optional[Dict[str, Any]] = None,
    cross_sections: Optional[List[Dict[str, float]]] = None,
    profile_samples: int = 200,
) -> Dict[str, Any]:
    p = Path(image_path_str)
    try:
        return run_algorithm_on_path(
            algorithm,
            p,
            roi_payload=roi_payload,
            cross_sections=cross_sections,
            profile_samples=profile_samples,
        )
    except Exception as e:
        return {"filename": p.name, "path": str(p), "error": f"{type(e).__name__}: {e!r}"}
