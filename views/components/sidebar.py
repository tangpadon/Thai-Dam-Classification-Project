"""Sidebar component rendering navigation and system branding."""

import streamlit as st
from views.icons import svg_icon


def render_sidebar():
    """Render the sidebar with Dam Forecast logo and smooth scroll navigation links."""
    with st.sidebar:
        # Top Logo & Title
        st.markdown("""
        <div style="display:flex; align-items:flex-start; gap:12px; margin-bottom: 24px; padding-top: 4px;">
            <span style="display:inline-flex; flex-shrink:0;">
                <svg width="34" height="34" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M18 3L23.5 12C26.5 17 25 21 21.5 23C19.5 24 16.5 24 14.5 23C11 21 9.5 17 12.5 12L18 3Z" fill="#0284c7"/>
                    <path d="M6 26C10 24 14 28 18 26C22 24 26 28 30 26" stroke="#0284c7" stroke-width="2.5" stroke-linecap="round"/>
                    <path d="M6 30C10 28 14 32 18 30C22 28 26 32 30 30" stroke="#0284c7" stroke-width="2.5" stroke-linecap="round"/>
                </svg>
            </span>
            <div>
                <h3 style="margin:0; font-size:1.15rem; font-weight:700; color:#0f172a; line-height:1.2;">Dam Forecast</h3>
                <p style="margin:4px 0 0 0; font-size:0.75rem; color:#64748b; line-height:1.3;">ระบบพยากรณ์ระดับ<br>สถานการณ์น้ำในอ่างเก็บน้ำ</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Menu List
        st.markdown(f"""
        <div class="sidebar-nav">
            <div role="button" tabindex="0" data-target="section-top" class="nav-link active">{svg_icon("home", 17, "#0284c7")} <span>หน้าแรก (ภาพรวม)</span></div>
            <div role="button" tabindex="0" data-target="section-select" class="nav-link">{svg_icon("search", 17, "#475569")} <span>ค้นหา / เลือกอ่างเก็บน้ำ</span></div>
            <div role="button" tabindex="0" data-target="section-forecast" class="nav-link">{svg_icon("shield-check", 17, "#475569")} <span>ผลการพยากรณ์</span></div>
            <div role="button" tabindex="0" data-target="section-trend" class="nav-link">{svg_icon("chart", 17, "#475569")} <span>แนวโน้มและกราฟ</span></div>
            <div role="button" tabindex="0" data-target="section-history" class="nav-link">{svg_icon("clock", 17, "#475569")} <span>ข้อมูลย้อนหลัง</span></div>
            <div role="button" tabindex="0" data-target="section-summary" class="nav-link">{svg_icon("document-check", 17, "#475569")} <span>สรุปสถานการณ์</span></div>
            <div role="button" tabindex="0" data-target="section-about" class="nav-link">{svg_icon("info", 17, "#475569")} <span>เกี่ยวกับระบบ</span></div>
        </div>
        """, unsafe_allow_html=True)

