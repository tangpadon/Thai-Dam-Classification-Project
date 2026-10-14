import streamlit as st
from core.risk_predictor import init_jvm_safe, load_resources
from core.dam_api import fetch_and_save_data, backfill_historical_data
from views import dashboard


# Streamlit Page Configuration
st.set_page_config(
    page_title="ระบบพยากรณ์ระดับน้ำในอ่างเก็บน้ำ",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ฟังก์ชันเริ่มต้นการทำงานของ JVM และโหลดแบบจำลอง Weka (Initialize Models)
@st.cache_resource
def init_models():
    init_jvm_safe()
    return load_resources()


models_dict = init_models()


# Daily Dam Data
raw_df, data_date, recorded_at = fetch_and_save_data()

# ตรวจสอบและดึงข้อมูลย้อนหลัง 30 วันในครั้งแรกที่เปิดเว็บ
if "backfill_checked" not in st.session_state:
    backfill_historical_data(lookback_days=30)
    st.session_state["backfill_checked"] = True


# Render Dashboard
if not raw_df.empty:
    dashboard.render(raw_df, models_dict, data_date, recorded_at)

else:
    fetch_and_save_data.clear()
    st.error("ไม่สามารถเชื่อมต่อฐานข้อมูลหรือดึงข้อมูลเขื่อนได้ในขณะนี้")
