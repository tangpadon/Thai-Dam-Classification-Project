# views/user_view.py
import streamlit as st
import datetime
from weka_model import predict_single_dam

# ฟังก์ชันแปลผลจากภาษาอังกฤษของ Weka เป็นภาษาไทย
def translate_status(status_text):
    status_lower = str(status_text).lower()
    if "flood" in status_lower: 
        return "น้ำล้น (Flood)"
    elif "drought" in status_lower: 
        return "น้ำแล้ง (Drought)"
    else: 
        return "ปกติ (Normal)"

# ฟังก์ชันดึงชุดสีให้สอดคล้องกับสถานะความเสี่ยง
def get_color_theme(status):
    if "flood" in status.lower() or "ล้น" in status:
        return {"bg": "#ff4b4b", "text": "white", "border": "#ff4b4b", "box_text": "#ff4b4b"}
    elif "drought" in status.lower() or "แล้ง" in status:
        return {"bg": "#ffa421", "text": "white", "border": "#ffa421", "box_text": "#ffa421"}
    else:
        return {"bg": "#28a745", "text": "white", "border": "#28a745", "box_text": "#28a745"}

def render(raw_df, models_dict):
    # ==========================
    # 1. Sidebar & Data Selection
    # ==========================
    with st.sidebar:
        st.subheader("เลือกอ่างเก็บน้ำ:")
        dam_list = raw_df['name'].tolist()
        selected_dam_name = st.selectbox("", dam_list, label_visibility="collapsed")
    
    # ดึงข้อมูลแถวของเขื่อนที่ถูกเลือก
    dam_data = raw_df[raw_df['name'] == selected_dam_name].iloc[0].copy()
    
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
    
    current_date_str = datetime.datetime.now().strftime("%d/%m/%Y")

    # ==========================
    # 3. วาด UI ด้วย HTML/CSS
    # ==========================
    st.markdown(f"### สถานการณ์น้ำปัจจุบัน: {selected_dam_name}")
    
    # กล่องสถานะปัจจุบัน (พื้นหลังทึบ สีเปลี่ยนตามสถานการณ์)
    current_status_html = f"""
    <div style="background-color: {curr_theme['bg']}; padding: 50px 20px; border-radius: 12px; text-align: center; color: {curr_theme['text']}; margin-bottom: 40px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h1 style="font-size: 4rem; margin: 0 0 15px 0; color: {curr_theme['text']};">{current_status}</h1>
        <p style="font-size: 1.2rem; margin: 0; opacity: 0.9;">สถานะ ณ วันที่ {current_date_str}</p>
    </div>
    """
    st.markdown(current_status_html, unsafe_allow_html=True)

    st.markdown("### การพยากรณ์ความเสี่ยงในอนาคต")
    
    col1, col2 = st.columns(2)
    
    # กล่องพยากรณ์ 7 วัน (พื้นฐานโปร่งขาว เส้นขอบและข้อความสีเปลี่ยนตามสถานการณ์)
    with col1:
        box_7d_html = f"""
        <div style="border: 3px solid {theme_7d['border']}; border-radius: 12px; padding: 40px 20px; text-align: center; background-color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <p style="font-size: 1.1rem; color: #555; margin: 0 0 15px 0; font-weight: bold;">พยากรณ์ล่วงหน้า 7 วัน</p>
            <h2 style="font-size: 2.5rem; color: {theme_7d['box_text']}; margin: 0;">{pred_7d}</h2>
        </div>
        """
        st.markdown(box_7d_html, unsafe_allow_html=True)
        
    # กล่องพยากรณ์ 30 วัน
    with col2:
        box_30d_html = f"""
        <div style="border: 3px solid {theme_30d['border']}; border-radius: 12px; padding: 40px 20px; text-align: center; background-color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <p style="font-size: 1.1rem; color: #555; margin: 0 0 15px 0; font-weight: bold;">พยากรณ์ล่วงหน้า 30 วัน</p>
            <h2 style="font-size: 2.5rem; color: {theme_30d['box_text']}; margin: 0;">{pred_30d}</h2>
        </div>
        """
        st.markdown(box_30d_html, unsafe_allow_html=True)