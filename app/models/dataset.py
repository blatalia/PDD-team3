# app/models/dataset.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


@dataclass
class ImageRecord:
    path: Path
    parameters: Dict[str, Any] = field(default_factory=dict)
    color_mode: str | None = None  # "grayscale" | "rgb"
    results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Dataset:
    records: List[ImageRecord]

    @staticmethod
    def from_paths(items: Iterable[Tuple[Path, Dict[str, Any]]]) -> "Dataset":
        recs = [ImageRecord(path=p, parameters=params) for (p, params) in items]
        return Dataset(records=recs)
