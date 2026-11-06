import os
import datetime
import streamlit as st
import pandas as pd
import weka.core.jvm as jvm
import weka.core.serialization as serialization
from weka.classifiers import Classifier
from weka.core.dataset import Instance, Instances
from weka.core.converters import Loader

# Features ที่โมเดลใช้ในการพยากรณ์
FEATURES = ["percent_storage", "inflow_pct", "outflow_pct", "month"]


# การจัดการ Java Virtual Machine (JVM)

# ฟังก์ชันตรวจสอบและตั้งค่าเส้นทาง JAVA_HOME สำหรับ Weka
def _ensure_java_home():
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


# ฟังก์ชันเริ่มต้นการทำงานของ JVM อย่างปลอดภัย
@st.cache_resource
def init_jvm_safe(max_heap_size: str = "128m"):
    try:
        if not jvm.started:
            _ensure_java_home()
            heap_size = os.environ.get("WEKA_MAX_HEAP_SIZE", max_heap_size)
            jvm.start(max_heap_size=heap_size, packages=False)
        return True
    except Exception as e:
        print(f"JVM Error: {e}")
        return False


# โหลดโมเดลและ Header ARFF

# ฟังก์ชันสกัดและสร้าง Header Attributes จากไฟล์ ARFF
def _extract_header(arff_path, class_attr_name, features=None):
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


# ฟังก์ชันโหลดโมเดลและชุดข้อมูล Header สำหรับการพยากรณ์
@st.cache_resource
def load_resources():
    base = os.path.join(os.path.dirname(__file__), "..", "models")

    # โมเดลพยากรณ์ 7 วัน
    path_7d = os.path.join(base, "trained", "Log_7days.model")
    raw_7d = serialization.read(path_7d)
    model_7d = Classifier(jobject=raw_7d)
    header_7d = _extract_header(os.path.join(base, "datasets", "dam_risk_forecast_7days_header.arff"), "risk_class_7d")

    # โมเดลพยากรณ์ 30 วัน
    path_30d = os.path.join(base, "trained", "RF_30days.model")
    raw_30d = serialization.read(path_30d)
    model_30d = Classifier(jobject=raw_30d)
    header_30d = _extract_header(os.path.join(base, "datasets", "dam_risk_forecast_30days_header.arff"), "risk_class_30d")

    return {
        "7_day": {"model": model_7d, "header": header_7d, "name": "พยากรณ์ล่วงหน้า 7 วัน (Logistic Regression)"},
        "30_day": {"model": model_30d, "header": header_30d, "name": "พยากรณ์ล่วงหน้า 30 วัน (Random Forest)"}
    }


# ฟังก์ชันสร้างการจับคู่ Attributes เชิงตัวเลขและเชิงกลุ่ม
def _build_attr_mapping(header):
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


# ฟังก์ชันจัดเตรียมและคำนวณคุณลักษณะของเขื่อนสำหรับโมเดล
def _prepare_dam_features(row_dict):
    data = dict(row_dict)

    # คำนวณ Feature อัตราส่วนความจุ Inflow/Outflow (%)
    cap = float(data.get('capacity', 0) or 0)
    if (data.get('percent_storage') is None or pd.isna(data.get('percent_storage'))) and data.get('volume') and cap > 0:
        data['percent_storage'] = (float(data['volume']) / cap) * 100.0

    raw_in = data.get('inflow')
    inflow = float(raw_in) if (raw_in is not None and not pd.isna(raw_in)) else 0.0
    data["inflow"] = inflow
    if "inflow_pct" not in data or pd.isna(data["inflow_pct"]):
        data["inflow_pct"] = (inflow / cap * 100.0) if cap > 0 else 0.0

    raw_out = data.get('outflow')
    outflow = float(raw_out) if (raw_out is not None and not pd.isna(raw_out)) else 0.0
    data["outflow"] = outflow
    if "outflow_pct" not in data or pd.isna(data["outflow_pct"]):
        data["outflow_pct"] = (outflow / cap * 100.0) if cap > 0 else 0.0

    # ตั้งค่าเดือนปัจจุบันหากไม่มีการระบุ
    if "month" not in data or pd.isna(data["month"]) or data["month"] is None:
        data["month"] = datetime.datetime.now().month

    return data


