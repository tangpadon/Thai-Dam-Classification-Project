"""
Database Schema Initialization Script.
Run this script once when setting up a fresh database instance (Local MySQL or TiDB Cloud).
Usage:
    python pipelines/init_db.py
"""

import sys
import os

# เพิ่ม root directory ใน sys.path เพื่อให้อ่าน config ได้
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.db import get_connection


def init_db_schema():
    """สร้างตาราง dam_info และ dam_daily พร้อม Indexes อัตโนมัติหากยังไม่มีใน Database"""
    print("🔄 กำลังตรวจสอบและตั้งค่า Schema ฐานข้อมูล...")
    conn = None
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
        print("  ✅ ตาราง dam_info พร้อมใช้งาน")

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
        print("  ✅ ตาราง dam_daily พร้อมใช้งาน")

        # 3. ตรวจสอบ Composite Index
        cursor.execute("SHOW INDEX FROM dam_daily WHERE Key_name = %s", ('idx_dam_record_date',))
        if not cursor.fetchall():
            cursor.execute("ALTER TABLE dam_daily ADD INDEX idx_dam_record_date (dam_id, record_date DESC);")
            print("  ✅ เพิ่ม Index idx_dam_record_date เรียบร้อย")

        conn.commit()
        print("🎉 ตั้งค่า Schema ฐานข้อมูลเสร็จสมบูรณ์!")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการตั้งค่า Schema: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    init_db_schema()

