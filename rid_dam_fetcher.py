"""
RID Dam Data Fetcher with Shifted Risk Prediction
สร้างไฟล์ ARFF สำหรับพยากรณ์ความเสี่ยงน้ำท่วมและภัยแล้ง
โดย shift percent_storage ล่วงหน้า 7 วัน และ 30 วัน

หลักการ:
- shift(-N) ทำให้แถว t ได้ค่า percent_storage ของวัน t+N
  → วัน (END_DATE - N + 1) ถึง END_DATE จึงไม่มี future value → ถูกตัดทิ้ง
- แก้โดยดึงข้อมูล buffer หลัง END_DATE อีก MAX_SHIFT วัน
  → output จะมีครบทุกวันใน [START_DATE, END_DATE] = 35 × 365 × 2 = 25,550 records
- ไม่มี attribute "total" และ "date" (แปลงเป็น month + season แล้ว)
- Missing value → Forward Fill ด้วยข้อมูลวันก่อนหน้าของเขื่อนเดียวกัน
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Dict, Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# 1. Fetcher
# ──────────────────────────────────────────────────────────────────────────────

class RIDDataFetcher:
    """ดึงข้อมูลจาก RID API"""

    BASE_URL = "https://app.rid.go.th/reservoir/api/dam/public"

    def __init__(self):
        self.session = requests.Session()

    def fetch_daily_data(self, date: datetime) -> Optional[Dict]:
        date_str = date.strftime("%Y-%m-%d")
        try:
            response = self.session.get(
                f"{self.BASE_URL}/{date_str}", timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {date_str}: {e}")
            return None

    def fetch_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        delay: float = 0.5,
    ) -> pd.DataFrame:
        """ดึงข้อมูลในช่วงวันที่กำหนด (inclusive)"""
        all_records = []
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        processed = 0

        while current_date <= end_date:
            data = self.fetch_daily_data(current_date)
            if data and isinstance(data, dict) and "data" in data:
                for region in data["data"]:
                    if not isinstance(region.get("dam"), list):
                        continue
                    for dam in region["dam"]:
                        all_records.append({
                            "date":            current_date.strftime("%Y-%m-%d"),
                            "region":          region.get("region",          "Unknown"),
                            "dam_id":          dam.get("id",                 "Unknown"),
                            "dam_name":        dam.get("name",               "Unknown"),
                            "owner":           dam.get("owner",              "Unknown"),
                            "capacity":        dam.get("capacity",           0),
                            "storage":         dam.get("storage",            0),
                            "active_storage":  dam.get("active_storage",     0),
                            "dead_storage":    dam.get("dead_storage",       0),
                            "volume":          dam.get("volume",             0),
                            "percent_storage": dam.get("percent_storage",    0),
                            "inflow":          dam.get("inflow",             0),
                            "outflow":         dam.get("outflow",            0),
                        })

            processed += 1
            if processed % 10 == 0:
                logger.info(f"Progress: {processed}/{total_days} days")
            current_date += timedelta(days=1)
            time.sleep(delay)

        logger.info(f"Fetched {len(all_records)} records total")
        return pd.DataFrame(all_records)


# ──────────────────────────────────────────────────────────────────────────────
# 2. Risk Classifier
# ──────────────────────────────────────────────────────────────────────────────

class RiskClassifier:
    @staticmethod
    def classify(pct: float) -> str:
        if pd.isna(pct):
            return "normal"
        if pct < 30:
            return "drought"
        if pct > 80:
            return "flood"
        return "normal"


# ──────────────────────────────────────────────────────────────────────────────
# 3. DataProcessor
# ──────────────────────────────────────────────────────────────────────────────

class DataProcessor:
    """
    รับ df_raw ที่ครอบคลุม [START_DATE, END_DATE + MAX_SHIFT วัน] แล้ว:
      1. Forward-fill missing values (groupby dam_id)
      2. Shift percent_storage ล่วงหน้า shift_days วัน → สร้าง target
      3. ตัดแถว buffer หลัง end_date ออก  → เหลือเฉพาะ [start_date, end_date]
      4. แปลง date → month + season แล้วตัด date ทิ้ง
    """

    # คอลัมน์ที่ 0 = missing (API ส่ง 0 แทน null) → แปลงเป็น NaN ก่อน ffill
    # ยกเว้น dead_storage: 0 มีความหมายจริง
    _FILL_ZERO_AS_NAN = [
        "capacity", "storage", "active_storage",
        "volume", "percent_storage", "inflow", "outflow",
    ]
    _ALL_NUMERIC = _FILL_ZERO_AS_NAN + ["dead_storage"]

    # ── season ────────────────────────────────────────────────────────

    @staticmethod
    def _season(ts: pd.Timestamp) -> str:
        """ฤดูกาลตามประกาศกรมอุตุนิยมวิทยา"""
        y, m, d = ts.year, ts.month, ts.day
        if y == 2024:
            if (m == 2 and d >= 21) or m in (3, 4) or (m == 5 and d <= 19):
                return "summer"
            if (m == 5 and d >= 20) or m in (6, 7, 8, 9) or (m == 10 and d <= 28):
                return "rainy"
            return "winter"
        if y == 2025:
            if (m == 2 and d >= 28) or m in (3, 4) or (m == 5 and d <= 14):
                return "summer"
            if (m == 5 and d >= 15) or m in (6, 7, 8, 9) or (m == 10 and d <= 22):
                return "rainy"
            return "winter"
        # ปีอื่น (fallback)
        if m in (3, 4, 5):   return "summer"
        if m in (6, 7, 8, 9, 10): return "rainy"
        return "winter"

    # ── forward fill ──────────────────────────────────────────────────

    @classmethod
    def _forward_fill(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        แปลง 0 → NaN เฉพาะคอลัมน์ที่กำหนด แล้ว ffill ตาม dam_id
        แถวที่ยังเป็น NaN หลัง ffill (เขื่อนที่ไม่มีข้อมูลเลยในช่วงดึง) → 0
        """
        out = df.sort_values(["dam_id", "date"]).copy()
        out[cls._FILL_ZERO_AS_NAN] = out[cls._FILL_ZERO_AS_NAN].replace(0, pd.NA)
        out[cls._ALL_NUMERIC] = out.groupby("dam_id")[cls._ALL_NUMERIC].ffill()
        out[cls._ALL_NUMERIC] = out[cls._ALL_NUMERIC].fillna(0)
        return out

    # ── public API ────────────────────────────────────────────────────

    @classmethod
    def build_dataset(
        cls,
        df_raw: pd.DataFrame,
        start_date: datetime,
        end_date: datetime,
        shift_days: int,
    ) -> pd.DataFrame:
        """
        สร้าง dataset ครบ 35 × 365 × n_years records

        Args:
            df_raw     : raw DataFrame จาก RIDDataFetcher
                         ต้องครอบคลุมถึง end_date + shift_days วัน
            start_date : วันเริ่มต้นของ output
            end_date   : วันสุดท้ายของ output
            shift_days : 7 หรือ 30

        Returns:
            DataFrame ที่มีเฉพาะแถว [start_date, end_date]
            ไม่มีคอลัมน์ date (แทนด้วย month + season)
        """
        df = df_raw.copy()
        df["date"] = pd.to_datetime(df["date"])

        # 1. Forward fill
        df = cls._forward_fill(df)

        # 2. Shift → สร้าง future_pct และ target
        #    shift(-N): แถว t จะได้ percent_storage ของวัน t+N
        #    วัน end_date+1 ถึง end_date+N มาจาก buffer ที่ดึงไว้
        future_col = f"future_pct_{shift_days}d"
        target_col = f"risk_class_{shift_days}d"

        df = df.sort_values(["dam_id", "date"])
        df[future_col] = (
            df.groupby("dam_id")["percent_storage"].shift(-shift_days)
        )
        df[target_col] = df[future_col].apply(RiskClassifier.classify)

        # 3. ตัด buffer rows ออก (เก็บเฉพาะ start_date ถึง end_date)
        #    → แถวหลัง end_date (buffer ที่ดึงมาเพื่อ shift) ถูกตัดออก
        #    → แถวใน [start_date, end_date] จะมี future_pct ครบทุกแถว
        #       เพราะ buffer รับประกันว่ามีข้อมูล shift_days วันถัดไปให้
        start_ts = pd.Timestamp(start_date)
        end_ts   = pd.Timestamp(end_date)
        df = df[(df["date"] >= start_ts) & (df["date"] <= end_ts)].copy()

        # 4. ลบ future_pct (ไม่ใช้เป็น feature)
        df = df.drop(columns=[future_col])

        # 5. แปลง date → month + season แล้วตัด date
        df["month"]  = df["date"].dt.month
        df["season"] = df["date"].apply(cls._season)
        df = df.drop(columns=["date"])

        logger.info(
            f"Dataset ({shift_days}d): {len(df):,} records\n"
            + df[target_col].value_counts().to_string()
        )
        return df


