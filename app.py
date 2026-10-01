"""
ไฟล์หลักสำหรับเริ่มต้นแอปพลิเคชัน (Main Entry Point)
ระบบพยากรณ์ระดับน้ำในอ่างเก็บน้ำขนาดใหญ่ของประเทศไทย (Dam Forecast Dashboard)
"""

import streamlit as st
from core.weka_model import init_jvm_safe, load_resources
from core.rid_api import fetch_and_save_data, backfill_historical_data
from views import user_view


# ==============================================================================
# ขั้นตอนที่ 1: ตั้งค่าหน้าเว็บ Streamlit (Page Configuration)
# ==============================================================================
st.set_page_config(
    page_title="ระบบพยากรณ์ระดับน้ำในอ่างเก็บน้ำ",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==============================================================================
# ขั้นตอนที่ 2: โหลดโมเดล Machine Learning (Weka Models)
# ==============================================================================
@st.cache_resource
def init_models():
    """เริ่มต้น Java Virtual Machine (JVM) และโหลดโมเดลพยากรณ์ 7 วัน และ 30 วัน (แคชไว้ในหน่วยความจำ)"""
    init_jvm_safe()
    return load_resources()

models_dict = init_models()


# ==============================================================================
# ขั้นตอนที่ 3: ดึงข้อมูลสถานการณ์น้ำประจำวัน (Daily Dam Data)
# ==============================================================================
# ดึงข้อมูลจากฐานข้อมูล/API (หากวันนี้ยังไม่มีข้อมูล จะใช้ข้อมูลเมื่อวานเป็น Input อัตโนมัติ)
raw_df, data_date, recorded_at = fetch_and_save_data()

# ตรวจสอบและดึงข้อมูลย้อนหลัง 30 วันในครั้งแรกที่เปิดเว็บ (ทำเพียง 1 ครั้งต่อเซสชัน)
if "backfill_checked" not in st.session_state:
    backfill_historical_data(lookback_days=30)
    st.session_state["backfill_checked"] = True


# ==============================================================================
# ขั้นตอนที่ 4: แสดงผลหน้าจอ Dashboard (Render Dashboard)
# ==============================================================================
if not raw_df.empty:
    user_view.render(raw_df, models_dict, data_date, recorded_at)
else:
    st.error("⚠️ ระบบไม่พร้อมใช้งาน: ไม่สามารถเชื่อมต่อฐานข้อมูลหรือดึงข้อมูลเขื่อนได้ในขณะนี้")
