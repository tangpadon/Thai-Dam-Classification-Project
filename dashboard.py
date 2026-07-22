import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.db import get_historical_data
from core.rid_api import fetch_and_save_data, backfill_historical_data
from core.weka_model import init_jvm_safe, load_resources, predict_single_dam
from core.utils import translate_status

st.set_page_config(page_title="Dam Forecast", layout="wide", initial_sidebar_state="expanded")

init_jvm_safe()
models_dict = load_resources()
raw_df, data_date, recorded_at = fetch_and_save_data()
backfill_historical_data(lookback_days=30)

if not raw_df.empty:
    with st.sidebar:
        st.title("Dam Forecast")
        dam_list = raw_df['name'].tolist()
        selected_dam_name = st.selectbox("เลือกอ่างเก็บน้ำ:", dam_list)

    dam_matches = raw_df[raw_df['name'] == selected_dam_name]
    if dam_matches.empty:
        st.error("ไม่พบข้อมูลเขื่อนที่เลือก")
        st.stop()
    dam_data = dam_matches.iloc[0]

    pred_7d = predict_single_dam(dam_data, models_dict["7_day"])
    pred_30d = predict_single_dam(dam_data, models_dict["30_day"])

    st.header(f"ข้อมูลของ: {selected_dam_name}")
    time_str = recorded_at.strftime("%d/%m/%Y %H:%M น.") if recorded_at else str(data_date)
    st.caption(f"📅 ข้อมูลวันที่ {time_str}")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("ความเสี่ยง (7 วัน)", pred_7d)
    with col2: st.metric("ความเสี่ยง (30 วัน)", pred_30d)
    with col3: st.metric("ร้อยละความจุ", f"{dam_data.get('percent_storage', 0)}%")
    with col4: st.metric("Inflow (ลบ.ม./วัน)", dam_data.get('inflow', 0))
    with col5: st.metric("Outflow (ลบ.ม./วัน)", dam_data.get('outflow', 0))

    st.subheader("📈 กราฟแนวโน้มย้อนหลัง (Percent Storage / Inflow / Outflow)")
    hist_df = get_historical_data(dam_data['id'])

    if not hist_df.empty and len(hist_df) > 1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist_df['record_date'], y=hist_df['percent_storage'],
            name='% Storage', mode='lines+markers',
            line=dict(color='#1f77b4', width=2), marker=dict(size=6), yaxis='y1'
        ))
        fig.add_trace(go.Scatter(
            x=hist_df['record_date'], y=hist_df['inflow'],
            name='Inflow', mode='lines+markers',
            line=dict(color='#2ca02c', width=2, dash='dash'), marker=dict(size=6), yaxis='y2'
        ))
        fig.add_trace(go.Scatter(
            x=hist_df['record_date'], y=hist_df['outflow'],
            name='Outflow', mode='lines+markers',
            line=dict(color='#d62728', width=2, dash='dash'), marker=dict(size=6), yaxis='y2'
        ))

        io_vals = hist_df[['inflow', 'outflow']].dropna().values.flatten()
        io_min, io_max = max(0, io_vals.min() - 5), io_vals.max() + 5

        fig.add_hline(y=80, line_dash="dot", line_color="red", annotation_text="น้ำล้น (80%)", yref='y1')
        fig.add_hline(y=30, line_dash="dot", line_color="orange", annotation_text="น้ำแล้ง (30%)", yref='y1')
        fig.update_layout(
            yaxis=dict(title="ร้อยละความจุ (%)", range=[0, 100]),
            yaxis2=dict(title="Inflow / Outflow (ล้านลบ.ม./วัน)", overlaying='y', side='right',
                        range=[io_min, io_max]),
            xaxis_title="",
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=450
        )
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
else:
    st.error("ไม่พบข้อมูลจากระบบ โปรดตรวจสอบการเชื่อมต่อ API ของกรมชลประทาน")
