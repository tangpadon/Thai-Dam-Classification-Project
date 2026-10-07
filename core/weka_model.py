"""
โมดูลการพยากรณ์ด้วยโมเดล Machine Learning (Weka Model Module)
ทำหน้าที่เริ่มต้น Java Virtual Machine (JVM), โหลดโมเดล Weka (.model),
และทำการจำแนกระดับความเสี่ยงน้ำล่วงหน้า 7 วัน (Logistic Regression) และ 30 วัน (Random Forest)
"""

import os
import streamlit as st
import pandas as pd
import weka.core.jvm as jvm
import weka.core.serialization as serialization
from weka.classifiers import Classifier
from weka.core.dataset import Instance, Instances
from weka.core.converters import Loader

# คุณลักษณะ (Features) ที่โมเดลใช้ในการพยากรณ์
FEATURES = ["percent_storage", "inflow_pct", "outflow_pct", "month"]


# 1. การจัดการ Java Virtual Machine (JVM)

def _ensure_java_home():
    """ค้นหาและตั้งค่า JAVA_HOME อัตโนมัติ (จำเป็นสำหรับการรัน Weka บน Linux/Debian/Streamlit Cloud)"""
    if not os.environ.get("JAVA_HOME"):
        candidates = [
            "/usr/lib/jvm/default-java",
            "/usr/lib/jvm/java-17-openjdk-amd64",
            "/usr/lib/jvm/java-11-openjdk-amd64",
            "/usr/lib/jvm/java-21-openjdk-amd64",
        ]
        for path in candidates:
            if os.path.exists(path):
                os.environ["JAVA_HOME"] = path
                break


@st.cache_resource
def init_jvm_safe(max_heap_size: str = "128m"):
    """เริ่มต้นการทำงานของ Java Virtual Machine (JVM) อย่างปลอดภัย พร้อมกำหนดขนาด Memory"""
    try:
        if not jvm.started:
            _ensure_java_home()
            heap_size = os.environ.get("WEKA_MAX_HEAP_SIZE", max_heap_size)
            jvm.start(max_heap_size=heap_size, packages=False)
        return True
    except Exception as e:
        print(f"JVM Error: {e}")
        return False


# 2. การโหลดโมเดลและ Header (Load Models & Resources)

def _extract_header(arff_path, class_attr_name, features=None):
    """สกัดโครงสร้าง Header จากไฟล์ ARFF เพื่อใช้สร้าง Instance ในการทำนาย"""
    if features is None:
        features = FEATURES
    from jpype import JClass
    loader = Loader("weka.core.converters.ArffLoader")
    full = loader.load_file(arff_path)
    full.class_is_last()

    ArrayList = JClass("java.util.ArrayList")
    InstancesJ = JClass("weka.core.Instances")

    attr_list = ArrayList()
    for name in features:
        for attr in full.attributes():
            if attr.name == name:
                attr_list.add(attr.jobject)
                break

    for attr in full.attributes():
        if attr.name == class_attr_name:
            attr_list.add(attr.jobject)
            break

    header = Instances(jobject=InstancesJ("header", attr_list, 0))
    header.class_index = header.num_attributes - 1
    return header


@st.cache_resource
def load_resources():
    """
    โหลดโมเดลที่เทรนไว้และโครงสร้าง Header (แคชไว้ในหน่วยความจำ ไม่ต้องอ่านไฟล์ซ้ำ):
    - 7_day: โมเดล Logistic Regression (ทำนายความเสี่ยง 7 วันข้างหน้า)
    - 30_day: โมเดล Random Forest (ทำนายความเสี่ยง 30 วันข้างหน้า)
    """
    base = os.path.join(os.path.dirname(__file__), "..", "models")

    # โมเดลพยากรณ์ 7 วัน
    path_7d = os.path.join(base, "trained", "Log_7days.model")
    if not os.path.exists(path_7d):
        path_7d = os.path.join(base, "trained", "Logistic_7days.model")
    raw_7d = serialization.read(path_7d)
    model_7d = Classifier(jobject=raw_7d)
    header_7d = _extract_header(os.path.join(base, "datasets", "dam_risk_forecast_7days_header.arff"), "risk_class_7d")

    # โมเดลพยากรณ์ 30 วัน
    path_30d = os.path.join(base, "trained", "RF_30days.model")
    if not os.path.exists(path_30d):
        path_30d = os.path.join(base, "trained", "RandomForest_30days.model")
    raw_30d = serialization.read(path_30d)
    model_30d = Classifier(jobject=raw_30d)
    header_30d = _extract_header(os.path.join(base, "datasets", "dam_risk_forecast_30days_header.arff"), "risk_class_30d")

    return {
        "7_day": {"model": model_7d, "header": header_7d},
        "30_day": {"model": model_30d, "header": header_30d}
    }


