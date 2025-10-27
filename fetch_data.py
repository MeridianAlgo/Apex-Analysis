import yfinance as yf
import pandas as pd
from utils import handle_errors, logger, load_cache, cache_data

@handle_errors
def fetch_stock_history(ticker: str, period: str = '1y') -> pd.DataFrame:
    cache_key = f"{ticker}_history_{period}"
    cached = load_cache(cache_key)
    if cached is not None:
        return cached
    logger.info(f"Fetching history for {ticker}")
    data = yf.Ticker(ticker).history(period=period)
    cache_data(cache_key, data)
    return data

@handle_errors
def fetch_stock_info(ticker: str) -> dict:
    cache_key = f"{ticker}_info"
    cached = load_cache(cache_key)
    if cached is not None:
        return cached
    logger.info(f"Fetching info for {ticker}")
    t = yf.Ticker(ticker)
    try:
        data = t.get_info()
    except Exception:
        data = t.info
    cache_data(cache_key, data)
    return data

@handle_errors
def fetch_financials(ticker: str) -> dict:
    cache_key = f"{ticker}_financials"
    cached = load_cache(cache_key)
    if cached is not None:
        return cached
    t = yf.Ticker(ticker)
    data = {
        'income_stmt': t.financials,
        'balance_sheet': t.balance_sheet,
        'cashflow': t.cashflow
    }
    cache_data(cache_key, data)
    return data


def fetch_stock_data(ticker: str, period: str = '1y') -> dict:
    return {
        'history': fetch_stock_history(ticker, period),
        'info': fetch_stock_info(ticker),
        'financials': fetch_financials(ticker)
    }
