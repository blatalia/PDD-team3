# app/controllers/app_controller.py
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from app.models.dataset import Dataset
from core.io.filename_parser import parse_parameters_from_filename


class AppController:
    """
    Lightweight controller.
    Later: will also manage ROI/cross-sections + plotting/export in a cleaner way.
    """

    def build_dataset(self, paths: Iterable[Path]) -> Dataset:
        records = []
        for p in paths:
            params = parse_parameters_from_filename(p.name)
            records.append((p, params))
        return Dataset.from_paths(records)
