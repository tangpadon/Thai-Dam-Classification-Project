import numpy as np
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Dict, Optional, Tuple, Union
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
    BASE_URL = "https://app.rid.go.th/reservoir/api/dam/public"

    def __init__(self):
        self.session = requests.Session()

    def fetch_daily_data(
        self,
        date: datetime,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> Optional[Dict]:
        date_str = date.strftime("%Y-%m-%d")
        for attempt in range(1, max_retries + 1):
            try:
                response = self.session.get(
                    f"{self.BASE_URL}/{date_str}", timeout=10
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"[{date_str}] Attempt {attempt}/{max_retries} failed: {e}"
                )
                if attempt < max_retries:
                    backoff = retry_delay * (2 ** (attempt - 1))
                    logger.info(f"[{date_str}] Retrying in {backoff:.0f}s...")
                    time.sleep(backoff)
        logger.error(f"[{date_str}] All {max_retries} attempts failed, skipping")
        return None

    def fetch_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        delay: float = 0.5,
    ) -> pd.DataFrame:
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
                            "id":          dam.get("id",                 "Unknown"),
                            "name":        dam.get("name",               "Unknown"),
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
        if pct < 30:
            return "drought"
        if pct > 80:
            return "flood"
        return "normal"


# ──────────────────────────────────────────────────────────────────────────────
# 3. DataProcessor
# ──────────────────────────────────────────────────────────────────────────────

class DataProcessor:
    _FILL_ZERO_AS_NAN = [
        "capacity", "storage", "active_storage",
        "volume", "percent_storage", "inflow", "outflow",
    ]
    _ALL_NUMERIC = _FILL_ZERO_AS_NAN + ["dead_storage"]

    # ── forward fill ──────────────────────────────────────────────────

    @classmethod
    def _forward_fill(cls, df: pd.DataFrame) -> pd.DataFrame:
        out = df.sort_values(["id", "date"]).copy()
        out[cls._FILL_ZERO_AS_NAN] = (
            out[cls._FILL_ZERO_AS_NAN].replace(0, np.nan)
        )
        out[cls._ALL_NUMERIC] = out.groupby("id")[cls._ALL_NUMERIC].ffill()
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
        test_ratio: float = 0.0,
    ) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]]:
        df = df_raw.copy()
        df["date"] = pd.to_datetime(df["date"])

        df = cls._forward_fill(df)

        future_col = f"future_pct_{shift_days}d"
        target_col = f"risk_class_{shift_days}d"

        df = df.sort_values(["id", "date"])
        df[future_col] = (
            df.groupby("id")["percent_storage"].shift(-shift_days)
        )

        n_missing = int(df[future_col].isna().sum())
        if n_missing:
            logger.warning(
                f"Dropped {n_missing:,} rows without "
                f"{shift_days}d-ahead target value "
                f"(last {shift_days}d by design + missing source days)"
            )
        df = df.dropna(subset=[future_col])
        df[target_col] = df[future_col].apply(RiskClassifier.classify)

        start_ts = pd.Timestamp(start_date)
        end_ts   = pd.Timestamp(end_date)
        df = df[(df["date"] >= start_ts) & (df["date"] <= end_ts)].copy()

        if test_ratio > 0:
            n_days = (end_ts - start_ts).days + 1
            cutoff = start_ts + pd.Timedelta(
                days=round(n_days * (1 - test_ratio))
            )
            splits = {
                "train": df[df["date"] <  cutoff],
                "test":  df[df["date"] >= cutoff],
            }
            logger.info(
                f"Temporal split ({shift_days}d): cutoff = {cutoff.date()}  "
                f"(train {len(splits['train']):,} / test {len(splits['test']):,})"
            )
        else:
            splits = {"all": df}

        out = {}
        for key, part in splits.items():
            p = part.drop(columns=[future_col])
            p["month"] = p["date"].dt.month
            out[key] = p.drop(columns=["date"])
            logger.info(
                f"Dataset ({shift_days}d, {key}): {len(p):,} records\n"
                + p[target_col].value_counts().to_string()
            )

        if test_ratio > 0:
            return out["train"], out["test"]
        return out["all"]


# ──────────────────────────────────────────────────────────────────────────────
# 4. ARFF Exporter
# ──────────────────────────────────────────────────────────────────────────────

