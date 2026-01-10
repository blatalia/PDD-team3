# core/io/filename_parser.py
from __future__ import annotations

import re
from typing import Any, Dict

_PATTERNS = [
    re.compile(r"(?P<key>[A-Za-z]+)\s*=\s*(?P<val>-?\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z]+)"),
    re.compile(r"(?P<key>[A-Za-z]+)[_\-](?P<val>-?\d+(?:\.\d+)?)(?P<unit>[A-Za-z]+)"),
    re.compile(r"(?P<key>[A-Za-z]+)(?P<val>-?\d+(?:\.\d+)?)(?P<unit>[A-Za-z]+)"),
]


def parse_parameters_from_filename(filename: str) -> Dict[str, Any]:
    """
    Returns a dict of extracted parameters, e.g. {"I_mA": 120, "T_C": 22}
    Very simple parser
    """
    base = filename.rsplit(".", 1)[0]
    params: Dict[str, Any] = {}

    for pat in _PATTERNS:
        for m in pat.finditer(base):
            key = m.group("key")
            val = float(m.group("val"))
            unit = m.group("unit")

            # Normalize keys a bit
            norm_key = f"{key}_{unit}"
            # avoid overwriting if duplicates
            if norm_key not in params:
                params[norm_key] = val

    return params
