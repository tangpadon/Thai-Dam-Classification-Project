"""
โมดูลจัดการฐานข้อมูล (Database Module)
ทำหน้าที่เชื่อมต่อฐานข้อมูล TiDB Cloud / MySQL,
บันทึกข้อมูลเขื่อนประจำวัน, และดึงข้อมูลย้อนหลังสำหรับแสดงผลและพยากรณ์
"""

import datetime
import math
import mysql.connector
from mysql.connector import pooling
import pandas as pd
import streamlit as st
from config import DB_CONFIG

# ตัวแปร Connection Pool ระดับโกลบอล
_pool = None


# 1. การเชื่อมต่อฐานข้อมูล (Database Connection)

def get_connection():
    """
    สร้างหรือดึง Connection จาก Pool เพื่อลด Overhead การทำ TLS Handshake ไปยัง Cloud DB
    หาก Connection Pool ขัดข้อง จะ fallback ไปเชื่อมต่อตรงกับฐานข้อมูลอัตโนมัติ
    """
    global _pool
    try:
        if _pool is None:
            pool_config = dict(DB_CONFIG)
            _pool = pooling.MySQLConnectionPool(
                pool_name="dam_pool",
                pool_size=5,
                pool_reset_session=True,
                **pool_config
            )
        return _pool.get_connection()
    except Exception:
        # หากเกิดข้อผิดพลาดกับ Connection Pool ให้ fallback ไปเชื่อมต่อตรง
        return mysql.connector.connect(**DB_CONFIG)


def _safe_float(val):
    """แปลงค่าเป็น float อย่างปลอดภัย โดยแปลงค่าว่าง (None หรือ NaN) ให้เป็น None สำหรับบันทึกลงฐานข้อมูล"""
    if val is None:
        return None
    try:
        if math.isnan(val):
            return None
    except (TypeError, ValueError):
        pass
    return float(val)


# 2. การบันทึกข้อมูลเขื่อน (Save Data)

def save_to_characteristics(df):
    """
    บันทึกหรืออัปเดตข้อมูลคุณลักษณะจำเพาะของเขื่อนลงตาราง dam_info
    (เช่น ความจุอ่าง, ปริมาณน้ำกักเก็บ, หน่วยงานที่ดูแล)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO dam_info
            (dam_id, dam_name, owner, region, capacity, storage, active_storage, dead_storage)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                dam_name=VALUES(dam_name), owner=VALUES(owner), region=VALUES(region),
                capacity=VALUES(capacity), storage=VALUES(storage),
                active_storage=VALUES(active_storage), dead_storage=VALUES(dead_storage)
        """
        data = [
            (
                str(row.get('id')), row.get('name'), row.get('owner'), row.get('region'),
                _safe_float(row.get('capacity')), _safe_float(row.get('storage')),
                _safe_float(row.get('active_storage')), _safe_float(row.get('dead_storage')),
            )
            for _, row in df.iterrows()
        ]
        cursor.executemany(sql, data)
        conn.commit()
        return True
    except Exception as e:
        print(f"DB Characteristics Save Error: {e}")
        return False
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


