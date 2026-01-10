# core/params.py
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional, Tuple


def _to_float(s: str) -> Optional[float]:
    try:
        return float(s.replace(",", "."))
    except Exception:
        return None


# --- SI prefixes (mA -> A, mV -> V, µs -> s, etc.)
_SI_PREFIX = {
    "p": 1e-12,
    "n": 1e-9,
    "u": 1e-6,
    "µ": 1e-6,
    "μ": 1e-6,
    "m": 1e-3,
    "k": 1e3,
    "M": 1e6,
    "G": 1e9,
}


def _apply_si_prefix(value: float, unit: str) -> Tuple[float, str]:
    unit = unit.replace("μ", "µ")
    if len(unit) >= 2 and unit[0] in _SI_PREFIX and unit[1:].isalpha():
        return value * _SI_PREFIX[unit[0]], unit[1:]
    return value, unit


# --- normalize / aliases
# may extend this list freely.
_ALIAS = {
    # current
    "i": "I",
    "prad": "I",
    "current": "I",
    "curr": "I",
    "ia": "I",
    "ib": "I",
    # voltage
    "u": "U",
    "v": "U",
    "voltage": "U",
    # temperature
    "t": "t",      # time
    "time": "t",
    "temp": "T",   # temperature
    "temperature": "T",
    "tt": "T",
    "t_c": "T",
    # misc
    "iso": "ISO",
    "x": "x",
    "y": "y",
    "light": "light",
}


def _canon_key(key: str) -> str:
    k = key.strip()
    if not k:
        return k
    low = k.lower()
    return _ALIAS.get(low, k)


def _set_param(params: Dict[str, float], key: str, value: float) -> None:
    key = _canon_key(key)
    if not key:
        return
    params[key] = float(value)


# ------------------ regexes ------------------

_NUM = r"[-+]?\d+(?:[.,]\d+)?"

# key=value (allow digits in key here)
_PAT_EQ = re.compile(rf"(?P<key>[A-Za-z][A-Za-z0-9]*)\s*=\s*(?P<val>{_NUM})\s*(?P<unit>[A-Za-z%µμ]*)")

# key-val with separator (prad-5mA, light-4, I-0.5A)
_PAT_KEYVAL = re.compile(rf"(?P<key>[A-Za-z][A-Za-z0-9]*)\s*[-_ ]\s*(?P<val>{_NUM})\s*(?P<unit>[A-Za-z%µμ]*)")

# CRITICAL WYJEBANIEC
_PAT_GLUE = re.compile(rf"(?P<key>[A-Za-z]+)(?P<val>{_NUM})(?P<unit>[A-Za-z%µμ]*)")

# x56y33 packed coords
_PAT_XY = re.compile(rf"(?:^|[_-])x(?P<x>{_NUM})(?:[_-]?)y(?P<y>{_NUM})(?:$|[_-])", re.IGNORECASE)

# stand-alone value+unit token: 0.40A, 800mA, 1.95V, 30C, 1.25s
_PAT_VALUNIT = re.compile(rf"^(?P<val>{_NUM})(?P<unit>[A-Za-z%µμ]+)$")

_DEFAULT_KEY_FOR_UNIT = {
    "A": "I",
    "V": "U",
    "C": "T",
    "K": "T",
    "s": "t",
    "ms": "t",
    "us": "t",
    "µs": "t",
    "ns": "t",
}

# Only accept unitless glued keys that are meaningful
_ALLOW_NO_UNIT_KEYS = {"ISO", "x", "y", "I", "U", "T", "t"}


def parse_params_from_filename(filename: str) -> Dict[str, float]:
    """
    Extracts numeric experimental parameters from filenames like:
      Dallas1_x56y33_0.40A_1.95V_T30C_trybS_t1.2500s_light-4.JPG
      Dallas_1_x56_y32_T50C_800mA ... prad-5mA_ISO100_06

    Output: dict of {key: numeric_value}
    - SI prefixes are converted to base (mA->A, mV->V, µs->s, etc.)
    - Value+unit tokens get default keys (A->I, V->U, C->T, s->t)
    - Aliases normalize common names into I/U/T/t/ISO/x/y
    """
    stem = Path(filename).stem

    # tokenize: split on underscores/spaces; keep hyphens inside tokens for prad-5mA etc.
    tokens = re.split(r"[ _]+", stem)

    params: Dict[str, float] = {}

    # 1) packed coords
    for tok in tokens:
        mxy = _PAT_XY.search(tok)
        if mxy:
            xv = _to_float(mxy.group("x"))
            yv = _to_float(mxy.group("y"))
            if xv is not None:
                _set_param(params, "x", xv)
            if yv is not None:
                _set_param(params, "y", yv)

    # 2) key=value
    for tok in tokens:
        for m in _PAT_EQ.finditer(tok):
            key = m.group("key")
            val = _to_float(m.group("val"))
            unit = (m.group("unit") or "").strip()
            if val is None:
                continue
            if unit:
                val2, _base = _apply_si_prefix(val, unit)
                _set_param(params, key, val2)
            else:
                _set_param(params, key, val)

    # 3) key-val (separator)
    for tok in tokens:
        for m in _PAT_KEYVAL.finditer(tok):
            key = m.group("key")
            val = _to_float(m.group("val"))
            unit = (m.group("unit") or "").strip()
            if val is None:
                continue
            if unit:
                val2, _base = _apply_si_prefix(val, unit)
                _set_param(params, key, val2)
            else:
                _set_param(params, key, val)

    # 4) glued: T30C, t1.2500s, ISO100, I68, U1.95V (if it happens)
    for tok in tokens:
        for m in _PAT_GLUE.finditer(tok):
            key = m.group("key")
            val = _to_float(m.group("val"))
            unit = (m.group("unit") or "").strip()
            if val is None:
                continue

            if unit:
                val2, _base = _apply_si_prefix(val, unit)
                _set_param(params, key, val2)
            else:
                ck = _canon_key(key)
                if ck in _ALLOW_NO_UNIT_KEYS:
                    _set_param(params, ck, val)

    # 5) stand-alone value+unit token
    for tok in tokens:
        m = _PAT_VALUNIT.match(tok)
        if not m:
            continue
        val = _to_float(m.group("val"))
        unit = (m.group("unit") or "").strip()
        if val is None or not unit:
            continue

        val2, base_unit = _apply_si_prefix(val, unit)

        # choose default key based on unit (prefer full unit, then base unit)
        key = _DEFAULT_KEY_FOR_UNIT.get(unit) or _DEFAULT_KEY_FOR_UNIT.get(base_unit) or base_unit
        _set_param(params, key, val2)

    return params
