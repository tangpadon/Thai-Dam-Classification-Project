"""Section 1: Dam Selector component."""

import streamlit as st
import pandas as pd
from typing import Tuple
from views.icons import svg_icon
from views.constants import get_dam_location


def render_dam_selector(raw_df: pd.DataFrame) -> Tuple[str, pd.Series]:
    """Render Section 1: Dam selection dropdown with visual illustration, returning (name, data)."""
    with st.container(border=True, key="sec_dam_select"):
        st.markdown(
            '<div id="section-select" class="section-title">'
            '<span class="badge-num">1</span> เลือกอ่างเก็บน้ำ</div>',
            unsafe_allow_html=True
        )
        b1_c1, b1_c2 = st.columns([1.1, 1.1])
        with b1_c1:
            dam_names = raw_df['name'].tolist()
            default_idx = 0
            for idx, name in enumerate(dam_names):
                if "ภูมิพล" in str(name):
                    default_idx = idx
                    break
            selected_dam_name = st.selectbox("อ่างเก็บน้ำ", dam_names, index=default_idx, key="dam_select")
            dam_data = raw_df[raw_df['name'] == selected_dam_name].iloc[0]

        province, region = get_dam_location(selected_dam_name, dam_data)
        prov_label = province if province.startswith("จังหวัด") else f"จังหวัด{province}"

        with b1_c2:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:12px; height:100%; padding-top:10px;">
                <div style="flex-shrink:0;">
                    <svg width="46" height="46" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <!-- Green banks -->
                        <path d="M4 50L18 20L26 20L20 50H4Z" fill="#34d399" opacity="0.85"/>
                        <path d="M60 50L46 20L38 20L44 50H60Z" fill="#34d399" opacity="0.85"/>
                        <!-- Dam wall -->
                        <path d="M18 20H46V28H18V20Z" fill="#93c5fd"/>
                        <path d="M20 28H44L40 50H24L20 28Z" fill="#60a5fa"/>
                        <!-- Spillway lines -->
                        <line x1="28" y1="28" x2="26" y2="50" stroke="#ffffff" stroke-width="2" stroke-dasharray="2 2"/>
                        <line x1="32" y1="28" x2="32" y2="50" stroke="#ffffff" stroke-width="2" stroke-dasharray="2 2"/>
                        <line x1="36" y1="28" x2="38" y2="50" stroke="#ffffff" stroke-width="2" stroke-dasharray="2 2"/>
                        <!-- Water base -->
                        <path d="M10 50C16 47 22 53 28 50C34 47 40 53 46 50C52 47 58 53 64 50V56H0V50H10Z" fill="#38bdf8"/>
                    </svg>
                </div>
                <div>
                    <div style="font-weight:700; font-size:1.05rem; color:#0f172a; margin-bottom:4px; line-height:1.2;">{selected_dam_name}</div>
                    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap; font-size:0.83rem; color:#475569;">
                        <span style="display:inline-flex; align-items:center; gap:4px; color:#0369a1; font-weight:500;">
                            {svg_icon("map-pin", 14, "#0284c7")} {prov_label}
                        </span>
                        <span style="color:#cbd5e1;">•</span>
                        <span style="background-color:#e0f2fe; color:#0284c7; padding:2px 8px; border-radius:9999px; font-size:0.75rem; font-weight:600; border:1px solid #bae6fd;">
                            {region}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)

    return selected_dam_name, dam_data
