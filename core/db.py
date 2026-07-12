import mysql.connector
import pandas as pd
import datetime
import streamlit as st
from config import DB_CONFIG

def _safe_float(val):
    if val is None:
        return None
    try:
        import math
        if math.isnan(val):
            return None
    except (TypeError, ValueError):
        pass
    return float(val)

def save_to_database(df, record_date=None):
    if record_date is None:
        record_date = datetime.date.today()
    now = datetime.datetime.now()
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        sql = """
            INSERT IGNORE INTO dam_records
            (dam_id, dam_name, owner, region, record_date, recorded_at,
             capacity, storage, active_storage, dead_storage, volume,
             percent_storage, inflow, outflow)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        data = [
            (
                row.get('id'),
                row.get('name'),
                row.get('owner'),
                row.get('region'),
                record_date,
                now,
                _safe_float(row.get('capacity')),
                _safe_float(row.get('storage')),
                _safe_float(row.get('active_storage')),
                _safe_float(row.get('dead_storage')),
                _safe_float(row.get('volume')),
                _safe_float(row.get('percent_storage')),
                _safe_float(row.get('inflow')),
                _safe_float(row.get('outflow')),
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
        query = """
            SELECT record_date, percent_storage
            FROM dam_records
            WHERE dam_id = %s
            ORDER BY record_date DESC
            LIMIT 30
        """
        df_hist = pd.read_sql(query, conn, params=(int(dam_id),))
        if not df_hist.empty:
            df_hist = df_hist.sort_values('record_date', ascending=True).reset_index(drop=True)
        return df_hist
    except Exception as e:
        return pd.DataFrame()
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
