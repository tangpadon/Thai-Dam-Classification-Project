"""Section 6 (Historical Table) and Section 7 (Summary Box) component."""

import streamlit as st
import pandas as pd
from typing import Any
from views.icons import svg_icon
from views.utils import to_num, classify_by_percent, get_status_theme, format_date_th_short


from core.weka_model import predict_single_dam


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
    models_dict: dict = None,
):
    """Render Section 6 (Historical data table) and Section 7 (Risk summary card)."""
    b5_col, b6_col = st.columns([1.45, 1.05])
    with b5_col:
        with st.container(border=True, key="sec_history"):
            has_models = bool(models_dict and "7_day" in models_dict and "30_day" in models_dict)
            if has_models:
                h_col1, h_col2 = st.columns([1.1, 1.4])
                with h_col1:
                    st.markdown(
                        '<div id="section-history" class="section-title" style="margin-bottom:0;">'
                        '<span class="badge-num">6</span> ข้อมูลย้อนหลัง 30 วัน (ตาราง)</div>',
                        unsafe_allow_html=True
                    )
                with h_col2:
                    pred_mode = st.radio(
                        "โมเดลพยากรณ์:",
                        options=["พยากรณ์ 7 วัน", "พยากรณ์ 30 วัน", "แสดงทั้ง 2 โมเดล"],
                        horizontal=True,
                        index=0,
                        key="sec6_pred_mode",
                        label_visibility="collapsed"
                    )
            else:
                st.markdown(
                    '<div id="section-history" class="section-title">'
                    '<span class="badge-num">6</span> ข้อมูลย้อนหลัง 30 วัน (ตาราง)</div>',
                    unsafe_allow_html=True
                )
                pred_mode = None

            show_7d = has_models and pred_mode in ("พยากรณ์ 7 วัน", "แสดงทั้ง 2 โมเดล")
            show_30d = has_models and pred_mode in ("พยากรณ์ 30 วัน", "แสดงทั้ง 2 โมเดล")

            if not hist_df.empty:
                t_df = hist_df.copy()
                t_df['record_date'] = pd.to_datetime(t_df['record_date'])
                daily_table = (
                    t_df.sort_values('record_date', ascending=False)
                    .groupby(t_df['record_date'].dt.date)
                    .first()
                    .reset_index(drop=True)
                )

                table_rows = []
                match_7d_cnt = 0
                match_30d_cnt = 0
                total_cnt = len(daily_table)

                for _, r in daily_table.iterrows():
                    r_pct = to_num(r.get('percent_storage'))
                    r_pct_str = f"{r_pct:.2f}" if r_pct is not None else "-"
                    r_storage = to_num(r.get('volume'))
                    if r_storage is None:
                        r_storage = to_num(r.get('storage'))
                    if r_storage is None:
                        r_storage = to_num(dam_data.get('storage'))
                    r_storage_str = f"{r_storage:,.2f}" if r_storage is not None else "-"
                    r_in = to_num(r.get('inflow'))
                    r_in_str = f"{r_in:.2f}" if r_in is not None else "-"
                    r_out = to_num(r.get('outflow'))
                    r_out_str = f"{r_out:.2f}" if r_out is not None else "-"

                    theme_r = get_status_theme(classify_by_percent(r_pct))
                    date_val = r['record_date']
                    if hasattr(date_val, 'strftime'):
                        date_cell = format_date_th_short(date_val)
                    else:
                        date_cell = str(date_val)

                    actual_badge = _render_badge(theme_r, tooltip="ระดับสถานการณ์จริงตามร้อยละความจุ")

                    td_pred_7d = ""
                    td_pred_30d = ""

                    if has_models:
                        month_val = date_val.month if hasattr(date_val, 'month') else 1
                        row_input = dict(dam_data)
                        row_input.update({
                            'percent_storage': r_pct,
                            'volume': r_storage,
                            'inflow': r_in or 0.0,
                            'outflow': r_out or 0.0,
                            'month': month_val,
                        })

                        if show_7d:
                            p7 = predict_single_dam(row_input, models_dict["7_day"])
                            t7 = get_status_theme(p7)
                            is_match_7d = (t7['label'] == theme_r['label'])
                            if is_match_7d:
                                match_7d_cnt += 1
                            tooltip_7d = "พยากรณ์ 7 วัน: ตรงกับสถานการณ์จริง" if is_match_7d else "พยากรณ์ 7 วัน: ต่างจากสถานการณ์จริง"
                            badge_7d = _render_badge(t7, tooltip=tooltip_7d)
                            td_pred_7d = f'<td style="padding:7px 8px; white-space:nowrap;">{badge_7d}</td>'

                        if show_30d:
                            p30 = predict_single_dam(row_input, models_dict["30_day"])
                            t30 = get_status_theme(p30)
                            is_match_30d = (t30['label'] == theme_r['label'])
                            if is_match_30d:
                                match_30d_cnt += 1
                            tooltip_30d = "พยากรณ์ 30 วัน: ตรงกับสถานการณ์จริง" if is_match_30d else "พยากรณ์ 30 วัน: ต่างจากสถานการณ์จริง"
                            badge_30d = _render_badge(t30, tooltip=tooltip_30d)
                            td_pred_30d = f'<td style="padding:7px 8px; white-space:nowrap;">{badge_30d}</td>'

                    table_rows.append(
                        f'<tr style="border-bottom:1px solid #f1f5f9; text-align:center;">'
                        f'<td style="padding:7px 8px; text-align:left; color:#1e293b; white-space:nowrap;">{date_cell}</td>'
                        f'<td style="padding:7px 8px; color:#1e293b;">{r_pct_str}</td>'
                        f'<td style="padding:7px 8px; color:#1e293b;">{r_storage_str}</td>'
                        f'<td style="padding:7px 8px; color:#1e293b;">{r_in_str}</td>'
                        f'<td style="padding:7px 8px; color:#1e293b;">{r_out_str}</td>'
                        f'<td style="padding:7px 8px; white-space:nowrap;">{actual_badge}</td>'
                        f'{td_pred_7d}'
                        f'{td_pred_30d}'
                        f'</tr>'
                    )

                th_actual = '<th style="padding:9px 8px; background-color:#f8fafc;">สถานการณ์จริง (Actual)</th>'
                th_pred_7d = '<th style="padding:9px 8px; background-color:#f8fafc;">พยากรณ์ 7 วัน (Predicted)</th>' if show_7d else ''
                th_pred_30d = '<th style="padding:9px 8px; background-color:#f8fafc;">พยากรณ์ 30 วัน (Predicted)</th>' if show_30d else ''

                if not (show_7d or show_30d):
                    th_actual = '<th style="padding:9px 8px; background-color:#f8fafc;">ระดับสถานการณ์น้ำ</th>'

                rows_html = "".join(table_rows)
                table_html = (
                    '<div class="table-responsive" style="max-height:480px; overflow-y:auto; border:1px solid #e2e8f0; border-radius:8px;">'
                    '<table style="width:100%; border-collapse:collapse; font-size:0.8rem; background:white;">'
                    '<thead>'
                    '<tr style="background-color:#f8fafc; border-bottom:2px solid #e2e8f0; color:#475569; font-weight:600; text-align:center; position:sticky; top:0; z-index:2; box-shadow:0 1px 2px rgba(0,0,0,0.05);">'
                    '<th style="padding:9px 8px; text-align:left; background-color:#f8fafc;">วันที่</th>'
                    '<th style="padding:9px 8px; background-color:#f8fafc;">ร้อยละความจุ (%)</th>'
                    '<th style="padding:9px 8px; background-color:#f8fafc;">ปริมาณน้ำกักเก็บ (ล้าน ลบ.ม.)</th>'
                    '<th style="padding:9px 8px; background-color:#f8fafc;">Inflow (ล้าน ลบ.ม./วัน)</th>'
                    '<th style="padding:9px 8px; background-color:#f8fafc;">Outflow (ล้าน ลบ.ม./วัน)</th>'
                    f'{th_actual}'
                    f'{th_pred_7d}'
                    f'{th_pred_30d}'
                    '</tr>'
                    '</thead>'
                    f'<tbody>{rows_html}</tbody>'
                    '</table>'
                    '</div>'
                )
                st.markdown(table_html, unsafe_allow_html=True)

                footnote_parts = ['<span>💡 <b>Actual</b> = สถานการณ์จริง ณ วันที่บันทึก | <b>Predicted</b> = ผลพยากรณ์จากโมเดล AI</span>']
                if has_models and total_cnt > 0:
                    stats = []
                    if show_7d:
                        pct_7d = (match_7d_cnt / total_cnt) * 100.0
                        stats.append(f'ความสอดคล้อง 7 วัน: <b style="color:#0284c7;">{match_7d_cnt}/{total_cnt} วัน ({pct_7d:.1f}%)</b>')
                    if show_30d:
                        pct_30d = (match_30d_cnt / total_cnt) * 100.0
                        stats.append(f'ความสอดคล้อง 30 วัน: <b style="color:#0284c7;">{match_30d_cnt}/{total_cnt} วัน ({pct_30d:.1f}%)</b>')
                    if stats:
                        footnote_parts.append(f'<span>{" &nbsp;|&nbsp; ".join(stats)}</span>')

                footnote_html = f'<div style="font-size:0.75rem; color:#64748b; margin-top:8px; display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px;">{"".join(footnote_parts)}</div>'
                st.markdown(footnote_html, unsafe_allow_html=True)
            else:
                st.info("ไม่พบข้อมูลย้อนหลัง")
            st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)

    with b6_col:
        with st.container(border=True, key="sec_summary"):
            st.markdown(
                '<div id="section-summary" class="section-title">'
                '<span class="badge-num">7</span> สรุปสถานการณ์น้ำ</div>',
                unsafe_allow_html=True
            )
            # Resolve themes
            curr_theme = theme_curr or get_status_theme(classify_by_percent(pct))
            t_7d = theme_7d or get_status_theme("normal")
            t_30d = theme_30d or get_status_theme("normal")

            # Determine overall box theme based on highest risk (flood > drought > normal)
            box_theme = curr_theme
            all_themes = [curr_theme, t_7d, t_30d]
            if any(t.get("color") == "#dc2626" for t in all_themes):
                box_theme = get_status_theme("flood")
            elif any(t.get("color") == "#eab308" for t in all_themes):
                box_theme = get_status_theme("drought")

            summary_html = (
                f'<div style="background-color:{box_theme["bg_light"]}; border:1px solid {box_theme["border"]}; border-radius:8px; padding:16px; display:flex; gap:12px; align-items:flex-start;">'
                f'<div style="flex-shrink:0; margin-top:2px;">{svg_icon("document-check", 30, box_theme["color"])}</div>'
                f'<div style="font-size:0.85rem; color:#1e293b; line-height:1.65;">'
                f'สถานการณ์ปัจจุบันของอ่างเก็บน้ำ{selected_dam_name} อยู่ในระดับ <b style="color:{curr_theme["color"]};">{curr_theme["label_short"]}</b> โดยมีร้อยละความจุ <b>{pct:.2f}%</b> ปริมาณน้ำไหลเข้า <b>{inflow_m:.1f} ล้าน ลบ.ม./วัน</b> และปริมาณน้ำระบาย <b>{outflow_m:.1f} ล้าน ลบ.ม./วัน</b><br><br>'
                f'ผลการพยากรณ์ล่วงหน้า 7 วัน อยู่ในระดับ <b style="color:{t_7d["color"]};">{t_7d["label_short"]}</b> และพยากรณ์ล่วงหน้า 30 วัน อยู่ในระดับ <b style="color:{t_30d["color"]};">{t_30d["label_short"]}</b>'
                f'</div>'
                f'</div>'
            )
            st.markdown(summary_html, unsafe_allow_html=True)
            st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)

