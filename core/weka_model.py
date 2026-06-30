import os
import streamlit as st
import pandas as pd
import weka.core.jvm as jvm
import weka.core.serialization as serialization
from weka.classifiers import Classifier
from weka.core.dataset import Instance, Instances
from weka.core.converters import Loader

FEATURES = ["percent_storage", "inflow", "outflow", "month", "id"]

@st.cache_resource
def init_jvm_safe():
    try:
        jvm.start(packages=True)
        return True
    except Exception as e:
        print(f"JVM Error: {e}")
        return False

def _extract_header(arff_path, class_attr_name):
    from jpype import JClass
    loader = Loader("weka.core.converters.ArffLoader")
    full = loader.load_file(arff_path)
    full.class_is_last()

    ArrayList = JClass("java.util.ArrayList")
    InstancesJ = JClass("weka.core.Instances")

    attr_list = ArrayList()
    for name in FEATURES:
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

    raw_7d = serialization.read(os.path.join(base, "model7d.model"))
    model_7d = Classifier(jobject=raw_7d)
    header_7d = _extract_header(os.path.join(base, "dam_risk_forecast_7days.arff"), "risk_class_7d")

    raw_30d = serialization.read(os.path.join(base, "model30d.model"))
    model_30d = Classifier(jobject=raw_30d)
    header_30d = _extract_header(os.path.join(base, "dam_risk_forecast_30days.arff"), "risk_class_30d")

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

    for attr in numeric_attrs:
        val = row_series.get(attr.name, None)
        if val is None or pd.isna(val) or val == "None":
            inst.set_missing(attr.index)
            continue
        try:
            inst.set_value(attr.index, float(val))
        except:
            inst.set_value(attr.index, 0.0)

    for attr in nominal_attrs:
        val = row_series.get(attr.name, None)
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
