# app.py
import streamlit as st
from weka_model import init_jvm_safe, load_resources
from rid_api import fetch_and_save_data

# นำเข้า Views ที่แยกไว้
from views import admin_view
from views import user_view  # เตรียมไว้สร้างหน้าสำหรับผู้ใช้ทั่วไป

st.set_page_config(page_title="Dam Forecast System", layout="wide", initial_sidebar_state="expanded")

# 1. Initialize Core Systems
init_jvm_safe()
models_dict = load_resources()

# 2. Fetch Base Data
raw_df = fetch_and_save_data()

# 3. Role-Based Navigation
if not raw_df.empty:
    st.sidebar.title("🔐 Authentication")
    user_role = st.sidebar.selectbox("เลือกมุมมอง (Role):", ["Administrator", "General User"])
    
    st.sidebar.markdown("---")
    
    # Router สำหรับสลับหน้าจอตาม Role
    if user_role == "Administrator":
        # เรียกหน้าแดชบอร์ดตัวเต็มแบบที่เราทำกันเมื่อกี้
        admin_view.render(raw_df, models_dict)
        
    elif user_role == "General User":
        user_view.render(raw_df, models_dict) 
        #st.title("🌊 ข้อมูลสถานการณ์น้ำสำหรับประชาชน")
        #st.info("กำลังออกแบบหน้าแสดงผลสำหรับผู้ใช้งานทั่วไป...")
else:
    st.error("ระบบไม่พร้อมใช้งาน: ไม่สามารถดึงข้อมูลตั้งต้นได้")