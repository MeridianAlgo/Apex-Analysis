import pandas as pd
import numpy as np
from fetch_data import fetch_stock_data
from news_processor import fetch_news_rss
from sentiment_analyzer import batch_analyze
from utils import logger

def aggregate_analysis(ticker: str, period: str = '1y') -> dict:
    logger.info(f"Aggregating for {ticker}")
    stock_data = fetch_stock_data(ticker, period)
    history = stock_data.get('history')

    volatility = 0.0
    df = None
    if history is not None and not history.empty:
        df = history.copy()
        df['return'] = df['Close'].pct_change()
        df['MA50'] = df['Close'].rolling(window=50, min_periods=1).mean()
        volatility = float(np.std(df['return'].dropna()))
        stock_data['volatility'] = volatility
    else:
        stock_data['volatility'] = 0.0

    news = fetch_news_rss(ticker)
    analyzed_news = batch_analyze(news)
    sentiments = [a.get('sentiment', 0.0) for a in analyzed_news]
    avg_sentiment = float(np.mean(sentiments)) if sentiments else 0.0

    if df is not None and not df.empty and analyzed_news:
        news_df = pd.DataFrame(analyzed_news)
        news_df['date_only'] = pd.to_datetime(news_df['date']).dt.date
        price = df.copy()
        price['date_only'] = pd.to_datetime(price.index).date
        day_sent = news_df.groupby('date_only', as_index=False)['sentiment'].mean()
        merged = pd.merge(price[['date_only', 'return']], day_sent, on='date_only', how='inner').dropna()
        correlation = float(merged['return'].corr(merged['sentiment'])) if not merged.empty else 0.0
    else:
        correlation = 0.0

    report_df = pd.DataFrame({
        'Metric': ['Avg Sentiment', 'Volatility', 'Correlation'],
        'Value': [avg_sentiment, volatility, correlation]
    })

    return {
        'stock_data': stock_data,
        'news': analyzed_news,
        'avg_sentiment': avg_sentiment,
        'correlation': correlation,
        'volatility': volatility,
        'report_df': report_df
    }
