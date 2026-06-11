# weka_model.py
import streamlit as st
import pandas as pd
import weka.core.jvm as jvm
import weka.core.serialization as serialization
from weka.classifiers import Classifier
from weka.core.dataset import Instance
from weka.core.converters import Loader

@st.cache_resource
def init_jvm_safe():
    try:
        # สั่ง start ไปเลย Streamlit @st.cache_resource จะคุมให้รันแค่รอบเดียวอยู่แล้ว
        jvm.start(packages=True)
        return True
    except Exception as e:
        print(f"JVM Error: {e}")
        return False

@st.cache_resource
def load_resources():
    # โหลด 7 วัน
    raw_j48_7d = serialization.read("model7d.model")  
    model_7d = Classifier(jobject=raw_j48_7d)
    loader_7d = Loader("weka.core.converters.ArffLoader")
    header_7d = loader_7d.load_file("dam_risk_forecast_7days.arff")
    header_7d.class_is_last()

    # โหลด 30 วัน
    raw_j48_30d = serialization.read("model30d.model") 
    model_30d = Classifier(jobject=raw_j48_30d)
    loader_30d = Loader("weka.core.converters.ArffLoader")
    header_30d = loader_30d.load_file("dam_risk_forecast_30days.arff")
    header_30d.class_is_last()

    return {"7_day": {"model": model_7d, "header": header_7d}, "30_day": {"model": model_30d, "header": header_30d}}

def predict_single_dam(row_series, model_config):
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