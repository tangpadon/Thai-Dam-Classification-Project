# views/admin_view.py
import streamlit as st
import plotly.express as px
from core.db import get_historical_data
from core.weka_model import predict_single_dam

def translate_status(status_text):
    status_lower = str(status_text).lower()
    if "flood" in status_lower: return "น้ำล้น (Flood)"
    elif "drought" in status_lower: return "น้ำแล้ง (Drought)"
    else: return "ปกติ (Normal)"

def render(raw_df, models_dict, data_date=None, recorded_at=None):
    st.title("🌊 Dam Forecast Dashboard")
    if recorded_at:
        time_str = recorded_at.strftime("%d/%m/%Y %H:%M น.")
    elif data_date:
        time_str = str(data_date)
    else:
        time_str = ""
    if time_str:
        st.caption(f"📅 ข้อมูลวันที่ {time_str}")
    
    with st.sidebar:
        st.subheader("ตัวกรองข้อมูล")
        dam_list = raw_df['name'].tolist()
        selected_dam_name = st.selectbox("เลือกอ่างเก็บน้ำ:", dam_list)
    
    dam_matches = raw_df[raw_df['name'] == selected_dam_name]
    if dam_matches.empty:
        st.error("ไม่พบข้อมูลเขื่อนที่เลือก")
        return
    dam_data = dam_matches.iloc[0]
    
    pred_7d = predict_single_dam(dam_data, models_dict["7_day"])
    pred_30d = predict_single_dam(dam_data, models_dict["30_day"])
    
    st.header(f"ข้อมูลของ: {selected_dam_name}")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("ความเสี่ยง (7 วัน)", pred_7d)
    with col2: st.metric("ความเสี่ยง (30 วัน)", pred_30d)
    with col3: st.metric("ร้อยละความจุ", f"{dam_data.get('percent_storage', 0)}%")
    with col4: st.metric("Inflow (M)", dam_data.get('inflow', 0))
    with col5: st.metric("Outflow (M)", dam_data.get('outflow', 0))

    st.subheader("📈 กราฟแนวโน้มร้อยละความจุย้อนหลัง")
    hist_df = get_historical_data(dam_data['id'])
    
    if not hist_df.empty and len(hist_df) > 1:
        fig = px.line(hist_df, x='record_date', y='percent_storage', markers=True)
        fig.update_layout(yaxis_range=[0, 100], xaxis_title="", yaxis_title="ร้อยละความจุ (%)")
        fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="เกณฑ์น้ำล้น (80%)")
        fig.add_hline(y=30, line_dash="dash", line_color="orange", annotation_text="เกณฑ์น้ำแล้ง (30%)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("กำลังสะสมข้อมูลประวัติ...")
        st.progress(int(float(dam_data.get('percent_storage', 0))))

    st.markdown("### สรุปแผนการจัดการน้ำ")
    status_7d_th = translate_status(pred_7d)
    status_30d_th = translate_status(pred_30d)
    is_risk_7d = "normal" not in str(pred_7d).lower()
    is_risk_30d = "normal" not in str(pred_30d).lower()

    if is_risk_7d and is_risk_30d:
        st.error(f"🚨 **ประกาศฉุกเฉิน:** เฝ้าระวังสูงสุด! 7 วัน: **{status_7d_th}** | 30 วัน: **{status_30d_th}**")
    elif is_risk_7d:
        st.warning(f"⚠️ **ประกาศเตือนระยะสั้น:** 7 วัน: **{status_7d_th}** (30 วัน: ปกติ)")
    elif is_risk_30d:
        st.warning(f"⚠️ **ประกาศเตือนระยะกลาง:** 7 วันนี้ปกติ แต่ 30 วันมีแนวโน้ม: **{status_30d_th}**")
    else:
        st.success(f"✅ **สถานการณ์ปกติ:** 7 วันและ 30 วันอยู่ในระดับ **{status_7d_th}**")