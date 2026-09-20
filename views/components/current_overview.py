"""Section 2: Current Overview component."""

import streamlit as st
from typing import Dict, Any
from views.icons import svg_icon


def render_current_overview(
    dam_data: Any,
    theme_curr: Dict[str, str],
    pct: float,
    inflow_m: float,
    outflow_m: float
):
    """Render Section 2: Four current status metric cards (Risk status, % Capacity, Inflow, Outflow)."""
    with st.container(border=True, key="sec_overview"):
        st.markdown(
            '<div id="section-overview" class="section-title">'
            '<span class="badge-num">2</span> ภาพรวมสถานการณ์น้ำปัจจุบัน</div>',
            unsafe_allow_html=True
        )
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="overview-metric-card">
                <div style="flex-shrink:0;">{svg_icon("shield-check", 26, "#16a34a")}</div>
                <div style="min-width:0; overflow:hidden;">
                    <div class="metric-title-text" style="font-size:0.7rem; color:#64748b; line-height:1.2;">ระดับสถานการณ์น้ำ</div>
                    <div style="font-size:1.15rem; font-weight:700; color:{theme_curr['color']}; line-height:1.2;">{theme_curr['label_short']}</div>
                    <div style="font-size:0.75rem; color:#64748b;">({theme_curr['en']})</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="overview-metric-card">
                <div style="flex-shrink:0;">{svg_icon("drop-waves", 26, "#0284c7")}</div>
                <div style="min-width:0; overflow:hidden;">
                    <div class="metric-title-text" style="font-size:0.7rem; color:#64748b; line-height:1.2;">ร้อยละความจุ</div>
                    <div style="font-size:1.15rem; font-weight:700; color:#0284c7; line-height:1.2;">{pct:,.2f}%</div>
                    <div style="font-size:0.75rem; color:#94a3b8;">% Capacity</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="overview-metric-card">
                <div style="flex-shrink:0;">{svg_icon("inflow-waves", 26, "#0284c7")}</div>
                <div style="min-width:0; overflow:hidden;">
                    <div class="metric-title-text" style="font-size:0.7rem; color:#64748b; line-height:1.2;">น้ำไหลเข้า (Inflow)</div>
                    <div style="font-size:1.15rem; font-weight:700; color:#0f172a; line-height:1.2;">{inflow_m:,.1f}M</div>
                    <div style="font-size:0.75rem; color:#94a3b8;">ลบ.ม./วัน</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="overview-metric-card">
                <div style="flex-shrink:0;">{svg_icon("outflow-waves", 26, "#ea580c")}</div>
                <div style="min-width:0; overflow:hidden;">
                    <div class="metric-title-text" style="font-size:0.7rem; color:#64748b; line-height:1.2;">น้ำระบาย (Outflow)</div>
                    <div style="font-size:1.15rem; font-weight:700; color:#0f172a; line-height:1.2;">{outflow_m:,.1f}M</div>
                    <div style="font-size:0.75rem; color:#94a3b8;">ลบ.ม./วัน</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)

