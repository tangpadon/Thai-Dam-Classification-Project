# 1. ใช้ภาพระบบจำลองทางการที่มีทั้ง Python 3.11 และ Java 11 ติดตั้งมาให้พร้อมกัน
FROM osgeo/gdal:ubuntu-small-latest

# 2. ติดตั้ง Python และเครื่องมือจัดการแพ็กเกจเพิ่มในระบบ
RUN apt-get update && apt-get install -y python3-pip python3-venv openjdk-11-jdk && rm -rf /var/lib/apt/lists/*

# 3. กำหนดโฟลเดอร์ทำงานภายในเซิร์ฟเวอร์
WORKDIR /app

# 4. คัดลอกไฟล์ทั้งหมดจากคอมพิวเตอร์ของเราเข้าเซิร์ฟเวอร์
COPY . /app

# 5. สร้าง Virtual Environment และติดตั้งไลบรารีตาม requirements.txt
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# 6. ตั้งค่าตัวแปรระบบเพื่อให้โปรแกรมเจอ Java (สำคัญมากสำหรับ Weka)
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PORT=10000

# 7. สั่งรันหน้าเว็บ Streamlit ทันทีที่เปิดเครื่อง
CMD ["sh", "-c", "python -m streamlit run app.py --server.port $PORT --server.address 0.0.0.0"]
