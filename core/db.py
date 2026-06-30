import mysql.connector
import pandas as pd
import datetime
import streamlit as st
from config import DB_CONFIG

def save_to_database(df, record_date=None):
    if record_date is None:
        record_date = datetime.date.today()
    now = datetime.datetime.now()
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        sql = """
            INSERT IGNORE INTO dam_records
            (dam_id, dam_name, record_date, recorded_at, percent_storage, inflow, outflow)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        data = [
            (
                row.get('id'), row.get('name'), record_date, now,
                row.get('percent_storage', 0), row.get('inflow', 0), row.get('outflow', 0)
            )
            for _, row in df.iterrows()
        ]
        cursor.executemany(sql, data)
        conn.commit()
    except Exception as e:
        print(f"DB Save Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def get_recorded_time(target_date):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(recorded_at) FROM dam_records WHERE record_date = %s", (target_date,))
        result = cursor.fetchone()[0]
        return result
    except Exception:
        return None
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def get_historical_data(dam_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        query = "SELECT record_date, percent_storage FROM dam_records WHERE dam_id = %s ORDER BY record_date ASC LIMIT 30"
        df_hist = pd.read_sql(query, conn, params=(int(dam_id),))
        return df_hist
    except Exception as e:
        return pd.DataFrame()
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
