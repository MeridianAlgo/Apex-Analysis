from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from src.config import DAYS_BACK_PRICE
from src.utils import handle_errors, logger, load_cache, cache_data, retry, cache_key
from src.technical_analysis import add_all_indicators

@handle_errors
def fetch_stock_history(ticker: str, period: str = '1y') -> pd.DataFrame:
    """Fetch stock history without caching."""
    logger.info(f"Fetching history for {ticker}")
    try:
        data = yf.Ticker(ticker).history(period=period)
        if data.empty:
            logger.warning(f"No data returned for {ticker}")
            return data
        
        # Add technical indicators
        data = add_all_indicators(data)
        return data
    except Exception as e:
        logger.error(f"Error fetching history for {ticker}: {e}")
        return pd.DataFrame()

@handle_errors
def fetch_stock_info(ticker: str) -> Dict[str, Any]:
    """Fetch stock info without caching."""
    logger.info(f"Fetching info for {ticker}")
    try:
        info = yf.Ticker(ticker).info
        if not info:
            logger.warning(f"No info returned for {ticker}")
        return info if info else {}
    except Exception as e:
        logger.error(f"Error fetching info for {ticker}: {e}")
        return {}

@handle_errors
def fetch_financials(ticker: str) -> Dict[str, pd.DataFrame]:
    """Fetch financial data without caching."""
    logger.info(f"Fetching financials for {ticker}")
    try:
        ticker_obj = yf.Ticker(ticker)
        financials = {
            'income': ticker_obj.financials,
            'balance': ticker_obj.balance_sheet,
            'cashflow': ticker_obj.cashflow
        }
        return {k: v for k, v in financials.items() if v is not None and not v.empty}
    except Exception as e:
        logger.error(f"Error fetching financials for {ticker}: {e}")
        return {}

def fetch_stock_data(ticker: str, period: str = '1y') -> dict:
    return {
        'history': fetch_stock_history(ticker, period),
        'info': fetch_stock_info(ticker),
        'financials': fetch_financials(ticker)
    }

@retry()
def fetch_price_history(ticker: str, days: Optional[int] = None) -> pd.DataFrame:
    days = days or DAYS_BACK_PRICE
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    key = cache_key(f"price:{ticker}:{start.date()}:{end.date()}")
    logger.info("Fetching price history %s", key)

    df = yf.download(
        ticker,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        progress=False,
    )

    if df is None or df.empty:
        raise ValueError(f"No price data for {ticker}")

    df = df.reset_index()
    df["Ticker"] = ticker.upper()
    return df
