import html
import streamlit as st
import datetime
import pandas as pd
from core.weka_model import predict_single_dam
from core.utils import translate_status


def get_color_theme(status):
    if "flood" in status.lower() or "ล้น" in status:
        return {"bg": "#ff4b4b", "text": "white", "border": "#ff4b4b", "box_text": "#ff4b4b"}
    elif "drought" in status.lower() or "แล้ง" in status:
        return {"bg": "#ffa421", "text": "white", "border": "#ffa421", "box_text": "#ffa421"}
    else:
        return {"bg": "#28a745", "text": "white", "border": "#28a745", "box_text": "#28a745"}


def render(raw_df, models_dict, data_date=None, recorded_at=None):
    st.title("🧪 ทดสอบพยากรณ์ด้วยข้อมูลกำหนดเอง")

    st.markdown("กรอกค่าที่ต้องการเพื่อทดสอบการทำนายของโมเดลในสถานการณ์ต่างๆ")

    dam_list = raw_df['name'].tolist()
    dam_ids = raw_df['id'].tolist()
    dam_map = dict(zip(dam_list, dam_ids))

    with st.form("manual_input_form"):
        st.subheader("ข้อมูลเขื่อน")
        col_dam, col_month = st.columns(2)
        with col_dam:
            selected_dam_name = st.selectbox("เลือกอ่างเก็บน้ำ:", dam_list)
        with col_month:
            month = st.selectbox("เดือน:", list(range(1, 13)),
                                 format_func=lambda m: datetime.date(2024, m, 1).strftime("%B"),
                                 index=datetime.date.today().month - 1)

        st.subheader("ค่าพารามิเตอร์")
        col1, col2, col3 = st.columns(3)
        with col1:
            percent_storage = st.slider("ร้อยละความจุ (%)", 0.0, 100.0, 50.0, step=0.1)
        with col2:
            inflow = st.number_input("Inflow (ล้านลบ.ม./วัน)", min_value=0.0, value=10.0, step=0.1)
        with col3:
            outflow = st.number_input("Outflow (ล้านลบ.ม./วัน)", min_value=0.0, value=10.0, step=0.1)

        submitted = st.form_submit_button("พยากรณ์", use_container_width=True)

    if submitted:
        dam_data = pd.Series({
            "id": dam_map[selected_dam_name],
            "name": selected_dam_name,
            "percent_storage": percent_storage,
            "inflow": inflow,
            "outflow": outflow,
            "month": month,
        })

        pred_7d_raw = predict_single_dam(dam_data, models_dict["7_day"])
        pred_30d_raw = predict_single_dam(dam_data, models_dict["30_day"])

        pred_7d = translate_status(pred_7d_raw)
        pred_30d = translate_status(pred_30d_raw)

        if percent_storage > 80:
            current_status = "น้ำล้น (Flood)"
        elif percent_storage < 30:
            current_status = "น้ำแล้ง (Drought)"
        else:
            current_status = "ปกติ (Normal)"

        curr_theme = get_color_theme(current_status)
        theme_7d = get_color_theme(pred_7d)
        theme_30d = get_color_theme(pred_30d)

        st.markdown("---")

        safe_dam_name = html.escape(selected_dam_name)
        safe_current_status = html.escape(current_status)
        safe_pred_7d = html.escape(pred_7d)
        safe_pred_30d = html.escape(pred_30d)

        current_status_html = f"""
        <div style="background-color: {curr_theme['bg']}; padding: 50px 20px; border-radius: 12px; text-align: center; color: {curr_theme['text']}; margin-bottom: 40px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h1 style="font-size: 4rem; margin: 0 0 15px 0; color: {curr_theme['text']};">{safe_current_status}</h1>
            <p style="font-size: 1.2rem; margin: 0; opacity: 0.9;">สถานะที่กรอก: {safe_dam_name} | ความจุ {percent_storage}%</p>
        </div>
        """
        st.markdown(current_status_html, unsafe_allow_html=True)

        st.markdown("### ผลการพยากรณ์")

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
