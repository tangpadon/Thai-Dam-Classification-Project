import datetime
import time
import streamlit as st
import requests
import pandas as pd
import mysql.connector
from config import RID_API_URL, DB_CONFIG
from core.db import save_to_database, get_recorded_time

DATA_API_URL = "https://app.rid.go.th/reservoir/api/dam/public/"

def _count_records_for_date(target_date):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dam_records WHERE record_date = %s", (target_date,))
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
            "SELECT dam_id, dam_name, percent_storage, inflow, outflow FROM dam_records WHERE record_date = %s",
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

def fetch_and_save_data():
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    df, recorded_at = _load_from_db(today)
    if df is not None:
        return df, today, recorded_at

    try:
        response = requests.get(RID_API_URL, timeout=10)
        res_data = response.json()
        records = res_data.get("data", res_data)

        if not records:
            df_y, _ = _load_from_db(yesterday)
            if df_y is not None:
                return df_y, yesterday, None
            return pd.DataFrame(), yesterday, None

        df = pd.json_normalize(records, record_path=['dam'], meta=['region'])
        mapping = {"dam_id": "id", "dam_name": "name"}
        df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})

        save_to_database(df, record_date=today)
        count_after = _count_records_for_date(today)

        if count_after > 0:
            effective_date = today
            recorded_at = get_recorded_time(today)
        else:
            effective_date = yesterday
            recorded_at = None

        df['month'] = effective_date.month
        return df, effective_date, recorded_at

    except Exception as e:
        st.error(f"ไม่สามารถเชื่อมต่อ API ได้: {e}")
        df_y, _ = _load_from_db(yesterday)
        if df_y is not None:
            return df_y, yesterday, None
        return pd.DataFrame(), None, None

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
                    df_hist = pd.json_normalize(records, record_path=['dam'])
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
