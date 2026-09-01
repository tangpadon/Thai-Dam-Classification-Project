import mysql.connector
import pandas as pd
import datetime
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

def save_to_characteristics(df):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
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
                row.get('id'), row.get('name'), row.get('owner'), row.get('region'),
                _safe_float(row.get('capacity')), _safe_float(row.get('storage')),
                _safe_float(row.get('active_storage')), _safe_float(row.get('dead_storage')),
            )
            for _, row in df.iterrows()
        ]
        cursor.executemany(sql, data)
        conn.commit()
    except Exception as e:
        print(f"DB Characteristics Save Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def save_to_database(df, record_date=None):
    if record_date is None:
        record_date = datetime.date.today()
    now = datetime.datetime.now()
    try:
        save_to_characteristics(df)

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        sql = """
            INSERT IGNORE INTO dam_daily
            (dam_id, record_date, recorded_at, volume,
             percent_storage, inflow, outflow)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        data = [
            (
                row.get('id'),
                record_date,
                now,
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
        cursor.execute("SELECT MAX(recorded_at) FROM dam_daily WHERE record_date = %s", (target_date,))
        result = cursor.fetchone()[0]
        return result
    except Exception:
        return None
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def get_historical_data(dam_id, limit=30):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        query = """
            SELECT d.record_date, d.percent_storage, d.inflow, d.outflow
            FROM dam_daily d
            INNER JOIN (
                SELECT record_date, MAX(recorded_at) AS latest_ts
                FROM dam_daily
                WHERE dam_id = %s
                GROUP BY record_date
            ) m
            ON d.dam_id = %s AND d.record_date = m.record_date AND d.recorded_at = m.latest_ts
            ORDER BY d.record_date DESC
            LIMIT %s
        """
        df_hist = pd.read_sql(query, conn, params=(int(dam_id), int(dam_id), int(limit)))
        if not df_hist.empty:
            df_hist = df_hist.sort_values('record_date', ascending=True).reset_index(drop=True)
        return df_hist
    except Exception as e:
        return pd.DataFrame()
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
