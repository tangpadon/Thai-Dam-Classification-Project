import datetime
import time
import streamlit as st
import requests
import pandas as pd
from config import RID_API_URL
from core.database import get_connection, save_to_database, get_recorded_time


DATA_API_URL = RID_API_URL


def _load_from_db(target_date):
    try:
        conn = get_connection()
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

        if rows and len(rows) >= 30:
            valid_count = sum(
                1 for r in rows
                if r.get('percent_storage') is not None or r.get('volume') is not None
            )
            # ถ้า NULL ถือว่าวันนี้ยังไม่มีข้อมูลตรวจวัด
            if valid_count < 15:
                return None, None

            df = pd.DataFrame(rows)
            df = df.rename(columns={"dam_id": "id", "dam_name": "name"})
            recorded_at = get_recorded_time(target_date)
            df['month'] = target_date.month
            return df, recorded_at
        return None, None
    except Exception:
        return None, None


# การเชื่อมต่อและแปลงข้อมูลจาก API

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


def _fill_missing_from_yesterday(target_df, source_df_y):
    if target_df is None or target_df.empty or source_df_y is None or source_df_y.empty:
        return target_df
    for idx, row in target_df.iterrows():
        pct_val = row.get('percent_storage')
        vol_val = row.get('volume')
        if (pct_val is None or pd.isna(pct_val)) and (vol_val is None or pd.isna(vol_val)):
            d_id = str(row.get('id'))
            y_matches = source_df_y[source_df_y['id'].astype(str) == d_id]
            if not y_matches.empty:
                y_row = y_matches.iloc[0]
                for col in ['percent_storage', 'volume', 'inflow', 'outflow']:
                    if col in y_row and pd.notna(y_row[col]):
                        target_df.at[idx, col] = y_row[col]
    return target_df


# ฟังก์ชันหลักสำหรับดึงและจัดเก็บข้อมูล (Main Fetch & Save)

@st.cache_data(ttl=300, show_spinner=False)
def fetch_and_save_data():
    now = datetime.datetime.now()
    today = now.date()
    yesterday = today - datetime.timedelta(days=1)

    # โหลดข้อมูลของเมื่อวานไว้เป็นฐานสำรอง
    df_y, recorded_at_y = _load_from_db(yesterday)

    # ตรวจสอบข้อมูลวันนี้ในฐานข้อมูล
    df, recorded_at = _load_from_db(today)
    if df is not None:
        df = _fill_missing_from_yesterday(df, df_y)
        return df, today, recorded_at

    # ดึงข้อมูลวันนี้จาก RID API
    try:
        records = _fetch_from_api(today.strftime("%Y-%m-%d"))
        data_available = _has_measurements(records)
    except Exception as e:
        st.error(f"⚠️ ไม่สามารถเชื่อมต่อ RID API ได้: {e}")
        if df_y is not None:
            return df_y, yesterday, recorded_at_y
        return pd.DataFrame(), None, None

    # หากมีข้อมูลตรวจวัดวันนี้ ให้บันทึกลงฐานข้อมูล
    if data_available:
        df_new = _normalize_records(records)
        if 'month' not in df_new.columns:
            df_new['month'] = today.month
        df_new = _fill_missing_from_yesterday(df_new, df_y)
        saved = save_to_database(df_new, record_date=today)
        if saved:
            return df_new, today, get_recorded_time(today)
        return df_new, today, None

    # หากวันนี้ยังไม่มีข้อมูลการตรวจวัด ให้ใช้ข้อมูลของเมื่อวาน
    if df_y is not None:
        return df_y, yesterday, recorded_at_y

    # หากในฐานข้อมูลยังไม่มีข้อมูลเมื่อวาน ให้ดึงข้อมูลย้อนหลังจาก RID API อัตโนมัติ (ย้อนหลังสูงสุด 3 วัน)
    for days_back in range(1, 4):
        fallback_date = today - datetime.timedelta(days=days_back)
        try:
            records_fb = _fetch_from_api(fallback_date.strftime("%Y-%m-%d"))
            if _has_measurements(records_fb):
                df_fb = _normalize_records(records_fb)
                if 'month' not in df_fb.columns:
                    df_fb['month'] = fallback_date.month
                saved = save_to_database(df_fb, record_date=fallback_date)
                rec_time = get_recorded_time(fallback_date) if saved else None
                return df_fb, fallback_date, rec_time
        except Exception:
            continue

    return pd.DataFrame(), today, None


# การดึงข้อมูลย้อนหลัง 30 วัน

def _get_missing_historical_dates(lookback_days=30):
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=lookback_days)
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT record_date
               FROM dam_daily
               WHERE record_date >= %s
               GROUP BY record_date
               HAVING COUNT(*) >= 30""",
            (start_date,)
        )
        existing_dates = {row[0] for row in cursor.fetchall()}
    except Exception as e:
        print(f"Error checking backfill dates: {e}")
        existing_dates = set()
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

    return [
        today - datetime.timedelta(days=d)
        for d in range(1, lookback_days + 1)
        if (today - datetime.timedelta(days=d)) not in existing_dates
    ]


def backfill_historical_data(lookback_days=30):
    # หาวันที่ยังขาดหายไปในฐานข้อมูล
    days_to_fetch = _get_missing_historical_dates(lookback_days)
    if not days_to_fetch:
        return

    # แสดง Progress Bar บนแถบด้านข้าง (Sidebar) ระหว่างดึงข้อมูล
    progress_bar = st.sidebar.progress(0, text="กำลังตรวจสอบข้อมูลย้อนหลัง...")
    status_text = st.sidebar.empty()

    # ทยอยดึงข้อมูลทีละวันแล้วบันทึกลงฐานข้อมูล
    for i, target_date in enumerate(days_to_fetch):
        date_str = target_date.strftime("%Y-%m-%d")
        status_text.info(f"ดึงข้อมูลวันที่ {date_str}")
        progress_bar.progress((i + 1) / len(days_to_fetch))

        try:
            records = _fetch_from_api(date_str)
            if records:
                df_hist = _normalize_records(records)
                save_to_database(df_hist, record_date=target_date)
        except Exception:
            pass

        time.sleep(0.3)

    progress_bar.empty()
    status_text.empty()

