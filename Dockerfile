# 1. ใช้ภาพระบบจำลอง Ubuntu มาตรฐาน
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# 2. ติดตั้ง Java 11 (Headless JRE เพื่อประหยัด RAM และพื้นที่), Python 3, และ pip
RUN apt-get update && apt-get install -y \
    openjdk-11-jre-headless \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# 🌟 ลิงก์คำสั่ง python และ pip ให้เรียกใช้งาน python3/pip3 อัตโนมัติ
RUN ln -sf /usr/bin/python3 /usr/bin/python && ln -sf /usr/bin/pip3 /usr/bin/pip

# 3. กำหนดโฟลเดอร์ทำงานภายในเซิร์ฟเวอร์
WORKDIR /app

# 4. คัดลอกไฟล์ทั้งหมดจาก GitHub เข้ามา
COPY . /app

# 5. ติดตั้งไลบรารี Python
RUN pip install --no-cache-dir -r requirements.txt

# 6. ตั้งค่าตัวแปรระบบ Java และการจำกัด RAM สำหรับเครื่อง 512MB
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV JAVA_TOOL_OPTIONS="-Xmx128m -Xms32m -Xss512k -XX:+UseSerialGC"
ENV WEKA_MAX_HEAP_SIZE="128m"
ENV PORT=10000

# 7. สั่งรันหน้าเว็บ Streamlit (ปิด telemetry เพื่อประหยัดแรม)
CMD ["sh", "-c", "streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --browser.gatherUsageStats false --server.maxUploadSize 10"]
