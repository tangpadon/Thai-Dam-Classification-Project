"""
User View Module for Dam Forecast Dashboard.
Orchestrates styles, scripts, and components for Sections 1 to 7.
"""

import streamlit as st
import streamlit.components.v1 as components

from views.styles import get_custom_css, get_client_js
from views.utils import classify_by_percent, get_status_theme, to_num
from core.db import get_yesterday_valid_data
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
    """Main entry point to render the Dam Forecast dashboard."""
    # 1. Inject Styles
    st.markdown(get_custom_css(), unsafe_allow_html=True)

    # 2. Sidebar Navigation
    render_sidebar()

    # 3. Main Header (Title & Timestamp)
    _dt = render_header(recorded_at=recorded_at, data_date=data_date)

    # 4. Section 1 & Section 2 (Top Row)
    top_left, top_right = st.columns([1.1, 1.4])
    with top_left:
        selected_dam_name, dam_data = render_dam_selector(raw_df)

    # ตรวจสอบว่าวันนี้มีค่า input ของเขื่อนนี้หรือไม่ หากไม่มีเลย ให้ดึงค่าจากเมื่อวาน
    dam_dict = dict(dam_data)
    pct_raw = to_num(dam_dict.get('percent_storage'))
    vol_raw = to_num(dam_dict.get('volume'))
    has_input = (pct_raw is not None and pct_raw > 0) or (vol_raw is not None and vol_raw > 0)

    is_fallback = False
    fallback_date = None
    if not has_input:
        dam_id = dam_dict.get('id') or dam_dict.get('dam_id')
        y_data = get_yesterday_valid_data(dam_id, current_date=data_date)
        if y_data:
            if y_data.get('percent_storage') is not None:
                dam_dict['percent_storage'] = float(y_data['percent_storage'])
            if y_data.get('volume') is not None:
                dam_dict['volume'] = float(y_data['volume'])
            if y_data.get('inflow') is not None:
                dam_dict['inflow'] = float(y_data['inflow'])
            if y_data.get('outflow') is not None:
                dam_dict['outflow'] = float(y_data['outflow'])
            is_fallback = True
            fallback_date = y_data.get('record_date')
            dam_data = dam_dict

    pct = float(dam_data.get('percent_storage', 0) or 0)
    if pct <= 0 and dam_data.get('volume') and dam_data.get('capacity'):
        cap = float(dam_data.get('capacity', 0) or 0)
        vol = float(dam_data.get('volume', 0) or 0)
        if cap > 0:
            pct = (vol / cap) * 100.0
            if isinstance(dam_data, dict):
                dam_data['percent_storage'] = pct

    theme_curr = get_status_theme(classify_by_percent(pct))
    inflow_m = float(dam_data.get('inflow', 0) or 0)
    outflow_m = float(dam_data.get('outflow', 0) or 0)

    with top_right:
        render_current_overview(dam_data, theme_curr, pct, inflow_m, outflow_m)

    # 5. Section 3: Forecast Cards
    theme_7d, theme_30d = render_forecast_cards(
        dam_data, models_dict, _dt, theme_curr,
        is_fallback=is_fallback, fallback_date=fallback_date
    )

    # 6. Section 4 (Trend Chart) & Section 5 (Dam Details)
    hist_df = render_trend_and_details(dam_data, selected_dam_name, pct, inflow_m, outflow_m)

    # 7. Section 6 (Historical Table) & Section 7 (Summary Box)
    render_history_and_summary(
        dam_data, selected_dam_name, pct, inflow_m, outflow_m, hist_df,
        theme_curr=theme_curr, theme_7d=theme_7d, theme_30d=theme_30d,
        models_dict=models_dict
    )

    # 8. Footer Note
    render_footer()

    # 9. Client-side JavaScript (Smooth scrolling, Search icon, Section padding)
    components.html(get_client_js(), height=0, width=0)
