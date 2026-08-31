# Thai Dam Forecast Project

ระบบพยากรณ์ความเสี่ยงน้ำ (Flood/Drought/Normal) ของเขื่อน 35 แห่งในกรมชลประทาน โดยใช้ Machine Learning (RandomForest) + Streamlit Dashboard

## สิ่งที่มีอยู่แล้ว

### โครงสร้างโปรเจค

```
├── app.py                  # Entry point (Streamlit)
├── config.py               # DB_CONFIG, RID_API_URL
├── requirements.txt
├── .gitignore
│
├── core/
│   ├── db.py               # Database operations (save, query, backfill)
│   ├── rid_api.py          # RID API fetch (DB-first approach)
│   └── weka_model.py       # JVM init + model load + prediction
│
├── views/
│   └── user_view.py        # Main dashboard (single page, 6 sections)
│
├── models/
│   ├── trained/            # Trained Weka models
│   │   ├── model7d.model   # RandomForest 100 trees (98.64%)
│   │   └── model30d.model  # RandomForest 100 trees (98.54%)
│   ├── datasets/           # ARFF training datasets
│   │   ├── dam_risk_forecast_7days.arff
│   │   └── dam_risk_forecast_30days.arff
│   └── results/            # Weka evaluation results
│       ├── Weka result 7days.txt
│       └── Weka result 30days.txt
│
├── training/
│   ├── rid_dam_fetcher.py  # Training data pipeline + ARFF export
│   └── historical_data.py  # Fetch real historical data from RID API
│
├── scripts/
│   ├── generate_report.py  # Model evaluation Excel report
│   └── infogain.py         # InfoGain feature ranking
│
└── data/
    ├── dam_forecast_db.sql # DB schema + seed data
    └── dam_forecast_db_v2.sql
```

### ฟีเจอร์ปัจจุบัน

| ฟีเจอร์ | รายละเอียด |
|---------|------------|
| **Predictions** | 7 วัน และ 30 วันล่วงหน้า (Flood/Drought/Normal) |
| **DB-first** | ตรวจสอบฐานข้อมูลก่อน → ถ้ามีข้อมูลวันนี้แล้วข้าม API |
| **Auto-fetch** | ดึงข้อมูลจาก RID API ทุกครั้งที่โหลด ถ้ายังไม่มีวันนี้ |
| **Historical graph** | กราฟแนวโน้มร้อยละความจุย้อนหลัง (30 วัน) |
| **Alert system** | แจ้งเตือนตามระดับความเสี่ยง (🚨/⚠️/✅) |
| **Backfill** | ดึงข้อมูลย้อนหลัง 31 วันในรอบเดียว |
| **Single-page dashboard** | รวมผู้ใช้งาน/ผู้บริหารในหน้าเดียว (6 sections) |
| **InfoGain ranking** | จัดอันดับความสำคัญของ features |
| **Model evaluation** | Export สรุปผลไป Excel |

### Features ที่ใช้ (5 ตัว)
1. `percent_storage` — ร้อยละความจุ
2. `inflow` — น้ำไหลเข้า
3. `outflow` — น้ำไหลออก
4. `month` — เดือน (1-12)
5. `id` — รหัสเขื่อน

### Target classes
- `Normal` — ปกติ
- `Flood` — น้ำล้น (≥80%)
- `Drought` — น้ำแล้ง (<30%)

### Model performance
| Model | Accuracy |
|-------|----------|
| 7 วัน | 98.64% |
| 30 วัน | 98.54% |

### การรัน
```bash
# หน้าหลัก
streamlit run app.py
python -m streamlit run app.py
```

### การตั้งค่า .env
คัดลอก `.env.example` เป็น `.env` แล้วแก้ค่าฐานข้อมูลของคุณ (ไม่ได้อัปโหลดขึ้น git):
```bash
cp .env.example .env
```
ตัวแปรที่ใช้: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `RID_API_URL`

### ฐานข้อมูล
- **DB**: MySQL (`dam_forecast_db`)
- **Table**: `dam_records` (31 วัน × 35 เขื่อน = 1,085 rows)
- **Schema**: `id, dam_id, dam_name, record_date, recorded_at, percent_storage, inflow, outflow`

---

## สิ่งที่ควรทำในอนาคต

### 1. Infrastructure
- [ ] **Dockerize** — docker-compose (MySQL + app)
- [ ] **CI/CD** — GitHub Actions deploy
- [x] **Environment variables** — ✅ ย้าย secrets จาก `config.py` ไป `.env` (ดูหัวข้อ "การตั้งค่า .env")
- [ ] `.gitignore` — ✅ ทำแล้ว (exclude `.model`, `.arff`, `__pycache__`, `.xlsx`, `.env`)

### 2. Model & Training
- [ ] **Auto-retrain** — retrain model ทุก 3-6 เดือนเมื่อมีข้อมูลใหม่
- [ ] **Feature engineering** — เพิ่ม features เช่น rainfall, reservoir capacity
- [ ] **Model comparison** — ทดลอง XGBoost, LightGBM, LSTM
- [ ] **Probability output** — แสดง confidence score แทนแค่ label
- [ ] **Threshold tuning** — optimize precision/recall สำหรับ Flood/Drought

### 3. UI & User Experience
- [ ] **Multi-language** — EN/TH toggle
- [ ] **Map view** — แผนที่แสดงเขื่อนพร้อมสีแสดงความเสี่ยง
- [ ] **Export reports** — PDF/CSV export สำหรับผู้บริหาร
- [ ] **Notification** — Line notify / email เมื่อความเสี่ยงสูง
- [ ] **Mobile responsive** — ปรับ UI ให้ใช้บนมือถือได้

### 4. Data & API
- [ ] **API caching** — Redis/ในตัวเพื่อลดเรียก RID API ซ้ำ
- [ ] **Historical DB** — เก็บข้อมูลเกิน 31 วันเพื่อวิเคราะห์แนวโน้มรายปี
- [ ] **Fallback API** — API สำรองเมื่อ RID API ไม่ตอบ
- [ ] **Rate limiting** — ป้องกัน API abuse

### 5. Monitoring
- [ ] **Logging** — structured logging (JSON)
- [ ] **Prediction monitoring** — track accuracy เมื่อมี actual data
- [ ] **Performance metrics** — response time, DB latency, model inference time
- [ ] **Uptime monitoring** — ตรวจสอบว่า app ทำงานตลอด 24/7

### 6. Testing
- [ ] **Unit tests** — pytest สำหรับ `core/*.py`
- [ ] **Integration tests** — ทดสอบ DB ↔ API ↔ Model pipeline
- [ ] **End-to-end** — Streamlit UI test (Playwright/Selenium)
