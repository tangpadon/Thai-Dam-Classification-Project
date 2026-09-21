"""Section 4 (Trend Chart) and Section 5 (Dam Details) component."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Any
from views.utils import fmt_num
from core.db import get_historical_data


def render_trend_and_details(
    dam_data: Any,
    selected_dam_name: str,
    pct: float,
    inflow_m: float,
    outflow_m: float
) -> pd.DataFrame:
    """Render Section 4 (Historical % Storage trend chart) and Section 5 (Dam specifications table)."""
    with st.container(border=True, key="sec_trend"):
        m_left, m_right = st.columns([1.7, 1.3])
        with m_left:
            g_head1, g_head2 = st.columns([2, 1])
            with g_head1:
                st.markdown(
                    '<div id="section-trend" class="section-title">'
                    '<span class="badge-num">4</span> แนวโน้มร้อยละความจุของอ่างเก็บน้ำย้อนหลัง</div>',
                    unsafe_allow_html=True
                )
            with g_head2:
                time_range = st.selectbox(
                    "ช่วงเวลา", ["30 วันล่าสุด", "7 วันล่าสุด"],
                    label_visibility="collapsed", filter_mode=None
                )
            limit_days = 30 if "30" in time_range else 7
            hist_df = get_historical_data(dam_data['id'], limit=30)

            if not hist_df.empty and len(hist_df) > 1:
                hist_df = hist_df.sort_values('record_date').reset_index(drop=True)
                hist_df['record_date'] = pd.to_datetime(hist_df['record_date'])
                chart_data = hist_df.tail(limit_days) if len(hist_df) > limit_days else hist_df
                daily = (
                    chart_data.sort_values('record_date')
                    .groupby(chart_data['record_date'].dt.date)
                    .tail(1)
                    .reset_index(drop=True)
                )
                if len(daily) > 1:
                    x_start = daily['record_date'].dt.normalize().min()
                    x_end = daily['record_date'].max() + pd.Timedelta(hours=12)
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=daily['record_date'], y=daily['percent_storage'],
                        mode='lines+markers', line=dict(color='#0284c7', width=2),
                        marker=dict(size=5, color='#0284c7'), name='ร้อยละความจุ (%)',
                        hovertemplate='%{x|%d/%m/%Y}<br>ร้อยละความจุ: %{y:.2f}%<extra></extra>'
                    ))
                    fig.add_hline(
                        y=80, line_dash="dash", line_color="#ef4444",
                        annotation_text="เกณฑ์เสี่ยงน้ำล้น (80%)",
                        annotation_position="top right", annotation_font_color="#ef4444"
                    )
                    fig.add_hline(
                        y=30, line_dash="dash", line_color="#f59e0b",
                        annotation_text="เกณฑ์เสี่ยงน้ำแห้ง (30%)",
                        annotation_position="bottom right", annotation_font_color="#f59e0b"
                    )
                    fig.update_layout(
                        yaxis=dict(range=[0, 100], title="ร้อยละความจุ (%)"),
                        margin=dict(l=10, r=10, t=20, b=10), height=320,
                        autosize=True,
                        xaxis=dict(
                            range=[x_start, x_end],
                            tickformat="%d/%m",
                            dtick=f"D{max(1, limit_days // 6)}"
                        ),
                        hovermode="x unified",
                        hoverlabel=dict(font_size=12),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        dragmode=False
                    )
                    st.plotly_chart(
                        fig, use_container_width=True,
                        config={'displayModeBar': False, 'scrollZoom': False, 'doubleClick': False}
                    )
                else:
                    st.info("ไม่พบข้อมูลประวัติย้อนหลังสำหรับการแสดงผลกราฟ")
            else:
                st.info("ไม่พบข้อมูลประวัติย้อนหลังสำหรับการแสดงผลกราฟ")

        with m_right:
            st.markdown(
                '<div id="section-details" class="section-title">'
                '<span class="badge-num">5</span> รายละเอียดข้อมูลอ่างเก็บน้ำ</div>',
                unsafe_allow_html=True
            )
            vol_val = dam_data.get('volume')
            vol_str = f"{fmt_num(vol_val, 2)} ล้าน ลบ.ม." if vol_val is not None else "-"

            owner_str = dam_data.get('owner') or dam_data.get('agency')
            if not owner_str or pd.isna(owner_str):
                owner_str = "การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย" if "ภูมิพล" in str(selected_dam_name) else "กรมชลประทาน"

            rows = [
                ("ชื่ออ่างเก็บน้ำ", selected_dam_name),
                ("ความจุที่ระดับเก็บกัก (ความจุรวม)", f"{fmt_num(dam_data.get('capacity'), 0)} ล้าน ลบ.ม."),
                ("ปริมาณน้ำกักเก็บปัจจุบัน", f"{fmt_num(dam_data.get('storage'), 0)} ล้าน ลบ.ม."),
                ("ร้อยละความจุปัจจุบัน", f"{pct:.2f} %"),
                ("ปริมาณน้ำปัจจุบัน (Volume)", vol_str),
                ("ปริมาณน้ำไหลเข้า (Inflow)", f"{inflow_m:.1f} ล้าน ลบ.ม./วัน"),
                ("ปริมาณน้ำระบาย (Outflow)", f"{outflow_m:.1f} ล้าน ลบ.ม./วัน"),
                ("หน่วยงานรับผิดชอบ", owner_str),
            ]
            rows_html = "".join(
                f'<tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:7px 10px; font-weight:600; color:#475569; word-break:break-word;">{k}</td>'
                f'<td style="padding:7px 10px; text-align:right; color:#0f172a; word-break:break-word;">{v}</td></tr>'
                for k, v in rows
            )
            st.markdown(
                f'<table class="dam-details-table">{rows_html}</table>',
                unsafe_allow_html=True
            )
        st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)

    return hist_df

