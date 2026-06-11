import streamlit as st
import pandas as pd
import requests
import datetime
import mysql.connector
import plotly.express as px
import jpype
import weka.core.jvm as jvm
import weka.core.serialization as serialization
from weka.classifiers import Classifier
from weka.core.dataset import Instance
from weka.core.converters import Loader

# ==========================================
# ⚙️ CONFIG & INITIALIZATION
# ==========================================
st.set_page_config(page_title="Dam Forecast", layout="wide", initial_sidebar_state="expanded")

# ตั้งค่าการเชื่อมต่อฐานข้อมูล XAMPP MySQL
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '', # ใส่รหัสผ่านถ้าคุณตั้งไว้ใน XAMPP
    'database': 'dam_forecast_db'
}

@st.cache_resource
def init_jvm_safe():
    try:
        jvm.start(packages=True)
        return True
    except:
        return False

init_jvm_safe()

@st.cache_resource
def load_resources():
    # โหลดโมเดล 7 วัน
    raw_j48_7d = serialization.read("model7d.model")  
    model_7d = Classifier(jobject=raw_j48_7d)
    loader_7d = Loader("weka.core.converters.ArffLoader")
    header_7d = loader_7d.load_file("dam_risk_forecast_7days.arff")
    header_7d.class_is_last()

    # โหลดโมเดล 30 วัน (เปลี่ยนชื่อไฟล์ให้ตรงกับของคุณ)
    raw_j48_30d = serialization.read("model30d.model") 
    model_30d = Classifier(jobject=raw_j48_30d)
    loader_30d = Loader("weka.core.converters.ArffLoader")
    header_30d = loader_30d.load_file("dam_risk_forecast_30days.arff")
    header_30d.class_is_last()

    return {"7_day": {"model": model_7d, "header": header_7d}, "30_day": {"model": model_30d, "header": header_30d}}

models_dict = load_resources()

