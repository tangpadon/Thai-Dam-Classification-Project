import streamlit as st
from core.risk_predictor import init_jvm_safe, load_resources
from core.dam_api import fetch_and_save_data, backfill_historical_data
from views import dashboard


# 1. ตั้งค่าหน้าเว็บ Streamlit (Page Configuration)
st.set_page_config(
    page_title="ระบบพยากรณ์ระดับน้ำในอ่างเก็บน้ำ",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# 2. โหลดโมเดล Machine Learning (Weka Models)
@st.cache_resource
def init_models():
    init_jvm_safe()
    return load_resources()

models_dict = init_models()


# 3. ดึงข้อมูลสถานการณ์น้ำประจำวัน (Daily Dam Data)
raw_df, data_date, recorded_at = fetch_and_save_data()

# ตรวจสอบและดึงข้อมูลย้อนหลัง 30 วันในครั้งแรกที่เปิดเว็บ (ทำเพียง 1 ครั้งต่อเซสชัน)
if "backfill_checked" not in st.session_state:
    backfill_historical_data(lookback_days=30)
    st.session_state["backfill_checked"] = True


# 4. แสดงผลหน้าจอ Dashboard (Render Dashboard)
if not raw_df.empty:
    dashboard.render(raw_df, models_dict, data_date, recorded_at)

else:
    fetch_and_save_data.clear()
    st.error("⚠️ ระบบไม่พร้อมใช้งาน: ไม่สามารถเชื่อมต่อฐานข้อมูลหรือดึงข้อมูลเขื่อนได้ในขณะนี้")
