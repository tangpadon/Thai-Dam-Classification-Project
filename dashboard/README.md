คู่มือการใช้งาน: เว็บแดชบอร์ดพยากรณ์สถานการณ์น้ำ


1. ภาพรวมระบบ 
เว็บแดชบอร์ดพัฒนาด้วย Streamlit สำหรับติดตามสถานการณ์น้ำและพยากรณ์ความเสี่ยง
(แล้ง / ปกติ / น้ำล้น) ล่วงหน้า 7 วัน และ 30 วัน ของอ่างเก็บน้ำ 35 แห่งทั่วประเทศ
โดยประมวลผลด้วยโมเดล Machine Learning (Weka Framework: Logistic Regression
และ Random Forest) พร้อมกลไก DB-First ดึงข้อมูลอัตโนมัติจาก RID Open API
และเชื่อมต่อฐานข้อมูล MySQL


2. ข้อกำหนดของระบบ (Prerequisites)

  → Python 3.10 ขึ้นไป
  → Java Runtime Environment (JRE 8 ขึ้นไป)
   - จำเป็นสำหรับการรัน Weka บน JVM ผ่าน python-weka-wrapper3
  → ฐานข้อมูล MySQL Server


4. ขั้นตอนการติดตั้งและตั้งค่าระบบ

ขั้นตอนที่ 1: เข้าสู่โฟลเดอร์ dashboard
  cd dashboard

ขั้นตอนที่ 2: ติดตั้ง Dependencies ของ Python
  pip install -r requirements.txt

ขั้นตอนที่ 3: ตั้งค่าไฟล์ .env
  คัดลอกไฟล์ .env.example เป็น .env
    cp .env.example .env

  แก้ไขค่าในไฟล์ .env ให้ตรงกับฐานข้อมูล MySQL:
    DB_HOST=localhost
    DB_USER=root
    DB_PASSWORD=รหัสผ่านของคุณ
    DB_NAME=dam_forecast_db
    DB_PORT=3306
    RID_API_URL=https://app.rid.go.th/reservoir/api/dam/public/

ขั้นตอนที่ 4: นำเข้าฐานข้อมูล
  เลือกวิธีใดวิธีหนึ่ง:
  วิธีที่ 4.1: นำเข้าข้อมูลตัวอย่างล่าสุดจากไฟล์ SQL
    mysql -u root -p dam_forecast_db < data_backup/dam_forecast_db_backup.sql

  วิธีที่ 4.2: หรือสร้างเฉพาะตารางเปล่าผ่าน Python
    python pipelines/init_db.py


5. วิธีการรันแดชบอร์ด
  → สั่งรันเว็บแอปพลิเคชันด้วยคำสั่ง Streamlit:
    streamlit run app.py

  → หรือรันผ่านโมดูล Python:
    python -m streamlit run app.py

เมื่อเปิดเว็บเบราว์เซอร์แล้ว (ปกติที่ http://localhost:8501):
  - ระบบจะเชื่อมต่อ JVM และโหลดโมเดล Weka โดยอัตโนมัติ
  - ระบบจะตรวจสอบข้อมูลในฐานข้อมูล (DB-first Strategy)
  - หากเป็นวันใหม่ ระบบจะดึงข้อมูลอัตโนมัติจาก RID API และบันทึกลงฐานข้อมูล
  - หน้าเว็บจะแสดงผลครบ 7 ส่วน: ภาพรวม, ผลพยากรณ์, กราฟแนวโน้ม, และสรุปสถานการณ์
================================================================================
