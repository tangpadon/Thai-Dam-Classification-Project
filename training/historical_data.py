import requests
import pandas as pd
import datetime
import time
import mysql.connector
from config import DB_CONFIG

BASE_API_URL = "https://app.rid.go.th/reservoir/api/dam/public/"
DAYS_BACKWARD = 31

def fetch_real_historical_data():
    """ดึงข้อมูลจริงย้อนหลังจาก RID API ตามจำนวนวันที่กำหนด"""
    print(f"🔄 เริ่มดึงข้อมูลของจริงย้อนหลัง {DAYS_BACKWARD} วันจาก RID API...")
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        today = datetime.date.today()
        total_inserted = 0
        
        # วนลูปตั้งแต่วันที่ย้อนหลัง 31 วัน จนถึง วันปัจจุบัน
        for d in range(DAYS_BACKWARD, -1, -1):
            target_date = today - datetime.timedelta(days=d)
            date_str = target_date.strftime("%Y-%m-%d")
            api_url = f"{BASE_API_URL}{date_str}"
            
            print(f"📅 กำลังดึงข้อมูลวันที่: {date_str} ... ", end="")
            
            try:
                response = requests.get(api_url, timeout=15)
                response.raise_for_status()
                res_data = response.json()
                
                records = res_data.get("data", res_data)
                if not records:
                    print("ไม่มีข้อมูล")
                    continue
                    
                df = pd.json_normalize(records, record_path=['dam'])
                
                # เปลี่ยนชื่อคอลัมน์ให้ตรงกับฐานข้อมูล
                mapping = {"dam_id": "id", "dam_name": "name"}
                df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
                
                sql = """
                    INSERT IGNORE INTO dam_records 
                    (dam_id, dam_name, record_date, percent_storage, inflow, outflow) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                data = [
                    (
                        row.get('id'),
                        row.get('name'),
                        target_date,
                        float(row.get('percent_storage', 0) if pd.notna(row.get('percent_storage')) else 0),
                        float(row.get('inflow', 0) if pd.notna(row.get('inflow')) else 0),
                        float(row.get('outflow', 0) if pd.notna(row.get('outflow')) else 0)
                    )
                    for _, row in df.iterrows()
                ]
                cursor.executemany(sql, data)
                conn.commit()
                inserted_today = len(data)
                total_inserted += inserted_today
                print(f"บันทึกสำเร็จ {inserted_today} แถว")
                
                # หน่วงเวลา 1 วินาทีเพื่อไม่ให้ API ของกรมชลประทานทำงานหนักเกินไป (ป้องกันการโดนบล็อก IP)
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Error API: {e}")
            except Exception as e:
                print(f"❌ Error Processing: {e}")
                
        print(f"\n✨ เสร็จสิ้น! ดึงข้อมูลจริงย้อนหลังสำเร็จและบันทึกข้อมูลใหม่ทั้งหมด {total_inserted} แถว")
        
    except Exception as e:
        print(f"❌ Database Connection Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    fetch_real_historical_data()