def _build_attr_mapping(header):
    """สร้าง Mapping รายชื่อ Features ตัวเลขและ Nominal เพื่อให้การแปลงค่าเข้า Weka รวดเร็ว"""
    class_attr_name = header.class_attribute.name
    numeric_attrs = []
    nominal_attrs = []
    for attr in header.attributes():
        if attr.name == class_attr_name:
            continue
        if attr.is_numeric:
            numeric_attrs.append(attr)
        elif attr.is_nominal or attr.is_string:
            nominal_attrs.append(attr)
    return class_attr_name, numeric_attrs, nominal_attrs


# 3. การประมวลผลพยากรณ์ (Inference / Prediction)

def _prepare_dam_features(row_dict):
    """
    เตรียมค่า Features ให้พร้อมสำหรับโมเดล Weka:
    1. หากไม่มีค่า Input ตรวจวัดเลย ให้ดึงข้อมูลเมื่อวานมาใช้เป็น Fallback
    2. คำนวณ Features เสริม: percent_storage, inflow_pct, outflow_pct
    """
    data = dict(row_dict)

    # 1. ตรวจสอบค่า Input หากไม่มีค่าเลย ให้ดึงค่าจากเมื่อวาน
    pct_val = data.get('percent_storage')
    vol_val = data.get('volume')
    has_valid_input = (
        (pct_val is not None and not pd.isna(pct_val) and float(pct_val or 0) > 0) or
        (vol_val is not None and not pd.isna(vol_val) and float(vol_val or 0) > 0)
    )
    if not has_valid_input:
        dam_id = data.get('id') or data.get('dam_id')
        if dam_id:
            try:
                from core.db import get_yesterday_valid_data
                y_rec = get_yesterday_valid_data(dam_id)
                if y_rec:
                    for col in ['percent_storage', 'volume', 'inflow', 'outflow']:
                        if y_rec.get(col) is not None:
                            data[col] = float(y_rec[col])
            except Exception:
                pass

    # 2. คำนวณ Feature อัตราส่วนความจุ Inflow/Outflow (%)
    cap = float(data.get('capacity', 0) or 0)
    if (data.get('percent_storage') is None or pd.isna(data.get('percent_storage'))) and data.get('volume') and cap > 0:
        data['percent_storage'] = (float(data['volume']) / cap) * 100.0

    if "inflow_pct" not in data or pd.isna(data["inflow_pct"]):
        inflow = float(data.get('inflow', 0) or 0)
        data["inflow_pct"] = (inflow / cap * 100.0) if cap > 0 else 0.0

    if "outflow_pct" not in data or pd.isna(data["outflow_pct"]):
        outflow = float(data.get('outflow', 0) or 0)
        data["outflow_pct"] = (outflow / cap * 100.0) if cap > 0 else 0.0

    return data


def predict_single_dam(row_series, model_config):
    """
    พยากรณ์ระดับความเสี่ยงของเขื่อน 1 แห่ง:
    - row_series: ข้อมูลเขื่อน (dict หรือ pandas Series)
    - model_config: ออบเจกต์โมเดลและ Header ของ Weka
    คืนค่า: คลาสผลพยากรณ์ เช่น 'drought', 'normal', 'flood'
    """
    model = model_config["model"]
    header = model_config["header"]

    mapping = model_config.get("_attr_mapping")
    if mapping is None:
        mapping = _build_attr_mapping(header)
        model_config["_attr_mapping"] = mapping

    class_attr_name, numeric_attrs, nominal_attrs = mapping
    row_dict = _prepare_dam_features(dict(row_series))

    inst = Instance.create_instance([0.0] * header.num_attributes)
    inst.dataset = header

    # กำหนดค่าตัวเลขลงใน Weka Instance
    for attr in numeric_attrs:
        val = row_dict.get(attr.name, None)
        if val is None or pd.isna(val) or val == "None":
            inst.set_missing(attr.index)
            continue
        try:
            inst.set_value(attr.index, float(val))
        except:
            inst.set_value(attr.index, 0.0)

    # กำหนดค่าข้อความ/Nominal ลงใน Weka Instance
    for attr in nominal_attrs:
        val = row_dict.get(attr.name, None)
        if val is None or pd.isna(val) or val == "None":
            inst.set_missing(attr.index)
            continue
        try:
            inst.set_value(attr.index, str(val))
        except:
            inst.set_missing(attr.index)

    # สั่งให้โมเดลทำนายและส่งกลับผลลัพธ์
    pred_index = model.classify_instance(inst)
    if header.class_attribute.is_nominal:
        return header.class_attribute.value(int(pred_index))
    return pred_index

