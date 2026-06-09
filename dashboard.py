import streamlit as st
import pandas as pd
import requests
import jpype
import weka.core.jvm as jvm
import weka.core.serialization as serialization
from weka.classifiers import Classifier
from weka.core.dataset import Instance
from weka.core.converters import Loader

# ==========================================
# 1. INITIALIZE JVM (ใช้ st.cache_resource บังคับรันครั้งเดียวชัวร์ๆ)
# ==========================================
@st.cache_resource
def init_jvm_safe():
    try:
        jvm.start(packages=True)
        return True
    except Exception as e:
        # ในกรณีที่ JVM อาจจะเคยเปิดไปแล้วจาก process อื่น
        return False

# เรียกใช้งานฟังก์ชัน (Streamlit จะจำไว้ และรันแค่รอบแรกสุดรอบเดียว)
init_jvm_safe()

# ==========================================
# 2. CACHE MODELS & HEADERS (โหลดครั้งเดียวเก็บใน Memory)
# ==========================================
@st.cache_resource
def load_resources():
    # 📅 โหลด Model & Header สำหรับ 7 วัน (ครอบด้วย Classifier เพื่อแปลงเป็นวัตถุฝั่ง Python)
    raw_j48_7d = serialization.read("model7d.model")  
    model_7d = Classifier(jobject=raw_j48_7d)          # 💡 ห่อหุ้มโครงสร้างไว้ที่นี่
    
    loader_7d = Loader("weka.core.converters.ArffLoader")
    header_7d = loader_7d.load_file("dam_risk_forecast_7days.arff")
    header_7d.class_is_last()

    # 📅 โหลด Model & Header สำหรับ 30 วัน (ทำเหมือนกัน)
    raw_j48_30d = serialization.read("model30d.model") 
    model_30d = Classifier(jobject=raw_j48_30d)        # 💡 ห่อหุ้มโครงสร้างไว้ที่นี่
    
    loader_30d = Loader("weka.core.converters.ArffLoader")
    header_30d = loader_30d.load_file("dam_risk_forecast_30days.arff")
    header_30d.class_is_last()

    return {
        "7_day": {"model": model_7d, "header": header_7d},
        "30_day": {"model": model_30d, "header": header_30d}
    }

models_dict = load_resources()

# ==========================================
# 3. FETCH DATA FROM RID API
# ==========================================
RID_API_URL = "https://app.rid.go.th/reservoir/api/dam/public"

@st.cache_data(ttl=300)  # Cache ข้อมูลไว้ 5 นาที ลดภาระฝั่ง API
def fetch_rid_data():
    try:
        response = requests.get(RID_API_URL, timeout=10)
        response.raise_for_status()
        res_data = response.json()
        
        # ตรวจสอบโครงสร้าง JSON ของ RID
        if isinstance(res_data, dict) and "data" in res_data:
            records = res_data["data"]
        else:
            records = res_data
            
        # 💡 [แก้ไข] คลี่ข้อมูลจากคีย์ 'dam' ออกมาเป็นรายแถว และดึง 'region' ติดมาด้วย
        df = pd.json_normalize(records, record_path=['dam'], meta=['region'])
        
        # คราวนี้คอลัมน์ด้านในเขื่อน เช่น id, name, storage, inflow จะถูกดึงมาเป็นคอลัมน์หลักทันทีครับ
        return df
    except Exception as e:
        st.error(f"❌ ไม่สามารถดึงข้อมูลจาก RID API ได้: {e}")
        return pd.DataFrame()
    
# ==========================================
# 4. PREPROCESSING & PREDICTION FUNCTION
# ==========================================
def preprocess_and_predict(df, model_config):
    model = model_config["model"]
    header = model_config["header"]
    predictions = []

    for _, row in df.iterrows():
        try:
            # 1. สร้าง Instance จำลองด้วยเลข 0.0 ให้ครบทุกคอลัมน์
            inst = Instance.create_instance([0.0] * header.num_attributes)
            inst.dataset = header  # ผูกโครงสร้าง ARFF
            
            # 2. ไล่หยอดค่าจริงทีละ Attribute โดยเปลี่ยนมาใช้ Index (int) เพื่อเลี่ยงบั๊ก JPype Overload
            for attr in header.attributes():
                if attr.name == header.class_attribute.name:
                    continue  # ข้าม Class คอลัมน์ผลลัพธ์
                
                val = row.get(attr.name, None)
                
                # จัดการกรณีเจอค่าว่าง หรือคำว่า "None"
                if val is None or pd.isna(val) or val == "None":
                    inst.set_missing(attr.index)  # 👈 ใช้ attr.index แทนอ็อบเจกต์ attr
                    continue
                
                # 3. เซ็ตค่าลงตารางโดยส่งค่าผ่าน ดัชนีคอลัมน์ (attr.index) 
                if attr.is_numeric:
                    try:
                        # 💡 เมื่อใช้ attr.index แล้ว สามารถส่ง Python float มาตรฐานไปได้เลยครับ ชัวร์แน่นอน
                        inst.set_value(attr.index, float(val))
                    except (ValueError, TypeError):
                        inst.set_value(attr.index, 0.0)
                elif attr.is_nominal or attr.is_string:
                    try:
                        inst.set_value(attr.index, str(val))
                    except Exception:
                        inst.set_missing(attr.index)
            
            # 4. สั่งพยากรณ์ผลลัพธ์
            pred_index = model.classify_instance(inst)
            
            if header.class_attribute.is_nominal:
                res = header.class_attribute.value(int(pred_index))
            else:
                res = pred_index
            predictions.append(res)
            
        except Exception as e:
            predictions.append(f"Error: {str(e)}")
            
    return predictions

