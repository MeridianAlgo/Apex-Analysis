import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Union

import numpy as np
import pandas as pd

from src.fetch_data import fetch_stock_data
from src.news_processor import fetch_news_rss
from src.sentiment_analyzer import batch_analyze
from src.utils import (
    logger,
    get_company_dir as utils_get_company_dir,
    save_dataframe,
    save_json,
)


def get_company_dir(ticker: str) -> Path:
    return utils_get_company_dir(ticker)


def _normalize_tickers(tickers: Union[str, List[str]]) -> List[str]:
    if isinstance(tickers, str):
        raw = tickers.split(",")
    else:
        raw = tickers
    return [t.strip().upper() for t in raw if t and t.strip()]


def calculate_sentiment_metrics(rows):
    if not rows:
        return {}
    scores = []
    for r in rows:
        s = r.get("sentiment")
        if isinstance(s, (int, float)):
            scores.append(float(s))
    if not scores:
        return {}
    keywords = set()
    for r in rows:
        kws = r.get("sentiment_keywords")
        if isinstance(kws, (list, tuple, set)):
            for kw in kws:
                keywords.add(str(kw))
    return {
        "average": float(np.mean(scores)),
        "count": len(scores),
        "strongly_positive": len([s for s in scores if s >= 0.15]),
        "positive": len([s for s in scores if 0.05 <= s < 0.15]),
        "neutral": len([s for s in scores if -0.05 < s < 0.05]),
        "negative": len([s for s in scores if -0.15 < s <= -0.05]),
        "strongly_negative": len([s for s in scores if s <= -0.15]),
        "keywords": list(keywords),
    }


def _build_sentiment_df(analyzed: List[Dict[str, Any]]) -> pd.DataFrame:
    if not analyzed:
        return pd.DataFrame()
    rows = []
    for a in analyzed:
        ts = a.get("date") or a.get("published") or a.get("analysis_timestamp")
        rows.append(
            {
                "date": ts,
                "sentiment": a.get("sentiment", 0.0),
                "title": a.get("title", ""),
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date"].notna().any():
        df = df.set_index("date").sort_index()
    return df


def _analyze_single_ticker(
    ticker: str,
    period: str = "1y",
    num_articles: int = 20,
) -> Dict[str, Any]:
    t = ticker.upper()
    ts = datetime.now().isoformat()
    ts_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    out: Dict[str, Any] = {
        "ticker": t,
        "timestamp": ts,
        "price_df": pd.DataFrame(),
        "news_df": pd.DataFrame(),
        "sentiment_df": pd.DataFrame(),
        "sentiment_summary": {},
        "saved_files": [],
        "error": None,
    }

    ticker_dir = get_company_dir(t)

    try:
        stock_data = fetch_stock_data(t, period)
    except Exception as e:
        msg = f"Error fetching stock data for {t}: {e}"
        logger.error(msg, exc_info=True)
        out["error"] = msg
        stock_data = None

    if stock_data and isinstance(stock_data, dict) and "history" in stock_data:
        hist = stock_data["history"]
        if not hist.empty:
            if not isinstance(hist, pd.DataFrame):
                hist = pd.DataFrame(hist)
            out["price_df"] = hist
            csv_path = save_dataframe(hist.reset_index(), f"{t}_price_data_{ts_tag}", t)
            out["saved_files"].append(str(csv_path))
            out["price_data"] = hist.reset_index().to_dict(orient="records")
        else:
            logger.warning("No price history for %s", t)
    elif out["error"] is None:
        out["error"] = f"No price data available for {t}"

    try:
        news_raw = fetch_news_rss(t, num_articles)
    except Exception as e:
        msg = f"Error fetching news for {t}: {e}"
        logger.error(msg, exc_info=True)
        if not out["error"]:
            out["error"] = msg
        news_raw = []

    analyzed_rows: List[Dict[str, Any]] = []
    if news_raw:
        analyzed = batch_analyze(news_raw)
        if isinstance(analyzed, pd.DataFrame):
            news_df = analyzed.copy()
            analyzed_rows = news_df.to_dict(orient="records")
        else:
            analyzed_rows = list(analyzed)
            news_df = pd.DataFrame(analyzed_rows)
        out["news_df"] = news_df
        out["news"] = analyzed_rows
        out["sentiment_summary"] = calculate_sentiment_metrics(analyzed_rows)
        sent_df = _build_sentiment_df(analyzed_rows)
        out["sentiment_df"] = sent_df
        news_json_path = ticker_dir / f"{t}_news_{ts_tag}.json"
        save_json(news_json_path, analyzed_rows)
        out["saved_files"].append(str(news_json_path))
    else:
        out["news"] = []
        out["sentiment_summary"] = {}

    summary = {
        "ticker": t,
        "timestamp": ts,
        "price_data_points": int(len(out.get("price_data", []))),
        "news_articles_analyzed": int(len(out.get("news", []))),
        "sentiment_summary": out.get("sentiment_summary", {}),
        "saved_files": out.get("saved_files", []),
        "error": out.get("error"),
    }
    summary_path = ticker_dir / f"{t}_summary_{ts_tag}.json"
    save_json(summary_path, summary)
    out["saved_files"].append(str(summary_path))

    verified = []
    for p in out["saved_files"]:
        if Path(p).exists():
            verified.append(p)
        else:
            logger.warning("Expected file not found: %s", p)
    out["saved_files"] = verified

    if not verified and not out["error"]:
        out["error"] = "No report files were generated. Check logs."

    return out


def aggregate_analysis(
    tickers: Union[str, List[str]],
    period: str = "1y",
    num_articles: int = 20,
) -> Dict[str, Any]:
    symbols = _normalize_tickers(tickers)
    results: Dict[str, Any] = {}
    for t in symbols:
        try:
            results[t] = _analyze_single_ticker(t, period=period, num_articles=num_articles)
        except Exception as e:
            msg = f"Unexpected error in aggregate_analysis for {t}: {e}"
            logger.error(msg, exc_info=True)
            results[t] = {
                "ticker": t,
                "timestamp": datetime.now().isoformat(),
                "price_df": pd.DataFrame(),
                "news_df": pd.DataFrame(),
                "sentiment_df": pd.DataFrame(),
                "sentiment_summary": {},
                "saved_files": [],
                "error": msg,
            }
    return results
