"""
โมดูลหน้าจอผู้ใช้ (User View Module)
ทำหน้าที่เป็นศูนย์กลางเชื่อมโยงส่วนประกอบ (Components) ของ Dashboard
ตั้งแต่ Section 1 ถึง Section 8 ให้แสดงผลอย่างเป็นระเบียบบนหน้าเว็บ Streamlit
"""

import streamlit as st
import streamlit.components.v1 as components

from views.styles import get_custom_css, get_client_js
from views.utils import (
    classify_by_percent,
    get_status_theme,
    prepare_dam_data,
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


def render(raw_df, models_dict, data_date=None, recorded_at=None):
    """
    ฟังก์ชันหลักในการเรนเดอร์หน้า Dashboard ทั้งหมด:
    - raw_df: ตารางข้อมูลเขื่อนประจำวัน
    - models_dict: โมเดล Weka ML สำหรับพยากรณ์ 7 วัน และ 30 วัน
    - data_date: วันที่ของข้อมูล (เช่น วันนี้ หรือเมื่อวาน)
    - recorded_at: วันที่และเวลาที่มีการดึงข้อมูลล่าสุด
    """

    # 1. แทรกสไตล์ CSS ปรับแต่งความสวยงามของหน้าเว็บ
    st.markdown(get_custom_css(), unsafe_allow_html=True)

    # 2. แถบเมนูด้านข้าง (Sidebar) แนะนำการใช้งานและคำอธิบายเกณฑ์ความเสี่ยง
    render_sidebar()

    # 3. ส่วนหัวของหน้าเว็บ (Header) แสดงชื่อระบบและเวลาที่อัปเดตข้อมูล
    _dt = render_header(recorded_at=recorded_at, data_date=data_date)

    # 4. Section 1 (เลือกเขื่อน) และ Section 2 (ภาพรวมสถานการณ์น้ำปัจจุบัน)
    top_left, top_right = st.columns([1.1, 1.4])
    with top_left:
        selected_dam_name, raw_dam = render_dam_selector(raw_df)

    # จัดเตรียมข้อมูลเขื่อน (ตรวจสอบความสมบูรณ์ หากวันนี้ไม่มีค่าจะดึงค่าเมื่อวานมาใช้แทนอัตโนมัติ)
    dam_data, is_fallback, fallback_date = prepare_dam_data(raw_dam, data_date=data_date)

    pct = float(dam_data.get('percent_storage', 0) or 0)
    theme_curr = get_status_theme(classify_by_percent(pct))
    inflow_m = float(dam_data.get('inflow', 0) or 0)
    outflow_m = float(dam_data.get('outflow', 0) or 0)

    with top_right:
        render_current_overview(dam_data, theme_curr, pct, inflow_m, outflow_m)

    # 5. Section 3: การ์ดผลพยากรณ์ระดับน้ำ (สถานการณ์ปัจจุบัน, พยากรณ์ 7 วัน, พยากรณ์ 30 วัน)
    theme_7d, theme_30d = render_forecast_cards(
        dam_data,
        models_dict,
        _dt,
        theme_curr,
        is_fallback=is_fallback,
        fallback_date=fallback_date
    )

    # 6. Section 4 (กราฟแนวโน้มร้อยละความจุย้อนหลัง) และ Section 5 (ตารางข้อมูลจำเพาะของเขื่อน)
    hist_df = render_trend_and_details(dam_data, selected_dam_name, pct, inflow_m, outflow_m)

    # 7. Section 6 (ตารางข้อมูลย้อนหลัง 30 วัน) และ Section 7 (กล่องสรุปสถานการณ์น้ำภาพรวม)
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
        models_dict=models_dict
    )

    # 8. ส่วนท้ายของหน้าเว็บ (Footer) แสดงแหล่งที่มาและลิขสิทธิ์
    render_footer()

    # 9. สคริปต์ JavaScript เสริมบนเบราว์เซอร์ (Smooth Scroll และการปรับระยะห่าง)
    components.html(get_client_js(), height=0, width=0)
