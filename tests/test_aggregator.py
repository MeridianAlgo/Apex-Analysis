from datetime import datetime
from pathlib import Path

import pandas as pd

import src.aggregator as aggregator
import src.utils as utils


def test_single_ticker_runs(monkeypatch, tmp_path):
    history = pd.DataFrame(
        {"Close": [100.0, 101.5], "Volume": [10, 12]},
        index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
    )

    def fake_fetch_stock_data(ticker: str, period: str = "1y"):
        return {"history": history.copy()}

    sample_news = [
        {
            "title": "Sample Headline",
            "date": datetime(2024, 1, 1),
            "sentiment": 0.25,
            "sentiment_keywords": ["bullish"],
        }
    ]

    monkeypatch.setattr(aggregator, "fetch_stock_data", fake_fetch_stock_data)
    monkeypatch.setattr(
        aggregator, "fetch_news_rss", lambda ticker, num: sample_news
    )
    monkeypatch.setattr(
        aggregator, "batch_analyze", lambda news: sample_news
    )
    monkeypatch.setattr(aggregator, "utils_get_company_dir", lambda t: tmp_path / t)
    monkeypatch.setattr(utils, "REPORTS_DIR", tmp_path)

    result = aggregator.aggregate_analysis("AAPL")
    assert "AAPL" in result
    data = result["AAPL"]
    assert data["ticker"] == "AAPL"
    assert not data["price_df"].empty
    assert data["sentiment_summary"]["count"] == 1
    assert data["saved_files"]
    for path in data["saved_files"]:
        assert Path(path).exists()
