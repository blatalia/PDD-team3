# core/analysis/contrast_definitions.py
from __future__ import annotations

DEFINITIONS_TEXT = """\
Contrast metrics (grayscale array g):

1) Michelson contrast
   C_M = (I_max - I_min) / (I_max + I_min)
   where:
     I_max = max(g)
     I_min = min(g)

2) RMS contrast (standard deviation)
   C_RMS = std(g)

3) Std/Mean (coefficient of variation / speckle contrast)
   C_S = std(g) / mean(g)

4) Histogram spread (robust contrast using percentiles)
   C_H = (P95 - P5) / (P95 + P5)
   where:
     P5  = 5th percentile of g
     P95 = 95th percentile of g

Notes:
- g is clipped to non-negative values (g = clip(g, 0, +inf)).
- If a denominator is 0, the metric is returned as 0.0.
"""