# ==========================================
# 🔄 DATABASE & API FUNCTIONS
# ==========================================
def save_to_database(df):
    """ฟังก์ชันบันทึกข้อมูลวันนี้ลงฐานข้อมูลโดยอัตโนมัติ"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        today = datetime.date.today()
        
        # วนลูปบันทึกทีละเขื่อน
        for _, row in df.iterrows():
            sql = """
                INSERT IGNORE INTO dam_records 
                (dam_id, dam_name, record_date, percent_storage, inflow, outflow) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            val = (
                row.get('id'), row.get('name'), today, 
                row.get('percent_storage', 0), row.get('inflow', 0), row.get('outflow', 0)
            )
            cursor.execute(sql, val)
        
        conn.commit()
    except Exception as e:
        st.sidebar.error(f"DB Save Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def get_historical_data(dam_id):
    """ดึงข้อมูลประวัติย้อนหลังจาก MySQL"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        # ดึงย้อนหลัง 30 วันเพื่อมาวาดกราฟ
        query = f"SELECT record_date, percent_storage FROM dam_records WHERE dam_id = '{dam_id}' ORDER BY record_date ASC LIMIT 30"
        df_hist = pd.read_sql(query, conn)
        return df_hist
    except Exception as e:
        return pd.DataFrame()
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

@st.cache_data(ttl=3600) # Cache 1 ชั่วโมง
def fetch_and_save_data():
    try:
        response = requests.get("https://app.rid.go.th/reservoir/api/dam/public", timeout=10)
        res_data = response.json()
        records = res_data.get("data", res_data)
        
        df = pd.json_normalize(records, record_path=['dam'], meta=['region'])
        mapping = {"dam_id": "id", "dam_name": "name"}
        df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
        
        # บันทึกลงฐานข้อมูลทันทีเมื่อโหลดสำเร็จ
        save_to_database(df)
        return df
    except Exception as e:
        st.error("ไม่สามารถเชื่อมต่อ API ได้")
        return pd.DataFrame()

# ==========================================
# 🧠 WEKA PREDICTION
# ==========================================
def predict_single_dam(row_series, model_config):
    """ปรับแต่งให้พยากรณ์แค่แถวเดียว (Single Row)"""
    model = model_config["model"]
    header = model_config["header"]
    
    inst = Instance.create_instance([0.0] * header.num_attributes)
    inst.dataset = header  
    
    for attr in header.attributes():
        if attr.name == header.class_attribute.name:
            continue
        
        val = row_series.get(attr.name, None)
        
        if val is None or pd.isna(val) or val == "None":
            inst.set_missing(attr.index)
            continue
        
        if attr.is_numeric:
            try:
                inst.set_value(attr.index, float(val))
            except:
                inst.set_value(attr.index, 0.0)
        elif attr.is_nominal or attr.is_string:
            try:
                inst.set_value(attr.index, str(val))
            except:
                inst.set_missing(attr.index)
                
    pred_index = model.classify_instance(inst)
    if header.class_attribute.is_nominal:
        return header.class_attribute.value(int(pred_index))
    return pred_index

# ==========================================
# 🎨 STREAMLIT UI LAYOUT
# ==========================================
raw_df = fetch_and_save_data()

if not raw_df.empty:
    # --- Sidebar ---
    with st.sidebar:
        st.title("Dam Forecast")
        dam_list = raw_df['name'].tolist()
        selected_dam_name = st.selectbox("เลือกอ่างเก็บน้ำ:", dam_list)
    
    # กรองข้อมูลเอาเฉพาะเขื่อนที่เลือก (แถวเดียว)
    dam_data = raw_df[raw_df['name'] == selected_dam_name].iloc[0]
    
    # ทำนายผล
    pred_7d = predict_single_dam(dam_data, models_dict["7_day"])
    pred_30d = predict_single_dam(dam_data, models_dict["30_day"])
    
    # --- Main Content ---
    st.header(f"ข้อมูลของ: {selected_dam_name}")
    
    # 1. KPI Cards (ปรับเป็น 5 คอลัมน์ เพื่อโชว์ 7 วัน และ 30 วัน)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(label="ความเสี่ยง (7 วัน)", value=pred_7d)
    with col2:
        st.metric(label="ความเสี่ยง (30 วัน)", value=pred_30d)
    with col3:
        st.metric(label="ร้อยละความจุ", value=f"{dam_data.get('percent_storage', 0)}%")
    with col4:
        st.metric(label="Inflow (ลบ.ม./วัน)", value=f"{dam_data.get('inflow', 0)}")
    with col5:
        st.metric(label="Outflow (ลบ.ม./วัน)", value=f"{dam_data.get('outflow', 0)}")

    # 2. Historical Chart
    st.subheader("📈 กราฟแนวโน้มร้อยละความจุย้อนหลัง")
    hist_df = get_historical_data(dam_data['id'])
    
    if not hist_df.empty and len(hist_df) > 1:
        # สร้างกราฟเส้นด้วย Plotly
        fig = px.line(hist_df, x='record_date', y='percent_storage', markers=True)
        fig.update_layout(yaxis_range=[0, 100], xaxis_title="", yaxis_title="ร้อยละความจุ (%)")
        # เพิ่มเส้นเกณฑ์น้ำล้น (80%) และเกณฑ์น้ำแล้ง (30%)
        fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="เกณฑ์น้ำล้น (80%)")
        fig.add_hline(y=30, line_dash="dash", line_color="orange", annotation_text="เกณฑ์น้ำแล้ง (30%)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("กำลังสะสมข้อมูลประวัติ... (ระบบเพิ่งเริ่มบันทึกข้อมูลของเขื่อนนี้ลงในฐานข้อมูล หรือมีข้อมูลเพียง 1 วัน จึงยังไม่สามารถพล็อตกราฟเส้นได้)")
        # แสดงข้อมูลปัจจุบันเดี่ยวๆ แทนกราฟ
        st.progress(int(float(dam_data.get('percent_storage', 0))))

    # 3. Summary Alert Box (อัปเดตจับคลาส flood, normal, drought โดยเฉพาะ)
    st.markdown("### สรุปแผนการจัดการน้ำ")
    
    # ฟังก์ชันช่วยแปลคำศัพท์ให้เป็นมิตรกับผู้ใช้งาน (UX)
    def translate_status(status_text):
        status_lower = str(status_text).lower()
        if "flood" in status_lower:
            return "น้ำล้น (Flood)"
        elif "drought" in status_lower:
            return "น้ำแล้ง (Drought)"
        else:
            return "ปกติ (Normal)"

    # แปลงค่าที่ได้จาก Weka
    status_7d_th = translate_status(pred_7d)
    status_30d_th = translate_status(pred_30d)

    # เช็คว่ามีความเสี่ยงหรือไม่ (ถ้าไม่ใช่ normal ถือว่าเสี่ยง)
    is_risk_7d = "normal" not in str(pred_7d).lower()
    is_risk_30d = "normal" not in str(pred_30d).lower()

    # แสดงผลตามเงื่อนไข
    if is_risk_7d and is_risk_30d:
        st.error(f"🚨 **ประกาศฉุกเฉิน:** เฝ้าระวังสูงสุด! พยากรณ์ 7 วันอยู่ในเกณฑ์ **{status_7d_th}** และ 30 วันมีแนวโน้ม **{status_30d_th}** จำเป็นต้องพิจารณาแผนรับมือด่วน")
    elif is_risk_7d:
        st.warning(f"⚠️ **ประกาศเตือนระยะสั้น:** พยากรณ์ 7 วันอยู่ในเกณฑ์ **{status_7d_th}** (ส่วน 30 วัน: ปกติ) ควรติดตามสถานการณ์ใกล้ชิดในสัปดาห์นี้")
    elif is_risk_30d:
        st.warning(f"⚠️ **ประกาศเตือนระยะกลาง:** สถานการณ์ 7 วันนี้ยังปกติ แต่ใน 30 วันมีแนวโน้ม **{status_30d_th}** ควรวางแผนการบริหารจัดการน้ำล่วงหน้า")
    else:
        st.success(f"✅ **ประกาศ:** สถานการณ์น้ำปกติ ทั้งการพยากรณ์ 7 วันและ 30 วันยังอยู่ในระดับ **{status_7d_th}** ไม่มีความจำเป็นต้องปรับแผนฉุกเฉิน")

else:
    st.error("ไม่พบข้อมูลจากระบบ โปรดตรวจสอบการเชื่อมต่อ API ของกรมชลประทาน")