# ฟังก์ชันสร้างและกำหนดค่า Weka Instance จากข้อมูลเขื่อน
def _build_weka_instance(header, mapping, row_dict):
    _, numeric_attrs, nominal_attrs = mapping
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
        except (ValueError, TypeError):
            inst.set_value(attr.index, 0.0)

    # กำหนดค่าข้อความ/Nominal ลงใน Weka Instance
    for attr in nominal_attrs:
        val = row_dict.get(attr.name, None)
        if val is None or pd.isna(val) or val == "None":
            inst.set_missing(attr.index)
            continue
        try:
            inst.set_value(attr.index, str(val))
        except Exception:
            inst.set_missing(attr.index)

    return inst


# ฟังก์ชันพยากรณ์ระดับความเสี่ยงของเขื่อนเดี่ยวด้วยโมเดล Weka
def predict_single_dam(row_series, model_config, model_name: str = None):
    model = model_config["model"]
    header = model_config["header"]

    mapping = model_config.get("_attr_mapping")
    if mapping is None:
        mapping = _build_attr_mapping(header)
        model_config["_attr_mapping"] = mapping

    row_dict = _prepare_dam_features(dict(row_series))
    inst = _build_weka_instance(header, mapping, row_dict)

    # สั่งให้โมเดลทำนายและส่งกลับผลลัพธ์
    pred_index = model.classify_instance(inst)
    if header.class_attribute.is_nominal:
        pred_class = header.class_attribute.value(int(pred_index))
    else:
        pred_class = str(pred_index)

    # ดึงค่าความน่าจะเป็นของแต่ละคลาส
    dist_map = {}
    try:
        dist = model.distribution_for_instance(inst)
        if header.class_attribute.is_nominal:
            for i in range(header.class_attribute.num_values):
                c_val = header.class_attribute.value(i)
                dist_map[c_val] = float(dist[i])
    except Exception:
        pass

    # ระบุชื่อโมเดล / ระยะเวลาพยากรณ์
    if not model_name:
        model_name = model_config.get("name")
        if not model_name:
            rel = getattr(header, "relation_name", "")
            if "7day" in rel:
                model_name = "พยากรณ์ล่วงหน้า 7 วัน (Logistic Regression)"
            elif "30day" in rel:
                model_name = "พยากรณ์ล่วงหน้า 30 วัน (Random Forest)"
            else:
                model_name = rel or "Weka Model"

    dam_name = row_dict.get("name") or row_dict.get("dam_name") or "ไม่ระบุชื่อ"
    dam_id = row_dict.get("id") or row_dict.get("dam_id") or "-"

    # Print Debug: ค่าที่ส่งให้โมเดลและผลลัพธ์ที่ได้ออกมา
    print("=" * 65)
    print(f"🔍 [DEBUG PREDICTION] {model_name}")
    print(f"📍 เขื่อน: {dam_name} (ID: {dam_id})")
    print("-" * 65)
    print("📥 Features sent to Model:")
    pct_val = row_dict.get('percent_storage', 0.0)
    inflow_pct = row_dict.get('inflow_pct', 0.0)
    outflow_pct = row_dict.get('outflow_pct', 0.0)
    inflow_raw = row_dict.get('inflow', 0.0)
    outflow_raw = row_dict.get('outflow', 0.0)
    month_val = row_dict.get('month', '-')
    cap_val = row_dict.get('capacity', 0.0)

    print(f"   • percent_storage : {float(pct_val):.2f}%")
    print(f"   • inflow_pct      : {float(inflow_pct):.4f}% (inflow: {float(inflow_raw):,.2f} ล้าน ลบ.ม.)")
    print(f"   • outflow_pct     : {float(outflow_pct):.4f}% (outflow: {float(outflow_raw):,.2f} ล้าน ลบ.ม.)")
    print(f"   • month           : {month_val}")
    if cap_val:
        print(f"   • capacity        : {float(cap_val):,.2f} ล้าน ลบ.ม.")
    print("-" * 65)
    print("📤 Prediction Result:")
    print(f"   • Class  : {pred_class.upper()} ({pred_class})")
    if dist_map:
        prob_strs = [f"{c}={prob * 100:.2f}%" for c, prob in dist_map.items()]
        print(f"   • Probability : {', '.join(prob_strs)}")
    print("=" * 65 + "\n")

    return pred_class
