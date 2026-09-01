import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.db import get_historical_data
from core.weka_model import predict_single_dam

# สถานะน้ำ : จำแนก + ธีมสี + SVG ไอคอน
def _classify_by_percent(pct):
    try:
        pct = float(pct)
    except (TypeError, ValueError):
        return "ปกติ (Normal)"
    if pct > 80:
        return "น้ำล้น (Flood)"
    if pct < 30:
        return "น้ำแล้ง (Drought)"
    return "ปกติ (Normal)"


def _get_status_theme(status_text):
    s = str(status_text).lower()
    if "flood" in s or "ล้น" in s:
        return {"label": "น้ำล้น (Flood)", "label_short": "น้ำล้น", "en": "Flood",
                "color": "#dc2626", "bg_light": "#fef2f2", "border": "#ef4444", "icon": "waves"}
    if "drought" in s or "แล้ง" in s:
        return {"label": "น้ำแล้ง (Drought)", "label_short": "น้ำแล้ง", "en": "Drought",
                "color": "#d97706", "bg_light": "#fffbeb", "border": "#f59e0b", "icon": "sun"}
    return {"label": "ปกติ (Normal)", "label_short": "ปกติ", "en": "Normal",
            "color": "#16a34a", "bg_light": "#f0fdf4", "border": "#22c55e", "icon": "shield"}


def _fmt_num(val, nd=2):
    try:
        return f"{float(val):,.{nd}f}"
    except (TypeError, ValueError):
        return "-"


def _to_num(val):
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return float(str(val).replace(',', '').strip())
    except (TypeError, ValueError):
        return None


def _format_date_th(dt):
    months_th = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
                 "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    return f"{dt.day} {months_th[dt.month]} {dt.year + 543}"


# ---------- SVG icons (Feather - MIT) แทน emoji ----------
_SVG_PATHS = {
    "water":    '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path>',
    "home":     '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline>',
    "search":   '<circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>',
    "landmark": '<line x1="3" y1="22" x2="21" y2="22"></line><line x1="6" y1="18" x2="6" y2="11"></line><line x1="10" y1="18" x2="10" y2="11"></line><line x1="14" y1="18" x2="14" y2="11"></line><line x1="18" y1="18" x2="18" y2="11"></line><polygon points="12 2 20 7 4 7"></polygon>',
    "chart":    '<line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>',
    "clock":    '<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>',
    "info":     '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line>',
    "arrow-down": '<line x1="12" y1="5" x2="12" y2="19"></line><polyline points="19 12 12 19 5 12"></polyline>',
    "arrow-up": '<line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline>',
    "clipboard": '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>',
    "waves":    '<path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"></path><path d="M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"></path><path d="M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"></path>',
    "sun":      '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>',
    "shield":   '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>',
}


def _svg_icon(name, size=18, color="currentColor"):
    paths = _SVG_PATHS.get(name, "")
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display:inline-block; vertical-align:middle; flex-shrink:0;">{paths}</svg>')


# คอมโพเนนต์หน้า : การ์ดแสดงผลต่าง ๆ
def _card_box(inner, css=None):
    style_attr = " ".join(f"{k}:{v};" for k, v in (css or {}).items())
    return f'<div class="card-box" style="{style_attr}">{inner}</div>'


def _metric_card(label, value, sub=None, color="#0f172a", icon=None, icon_color=None):
    icon_html = f'<span style="display:inline-flex; vertical-align:middle;">{_svg_icon(icon, 20, icon_color)}</span> ' if icon else ""
    sub_html = f'<div style="font-size:0.75rem; color:#94a3b8;">{sub}</div>' if sub else ""
    return _card_box(f"""
        <div style="font-size:0.75rem; color:#64748b; margin-bottom:4px;">{label}</div>
        <div style="font-size:1.2rem; font-weight:700; color:{color}; display:flex; align-items:center; justify-content:center; gap:6px;">{icon_html}{value}</div>
        {sub_html}
    """, {"text-align": "center"})


