import datetime
import time
import streamlit as st
import requests
import pandas as pd
from config import RID_API_URL
from core.db import get_connection, save_to_database, get_recorded_time

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
            # ถ้าข้อมูลเกือบทั้งหมดเป็นค่าว่าง (NULL) ถือว่าวันนี้ยังไม่มีข้อมูล input
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


def _fill_missing_from_yesterday(target_df, source_df_y):
    """เติมค่า input จากเมื่อวานให้กับเขื่อนที่วันนี้ยังไม่มีข้อมูล เพื่อใช้ในการพยากรณ์"""
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


@st.cache_data(ttl=300, show_spinner=False)
def fetch_and_save_data():
    """
    ดึงข้อมูลสถานการณ์น้ำประจำวัน (แคช 5 นาที เพื่อให้การสลับเมนูและคลิกเลือกเขื่อนบนเว็บรวดเร็วระดับมิลลิวินาที)
    หากวันนี้ยังไม่มีค่า input จะ fallback ไปใช้ข้อมูลจากเมื่อวานอัตโนมัติ
    """
    now = datetime.datetime.now()
    today = now.date()
    yesterday = today - datetime.timedelta(days=1)

    df_y, recorded_at_y = _load_from_db(yesterday)
    df, recorded_at = _load_from_db(today)

    if df is not None:
        df = _fill_missing_from_yesterday(df, df_y)
        return df, today, recorded_at

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
        df_new = _fill_missing_from_yesterday(df_new, df_y)
        saved = save_to_database(df_new, record_date=today)
        if saved:
            return df_new, today, get_recorded_time(today)
        return df_new, today, None

    # หากวันนี้ยังไม่มีข้อมูลการตรวจวัด ให้ใช้ข้อมูลของเมื่อวาน
    if df_y is not None:
        return df_y, yesterday, recorded_at_y
    return pd.DataFrame(), today, None


def backfill_historical_data(lookback_days=30):
    """
    ตรวจสอบข้อมูลย้อนหลัง 30 วันแบบ Batch Query (1 รอบคำสั่ง) แทนการวนลูป Query 30 ครั้ง
    ช่วยประหยัดเวลาและลด Network Round-trip ไปยัง TiDB Cloud จากหลายสิบวินาทีเหลือเสี้ยววินาที
    """
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

    days_to_fetch = [
        today - datetime.timedelta(days=d)
        for d in range(1, lookback_days + 1)
        if (today - datetime.timedelta(days=d)) not in existing_dates
    ]

    if not days_to_fetch:
        return

    progress_bar = st.sidebar.progress(0, text="⏳ กำลังดึงข้อมูลย้อนหลัง...")
    status_text = st.sidebar.empty()
    backfill_count = 0

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
                saved = save_to_database(df_hist, record_date=target_date)
                if saved:
                    backfill_count += 1
                else:
                    status_text.error(f"❌ บันทึกวันที่ {date_str} ลงฐานข้อมูลไม่สำเร็จ")
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
