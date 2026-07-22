# app.py
import streamlit as st
from core.weka_model import init_jvm_safe, load_resources
from core.rid_api import fetch_and_save_data, backfill_historical_data

from views import admin_view
from views import user_view
from views import manual_test_view

st.set_page_config(page_title="Dam Forecast System", layout="wide", initial_sidebar_state="expanded")

init_jvm_safe()
models_dict = load_resources()

raw_df, data_date, recorded_at = fetch_and_save_data()
backfill_historical_data(lookback_days=30)

if not raw_df.empty:
    st.sidebar.title("🔐 Authentication")
    user_role = st.sidebar.selectbox("เลือกมุมมอง (Role):", ["Administrator", "General User", "Manual Test"])

    st.sidebar.markdown("---")

    if user_role == "Administrator":
        admin_view.render(raw_df, models_dict, data_date, recorded_at)
    elif user_role == "General User":
        user_view.render(raw_df, models_dict, data_date, recorded_at)
    elif user_role == "Manual Test":
        manual_test_view.render(raw_df, models_dict, data_date, recorded_at)
else:
    st.error("ระบบไม่พร้อมใช้งาน: ไม่สามารถดึงข้อมูลตั้งต้นได้")
