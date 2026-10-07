"""Section 3: Forecast Cards component."""

import datetime
import streamlit as st
from typing import Dict, Any, Tuple
from views.icons import svg_icon
from views.helpers import format_date_th_short, get_status_theme
from core.risk_predictor import predict_single_dam



def render_forecast_cards(
    dam_data: Any,
    models_dict: Dict,
    _dt: datetime.datetime,
    theme_curr: Dict[str, str],
    is_fallback: bool = False,
    fallback_date: Any = None,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Render Section 3: Three forecast cards (Current, 7-day, 30-day) styled by predicted risk level."""
    theme_7d = get_status_theme(predict_single_dam(dam_data, models_dict["7_day"]))
    theme_30d = get_status_theme(predict_single_dam(dam_data, models_dict["30_day"]))

    d_start_7 = _dt + datetime.timedelta(days=1)
    d_end_7 = _dt + datetime.timedelta(days=7)
    d_end_30 = _dt + datetime.timedelta(days=30)

    curr_date_str = format_date_th_short(fallback_date) if (is_fallback and fallback_date) else format_date_th_short(_dt)
    curr_date_suffix = " (เมื่อวาน)" if is_fallback else ""

    with st.container(border=True, key="sec_forecast"):
        st.markdown(
            '<div id="section-forecast" class="section-title">'
            '<span class="badge-num">3</span> ผลการพยากรณ์ระดับสถานการณ์น้ำ</div>',
            unsafe_allow_html=True
        )
        if is_fallback:
            st.caption(f"💡 *วันนี้ยังไม่มีข้อมูลตรวจวัด จึงใช้ค่า Input ล่าสุดจากเมื่อวาน ({curr_date_str}) ในการพยากรณ์")

        f_c1, f_c2, f_c3 = st.columns(3)
        with f_c1:
            st.markdown(f"""
            <div class="forecast-card" style="background:{theme_curr['bg_light']}; border:1px solid {theme_curr['border']}; border-left:4px solid {theme_curr['color']};">
                <div style="font-size:0.85rem; color:#64748b; margin-bottom:8px; display:flex; align-items:center; justify-content:center; gap:6px;">
                    {svg_icon("calendar", 15, "#64748b")} สถานการณ์ปัจจุบัน
                </div>
                <div class="forecast-risk-title" style="font-size:1.5rem; font-weight:700; color:{theme_curr['color']}; margin-bottom:2px;">{theme_curr['label_short']}</div>
                <div style="font-size:0.85rem; color:{theme_curr['color']};">({theme_curr['en']})</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:6px;">ข้อมูล ณ วันที่ {curr_date_str}{curr_date_suffix}</div>
            </div>
            """, unsafe_allow_html=True)
        with f_c2:
            st.markdown(f"""
            <div class="forecast-card" style="background:{theme_7d['bg_light']}; border:1px solid {theme_7d['border']}; border-left:4px solid {theme_7d['color']};">
                <div style="font-size:0.85rem; color:#64748b; margin-bottom:8px; display:flex; align-items:center; justify-content:center; gap:6px;">
                    {svg_icon("calendar", 15, "#64748b")} พยากรณ์ล่วงหน้า 7 วัน
                </div>
                <div class="forecast-risk-title" style="font-size:1.5rem; font-weight:700; color:{theme_7d['color']}; margin-bottom:2px;">{theme_7d['label_short']}</div>
                <div style="font-size:0.85rem; color:{theme_7d['color']};">({theme_7d['en']})</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:6px;">ช่วงวันที่ {format_date_th_short(d_start_7)} - {format_date_th_short(d_end_7)}</div>
            </div>
            """, unsafe_allow_html=True)
        with f_c3:
            st.markdown(f"""
            <div class="forecast-card" style="background:{theme_30d['bg_light']}; border:1px solid {theme_30d['border']}; border-left:4px solid {theme_30d['color']};">
                <div style="font-size:0.85rem; color:#64748b; margin-bottom:8px; display:flex; align-items:center; justify-content:center; gap:6px;">
                    {svg_icon("calendar", 15, "#64748b")} พยากรณ์ล่วงหน้า 30 วัน
                </div>
                <div class="forecast-risk-title" style="font-size:1.5rem; font-weight:700; color:{theme_30d['color']}; margin-bottom:2px;">{theme_30d['label_short']}</div>
                <div style="font-size:0.85rem; color:{theme_30d['color']};">({theme_30d['en']})</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:6px;">ช่วงวันที่ {format_date_th_short(d_start_7)} - {format_date_th_short(d_end_30)}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)

    return theme_7d, theme_30d