# ──────────────────────────────────────────────────────────────────────────────
# 4. ARFF Exporter
# ──────────────────────────────────────────────────────────────────────────────

class ARFFExporter:

    NUMERIC_COLS = [
        "capacity", "storage", "active_storage", "dead_storage",
        "volume", "percent_storage", "inflow", "outflow", "month",
    ]
    # dam_id (id) และ dam_name (name) อยู่ก่อน region/owner ตามลำดับใน API doc
    CATEGORICAL_COLS = ["dam_id", "dam_name", "region", "owner", "season"]

    @classmethod
    def export(
        cls,
        df: pd.DataFrame,
        filename: str,
        relation_name: str,
        target_col: str,
    ) -> None:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"@RELATION {relation_name}\n\n")

            for col in cls.NUMERIC_COLS:
                if col in df.columns:
                    f.write(f"@ATTRIBUTE {col} NUMERIC\n")

            for col in cls.CATEGORICAL_COLS:
                if col in df.columns:
                    vals = ",".join(
                        str(v) for v in sorted(df[col].dropna().unique())
                    )
                    f.write(f"@ATTRIBUTE {col} {{{vals}}}\n")

            f.write(f"@ATTRIBUTE {target_col} {{drought,normal,flood}}\n")
            f.write("\n@DATA\n")

            export_cols = (
                [c for c in cls.NUMERIC_COLS     if c in df.columns]
                + [c for c in cls.CATEGORICAL_COLS if c in df.columns]
                + [target_col]
            )

            for _, row in df.iterrows():
                values = []
                for col in export_cols:
                    val = row[col]
                    if pd.isna(val):
                        values.append("?")
                    elif col in cls.CATEGORICAL_COLS or col == target_col:
                        values.append(str(val))
                    else:
                        values.append(f"{float(val):.4f}")
                f.write(",".join(values) + "\n")

        logger.info(f"ARFF → {filename}  ({len(df):,} instances)")


