# core/export/pdf_report.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet


_PRETTY_NAMES = {
    "I": "Current [A]",
    "U": "Voltage [V]",
    "T": "Temperature [°C]",
    "t": "Exposure time [s]",
    "ISO": "ISO",
    "light": "Light mode",
    "x": "X position",
    "y": "Y position",

    # metrics
    "D": "Total intensity",
    "N": "Pixel count",
    "PR": "Mean intensity",
    "michelson": "Michelson contrast",
    "rms": "RMS contrast",
}



def _collect_columns(results: List[Dict[str, Any]]) -> tuple[list[str], list[str]]:
    """
    Returns (param_keys, metric_keys)
    """
    param_keys: Set[str] = set()
    metric_keys: Set[str] = set()

    for r in results:
        if not isinstance(r, dict) or "error" in r:
            continue

        params = r.get("params", {})
        if isinstance(params, dict):
            for k, v in params.items():
                if isinstance(v, (int, float)):
                    param_keys.add(k)

        for k, v in r.items():
            if k in ("filename", "path", "color_mode", "roi", "params", "summary", "profiles", "error"):
                continue
            if isinstance(v, (int, float)):
                metric_keys.add(k)

    return sorted(param_keys), sorted(metric_keys)


def export_pdf_report(
    results: List[Dict[str, Any]],
    out_dir: Path = Path("results"),
    title: str = "Analysis report",
    plot_png_path: Optional[Path] = None,
) -> Path:
    """
    Creates a PDF report containing:
    - title + timestamp
    - table of filename + params + metrics
    - optional plot image appended
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"report_{ts}.pdf"

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(title, styles["Title"]))
    story.append(Paragraph(f"Generated: {datetime.now().isoformat(timespec='seconds')}", styles["Normal"]))
    story.append(Spacer(1, 6 * mm))

    # Prepare table
    param_keys, metric_keys = _collect_columns(results)

    # --- keep table readable: limit how many columns go into PDF
    # may tweak these numbers.
    param_keys = param_keys[:4]     # max 4 params in PDF
    metric_keys = metric_keys[:6]   # max 6 metrics in PDF

    # Show status column only if any error exists
    has_any_error = any(isinstance(r, dict) and r.get("error") for r in results)

    # header = ["filename"] + [f"P:{k}" for k in param_keys] + metric_keys

    def _pretty(k: str) -> str:
        return _PRETTY_NAMES.get(k, k)

    header = (
        ["Filename"]
        + [_pretty(k) for k in param_keys]
        + [_pretty(k) for k in metric_keys]
    )

    if has_any_error:
        header += ["status"]

    data = [header]

    for r in results:
        if not isinstance(r, dict):
            continue

        row = []
        row.append(str(r.get("filename", "")))

        params = r.get("params", {})
        for k in param_keys:
            v = params.get(k) if isinstance(params, dict) else ""
            row.append(f"{v:.6g}" if isinstance(v, (int, float)) else "")

        for k in metric_keys:
            v = r.get(k)
            row.append(f"{v:.6g}" if isinstance(v, (int, float)) else "")

        if has_any_error:
            if "error" in r and r.get("error"):
                row.append("ERROR")
            else:
                row.append("OK")

        data.append(row)

    # --- column widths (prevents stretching)
    # A4 width minus margins: doc uses 15mm left + 15mm right
    # So safe width is about 180mm.
    total_w = 180 * mm
    n_cols = len(header)

    # Give filename more room, split remaining evenly.
    filename_w = 55 * mm
    remaining = max(10 * mm, total_w - filename_w)
    other_w = remaining / max(1, (n_cols - 1))

    col_widths = [filename_w] + [other_w] * (n_cols - 1)

    tbl = Table(data, repeatRows=1, colWidths=col_widths)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d1a4a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                # align numeric-ish columns to right for readability (everything except filename)
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ]
        )
    )


    story.append(Paragraph("Results table", styles["Heading2"]))
    story.append(Spacer(1, 2 * mm))
    story.append(tbl)
    story.append(Spacer(1, 8 * mm))

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "<b>Notes:</b> Parameters are extracted automatically from file names.",
        styles["Italic"]
    ))

    # Optional plot image
    if plot_png_path and plot_png_path.exists():
        story.append(Paragraph("Plot", styles["Heading2"]))
        story.append(Spacer(1, 2 * mm))

        # Fit image into a box (prevents cropping when image is too tall)
        img = RLImage(str(plot_png_path))

        max_w = 180 * mm            # page width minus margins
        max_h = 110 * mm            # SAFE height for plot section (prevents cutting)

        iw, ih = float(img.imageWidth), float(img.imageHeight)
        if iw > 0 and ih > 0:
            scale = min(max_w / iw, max_h / ih)
            img.drawWidth = iw * scale
            img.drawHeight = ih * scale

        img.hAlign = "CENTER"
        story.append(img)

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=title,
    )
    doc.build(story)

    return out_path