def save_to_database(df, record_date=None):
    """
    บันทึกข้อมูลตรวจวัดประจำวันของแต่ละเขื่อนลงตาราง dam_daily
    (เช่น ร้อยละความจุ, ปริมาณน้ำ, น้ำไหลเข้า Inflow, น้ำระบาย Outflow)
    """
    if record_date is None:
        record_date = datetime.date.today()
    now = datetime.datetime.now()
    try:
        ok = save_to_characteristics(df)
        if not ok:
            return False

        conn = get_connection()
        cursor = conn.cursor()

        # ลบข้อมูลเก่าของวันนี้ที่มีข้อผิดพลาด เพื่อป้องกันความขัดแย้ง
        cursor.execute("DELETE FROM dam_daily WHERE record_date = %s AND (id IS NULL OR id = 0);", (record_date,))

        # คำนวณค่า ID ล่าสุด เพื่อกำหนดค่า Primary Key id อย่างต่อเนื่อง
        cursor.execute("SELECT COALESCE(MAX(id), 0) FROM dam_daily;")
        row_max = cursor.fetchone()
        base_id = int(row_max[0]) if row_max and row_max[0] is not None else 0

        # ตรวจสอบว่าเขื่อนไหนบันทึกแล้วในวันนี้บ้าง เพื่อป้องกันการบันทึกซ้ำ
        cursor.execute("SELECT dam_id FROM dam_daily WHERE record_date = %s;", (record_date,))
        existing_dam_ids = {str(r[0]) for r in cursor.fetchall()}

        new_rows = []
        for _, row in df.iterrows():
            d_id = str(row.get('id'))
            if d_id not in existing_dam_ids:
                base_id += 1
                new_rows.append((
                    base_id,
                    d_id,
                    record_date,
                    now,
                    _safe_float(row.get('volume')),
                    _safe_float(row.get('percent_storage')),
                    _safe_float(row.get('inflow')),
                    _safe_float(row.get('outflow')),
                ))

        if new_rows:
            sql = """
                INSERT INTO dam_daily
                (id, dam_id, record_date, recorded_at, volume,
                 percent_storage, inflow, outflow)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(sql, new_rows)
            conn.commit()
        return True
    except Exception as e:
        print(f"DB Save Error: {e}")
        return False
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


# 3. การดึงข้อมูลสำหรับแสดงผล (Queries & Fallbacks)

@st.cache_data(ttl=300, show_spinner=False)
def get_recorded_time(target_date):
    """ดึงวันและเวลาล่าสุดที่มีการบันทึกข้อมูลของวันที่ระบุ"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(recorded_at) FROM dam_daily WHERE record_date = %s", (target_date,))
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception:
        return None
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


@st.cache_data(ttl=600, show_spinner=False)
def get_historical_data(dam_id, limit=30):
    """
    ดึงข้อมูลย้อนหลังของเขื่อนตามจำนวนวันที่กำหนด (ค่าเริ่มต้น 30 วัน)
    พร้อมแคช 10 นาที เพื่อให้การสลับเขื่อนและเปลี่ยนช่วงเวลาบนเว็บรวดเร็ว
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT record_date, volume, percent_storage, inflow, outflow
            FROM dam_daily
            WHERE dam_id = %s
            ORDER BY record_date DESC
            LIMIT %s
        """

        cursor.execute(query, (str(dam_id), int(limit) * 2))
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame(rows)
            df = df.drop_duplicates(subset=['record_date'], keep='first')
            df = df.head(int(limit))
            df = df.sort_values('record_date', ascending=True).reset_index(drop=True)
            return df
        return pd.DataFrame(columns=['record_date', 'volume', 'percent_storage', 'inflow', 'outflow'])
    except Exception as e:
        print(f"Historical query error: {e}")
        return pd.DataFrame(columns=['record_date', 'volume', 'percent_storage', 'inflow', 'outflow'])
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


@st.cache_data(ttl=600, show_spinner=False)
def get_yesterday_valid_data(dam_id, current_date=None):
    """
    ดึงข้อมูลย้อนหลังล่าสุด (เมื่อวาน หรือวันล่าสุดที่มีข้อมูล) ของเขื่อนที่มีค่า Input สมบูรณ์
    สำหรับใช้เป็น Fallback ในการพยากรณ์กรณีที่วันนี้ยังไม่มีข้อมูลตรวจวัด
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        if current_date is None:
            current_date = datetime.date.today()
        elif hasattr(current_date, 'date'):
            current_date = current_date.date()

        query = """
            SELECT record_date, volume, percent_storage, inflow, outflow
            FROM dam_daily
            WHERE dam_id = %s
              AND record_date < %s
              AND (percent_storage IS NOT NULL OR volume IS NOT NULL)
            ORDER BY record_date DESC, recorded_at DESC
            LIMIT 1
        """
        cursor.execute(query, (str(dam_id), current_date))
        row = cursor.fetchone()
        return row
    except Exception as e:
        print(f"Error getting yesterday valid data for dam {dam_id}: {e}")
        return None
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()
