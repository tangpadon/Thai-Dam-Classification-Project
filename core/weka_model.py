import os
import streamlit as st
import pandas as pd
import weka.core.jvm as jvm
import weka.core.serialization as serialization
from weka.classifiers import Classifier
from weka.core.dataset import Instance, Instances
from weka.core.converters import Loader

FEATURES = ["percent_storage", "inflow_pct", "outflow_pct", "month"]

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

    header = Instances(jobject=InstancesJ(f"header", attr_list, 0))
    header.class_index = header.num_attributes - 1
    return header

@st.cache_resource
def load_resources():
    base = os.path.join(os.path.dirname(__file__), "..", "models")

    # 7-day model (supports Log_7days.model or Logistic_7days.model)
    path_7d = os.path.join(base, "trained", "Log_7days.model")
    if not os.path.exists(path_7d):
        path_7d = os.path.join(base, "trained", "Logistic_7days.model")
    raw_7d = serialization.read(path_7d)
    model_7d = Classifier(jobject=raw_7d)
    header_7d = _extract_header(os.path.join(base, "datasets", "dam_risk_forecast_7days_header.arff"), "risk_class_7d")

    # 30-day model (supports RF_30days.model or RandomForest_30days.model)
    path_30d = os.path.join(base, "trained", "RF_30days.model")
    if not os.path.exists(path_30d):
        path_30d = os.path.join(base, "trained", "RandomForest_30days.model")
    raw_30d = serialization.read(path_30d)
    model_30d = Classifier(jobject=raw_30d)
    header_30d = _extract_header(os.path.join(base, "datasets", "dam_risk_forecast_30days_header.arff"), "risk_class_30d")

    return {"7_day": {"model": model_7d, "header": header_7d}, "30_day": {"model": model_30d, "header": header_30d}}

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

def predict_single_dam(row_series, model_config):
    model = model_config["model"]
    header = model_config["header"]

    inst = Instance.create_instance([0.0] * header.num_attributes)
    inst.dataset = header

    mapping = model_config.get("_attr_mapping")
    if mapping is None:
        mapping = _build_attr_mapping(header)
        model_config["_attr_mapping"] = mapping

    class_attr_name, numeric_attrs, nominal_attrs = mapping

    # Auto-calculate percentage features if needed (ensures compatibility with both old and new models)
    row_dict = dict(row_series)
    cap = float(row_dict.get('capacity', 0) or 0)
    if "inflow_pct" not in row_dict or pd.isna(row_dict["inflow_pct"]):
        inflow = float(row_dict.get('inflow', 0) or 0)
        row_dict["inflow_pct"] = (inflow / cap * 100.0) if cap > 0 else 0.0
    if "outflow_pct" not in row_dict or pd.isna(row_dict["outflow_pct"]):
        outflow = float(row_dict.get('outflow', 0) or 0)
        row_dict["outflow_pct"] = (outflow / cap * 100.0) if cap > 0 else 0.0

    for attr in numeric_attrs:
        val = row_dict.get(attr.name, None)
        if val is None or pd.isna(val) or val == "None":
            inst.set_missing(attr.index)
            continue
        try:
            inst.set_value(attr.index, float(val))
        except:
            inst.set_value(attr.index, 0.0)

    for attr in nominal_attrs:
        val = row_dict.get(attr.name, None)
        if val is None or pd.isna(val) or val == "None":
            inst.set_missing(attr.index)
            continue
        try:
            inst.set_value(attr.index, str(val))
        except:
            inst.set_missing(attr.index)

    pred_index = model.classify_instance(inst)
    if header.class_attribute.is_nominal:
        return header.class_attribute.value(int(pred_index))
    return pred_index
