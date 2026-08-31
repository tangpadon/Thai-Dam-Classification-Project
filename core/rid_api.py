import datetime
import time
import streamlit as st
import requests
import pandas as pd
import mysql.connector
from config import RID_API_URL, DB_CONFIG
from core.db import save_to_database, get_recorded_time

DATA_API_URL = RID_API_URL

def _count_records_for_date(target_date):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dam_daily WHERE record_date = %s", (target_date,))
        return cursor.fetchone()[0]
    except Exception:
        return 0
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def _load_from_db(target_date):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT dc.dam_id, dc.dam_name, dc.owner, dc.region,
                      dc.capacity, dc.storage, dc.active_storage, dc.dead_storage,
                      dr.volume, dr.percent_storage, dr.inflow, dr.outflow
               FROM dam_daily dr
               JOIN dam_info dc ON dr.dam_id = dc.dam_id
               WHERE dr.record_date = %s""",
            (target_date,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        if rows:
            df = pd.DataFrame(rows)
            df = df.rename(columns={"dam_id": "id", "dam_name": "name"})
            recorded_at = get_recorded_time(target_date)
            df['month'] = target_date.month
            return df, recorded_at
        return None, None
    except Exception:
        return None, None

NOON = datetime.time(12, 0)

def _has_measurements(records):
    for rec in (records or []):
        if not isinstance(rec, dict):
            continue
        for d in (rec.get("dam", []) or []):
            if d.get("volume") is not None or d.get("percent_storage") is not None:
                return True
    return False

def _normalize_records(records):
    df = pd.json_normalize(records, record_path=['dam'], meta=['region'])
    mapping = {"dam_id": "id", "dam_name": "name"}
    return df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})

def _fetch_from_api(date_str=None):
    url = f"{DATA_API_URL}{date_str}" if date_str else DATA_API_URL.rstrip('/')
    response = requests.get(url, timeout=10)
    res_data = response.json()
    return res_data.get("data", res_data)

def fetch_and_save_data():
    now = datetime.datetime.now()
    today = now.date()
    yesterday = today - datetime.timedelta(days=1)

    df, recorded_at = _load_from_db(today)
    if df is not None:
        return df, today, recorded_at

    df_y, recorded_at_y = _load_from_db(yesterday)

    try:
        records = _fetch_from_api(today.strftime("%Y-%m-%d"))
        data_available = _has_measurements(records)
    except Exception as e:
        st.error(f"ไม่สามารถเชื่อมต่อ API ได้: {e}")
        if df_y is not None:
            return df_y, yesterday, recorded_at_y
        return pd.DataFrame(), None, None

    if data_available:
        df_new = _normalize_records(records)
        if 'month' not in df_new.columns:
            df_new['month'] = today.month
        save_to_database(df_new, record_date=today)
        if _count_records_for_date(today) > 0:
            return df_new, today, get_recorded_time(today)
        return df_new, today, None

    if now.time() < NOON:
        if df_y is not None:
            return df_y, yesterday, recorded_at_y
        return pd.DataFrame(), yesterday, None
    else:
        if df_y is not None:
            save_to_database(df_y, record_date=today)
            return df_y, today, get_recorded_time(today)
        return pd.DataFrame(), today, None

def backfill_historical_data(lookback_days=30):
    today = datetime.date.today()
    backfill_count = 0
    days_to_fetch = []

    for d in range(1, lookback_days + 1):
        target = today - datetime.timedelta(days=d)
        if _count_records_for_date(target) == 0:
            days_to_fetch.append(target)

    if not days_to_fetch:
        return

    progress_bar = st.sidebar.progress(0, text="⏳ กำลังดึงข้อมูลย้อนหลัง...")
    status_text = st.sidebar.empty()

    for i, target_date in enumerate(days_to_fetch):
        date_str = target_date.strftime("%Y-%m-%d")
        status_text.info(f"⏳ ดึงข้อมูลวันที่ {date_str}")
        progress_bar.progress((i + 1) / len(days_to_fetch))

        try:
            resp = requests.get(f"{DATA_API_URL}{date_str}", timeout=15)
            resp.raise_for_status()
            data = resp.json()
            records = data.get("data", data)

            if records:
                if isinstance(records, list) and len(records) > 0 and isinstance(records[0], dict) and 'dam' in records[0]:
                    df_hist = pd.json_normalize(records, record_path=['dam'], meta=['region'])
                elif isinstance(records, list):
                    df_hist = pd.json_normalize(records)
                else:
                    df_hist = pd.json_normalize(records)
                mapping = {"dam_id": "id", "dam_name": "name"}
                df_hist = df_hist.rename(columns={k: v for k, v in mapping.items() if k in df_hist.columns})
                save_to_database(df_hist, record_date=target_date)
                backfill_count += 1
            else:
                status_text.warning(f"⚠️ API ไม่มีข้อมูลวันที่ {date_str}")
        except Exception as e:
            status_text.warning(f"⚠️ ดึงวันที่ {date_str} ไม่สำเร็จ: {e}")

        time.sleep(0.5)

    progress_bar.empty()
    status_text.empty()
    if backfill_count > 0:
        st.sidebar.success(f"✅ ดึงข้อมูลย้อนหลัง {backfill_count} วันเรียบร้อย")
    elif days_to_fetch:
        st.sidebar.warning(f"⚠️ ไม่สามารถดึงข้อมูลย้อนหลังได้ ({len(days_to_fetch)} วัน)")
