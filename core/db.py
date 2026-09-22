import datetime
import math
import mysql.connector
from mysql.connector import pooling
import pandas as pd
import streamlit as st
from config import DB_CONFIG

_pool = None


def get_connection():
    """สร้างหรือดึง Connection จาก Pool เพื่อลด Overhead การทำ TLS Handshake ไปยัง Cloud DB"""
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
    except Exception as e:
        # หากเกิดข้อผิดพลาดกับ Connection Pool ให้ fallback ไปเชื่อมต่อตรง
        return mysql.connector.connect(**DB_CONFIG)


def init_db_schema():
    """สร้างตาราง dam_info และ dam_daily พร้อม Indexes อัตโนมัติหากยังไม่มีใน Database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. ตารางข้อมูลเขื่อนหลัก
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `dam_info` (
              `dam_id` varchar(50) NOT NULL,
              `dam_name` varchar(255) NOT NULL,
              `owner` varchar(100) DEFAULT NULL,
              `region` varchar(100) DEFAULT NULL,
              `capacity` float DEFAULT NULL,
              `storage` float DEFAULT NULL,
              `active_storage` float DEFAULT NULL,
              `dead_storage` float DEFAULT NULL,
              PRIMARY KEY (`dam_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # 2. ตารางข้อมูลรายวัน
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `dam_daily` (
              `id` int(11) NOT NULL AUTO_INCREMENT,
              `dam_id` varchar(50) NOT NULL,
              `record_date` date NOT NULL,
              `recorded_at` datetime DEFAULT NULL,
              `volume` float DEFAULT NULL,
              `percent_storage` float DEFAULT NULL,
              `inflow` float DEFAULT NULL,
              `outflow` float DEFAULT NULL,
              PRIMARY KEY (`id`),
              KEY `idx_dam_id` (`dam_id`),
              KEY `idx_record_date` (`record_date`),
              KEY `idx_dam_record_date` (`dam_id`, `record_date` DESC),
              CONSTRAINT `fk_dam_char` FOREIGN KEY (`dam_id`) REFERENCES `dam_info` (`dam_id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # 3. ตรวจสอบว่าคอลัมน์ id มี AUTO_INCREMENT หรือไม่ (หากขาด AUTO_INCREMENT จะทำให้ TiDB ใส่ id=0 แถวแรก และแถวถัดไปติด Duplicate Key 0)
        cursor.execute("SHOW COLUMNS FROM dam_daily LIKE 'id';")
        col_id = cursor.fetchone()
        if col_id and 'auto_increment' not in str(col_id[5]).lower():
            try:
                cursor.execute("SELECT COUNT(*) FROM dam_daily;")
                cnt = cursor.fetchone()[0]
                # ใน TiDB Cloud ไม่สามารถ ALTER เพิ่ม AUTO_INCREMENT ได้ หากมีข้อมูลไม่สมบูรณ์ (< 50 แถว) ให้ Re-create ตารางอัตโนมัติ
                if cnt < 50:
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
                    cursor.execute("DROP TABLE IF EXISTS dam_daily;")
                    cursor.execute("""
                        CREATE TABLE `dam_daily` (
                          `id` int(11) NOT NULL AUTO_INCREMENT,
                          `dam_id` varchar(50) NOT NULL,
                          `record_date` date NOT NULL,
                          `recorded_at` datetime DEFAULT NULL,
                          `volume` float DEFAULT NULL,
                          `percent_storage` float DEFAULT NULL,
                          `inflow` float DEFAULT NULL,
                          `outflow` float DEFAULT NULL,
                          PRIMARY KEY (`id`),
                          KEY `idx_dam_id` (`dam_id`),
                          KEY `idx_record_date` (`record_date`),
                          KEY `idx_dam_record_date` (`dam_id`, `record_date` DESC),
                          CONSTRAINT `fk_dam_char` FOREIGN KEY (`dam_id`) REFERENCES `dam_info` (`dam_id`) ON DELETE CASCADE
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                    """)
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
                    conn.commit()
            except Exception as e:
                print(f"Auto-increment fix warning: {e}")

        # 4. ตรวจสอบและซ่อมแซมแถวที่ id เป็น NULL หรือ 0 (เช่น กรณี import ข้อมูลหรือ insert ขาด AUTO_INCREMENT บน Cloud)
        try:
            cursor.execute("SELECT COUNT(*) FROM dam_daily WHERE id IS NULL OR id = 0;")
            null_cnt = cursor.fetchone()[0]
            if null_cnt > 0:
                cursor.execute("SELECT COALESCE(MAX(CASE WHEN id > 0 THEN id ELSE 0 END), 0) FROM dam_daily;")
                base_id = cursor.fetchone()[0] or 0
                cursor.execute("SELECT dam_id, record_date FROM dam_daily WHERE id IS NULL OR id = 0;")
                missing_rows = cursor.fetchall()
                for i, (d_id, r_date) in enumerate(missing_rows):
                    new_id = base_id + i + 1
                    cursor.execute(
                        "UPDATE dam_daily SET id = %s WHERE dam_id = %s AND record_date = %s AND (id IS NULL OR id = 0) LIMIT 1;",
                        (new_id, d_id, r_date)
                    )
                conn.commit()
        except Exception as e:
            print(f"ID repair warning: {e}")

        # 5. ตรวจสอบ Composite Index เพิ่มเติมหากตารางมีอยู่เดิมแล้ว
        cursor.execute("SHOW INDEX FROM dam_daily WHERE Key_name = %s", ('idx_dam_record_date',))
        if not cursor.fetchall():
            cursor.execute("ALTER TABLE dam_daily ADD INDEX idx_dam_record_date (dam_id, record_date DESC);")

        conn.commit()
    except Exception as e:
        print(f"Database Schema Init Warning: {e}")
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


# เรียกใช้งานสร้างตารางอัตโนมัติเมื่อเริ่มต้นโมดูล
try:
    init_db_schema()
except Exception:
    pass


def _safe_float(val):
    if val is None:
        return None
    try:
        if math.isnan(val):
            return None
    except (TypeError, ValueError):
        pass
    return float(val)


def save_to_characteristics(df):
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
        err_msg = f"DB Characteristics Save Error: {e}"
        print(err_msg)
        try:
            st.error(f"⚠️ {err_msg}")
        except Exception:
            pass
        return False
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


def save_to_database(df, record_date=None):
    if record_date is None:
        record_date = datetime.date.today()
    now = datetime.datetime.now()
    try:
        ok = save_to_characteristics(df)
        if not ok:
            print("Warning: save_to_characteristics failed, skipping dam_daily insert")
            return False

        conn = get_connection()
        cursor = conn.cursor()

        # ลบข้อมูลเก่าของวันนี้ที่มีข้อผิดพลาด (เช่น id เป็น NULL หรือ 0) เพื่อป้องกันความขัดแย้ง
        cursor.execute("DELETE FROM dam_daily WHERE record_date = %s AND (id IS NULL OR id = 0);", (record_date,))

        # คำนวณ max_id ล่าสุดเพื่อส่งค่า id ชัดเจนเสมอ หมดปัญหา TiDB Cloud ไม่มี AUTO_INCREMENT หรือค่า id หลุดเป็น NULL
        cursor.execute("SELECT COALESCE(MAX(id), 0) FROM dam_daily;")
        row_max = cursor.fetchone()
        base_id = int(row_max[0]) if row_max and row_max[0] is not None else 0

        # ตรวจสอบว่ามี dam_id ไหนบันทึกแล้วในวันนี้บ้าง เพื่อไม่ให้ insert ซ้ำ
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
        err_msg = f"DB Save Error: {e}"
        print(err_msg)
        try:
            st.error(f"⚠️ {err_msg}")
        except Exception:
            pass
        return False
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


@st.cache_data(ttl=300, show_spinner=False)
def get_recorded_time(target_date):
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
    ดึงข้อมูลย้อนหลังของเขื่อน พร้อม Cache 10 นาที เพื่อให้การสลับเขื่อนและเปลี่ยนช่วงเวลาลื่นไหลทันที
    ไม่ผูกมัดกับคอลัมน์ id เพื่อป้องกันปัญหาข้อมูลของวันนี้ไม่แสดงกรณี id เป็น NULL
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT record_date, volume, percent_storage, inflow, outflow
            FROM dam_daily
            WHERE dam_id = %s
            ORDER BY record_date DESC, recorded_at DESC
            LIMIT %s
        """
        # ส่ง dam_id เป็น str เพื่อให้ตรงกับประเภท varchar(50) ของ column และใช้ Index ได้เต็มประสิทธิภาพ
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
