# db.py
import mysql.connector
import pandas as pd
import datetime
import streamlit as st
from config import DB_CONFIG

def save_to_database(df):
    """บันทึกข้อมูลรายวันลง MySQL"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        today = datetime.date.today()
        
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
        print(f"DB Save Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def get_historical_data(dam_id):
    """ดึงข้อมูลประวัติย้อนหลัง 30 วัน"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        query = f"SELECT record_date, percent_storage FROM dam_records WHERE dam_id = '{dam_id}' ORDER BY record_date ASC LIMIT 30"
        df_hist = pd.read_sql(query, conn)
        return df_hist
    except Exception as e:
        return pd.DataFrame()
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()