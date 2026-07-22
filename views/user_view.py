# views/user_view.py
import html
import streamlit as st
import datetime
from core.weka_model import predict_single_dam
from core.utils import translate_status

# ฟังก์ชันดึงชุดสีให้สอดคล้องกับสถานะความเสี่ยง
def get_color_theme(status):
    if "flood" in status.lower() or "ล้น" in status:
        return {"bg": "#ff4b4b", "text": "white", "border": "#ff4b4b", "box_text": "#ff4b4b"}
    elif "drought" in status.lower() or "แล้ง" in status:
        return {"bg": "#ffa421", "text": "white", "border": "#ffa421", "box_text": "#ffa421"}
    else:
        return {"bg": "#28a745", "text": "white", "border": "#28a745", "box_text": "#28a745"}

def render(raw_df, models_dict, data_date=None, recorded_at=None):
    # ==========================
    # 1. Sidebar & Data Selection
    # ==========================
    with st.sidebar:
        st.subheader("เลือกอ่างเก็บน้ำ:")
        dam_list = raw_df['name'].tolist()
        selected_dam_name = st.selectbox("", dam_list, label_visibility="collapsed")
    
    # ดึงข้อมูลแถวของเขื่อนที่ถูกเลือก
    dam_matches = raw_df[raw_df['name'] == selected_dam_name]
    if dam_matches.empty:
        st.error("ไม่พบข้อมูลเขื่อนที่เลือก")
        return
    dam_data = dam_matches.iloc[0].copy()
    
    # 💡 [จุดเชื่อมลอจิก] หากโมเดลต้องการฟีเจอร์ที่ไม่มีใน API (เช่น ฤดูกาล) ให้ทำ Custom Mapping ข้อมูลตรงนี้ก่อนส่งเข้า predict ได้เลย

    # ==========================
    # 2. ประมวลผลและเตรียมข้อมูล
    # ==========================
    # ทำนายผล 7 วัน และ 30 วัน
    pred_7d_raw = predict_single_dam(dam_data, models_dict["7_day"])
    pred_30d_raw = predict_single_dam(dam_data, models_dict["30_day"])
    
    pred_7d = translate_status(pred_7d_raw)
    pred_30d = translate_status(pred_30d_raw)

    # คำนวณสถานการณ์ปัจจุบัน (อิงตามเกณฑ์ร้อยละความจุ > 80% น้ำล้น, < 30% น้ำแล้ง)
    pct = float(dam_data.get('percent_storage', 0))
    if pct > 80:
        current_status = "น้ำล้น (Flood)"
    elif pct < 30:
        current_status = "น้ำแล้ง (Drought)"
    else:
        current_status = "ปกติ (Normal)"

    # ดึง Theme สีเตรียมไว้
    curr_theme = get_color_theme(current_status)
    theme_7d = get_color_theme(pred_7d)
    theme_30d = get_color_theme(pred_30d)
    
    if recorded_at:
        current_date_str = recorded_at.strftime("%d/%m/%Y %H:%M น.")
    else:
        current_date_str = (data_date or datetime.date.today()).strftime("%d/%m/%Y")

    # ==========================
    # 3. วาด UI ด้วย HTML/CSS
    # ==========================
    safe_dam_name = html.escape(selected_dam_name)
    st.markdown(f"### สถานการณ์น้ำปัจจุบัน: {safe_dam_name}")
    
    # กล่องสถานะปัจจุบัน (พื้นหลังทึบ สีเปลี่ยนตามสถานการณ์)
    safe_current_status = html.escape(current_status)
    safe_pred_7d = html.escape(pred_7d)
    safe_pred_30d = html.escape(pred_30d)

    current_status_html = f"""
    <div style="background-color: {curr_theme['bg']}; padding: 50px 20px; border-radius: 12px; text-align: center; color: {curr_theme['text']}; margin-bottom: 40px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h1 style="font-size: 4rem; margin: 0 0 15px 0; color: {curr_theme['text']};">{safe_current_status}</h1>
        <p style="font-size: 1.2rem; margin: 0; opacity: 0.9;">สถานะ ณ วันที่ {current_date_str}</p>
    </div>
    """
    st.markdown(current_status_html, unsafe_allow_html=True)

    st.markdown("### การพยากรณ์ความเสี่ยงในอนาคต")
    
    col1, col2 = st.columns(2)
    
    with col1:
        box_7d_html = f"""
        <div style="border: 3px solid {theme_7d['border']}; border-radius: 12px; padding: 40px 20px; text-align: center; background-color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <p style="font-size: 1.1rem; color: #555; margin: 0 0 15px 0; font-weight: bold;">พยากรณ์ล่วงหน้า 7 วัน</p>
            <h2 style="font-size: 2.5rem; color: {theme_7d['box_text']}; margin: 0;">{safe_pred_7d}</h2>
        </div>
        """
        st.markdown(box_7d_html, unsafe_allow_html=True)
        
    with col2:
        box_30d_html = f"""
        <div style="border: 3px solid {theme_30d['border']}; border-radius: 12px; padding: 40px 20px; text-align: center; background-color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <p style="font-size: 1.1rem; color: #555; margin: 0 0 15px 0; font-weight: bold;">พยากรณ์ล่วงหน้า 30 วัน</p>
            <h2 style="font-size: 2.5rem; color: {theme_30d['box_text']}; margin: 0;">{safe_pred_30d}</h2>
        </div>
        """
        st.markdown(box_30d_html, unsafe_allow_html=True)