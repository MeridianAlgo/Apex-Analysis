# Model Training Process

This document outlines how to train, evaluate, and deploy the ML components defined in `src/ml_models.py`.

## 1. Data Ingestion
- Use `aggregate_analysis()` or `data_handler.py` to pull OHLCV data, engineered indicators, and sentiment signals.
- Persist raw pulls in `cache/ml_data/` (ignored in git) to ensure reproducibility.

## 2. Feature Engineering
- Apply `technical_analysis.add_all_indicators()` for momentum/volatility signals.
- Merge alternative data (sentiment, macro) via consistent timestamps and forward-fill gaps.
- Normalize/scale features per ticker or per training batch (`sklearn.StandardScaler`).

## 3. Dataset Splits
- Chronological splits: 70% train, 15% validation, 15% test to avoid look-ahead bias.
- Optional walk-forward: retrain on rolling windows when evaluating live strategies.

## 4. Model Training
- **TrendClassifier**: train RandomForest/XGBoost classifiers on direction labels (`Close(t+N) > Close(t)`).
- **AnomalyDetector**: isolation forest or autoencoder to flag outlier price moves/vol spikes.
- Store fitted models and scalers in `cache/models/{model_name}_{timestamp}.joblib` with metadata JSON (features, label horizon, evaluation metrics).

## 5. Evaluation
- Compute precision/recall, ROC-AUC for classifiers; use hit ratio / average holding-period return for strategy alignment.
- Track baseline vs. model uplift; log metrics to `reports/model_metrics.json` for dashboards.

## 6. Deployment
- Ship the latest approved model artifact and load it lazily within API routes (e.g., `/api/v1/analyze` optional ML augmentations).
- Version models explicitly (`model_version` field) so downstream consumers can pin behavior.

## 7. Automation
- Use the provided profiling scripts (`profile_code.py`, `demo_ml_trading.py`) as templates for CI jobs.
- Nightly workflow: fetch latest data, retrain with updated window, run evaluation, and only promote if metrics beat thresholds.

Following these steps keeps the ML pipeline transparent and reproducible.
