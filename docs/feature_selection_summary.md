# Feature Selection Summary — Thai Dam Risk Forecast

## 1. Circular Logic Discovery (Critical)

**Problem:** `risk_class` (drought/normal/flood) is deterministically defined by `percent_storage` thresholds:

| `percent_storage` | `risk_class` |
|---|---|
| < 30% | drought |
| 30% – 80% | normal |
| ≥ 80% | flood |

If `percent_storage` (or any lagged/derived form of it) is included as a predictor, the model is essentially being given the answer. This causes:

- **InfoGain** → Gain ≈ 1.0 (percent_storage ranked #1 by a huge margin)
- **Accuracy** → artificially ≥97% (the model "cheats")
- **Feature selection** → CFS Subset Evaluator consistently picks percent_storage lags over inflow/outflow lags

## 2. Original Feature Set (Problematic)

| Attribute | Type | Issue |
|-----------|------|-------|
| capacity | numeric | OK |
| storage | numeric | correlates with percent_storage |
| active_storage | numeric | correlates with percent_storage |
| dead_storage | numeric | correlates with percent_storage |
| volume | numeric | correlates with percent_storage |
| **percent_storage** | **numeric** | **🔴 CIRCULAR — determines class directly** |
| inflow | numeric | OK |
| outflow | numeric | OK |
| month | numeric | OK (seasonal proxy) |
| **id** | **nominal (35 dams)** | **🔴 IDENTIFIER — causes memorisation** |
| **name** | **nominal (Thai)** | **🔴 IDENTIFIER — duplicate of id** |
| region | nominal (Thai) | OK, but needs encoding |
| owner | nominal (Thai) | OK, but needs encoding |
| season | nominal (English) | OK |

## 3. Proposed Feature Sets

### 3A. Minimal Clean Set
Remove all circular/identifier attributes:
```
inflow, outflow, month, region, owner, season
```

### 3B. With Engineered Lag Features (Implemented)
```
inflow, outflow, month, region, owner, season,
lag_1_inflow, lag_3_inflow, lag_7_inflow, lag_14_inflow, lag_30_inflow,
lag_1_outflow, lag_3_outflow, lag_7_outflow, lag_14_outflow, lag_30_outflow,
rolling_3d_mean_inflow, rolling_7d_mean_inflow,
rolling_3d_mean_outflow, rolling_7d_mean_outflow,
delta_1d_inflow, delta_3d_inflow, delta_7d_inflow,
delta_1d_outflow, delta_3d_outflow, delta_7d_outflow
```

### 3C. With net_inflow (This File)
Same as 3B, plus `net_inflow = inflow - outflow`.

## 4. CFS Subset Evaluator Results (Still Biased)

Even after removing raw `percent_storage`, `id`, `name`, the CFS Subset Evaluator **still picks `percent_storage` lag features** because they remain highly correlated with the target. The evaluator cannot distinguish causation from definitional correlation.

**For a truly unbiased ranking, ALL columns containing `percent_storage` must be removed before feature selection.**

## 5. Pipeline Results Summary

| Forecast | Features | Best Model | Accuracy | Kappa |
|----------|----------|------------|----------|-------|
| 7-day | With PS lags | RandomForest | 98.79% | 0.9745 |
| 7-day | **No PS anywhere** | **RandomForest** | **98.91%** | **0.9770** |
| 30-day | With PS lags | RandomForest | 98.91% | 0.9775 |
| 30-day | **No PS anywhere** | **RandomForest** | **98.77%** | **0.9746** |

**Key insight:** Accuracy stays ≈98% even without `percent_storage` — inflow, outflow, and their lag features provide genuine predictive signal.

## 6. Remaining Issues

| # | Issue | Severity |
|---|-------|----------|
| 1 | CFS still picks percent_storage lags — remove all PS columns before InfoGain | 🔴 |
| 2 | InfoGain Ranker API not producing per-attribute values | 🟡 |
| 3 | Logistic Regression on 30‑day weak (<85%) | 🟡 |
| 4 | Original production models trained with PS + id (inflated acc) | 🟡 |

## 7. Files Reference

| File | Description |
|------|-------------|
| `models/dam_risk_forecast_7days.arff` | Original 7‑day ARFF (15 attrs, unmodified) |
| `models/dam_risk_forecast_7days_with_netinflow.arff` | Copy with `net_inflow` added |
| `models/dam_risk_forecast_30days.arff` | Original 30‑day ARFF |
| `models/processed/dam_risk_forecast_7days_processed.arff` | Cleaned + lag features (with PS lags) |
| `models/processed/dam_risk_forecast_7days_no_ps.arff` | Cleaned + lag features (NO PS anywhere) |
| `models/processed/dam_risk_forecast_30days_processed.arff` | Cleaned + lag features (with PS lags) |
| `models/processed/dam_risk_forecast_30days_no_ps.arff` | Cleaned + lag features (NO PS anywhere) |
| `scripts/full_pipeline.py` | Preprocess → InfoGain → Train → Evaluate |
| `scripts/model_evaluation_summary.xlsx` | Excel report with all results |
