# Session Log — Thai Dam Forecast Project

> สรุปตอนท้าย session: 2026-06-30 16:22
> โหลดไฟล์นี้ขึ้นมาแล้วพิมพ์ `continue` เพื่อทำงานต่อ

---

## Current Structure
```
dam-forecast-project/
├── app.py              # Entry point → route admin/user
├── dashboard.py        # Standalone dashboard
├── config.py           # DB_CONFIG, RID_API_URL (no secrets hardcoded)
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
│   ├── dam_risk_forecast_7days.arff   # Header (14 attrs, used for metadata only)
│   └── dam_risk_forecast_30days.arff
├── training/
│   ├── rid_dam_fetcher.py      # ARFF generation pipeline
│   └── historical_data.py      # Bulk fetch from RID API
├── scripts/
│   ├── generate_report.py      # Excel evaluation report
│   └── infogain.py             # Feature ranking
└── data/
    └── dam_forecast_db.sql
```

## Key Architecture Decisions
1. **DB-first** — `fetch_and_save_data()` checks DB for today first; if exists, skip API
2. **5 features** — percent_storage, inflow, outflow, month, id (season dropped)
3. **Header from ARFF** — `_extract_header()` reads only 5 features + class from .arff metadata (6 attrs)
4. **No `@st.cache_data`** on fetch — DB check is fast enough (~1ms)
5. **`int(dam_id)`** in `get_historical_data` — prevents numpy.int64 crash with mysql.connector

## State
- Project reorganized into `core/`, `views/`, `models/`, `training/`, `scripts/`, `data/`
- All imports updated (root → `core.`)
- Old root-level `.py` files deleted (`db.py`, `rid_api.py`, `weka_model.py`)
- README.md updated with "done" + "future" sections
- JVM loads, models load, DB queries work

## Critical Constraints
- **Python 3.13** (Windows)
- **MySQL**: `dam_forecast_db.dam_records` — 1085 rows (31d × 35 dams)
- **RID API**: `https://app.rid.go.th/reservoir/api/dam/public/{YYYY-MM-DD}`
- **JVM**: Required by `python-weka-wrapper3` (javabridge)
- **Run**: `streamlit run app.py` or `streamlit run dashboard.py`

## Next Steps
1. **`.gitignore`** — add `*.model`, `*.arff`, `__pycache__/`, `*.xlsx`, `.env`
2. **Test `streamlit run app.py`** — verify predictions + graph render
3. **`__pycache__` cleanup** — remove root-level `__pycache__/`, keep only in `core/`
4. Then pick from README.md "สิ่งที่ควรทำในอนาคต" (Docker, auto-retrain, map view, etc.)

## Keywords for Search
- `ArrayIndexOutOfBoundsException` → model/header mismatch → fix: `_extract_header()` 6 attrs
- `numpy.int64` → `pd.read_sql` bug → fix: `int(dam_id)`
- `NameError: Instances` → missing import → fix: `from weka.core.dataset import Instances`
- backfill not working → `@st.cache_data` blocking → fix: extracted `backfill_historical_data()`
