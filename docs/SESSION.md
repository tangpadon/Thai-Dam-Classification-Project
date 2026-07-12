# Session Log — Thai Dam Forecast Project

> สรุปตอนท้าย session: 2026-07-03
> โหลดไฟล์นี้ขึ้นมาแล้วพิมพ์ `continue` เพื่อทำงานต่อ

---

## Current Structure
```
dam-forecast-project/
├── app.py              # Entry point → route admin/user
├── dashboard.py        # Standalone dashboard
├── config.py           # DB_CONFIG, RID_API_URL
├── core/
│   ├── db.py           # save_to_database, get_historical_data, get_recorded_time
│   ├── rid_api.py      # fetch_and_save_data (DB-first), backfill_historical_data
│   └── weka_model.py   # init_jvm_safe, load_resources, predict_single_dam
├── views/
│   ├── admin_view.py   # Graph + alerts
│   └── user_view.py    # Card layout for public
├── models/
│   ├── model7d.model           # RandomForest 100 trees (98.64%)
│   ├── model30d.model          # RandomForest 100 trees (98.54%)
│   ├── dam_risk_forecast_7days.arff   # Header (15 attrs)
│   ├── dam_risk_forecast_30days.arff
│   └── dam_risk_forecast_7days_with_netinflow.arff
├── training/
│   ├── rid_dam_fetcher.py      # ARFF generation pipeline
│   └── historical_data.py      # Bulk fetch from RID API
├── scripts/
│   ├── generate_report.py      # Excel evaluation report
│   ├── infogain.py             # Feature ranking (InfoGain + Ranker)
│   └── model_evaluation_summary.xlsx
└── data/
    └── dam_forecast_db.sql
```

## Key Architecture Decisions
1. **DB-first** — `fetch_and_save_data()` checks DB for today first; if exists, skip API
2. **5 features in current model** — percent_storage, inflow, outflow, month, id (but circular!)
3. **Header from ARFF** — `_extract_header()` reads 5 features + class from .arff metadata (6 attrs)
4. **No `@st.cache_data`** on fetch — DB check is fast enough (~1ms)
5. **`int(dam_id)`** in `get_historical_data` — prevents numpy.int64 crash with mysql.connector

---

## Session: 2026-07-03 — Feature Selection Analysis

### 1. เปิดเอกสารรายงาน (รวมเล่ม_พยากรณ์น้ำเขื่อน) — เปรียบเทียบ attributes

จากเอกสารบทที่ 3:
- **Input Features ที่ระบุ**: Inflow, Outflow, %Capacity, Volume, Date → Month, IsRainySeason
- **ไม่ใช้**: capacity, storage, active_storage, dead_storage, id, name, region, owner

### 2. สรุป Attribute ตัด/เก็บ

| Attribute | การตัดสินใจ | เหตุผล |
|-----------|------------|--------|
| inflow | ✅ เก็บ | ตรงเอกสาร |
| outflow | ✅ เก็บ | ตรงเอกสาร |
| month | ✅ เก็บ | จาก Date |
| season | ⚠️ เก็บหรือ drop (ซ้ำซ้อน month) | ไม่ต้องพึ่งกรมอุตุ |
| volume | ❌ ตัด | circular — volume ∝ percent_storage |
| percent_storage | ❌ ตัด | circular — ใช้ define target class โดยตรง |
| capacity | ❌ ตัด | metadata API |
| storage | ❌ ตัด | metadata API |
| active_storage | ❌ ตัด | metadata API |
| dead_storage | ❌ ตัด | metadata API |
| id | ❌ ตัด | identifier → memorization |
| name | ❌ ตัด | identifier ซ้ำ id |
| region | ❌ ตัด | metadata API |
| owner | ❌ ตัด | metadata API |

### 3. InfoGain Result — หลังตัด attributes จนเหลือ 5 attrs

Run บน `inflow, outflow, month, season, risk_class_7d` (ตัด volume, percent_storage, id, name, region, owner, capacity, storage, active_storage, dead_storage ออก):