def _pred_cards(items):
    cards = "".join(
        _card_box(f"""
            <div style="font-size:0.85rem; color:#64748b; margin-bottom:6px; display:flex; align-items:center; justify-content:center; gap:6px;">{_svg_icon("calendar", 15, "#64748b")} {title}</div>
            <div style="font-size:1.4rem; font-weight:700; color:{theme['color']};">{theme['label_short']}</div>
            <div style="font-size:0.8rem; color:#64748b;">({theme['en']})</div>
            <div style="font-size:0.75rem; color:#94a3b8; margin-top:4px;">{sub}</div>
        """, {"border-left": f"5px solid {theme['border']}", "flex": "1", "height": "100%",
            "display": "flex", "flex-direction": "column", "justify-content": "center"})
        for title, theme, sub in items
    )
    return f'<div style="display:flex; gap:16px; align-items:stretch;">{cards}</div>'


# Main Render
def render(raw_df, models_dict, data_date=None, recorded_at=None):
    st.markdown("""
        <style>
        .stApp { background-color: #f8fafc; }
        .badge-num { display: inline-flex; align-items: center; justify-content: center; background-color: #0284c7; color: white; border-radius: 50%; width: 22px; height: 22px; font-size: 13px; font-weight: bold; margin-right: 6px; }
        .section-title { font-size: 1.1rem; font-weight: 700; color: #1e293b; display: flex; align-items: center; margin-bottom: 12px; }
        .card-box { background: white; border-radius: 8px; padding: 14px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 8px; }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #e8f3ff;
            border: 1px solid #b9d8f7;
            border-radius: 12px;
            padding: 18px 18px 18px 18px;
            margin-bottom: 22px;
        }
        [data-testid="stVerticalBlockBorderWrapper"] > div { padding-bottom: 26px; }
        </style>
    """, unsafe_allow_html=True)

    # ---------- Sidebar ----------
    with st.sidebar:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom: 20px;">
            <span style="font-size:1.8rem; color:#0284c7; display:inline-flex;">{_svg_icon("water", 34, "#0284c7")}</span>
            <div>
                <h3 style="margin:0; font-size:1.1rem; color:#0f172a;">Dam Forecast</h3>
                <p style="margin:0; font-size:0.75rem; color:#64748b;">ระบบพยากรณ์ระดับสถานการณ์น้ำในอ่างเก็บน้ำ</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display:flex; flex-direction:column; gap:6px;">
            <div style="background-color:#eff6ff; color:#1d4ed8; padding:10px 14px; border-radius:8px; font-weight:600; font-size:0.9rem; display:flex; align-items:center; gap:8px;">{_svg_icon("home", 16, "#1d4ed8")} หน้าแรก (ภาพรวม)</div>
            <div style="color:#475569; padding:8px 14px; font-size:0.9rem; display:flex; align-items:center; gap:8px;">{_svg_icon("search", 16, "#475569")} ค้นหา / เลือกอ่างเก็บน้ำ</div>
            <div style="color:#475569; padding:8px 14px; font-size:0.9rem; display:flex; align-items:center; gap:8px;">{_svg_icon("landmark", 16, "#475569")} อ่างเก็บน้ำ</div>
            <div style="color:#475569; padding:8px 14px; font-size:0.9rem; display:flex; align-items:center; gap:8px;">{_svg_icon("chart", 16, "#475569")} แนวโน้มและกราฟ</div>
            <div style="color:#475569; padding:8px 14px; font-size:0.9rem; display:flex; align-items:center; gap:8px;">{_svg_icon("clock", 16, "#475569")} ข้อมูลย้อนหลัง</div>
            <div style="color:#475569; padding:8px 14px; font-size:0.9rem; display:flex; align-items:center; gap:8px;">{_svg_icon("info", 16, "#475569")} เกี่ยวกับระบบ</div>
        </div>
        """, unsafe_allow_html=True)

    # ---------- Header ----------
    _dt = recorded_at or data_date or datetime.date.today()
    if isinstance(_dt, datetime.date) and not isinstance(_dt, datetime.datetime):
        _dt = datetime.datetime.combine(_dt, datetime.time(8, 0))
    date_str = f"{_format_date_th(_dt)} เวลา {_dt.strftime('%H:%M')} น."
    saved_note = f"ข้อมูลที่ใช้ถูกบันทึกเมื่อ {date_str}" if recorded_at else f"ข้อมูล ณ วันที่ {date_str}"

    h_col1, h_col2 = st.columns([3, 1])
    with h_col1:
        st.markdown("## ระบบพยากรณ์ระดับสถานการณ์น้ำ")
        st.caption(saved_note)
    with h_col2:
        st.markdown(f'<div style="text-align:right; font-size:0.85rem; color:#64748b; margin-top:10px; display:flex; align-items:center; justify-content:flex-end; gap:6px;">{_svg_icon("calendar", 15, "#64748b")} {date_str}</div>', unsafe_allow_html=True)

    # ---------- 1. เลือกอ่างเก็บน้ำ ----------
    top_left, top_right = st.columns([1.2, 2.8])
    with top_left:
        with st.container(border=True):
            st.markdown('<div class="section-title"><span class="badge-num">1</span> เลือกอ่างเก็บน้ำ</div>', unsafe_allow_html=True)
            selected_dam_name = st.selectbox("อ่างเก็บน้ำ", raw_df['name'].tolist())
            dam_data = raw_df[raw_df['name'] == selected_dam_name].iloc[0]
            st.markdown(_card_box(f"""
                <div style="display:flex; align-items:center; gap:15px; margin-top:8px;">
                    <span style="font-size:2.2rem; color:#0284c7; display:inline-flex;">{_svg_icon("landmark", 40, "#0284c7")}</span>
                    <div>
                        <div style="font-weight:700; font-size:1.1rem; color:#0f172a;">{selected_dam_name}</div>
                        <div style="font-size:0.85rem; color:#64748b;">{dam_data.get("province", "จังหวัดตาก")}</div>
                    </div>
                </div>
            """), unsafe_allow_html=True)

    # ---------- คำนวณพยากรณ์ ----------
    pct = float(dam_data.get('percent_storage', 0) or 0)
    theme_curr = _get_status_theme(_classify_by_percent(pct))
    theme_7d = _get_status_theme(predict_single_dam(dam_data, models_dict["7_day"]))
    theme_30d = _get_status_theme(predict_single_dam(dam_data, models_dict["30_day"]))
    inflow_m = float(dam_data.get('inflow', 0) or 0)
    outflow_m = float(dam_data.get('outflow', 0) or 0)

    # ---------- 2. ภาพรวมสถานการณ์น้ำปัจจุบัน ----------
    with top_right:
        with st.container(border=True):
            st.markdown('<div class="section-title"><span class="badge-num">2</span> ภาพรวมสถานการณ์น้ำปัจจุบัน</div>', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(_metric_card("ระดับสถานการณ์น้ำ", theme_curr['label_short'], f"({theme_curr['en']})",
                                         theme_curr['color'], theme_curr['icon'], theme_curr['color']), unsafe_allow_html=True)
            with c2:
                st.markdown(_metric_card("ร้อยละความจุ", f"{pct:,.2f}%", "% Capacity",
                                         "#0284c7", "water", "#0284c7"), unsafe_allow_html=True)
            with c3:
                st.markdown(_metric_card("ปริมาณน้ำไหลเข้า (Inflow)", f"{inflow_m:,.1f}M", "ลบ.ม./วัน",
                                         "#0f172a", "arrow-down", "#16a34a"), unsafe_allow_html=True)
            with c4:
                st.markdown(_metric_card("ปริมาณน้ำระบาย (Outflow)", f"{outflow_m:,.1f}M", "ลบ.ม./วัน",
                                         "#0f172a", "arrow-up", "#dc2626"), unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)

    # ---------- 3. ผลการพยากรณ์ ----------
    d_start_7 = _dt + datetime.timedelta(days=1)
    d_end_7 = _dt + datetime.timedelta(days=7)
    d_end_30 = _dt + datetime.timedelta(days=30)
    with st.container(border=True):
        st.markdown('<div class="section-title"><span class="badge-num">3</span> ผลการพยากรณ์ระดับสถานการณ์น้ำ</div>', unsafe_allow_html=True)
        st.markdown(_pred_cards([
            ("สถานการณ์ปัจจุบัน", theme_curr, f"ข้อมูลวันที่ {_format_date_th(_dt)}"),
            ("พยากรณ์ล่วงหน้า 7 วัน", theme_7d, f"ช่วงวันที่ {_format_date_th(d_start_7)} - {_format_date_th(d_end_7)}"),
            ("พยากรณ์ล่วงหน้า 30 วัน", theme_30d, f"ช่วงวันที่ {_format_date_th(d_start_7)} - {_format_date_th(d_end_30)}"),
        ]), unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)

    # ---------- 4. กราฟแนวโน้ม + รายละเอียด ----------
    with st.container(border=True):
        m_left, m_right = st.columns([1.8, 1.2])
        with m_left:
            g_head1, g_head2 = st.columns([2, 1])
            with g_head1:
                st.markdown('<div class="section-title"><span class="badge-num">4</span> แนวโน้มร้อยละความจุของอ่างเก็บน้ำย้อนหลัง</div>', unsafe_allow_html=True)
            with g_head2:
                time_range = st.selectbox("ช่วงเวลา", ["30 วันล่าสุด", "7 วันล่าสุด"], label_visibility="collapsed", filter_mode=None)
            limit_days = 30 if "30" in time_range else 7
            hist_df = get_historical_data(dam_data['id'], limit=limit_days)

            if not hist_df.empty and len(hist_df) > 1:
                hist_df = hist_df.sort_values('record_date').reset_index(drop=True)
                hist_df['record_date'] = pd.to_datetime(hist_df['record_date'])
                daily = (hist_df.sort_values('record_date')
                                .groupby(hist_df['record_date'].dt.date)
                                .tail(1)
                                .reset_index(drop=True))
                if len(daily) > 1:
                    x_start = daily['record_date'].dt.normalize().min()
                    x_end = daily['record_date'].max() + pd.Timedelta(hours=12)
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=daily['record_date'], y=daily['percent_storage'],
                                             mode='lines+markers', line=dict(color='#0284c7', width=2),
                                             marker=dict(size=5), name='ร้อยละความจุ (%)',
                                             hovertemplate='%{x|%d/%m/%Y}<br>ร้อยละความจุ: %{y:.2f}%<extra></extra>'))
                    fig.add_hline(y=80, line_dash="dash", line_color="#ef4444", annotation_text="เกณฑ์เสี่ยงน้ำล้น (80%)", annotation_position="top right")
                    fig.add_hline(y=30, line_dash="dash", line_color="#f59e0b", annotation_text="เกณฑ์เสี่ยงน้ำแห้ง (30%)", annotation_position="bottom right")
                    fig.update_layout(yaxis=dict(range=[0, 100], title="ร้อยละความจุ (%)"),
                                      margin=dict(l=10, r=10, t=20, b=10), height=320,
                                      xaxis=dict(range=[x_start, x_end],
                                                 tickformat="%d/%m",
                                                 dtick=f"D{limit_days // 6}"),
                                      hovermode="x unified",
                                      hoverlabel=dict(font_size=12),
                                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                      dragmode=False)
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False, 'doubleClick': False})
                else:
                    st.info("ไม่พบข้อมูลประวัติย้อนหลังสำหรับการแสดงผลกราฟ")
            else:
                st.info("ไม่พบข้อมูลประวัติย้อนหลังสำหรับการแสดงผลกราฟ")

        with m_right:
            st.markdown('<div class="section-title"><span class="badge-num">4</span> รายละเอียดข้อมูลอ่างเก็บน้ำ</div>', unsafe_allow_html=True)
            rows = [
                ("ชื่ออ่างเก็บน้ำ", selected_dam_name),
                ("ความจุที่ระดับเก็บกัก (ความจุรวม)", f"{_fmt_num(dam_data.get('capacity'), 0)} ล้าน ลบ.ม."),
                ("ปริมาณน้ำกักเก็บปัจจุบัน", f"{_fmt_num(dam_data.get('storage'), 0)} ล้าน ลบ.ม."),
                ("ร้อยละความจุปัจจุบัน", f"{pct:.2f} %"),
                ("ระดับน้ำปัจจุบัน", f"{dam_data.get('water_level', '-')} ม. (รทก.)"),
                ("ปริมาณน้ำไหลเข้า (Inflow)", f"{inflow_m:.1f} ล้าน ลบ.ม./วัน"),
                ("ปริมาณน้ำระบาย (Outflow)", f"{outflow_m:.1f} ล้าน ลบ.ม./วัน"),
                ("หน่วยงานรับผิดชอบ", dam_data.get('agency', 'การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย')),
            ]
            rows_html = "".join(
                f'<tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:8px 12px; font-weight:600; color:#475569;">{k}</td>'
                f'<td style="padding:8px 12px; text-align:right;">{v}</td></tr>'
                for k, v in rows
            )
            st.markdown(
                f'<table style="width:100%; border-collapse:collapse; font-size:0.85rem; background:white; border-radius:8px; border:1px solid #e2e8f0;">{rows_html}</table>',
                unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)

    # ---------- 5. ข้อมูลย้อนหลัง (ตาราง) ----------
    with st.container(border=True):
        st.markdown('<div class="section-title"><span class="badge-num">5</span> ข้อมูลย้อนหลัง (ตาราง)</div>', unsafe_allow_html=True)
        if not hist_df.empty:
            t_df = hist_df.copy()
            t_df['วันที่'] = pd.to_datetime(t_df['record_date'])
            fmt = lambda v: f"{_to_num(v):.2f}" if _to_num(v) is not None else "-"
            t_df['ร้อยละความจุ (%)'] = t_df['percent_storage'].apply(fmt)
            t_df['ปริมาณน้ำกักเก็บ (ล้าน ลบ.ม.)'] = t_df.get('storage', pd.Series([_fmt_num(dam_data.get('storage'), 0)] * len(t_df))).apply(lambda v: f"{_to_num(v):,.0f}" if _to_num(v) is not None else "-")
            t_df['Inflow (ล้าน ลบ.ม./วัน)'] = t_df['inflow'].apply(fmt)
            t_df['Outflow (ล้าน ลบ.ม./วัน)'] = t_df['outflow'].apply(fmt)
            t_df['ระดับสถานการณ์น้ำ'] = t_df['percent_storage'].apply(lambda v: _get_status_theme(_classify_by_percent(_to_num(v)))['label'])
            disp_cols = ['วันที่', 'ร้อยละความจุ (%)', 'ปริมาณน้ำกักเก็บ (ล้าน ลบ.ม.)', 'Inflow (ล้าน ลบ.ม./วัน)', 'Outflow (ล้าน ลบ.ม./วัน)', 'ระดับสถานการณ์น้ำ']
            st.dataframe(t_df[disp_cols].sort_values('วันที่', ascending=False),
                         column_config={"วันที่": st.column_config.DateColumn("วันที่", format="DD/MM/YYYY")},
                         use_container_width=True, hide_index=True)

    # ---------- 6. สรุปสถานการณ์น้ำ ----------
    if "flood" in theme_7d['en'].lower() or "flood" in theme_30d['en'].lower():
        box_theme = _get_status_theme("flood")
    elif "drought" in str(theme_7d['en']).lower() or "drought" in str(theme_30d['en']).lower():
        box_theme = _get_status_theme("drought")
    else:
        box_theme = theme_curr

    with st.container(border=True):
        st.markdown('<div class="section-title"><span class="badge-num">6</span> สรุปสถานการณ์น้ำ</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background-color:{box_theme['bg_light']}; border:1px solid {box_theme['border']}; border-radius:8px; padding:16px; display:flex; gap:12px; align-items:flex-start;">
            <span style="font-size:1.5rem; display:inline-flex; color:{box_theme['color']};">{_svg_icon("clipboard", 32, box_theme['color'])}</span>
            <div style="font-size:0.9rem; color:#1e293b; line-height:1.6;">
                <b>สถานการณ์น้ำปัจจุบันของอ่างเก็บน้ำ{selected_dam_name}</b> อยู่ในระดับ <b style="color:{theme_curr['color']};">{theme_curr['label_short']}</b><br>
                โดยมีร้อยละความจุ <b>{pct:.2f}%</b> ปริมาณน้ำไหลเข้า <b>{inflow_m:.1f} ล้าน ลบ.ม./วัน</b> และปริมาณน้ำระบาย <b>{outflow_m:.1f} ล้าน ลบ.ม./วัน</b><br><br>
                ผลการพยากรณ์ล่วงหน้า 7 วัน อยู่ในระดับ <b style="color:{theme_7d['color']};">{theme_7d['label_short']}</b><br>
                และพยากรณ์ล่วงหน้า 30 วัน อยู่ในระดับ <b style="color:{theme_30d['color']};">{theme_30d['label_short']}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ---------- Footer ----------
    st.markdown("""
    <div style="text-align:center; color:#94a3b8; font-size:0.8rem; margin-top:25px;">
        หมายเหตุ: ข้อมูลนี้อาจมีข้อผิดพลาดหรือไม่สมบูรณ์ และเป็นเพียงการพยากรณ์เท่านั้น โปรดใช้วิจารณญาณในการตัดสินใจ
    </div>
    """, unsafe_allow_html=True)
