# 1. ใช้ภาพระบบจำลอง Ubuntu มาตรฐานที่เสถียรและใช้งานกันอย่างแพร่หลาย
FROM ubuntu:22.04

# ตั้งค่าไม่ให้ระบบหยุดถามคำถามระหว่างติดตั้งแพ็กเกจ (เช่น ป้อนโซนเวลา)
ENV DEBIAN_FRONTEND=noninteractive

# 2. อัปเดตและติดตั้ง Java 11, Python 3, และ pip พร้อมล้างแคชเพื่อลดขนาดไฟล์
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# 3. กำหนดโฟลเดอร์ทำงานภายในเซิร์ฟเวอร์
WORKDIR /app

# 4. คัดลอกไฟล์ทั้งหมดจาก GitHub เข้ามาในโฟลเดอร์ /app
COPY . /app

# 5. ติดตั้งไลบรารี Python ตามที่ระบุไว้ใน requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 6. ตั้งค่าตัวแปรระบบเพื่อให้ Python ดึงและเรียกใช้ Java (สำคัญมากสำหรับ Weka/JPype)
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PORT=10000

# 7. สั่งรันหน้าเว็บ Streamlit ทันทีเมื่อเซิร์ฟเวอร์เริ่มทำงาน
CMD ["sh", "-c", "python -m streamlit run app.py --server.port $PORT --server.address 0.0.0.0"]
