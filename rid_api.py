# rid_api.py
import streamlit as st
import requests
import pandas as pd
from config import RID_API_URL
from db import save_to_database

@st.cache_data(ttl=3600)
def fetch_and_save_data():
    try:
        response = requests.get(RID_API_URL, timeout=10)
        res_data = response.json()
        records = res_data.get("data", res_data)
        
        df = pd.json_normalize(records, record_path=['dam'], meta=['region'])
        mapping = {"dam_id": "id", "dam_name": "name"}
        df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
        
        # บันทึกลงฐานข้อมูลทันทีเมื่อดึง API สำเร็จ
        save_to_database(df)
        return df
    except Exception as e:
        st.error(f"ไม่สามารถเชื่อมต่อ API ได้: {e}")
        return pd.DataFrame()