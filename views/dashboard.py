import streamlit as st
import streamlit.components.v1 as components

from views.styles import get_custom_css, get_client_js
from views.helpers import (
    classify_by_percent,
    get_status_theme,
    prepare_dam_data,
    to_num,
)
from views.components import (
    render_sidebar,
    render_header,
    render_dam_selector,
    render_current_overview,
    render_forecast_cards,
    render_trend_and_details,
    render_history_and_summary,
    render_footer,
)


# ฟังก์ชันหลักสำหรับเรนเดอร์แดชบอร์ด
def render(raw_df, models_dict, data_date=None, recorded_at=None):
    # CSS 
    st.markdown(get_custom_css(), unsafe_allow_html=True)

    # แถบเมนู Sidebar
    render_sidebar()

    # Header
    base_date = render_header(recorded_at=recorded_at, data_date=data_date)

    # Section 1 (เลือกเขื่อน) และ Section 2 (ภาพรวมสถานการณ์น้ำปัจจุบัน)
    top_left, top_right = st.columns([1.1, 1.4])
    with top_left:
        selected_dam_name, raw_dam = render_dam_selector(raw_df)

    # จัดเตรียมข้อมูลเขื่อน
    dam_data, is_fallback, fallback_date = prepare_dam_data(raw_dam, data_date=data_date)

    pct = float(to_num(dam_data.get('percent_storage')) or 0.0)
    theme_curr = get_status_theme(classify_by_percent(pct))
    raw_in = dam_data.get('inflow')
    inflow_m = float(raw_in) if (raw_in is not None and str(raw_in).lower() != 'none') else float('nan')
    raw_out = dam_data.get('outflow')
    outflow_m = float(raw_out) if (raw_out is not None and str(raw_out).lower() != 'none') else float('nan')

    with top_right:
        render_current_overview(dam_data, theme_curr, pct, inflow_m, outflow_m)

    # Section 3: การ์ดผลพยากรณ์ระดับน้ำ
    theme_7d, theme_30d = render_forecast_cards(
        dam_data,
        models_dict,
        base_date,
        theme_curr,
        is_fallback=is_fallback,
        fallback_date=fallback_date
    )

    # Section 4 (กราฟแนวโน้มร้อยละความจุย้อนหลัง) และ Section 5 (ตารางข้อมูลจำเพาะของเขื่อน)
    hist_df = render_trend_and_details(dam_data, selected_dam_name, pct, inflow_m, outflow_m)

    # Section 6 (ตารางข้อมูลย้อนหลัง 30 วัน) และ Section 7 (กล่องสรุปสถานการณ์น้ำภาพรวม)
    render_history_and_summary(
        dam_data,
        selected_dam_name,
        pct,
        inflow_m,
        outflow_m,
        hist_df,
        theme_curr=theme_curr,
        theme_7d=theme_7d,
        theme_30d=theme_30d,
    )

    # ส่วนท้ายของหน้าเว็บ (Footer) แสดงแหล่งที่มา
    render_footer()

    # สคริปต์ JavaScript เสริมบนเบราว์เซอร์
    if hasattr(st, "iframe"):
        try:
            st.iframe(get_client_js(), height=0, width=0)
        except Exception:
            components.html(get_client_js(), height=0, width=0)
    else:
        components.html(get_client_js(), height=0, width=0)