# ──────────────────────────────────────────────────────────────────────────────
# 5. Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    # ── ช่วงข้อมูลที่ต้องการใน output ──────────────────────────────
    START_DATE = datetime(2024, 1, 1)
    END_DATE   = datetime(2025, 12, 31)

    # shift สูงสุดที่ใช้ = 30 วัน
    # → ต้องดึงข้อมูลถึง END_DATE + 30 วัน เพื่อให้แถว END_DATE มี future value
    MAX_SHIFT    = 30
    FETCH_END    = END_DATE + timedelta(days=MAX_SHIFT)

    logger.info("=" * 60)
    logger.info("RID Dam Data Fetcher with Risk Prediction")
    logger.info("=" * 60)
    logger.info(f"Output range  : {START_DATE.date()} → {END_DATE.date()}")
    logger.info(f"Fetch range   : {START_DATE.date()} → {FETCH_END.date()}  "
                f"(+{MAX_SHIFT}d buffer at end)")

    # ── Step 1: ดึงข้อมูล (รวม buffer ท้าย) ──────────────────────────
    logger.info("\n[Step 1] Fetching data from RID API...")
    fetcher = RIDDataFetcher()
    df_raw = fetcher.fetch_date_range(START_DATE, FETCH_END)

    if df_raw.empty:
        logger.error("No data fetched! Exiting.")
        return

    logger.info(f"Raw data shape (with buffer): {df_raw.shape}")

    # ── Step 2: สร้าง dataset ─────────────────────────────────────────
    logger.info("\n[Step 2.1] Building 7-day forecast dataset...")
    df_7d = DataProcessor.build_dataset(
        df_raw, START_DATE, END_DATE, shift_days=7
    )

    logger.info("\n[Step 2.2] Building 30-day forecast dataset...")
    df_30d = DataProcessor.build_dataset(
        df_raw, START_DATE, END_DATE, shift_days=30
    )

    # ── Step 3: ส่งออก ARFF ───────────────────────────────────────────
    logger.info("\n[Step 3] Exporting ARFF files...")
    ARFFExporter.export(
        df_7d,  "dam_risk_forecast_7days.arff",
        "dam_risk_forecast_7days",  "risk_class_7d",
    )
    ARFFExporter.export(
        df_30d, "dam_risk_forecast_30days.arff",
        "dam_risk_forecast_30days", "risk_class_30d",
    )

    # ── Step 4: สรุป ──────────────────────────────────────────────────
    # 2024 เป็นปีอธิกสุรทิน (366 วัน) → 35 × (366+365) = 35 × 731 = 25,585
    days_in_range = (END_DATE - START_DATE).days + 1
    expected = 35 * days_in_range
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Raw records (incl. buffer) : {len(df_raw):,}")
    logger.info(f"Expected output records    : {expected:,}  "
                f"(35 dams × {days_in_range}d = 366d[2024 leap]+365d[2025])")
    logger.info(f"7-day  dataset             : {len(df_7d):,}"
                + ("  ✓" if len(df_7d) == expected else f"  ✗ (diff={len(df_7d)-expected:+})"))
    logger.info(f"30-day dataset             : {len(df_30d):,}"
                + ("  ✓" if len(df_30d) == expected else f"  ✗ (diff={len(df_30d)-expected:+})"))
    logger.info("\nFiles created:")
    logger.info("  dam_risk_forecast_7days.arff")
    logger.info("  dam_risk_forecast_30days.arff")
    logger.info("\nRisk thresholds:")
    logger.info("  drought : percent_storage < 30%")
    logger.info("  normal  : 30% ≤ percent_storage ≤ 80%")
    logger.info("  flood   : percent_storage > 80%")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
