import datetime
import streamlit as st
from views.icons import svg_icon
from views.helpers import format_date_th


def render_header(recorded_at=None, data_date=None) -> datetime.datetime:
    base_date = recorded_at or data_date or datetime.date.today()
    if isinstance(base_date, datetime.date) and not isinstance(base_date, datetime.datetime):
        base_date = datetime.datetime.combine(base_date, datetime.time(8, 0))
    date_str = f"ข้อมูล ณ วันที่ {format_date_th(base_date)} เวลา {base_date.strftime('%H:%M')} น."

    col_title, col_date = st.columns([2.6, 1.4])
    with col_title:
        st.markdown('<div id="section-top" style="scroll-margin-top: 80px;"></div>', unsafe_allow_html=True)
        st.markdown("<h2 class='header-title' style='margin:0 0 4px 0; font-size:1.45rem; font-weight:700; color:#0f172a;'>ระบบพยากรณ์ระดับสถานการณ์น้ำ</h2>", unsafe_allow_html=True)
        st.caption("ติดตามและพยากรณ์ระดับน้ำในอ่างเก็บน้ำขนาดใหญ่ทั่วประเทศล่วงหน้า 7 และ 30 วัน")
    with col_date:
        st.markdown(
            f'<div class="header-date-box">'
            f'{svg_icon("calendar", 16, "#64748b")} <span>{date_str}</span></div>',
            unsafe_allow_html=True
        )

    return base_date

