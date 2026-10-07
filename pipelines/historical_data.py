"""
สคริปต์ดึงข้อมูลย้อนหลัง 31 วันจาก RID API และบันทึกลงฐานข้อมูล (Historical ETL Script)
ใช้สำหรับดึงข้อมูลประวัติย้อนหลังเมื่อเริ่มต้นระบบใหม่ หรือต้องการเติมข้อมูลในฐานข้อมูล
"""

import sys
import os
import datetime
import time
import requests
import pandas as pd

# เพิ่ม root directory ใน sys.path เพื่อให้อ่าน config และ core ได้
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import RID_API_URL
from core.db import save_to_database


BASE_API_URL = RID_API_URL
DAYS_BACKWARD = 31


def fetch_real_historical_data():
    """ดึงข้อมูลย้อนหลัง 31 วันจาก RID API และบันทึกลงฐานข้อมูลโดยอัตโนมัติ"""
    print(f"🔄 เริ่มดึงข้อมูลของจริงย้อนหลัง {DAYS_BACKWARD} วันจาก RID API...")
    today = datetime.date.today()
    total_days = 0

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

            df = pd.json_normalize(records, record_path=['dam'], meta=['region'])
            df = df.rename(columns={"dam_id": "id", "dam_name": "name"})

            saved = save_to_database(df, record_date=target_date)
            if saved:
                total_days += 1
                print(f"บันทึกสำเร็จ ({len(df)} เขื่อน)")
            else:
                print("เกิดข้อผิดพลาดในการบันทึก")

            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"❌ Error API: {e}")
        except Exception as e:
            print(f"❌ Error Processing: {e}")

    print(f"\n✨ เสร็จสิ้น! บันทึกข้อมูลย้อนหลังสำเร็จทั้งหมด {total_days} วัน")


if __name__ == "__main__":
    fetch_real_historical_data()