class ARFFExporter:

    NUMERIC_COLS = [
        "capacity", "storage", "active_storage", "dead_storage",
        "volume", "percent_storage", "inflow", "outflow", "month",
    ]
    CATEGORICAL_COLS = ["id", "name", "region", "owner"]

    @staticmethod
    def _quote(value) -> str:
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"

    @classmethod
    def export(
        cls,
        df: pd.DataFrame,
        filename: str,
        relation_name: str,
        target_col: str,
        domain_df: Optional[pd.DataFrame] = None,
    ) -> None:
        domain_src = df if domain_df is None else domain_df

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"@RELATION {relation_name}\n\n")

            for col in cls.NUMERIC_COLS:
                if col in df.columns:
                    f.write(f"@ATTRIBUTE {col} NUMERIC\n")

            for col in cls.CATEGORICAL_COLS:
                if col in domain_src.columns:
                    vals = ",".join(
                        cls._quote(v)
                        for v in sorted(domain_src[col].dropna().unique())
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
                        values.append(cls._quote(val))
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

    PRE_BUFFER_DAYS = 31

    FETCH_START = START_DATE - timedelta(days=PRE_BUFFER_DAYS)
    FETCH_END   = END_DATE

    logger.info("=" * 60)
    logger.info("RID Dam Data Fetcher with Risk Prediction")
    logger.info("=" * 60)
    logger.info(f"Output range  : {START_DATE.date()} → {END_DATE.date()}")
    logger.info(f"Fetch range   : {FETCH_START.date()} → {FETCH_END.date()}  "
                f"(-{PRE_BUFFER_DAYS}d missing-data buffer at start, "
                f"no end buffer — shift eats last N days by design)")

    # ── Step 1: ดึงข้อมูล ────────────────────────────────────────────
    logger.info("\n[Step 1] Fetching data from RID API...")
    fetcher = RIDDataFetcher()
    df_raw = fetcher.fetch_date_range(FETCH_START, FETCH_END)

    if df_raw.empty:
        logger.error("No data fetched! Exiting.")
        return

    logger.info(f"Raw data shape (incl. missing-data buffer): {df_raw.shape}")

    # ── Train/Test split (time series → temporal, ห้ามสุ่ม) ──────────
    TEST_RATIO = 0.2

    # ── Step 2: สร้าง dataset ─────────────────────────────────────────
    logger.info("\n[Step 2.1] Building 7-day forecast dataset...")
    df_7d_train, df_7d_test = DataProcessor.build_dataset(
        df_raw, START_DATE, END_DATE, shift_days=7, test_ratio=TEST_RATIO
    )

    logger.info("\n[Step 2.2] Building 30-day forecast dataset...")
    df_30d_train, df_30d_test = DataProcessor.build_dataset(
        df_raw, START_DATE, END_DATE, shift_days=30, test_ratio=TEST_RATIO
    )

    # ── Step 3: ส่งออก ARFF (train/test แยกไฟล์) ──────────────────────
    logger.info("\n[Step 3] Exporting ARFF files...")
    dom_7d  = pd.concat([df_7d_train, df_7d_test], ignore_index=True)
    dom_30d = pd.concat([df_30d_train, df_30d_test], ignore_index=True)

    ARFFExporter.export(
        df_7d_train, "dam_risk_forecast_7days_train.arff",
        "dam_risk_forecast_7days", "risk_class_7d", domain_df=dom_7d,
    )
    ARFFExporter.export(
        df_7d_test, "dam_risk_forecast_7days_test.arff",
        "dam_risk_forecast_7days", "risk_class_7d", domain_df=dom_7d,
    )
    ARFFExporter.export(
        df_30d_train, "dam_risk_forecast_30days_train.arff",
        "dam_risk_forecast_30days", "risk_class_30d", domain_df=dom_30d,
    )
    ARFFExporter.export(
        df_30d_test, "dam_risk_forecast_30days_test.arff",
        "dam_risk_forecast_30days", "risk_class_30d", domain_df=dom_30d,
    )

    # ── Step 4: สรุป ──────────────────────────────────────────────────
    days_in_range = (END_DATE - START_DATE).days + 1
    expected_7d   = 35 * (days_in_range - 7)
    expected_30d  = 35 * (days_in_range - 30)
    total_7d  = len(df_7d_train) + len(df_7d_test)
    total_30d = len(df_30d_train) + len(df_30d_test)
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Raw records (incl. missing-data buffer) : {len(df_raw):,}")
    logger.info(f"Full-range base                         : "
                f"{days_in_range}d (366[leap]+365) × 35 dams = "
                f"{35 * days_in_range:,}")
    logger.info(f"Temporal split                          : "
                f"{int((1 - TEST_RATIO) * 100)}% train / "
                f"{int(TEST_RATIO * 100)}% test (by time, no shuffle)")
    logger.info(f"7-day  train/test          : "
                f"{len(df_7d_train):,} / {len(df_7d_test):,}"
                + ("  ✓" if total_7d == expected_7d
                   else f"  ✗ vs expected {expected_7d:,} "
                        f"(diff={total_7d-expected_7d:+}, "
                        f"extra loss = API gaps)"))
    logger.info(f"30-day train/test          : "
                f"{len(df_30d_train):,} / {len(df_30d_test):,}"
                + ("  ✓" if total_30d == expected_30d
                   else f"  ✗ vs expected {expected_30d:,} "
                        f"(diff={total_30d-expected_30d:+}, "
                        f"extra loss = API gaps)"))
    logger.info("\nFiles created:")
    logger.info("  dam_risk_forecast_7days_train.arff")
    logger.info("  dam_risk_forecast_7days_test.arff")
    logger.info("  dam_risk_forecast_30days_train.arff")
    logger.info("  dam_risk_forecast_30days_test.arff")
    logger.info("\nRisk thresholds:")
    logger.info("  drought : percent_storage < 30%")
    logger.info("  normal  : 30% ≤ percent_storage ≤ 80%")
    logger.info("  flood   : percent_storage > 80%")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