# ==========================================
# 5. STREAMLIT UI DISPLAY
# ==========================================
st.set_page_config(page_title="Reservoir Risk Prediction", layout="wide")

st.title("🔮 แดชบอร์ดพยากรณ์ข้อมูลอ่างเก็บน้ำ (RID API x Weka)")
st.caption("ระบบดึงข้อมูล Real-time จากกรมชลประทานและประมวลผลด้วย Weka Model")

# ดึงข้อมูลมาแสดงผลก่อน
with st.spinner("กำลังโหลดข้อมูลจาก RID API..."):
    raw_df = fetch_rid_data()

if not raw_df.empty:
    st.subheader("📊 ข้อมูลปัจจุบันจาก RID API")
    st.dataframe(raw_df, use_container_width=True)

    st.markdown("---")
    st.subheader("🚀 ส่วนการประมวลผลโมเดล")

    # แยกระบบพยากรณ์ออกเป็น 2 แท็บ เพื่อความสะอาดตาและเปรียบเทียบง่าย
    tab1, tab2 = st.tabs(["📅 พยากรณ์ล่วงหน้า 7 วัน", "📅 พยากรณ์ล่วงหน้า 30 วัน"])

    with tab1:
        st.write("ใช้โมเดลระยะสั้นเพื่อดูแนวโน้มความเสี่ยงภายใน 1 สัปดาห์")
        if st.button("Run 7-Day Prediction", key="btn_7d"):
            with st.spinner("กำลังคำนวณ..."):
                processed_df = raw_df.copy()
                
                preds = preprocess_and_predict(processed_df, models_dict["7_day"])
                processed_df["ผลพยากรณ์ (7 วัน)"] = preds
                
                st.success("ประมวลผลสำเร็จ!")
                
                # 🛡️ ระบบจัดเรียงคอลัมน์แบบปลอดภัย (Bulletproof จาก KeyError)
                front_cols = [c for c in ["id", "name", "ผลพยากรณ์ (7 วัน)"] if c in processed_df.columns]
                remaining_cols = [c for c in processed_df.columns if c not in front_cols]
                
                st.dataframe(processed_df[front_cols + remaining_cols], width="stretch")
                
                if "ผลพยากรณ์ (7 วัน)" in processed_df.columns:
                    st.bar_chart(processed_df["ผลพยากรณ์ (7 วัน)"].value_counts())

    with tab2:
        st.write("ใช้โมเดลระยะกลางเพื่อวางแผนบริหารจัดการน้ำใน 1 เดือน")
        if st.button("Run 30-Day Prediction", key="btn_30d"):
            with st.spinner("กำลังคำนวณ..."):
                processed_df = raw_df.copy()
                
                preds = preprocess_and_predict(processed_df, models_dict["30_day"])
                processed_df["ผลพยากรณ์ (30 วัน)"] = preds
                
                st.success("ประมวลผลสำเร็จ!")
                
                # 🛡️ ระบบจัดเรียงคอลัมน์แบบปลอดภัยสำหรับ 30 วัน
                front_cols = [c for c in ["id", "name", "ผลพยากรณ์ (30 วัน)"] if c in processed_df.columns]
                remaining_cols = [c for c in processed_df.columns if c not in front_cols]
                
                st.dataframe(processed_df[front_cols + remaining_cols], width="stretch")
                
                if "ผลพยากรณ์ (30 วัน)" in processed_df.columns:
                    st.bar_chart(processed_df["ผลพยากรณ์ (30 วัน)"].value_counts())
else:
    st.warning("⚠️ ไม่มีข้อมูลสำหรับการพยากรณ์")