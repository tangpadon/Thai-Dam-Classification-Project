"""Utility functions for data formatting, date localization, and risk classification."""

from typing import Any, Optional, Dict
from views.constants import STATUS_THEMES


def classify_by_percent(pct: float) -> str:
    """Classify storage percent into drought, flood, or normal risk status."""
    if pct < 30:
        return "drought"
    elif pct > 80:
        return "flood"
    return "normal"


def get_status_theme(status_key: str) -> Dict[str, str]:
    """Retrieve color, label, and style theme for a given risk status."""
    return STATUS_THEMES.get(status_key, STATUS_THEMES["normal"])


def fmt_num(val: Any, decimals: int = 2) -> str:
    """Format numeric values with commas and specified decimal places."""
    if val is None:
        return "-"
    try:
        val_f = float(str(val).replace(',', '').strip())
        return f"{val_f:,.{decimals}f}"
    except (TypeError, ValueError):
        return str(val)


def to_num(val: Any) -> Optional[float]:
    """Convert value to float safely, returning None on error."""
    if val is None:
        return None
    try:
        return float(str(val).replace(',', '').strip())
    except (TypeError, ValueError):
        return None


def format_date_th(dt) -> str:
    """Format datetime/date object into full Thai date format (e.g. 20 มีนาคม 2568)."""
    months_th = [
        "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]
    return f"{dt.day} {months_th[dt.month]} {dt.year + 543}"


def format_date_th_short(dt) -> str:
    """Format datetime/date object into short Thai date format (e.g. 20 มี.ค. 2568)."""
    months_short = [
        "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
        "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
    ]
    return f"{dt.day} {months_short[dt.month]} {dt.year + 543}"


# Aliases for backward compatibility
_classify_by_percent = classify_by_percent
_get_status_theme = get_status_theme
_fmt_num = fmt_num
_to_num = to_num
_format_date_th = format_date_th
_format_date_th_short = format_date_th_short

