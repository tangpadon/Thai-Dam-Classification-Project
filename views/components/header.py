"""Header component for the dashboard title and date/time."""

import datetime
import streamlit as st
from views.icons import svg_icon
from views.utils import format_date_th


def render_header(recorded_at=None, data_date=None) -> datetime.datetime:
    """Render the dashboard top title and timestamp, returning the resolved datetime."""
    _dt = recorded_at or data_date or datetime.date.today()
    if isinstance(_dt, datetime.date) and not isinstance(_dt, datetime.datetime):
        _dt = datetime.datetime.combine(_dt, datetime.time(8, 0))
    date_str = f"{format_date_th(_dt)} เวลา {_dt.strftime('%H:%M')} น."
    date_header_right = f"{format_date_th(_dt)} {_dt.strftime('%H:%M')} น."
    saved_note = f"ข้อมูล ณ วันที่ {date_str}"

    h_col1, h_col2 = st.columns([3, 1.2])
    with h_col1:
        st.markdown('<div id="section-top" style="scroll-margin-top: 80px;"></div>', unsafe_allow_html=True)
        st.markdown("<h2 class='header-title' style='margin:0 0 4px 0; font-size:1.45rem; font-weight:700; color:#0f172a;'>ระบบพยากรณ์ระดับสถานการณ์น้ำ</h2>", unsafe_allow_html=True)
        st.caption(saved_note)
    with h_col2:
        st.markdown(
            f'<div class="header-date-box">'
            f'{svg_icon("calendar", 16, "#64748b")} {date_header_right}</div>',
            unsafe_allow_html=True
        )

    return _dt