```
average merit  average rank  attribute
 0.305         1             month
 0.187         2             outflow
 0.129         3             season
 0.07          4             inflow
```

**InfoGain สะท้อน causal signal จริงแล้ว** — month ครองเพราะ seasonality, inflow ต่ำสุดเพราะ daily noise สูง

### 4. ข้อสรุปเกี่ยวกับ season

- `season` ซ้ำซ้อนกับ `month` (month มี 12 levels, season มี 3)
- การอิง season จากกรมอุตุ (ประกาศฤดูกาลจริง) **เกินขอบเขตโครงการ** — maintenance overhead ไม่จำเป็น
- **แนะนำ**: ใช้แค่ `month` หรือ one-hot encode month 1-12 แทน

### 5. Alternative Attribute Selection Methods (นอกจาก InfoGain)

| Method | ประเภท | เหมาะกับ data นี้ |
|--------|--------|-------------------|
| **ReliefFAttributeEval** | Filter (ranking) | ⭐⭐⭐ ดีสุด — จับ non-linear interaction |
| **GainRatioAttributeEval** | Filter (ranking) | ⭐⭐ normalize InfoGain |
| **ChiSquaredAttributeEval** | Filter (ranking) | ⭐ nominal attributes |
| **SymmetricalUncertAttributeEval** | Filter (ranking) | ⭐⭐ normalized 0-1 |
| **CfsSubsetEval + BestFirst** | Filter (subset) | ⭐⭐ แต่ยังมี bias ถ้า PS lags |
| **WrapperSubsetEval + RandomForest** | Wrapper (subset) | ⭐⭐⭐ optimize accuracy จริง |
| **OneRAttributeEval** | Filter (ranking) | ⭐ รวดเร็วแต่หยาบ |

### 6. Circular Logic ที่พบ

- `risk_class_7d` ถูก define โดย threshold ของ `percent_storage` (drought <30%, normal 30-80%, flood ≥80%)
- `volume` = `percent_storage × capacity / 100` → correlation ≈ 1.0 กับ target class
- `percent_storage` → merit ~0.95+ ถ้าใส่ใน InfoGain (เทียบกับ inflow ~0.07)
- **ต้องตัด ALL columns ที่ derive จาก percent_storage ก่อน feature selection**

---

## Critical Constraints
- **Python 3.13** (Windows)
- **MySQL**: `dam_forecast_db.dam_records` — 1085 rows (31d × 35 dams)
- **RID API**: `https://app.rid.go.th/reservoir/api/dam/public/{YYYY-MM-DD}`
- **JVM**: Required by `python-weka-wrapper3` (javabridge)
- **Run**: `streamlit run app.py` or `streamlit run dashboard.py`
- **Current model uses 5 features** (percent_storage, inflow, outflow, month, id) — ต้อง retrain ถ้าจะเปลี่ยน feature set

## Next Steps (Future Work)
1. **Retrain model with clean feature set** — ใช้แค่ inflow, outflow, month (drop percent_storage, id, volume, season)
2. **Implement alternative evaluator** — เพิ่ม ReliefFAttributeEval ใน `scripts/infogain.py` หรือสร้าง script ใหม่
3. **Update `weka_model.py`** — ถ้าเปลี่ยน features ต้อง update `FEATURES` list + regenerate `.model` files
4. **Update README.md** — แก้ไข feature list และ model performance
5. **Train new model without circular features** — verify accuracy ยัง ~98% จริง

## Keywords for Search
- `ArrayIndexOutOfBoundsException` → model/header mismatch → fix: `_extract_header()` 6 attrs
- `numpy.int64` → `pd.read_sql` bug → fix: `int(dam_id)`
- `NameError: Instances` → missing import → fix: `from weka.core.dataset import Instances`
- backfill not working → `@st.cache_data` blocking → fix: extracted `backfill_historical_data()`
- **circular logic** → percent_storage/volume → risk_class → feature selection biased
- **InfoGain merit** → month=0.305, outflow=0.187, season=0.129, inflow=0.07
