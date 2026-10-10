import streamlit as st
import pandas as pd
from typing import Any
from views.icons import svg_icon
from views.helpers import (
    to_num,
    classify_by_percent,
    get_status_theme,
    format_date_th_short,
    calc_storage_percent,
)


def _render_badge(theme_r: dict, tooltip: str = "") -> str:
    bg_c = theme_r.get('bg_light', '#f1f5f9')
    txt_c = theme_r.get('color', '#475569')
    brd_c = theme_r.get('border', '#cbd5e1')
    lbl_t = theme_r.get('label', '-')
    title_attr = f' title="{tooltip}"' if tooltip else ''
    return (
        f'<span{title_attr} style="background-color:{bg_c}; color:{txt_c}; '
        f'border:1px solid {brd_c}; border-radius:9999px; padding:3px 10px; '
        f'font-weight:600; font-size:0.75rem; display:inline-block; white-space:nowrap;">{lbl_t}</span>'
    )


def render_history_and_summary(
    dam_data: Any,
    selected_dam_name: str,
    pct: float,
    inflow_m: float,
    outflow_m: float,
    hist_df: pd.DataFrame,
    theme_curr: dict = None,
    theme_7d: dict = None,
    theme_30d: dict = None,
):
    col_history, col_summary = st.columns([1.7, 1.0])

    # ฝั่งซ้าย: Section 6 ข้อมูลย้อนหลัง 30 วัน (ตาราง)
    with col_history:
        with st.container(border=True, key="sec_history"):
            st.markdown(
                '<div id="section-history" class="section-title">'
                '<span class="badge-num">6</span> ข้อมูลย้อนหลัง 30 วัน (ตาราง)</div>',
                unsafe_allow_html=True
            )

            if not hist_df.empty:
                # จัดเรียงข้อมูลตามวันที่จากล่าสุดไปเก่าสุด และรวมข้อมูลวันละ 1 แถว
                t_df = hist_df.copy()
                t_df['record_date'] = pd.to_datetime(t_df['record_date'])
                daily_table = (
                    t_df.sort_values('record_date', ascending=False)
                    .groupby(t_df['record_date'].dt.date)
                    .first()
                    .reset_index(drop=True)
                )

                table_rows = []
                for _, r in daily_table.iterrows():
                    # 1. ร้อยละความจุ
                    r_pct = to_num(r.get('percent_storage'))
                    r_storage = to_num(r.get('volume')) or to_num(r.get('storage')) or to_num(dam_data.get('storage'))
                    
                    # ถ้า percent_storage ว่าง ให้คำนวณสำรองจากปริมาตรน้ำและความจุอ่าง
                    if r_pct is None:
                        r_pct = calc_storage_percent(r_storage, dam_data.get('capacity'))


                    r_pct_str = f"{r_pct:.2f}" if r_pct is not None else "-"
                    r_storage_str = f"{r_storage:,.2f}" if r_storage is not None else "-"

                    # 2. ปริมาณน้ำเข้า/ออก
                    r_in = to_num(r.get('inflow'))
                    r_in_str = f"{r_in:.2f}" if r_in is not None else "-"
                    r_out = to_num(r.get('outflow'))
                    r_out_str = f"{r_out:.2f}" if r_out is not None else "-"

                    # 3. สถานะและวันที่
                    theme_r = get_status_theme(classify_by_percent(r_pct))
                    date_val = r['record_date']
                    date_cell = format_date_th_short(date_val) if hasattr(date_val, 'strftime') else str(date_val)
                    actual_badge = _render_badge(theme_r, tooltip="ระดับสถานการณ์น้ำตามร้อยละความจุ")

                    # สร้างแถว HTML
                    table_rows.append(
                        f'<tr style="border-bottom:1px solid #f1f5f9; text-align:center;">'
                        f'<td style="padding:7px 6px; text-align:left; color:#1e293b; white-space:nowrap;">{date_cell}</td>'
                        f'<td style="padding:7px 6px; color:#1e293b;">{r_pct_str}</td>'
                        f'<td style="padding:7px 6px; color:#1e293b;">{r_storage_str}</td>'
                        f'<td style="padding:7px 6px; color:#1e293b;">{r_in_str}</td>'
                        f'<td style="padding:7px 6px; color:#1e293b;">{r_out_str}</td>'
                        f'<td style="padding:7px 6px; white-space:nowrap;">{actual_badge}</td>'
                        f'</tr>'
                    )

                rows_html = "".join(table_rows)
                unit_style = 'font-weight:500; font-size:0.7rem; color:#64748b;'
                table_html = (
                    '<div class="table-responsive" style="max-height:480px; overflow-y:auto; overflow-x:hidden; border:1px solid #e2e8f0; border-radius:8px;">'
                    '<table style="width:100%; border-collapse:collapse; font-size:0.8rem; background:white; table-layout:auto;">'
                    '<thead>'
                    '<tr style="background-color:#f8fafc; border-bottom:2px solid #e2e8f0; color:#475569; font-weight:600; text-align:center; position:sticky; top:0; z-index:2; box-shadow:0 1px 2px rgba(0,0,0,0.05); line-height:1.25;">'
                    '<th style="padding:8px 6px; text-align:left; background-color:#f8fafc; white-space:nowrap;">วันที่</th>'
                    f'<th style="padding:8px 6px; background-color:#f8fafc; white-space:nowrap;">ร้อยละความจุ<br><span style="{unit_style}">(%)</span></th>'
                    f'<th style="padding:8px 6px; background-color:#f8fafc; white-space:nowrap;">ปริมาณน้ำกักเก็บ<br><span style="{unit_style}">(ล้าน ลบ.ม.)</span></th>'
                    f'<th style="padding:8px 6px; background-color:#f8fafc; white-space:nowrap;">Inflow<br><span style="{unit_style}">(ล้าน ลบ.ม./วัน)</span></th>'
                    f'<th style="padding:8px 6px; background-color:#f8fafc; white-space:nowrap;">Outflow<br><span style="{unit_style}">(ล้าน ลบ.ม./วัน)</span></th>'
                    '<th style="padding:8px 6px; background-color:#f8fafc; white-space:nowrap;">ระดับสถานการณ์น้ำ</th>'
                    '</tr>'
                    '</thead>'
                    f'<tbody>{rows_html}</tbody>'
                    '</table>'
                    '</div>'
                )
                st.markdown(table_html, unsafe_allow_html=True)
            else:
                st.info("ไม่พบข้อมูลย้อนหลัง")
            st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)

    # ฝั่งขวา: Section 7 สรุปสถานการณ์น้ำ (Summary Card)
    with col_summary:
        with st.container(border=True, key="sec_summary"):
            st.markdown(
                '<div id="section-summary" class="section-title">'
                '<span class="badge-num">7</span> สรุปสถานการณ์น้ำ</div>',
                unsafe_allow_html=True
            )
            # กำหนดธีมสีของการ์ด (หากมีระดับเสี่ยงน้ำล้นหรือน้ำแล้ง จะเน้นสีตามความเสี่ยงสูงสุด)
            curr_theme = theme_curr or get_status_theme(classify_by_percent(pct))
            t_7d = theme_7d or get_status_theme("normal")
            t_30d = theme_30d or get_status_theme("normal")

            box_theme = curr_theme
            all_themes = [curr_theme, t_7d, t_30d]
            if any(t.get("en") == "Flood Risk" for t in all_themes):
                box_theme = get_status_theme("flood")
            elif any(t.get("en") == "Drought Risk" for t in all_themes):
                box_theme = get_status_theme("drought")

            summary_html = (
                f'<div style="background-color:{box_theme["bg_light"]}; border:1px solid {box_theme["border"]}; border-radius:8px; padding:16px; display:flex; gap:12px; align-items:flex-start;">'
                f'<div style="flex-shrink:0; margin-top:2px;">{svg_icon("document-check", 28, box_theme["color"])}</div>'
                f'<div style="font-size:0.85rem; color:#1e293b; line-height:1.65;">'
                f'สถานการณ์ปัจจุบันของ{selected_dam_name} อยู่ในระดับ <b style="color:{curr_theme["color"]};">{curr_theme["label"]}</b> โดยมีร้อยละความจุ <b>{pct:.2f}%</b> ปริมาณน้ำไหลเข้า <b>{inflow_m:.1f} ล้าน ลบ.ม./วัน</b> และปริมาณน้ำระบาย <b>{outflow_m:.1f} ล้าน ลบ.ม./วัน</b><br><br>'
                f'ผลการพยากรณ์ล่วงหน้า 7 วัน อยู่ในระดับ <b style="color:{t_7d["color"]};">{t_7d["label"]}</b> และพยากรณ์ล่วงหน้า 30 วัน อยู่ในระดับ <b style="color:{t_30d["color"]};">{t_30d["label"]}</b>'
                f'</div>'
                f'</div>'
            )

            # ตั้งค่าเป็น True เมื่อต้องการเปิดแสดงผลกรอบคำแนะนำการเฝ้าระวังและเกณฑ์ระดับน้ำเพิ่มเติม
            show_extended_summary = False
            if show_extended_summary:
                if box_theme.get("en") == "Flood Risk":
                    advice_text = "ควรเฝ้าระวังระดับน้ำอย่างใกล้ชิด เตรียมแผนพร่องน้ำและแจ้งเตือนพื้นที่ท้ายเขื่อนตามเกณฑ์ปฏิบัติการ"
                elif box_theme.get("en") == "Drought Risk":
                    advice_text = "ควรวางแผนจัดสรรน้ำอย่างรัดกุม โดยให้ความสำคัญกับการอุปโภคบริโภคและการรักษาระบบนิเวศเป็นอันดับแรก"
                else:
                    advice_text = "ปริมาณน้ำอยู่ในเกณฑ์ปลอดภัย สามารถบริหารจัดการและส่งน้ำได้ตามแผนปกติ"

                net_flow = inflow_m - outflow_m
                if net_flow > 0.05:
                    balance_text = f"น้ำไหลเข้ามากกว่าน้ำระบาย <b>+{net_flow:,.1f} ล้าน ลบ.ม./วัน</b>"
                elif net_flow < -0.05:
                    balance_text = f"น้ำระบายมากกว่าน้ำไหลเข้า <b>{abs(net_flow):,.1f} ล้าน ลบ.ม./วัน</b>"
                else:
                    balance_text = "ปริมาณน้ำไหลเข้าและน้ำระบายอยู่ในระดับสมดุลใกล้เคียงกัน"

                flood_theme = get_status_theme("flood")
                normal_theme = get_status_theme("normal")
                drought_theme = get_status_theme("drought")

                summary_html += (
                    f'<div style="margin-top:12px; background-color:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:14px 16px;">'
                    f'<div style="font-size:0.82rem; font-weight:700; color:#0f172a; margin-bottom:6px; display:flex; align-items:center; gap:6px;">'
                    f'{svg_icon("shield-check", 18, box_theme["color"])} คำแนะนำการเฝ้าระวังและสมดุลน้ำรายวัน'
                    f'</div>'
                    f'<div style="font-size:0.8rem; color:#334155; line-height:1.55;">'
                    f'• <b>สมดุลน้ำวันนี้:</b> {balance_text}<br>'
                    f'• <b>แนวทางปฏิบัติ:</b> {advice_text}'
                    f'</div>'
                    f'</div>'
                    f'<div style="margin-top:12px; background-color:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:14px 16px;">'
                    f'<div style="font-size:0.82rem; font-weight:700; color:#0f172a; margin-bottom:10px;">เกณฑ์การจำแนกระดับสถานการณ์น้ำ</div>'
                    f'<div style="display:flex; flex-direction:column; gap:8px; font-size:0.78rem; color:#475569;">'
                    f'<div style="display:flex; align-items:center; justify-content:space-between; gap:8px; padding-bottom:7px; border-bottom:1px solid #e2e8f0;">'
                    f'<div>{_render_badge(flood_theme)} <span style="margin-left:6px; color:#334155;">เฝ้าระวังน้ำล้นตลิ่งและเร่งพร่องน้ำ</span></div>'
                    f'<span style="font-weight:700; color:{flood_theme["color"]}; white-space:nowrap; font-variant-numeric:tabular-nums;">&gt; 80%</span>'
                    f'</div>'
                    f'<div style="display:flex; align-items:center; justify-content:space-between; gap:8px; padding-bottom:7px; border-bottom:1px solid #e2e8f0;">'
                    f'<div>{_render_badge(normal_theme)} <span style="margin-left:6px; color:#334155;">ปริมาณน้ำเหมาะสม บริหารจัดการตามแผน</span></div>'
                    f'<span style="font-weight:700; color:{normal_theme["color"]}; white-space:nowrap; font-variant-numeric:tabular-nums;">30% – 80%</span>'
                    f'</div>'
                    f'<div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">'
                    f'<div>{_render_badge(drought_theme)} <span style="margin-left:6px; color:#334155;">สำรองน้ำเพื่ออุปโภคบริโภคและระบบนิเวศ</span></div>'
                    f'<span style="font-weight:700; color:{drought_theme["color"]}; white-space:nowrap; font-variant-numeric:tabular-nums;">&lt; 30%</span>'
                    f'</div>'
                    f'</div>'
                    f'</div>'
                )

            st.markdown(summary_html, unsafe_allow_html=True)
            st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
