import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

from src.fetch_data import fetch_stock_data
from src.news_processor import fetch_news_rss
from src.sentiment_analyzer import batch_analyze
from src.utils import logger

def get_company_dir(ticker: str) -> Path:
    """
    Get the directory path for storing reports for a given ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Path: Path object pointing to the company's report directory
    """
    return Path("reports") / ticker.upper()

def calculate_sentiment_metrics(analyzed_news: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate sentiment metrics from analyzed news articles.
    
    Args:
        analyzed_news: List of analyzed news articles with sentiment data
        
    Returns:
        Dict containing sentiment metrics
    """
    if not analyzed_news:
        return {}
        
    sentiment_scores = [
        n.get('sentiment', 0) 
        for n in analyzed_news 
        if 'sentiment' in n
    ]
    
    if not sentiment_scores:
        return {}
        
    # Extract unique keywords from all articles
    keywords = {
        kw 
        for article in analyzed_news 
        for kw in article.get('sentiment_keywords', [])
    }
    
    return {
        'average': float(np.mean(sentiment_scores)),
        'count': len(sentiment_scores),
        'strongly_positive': len([s for s in sentiment_scores if s >= 0.15]),
        'positive': len([s for s in sentiment_scores if 0.05 <= s < 0.15]),
        'neutral': len([s for s in sentiment_scores if -0.05 < s < 0.05]),
        'negative': len([s for s in sentiment_scores if -0.15 < s <= -0.05]),
        'strongly_negative': len([s for s in sentiment_scores if s <= -0.15]),
        'keywords': list(keywords)
    }

def save_report(data: Any, filepath: Path) -> Path:
    """
    Save data to a file with proper error handling and directory creation.
    
    Args:
        data: Data to be saved (will be JSON serialized)
        filepath: Path where to save the file
        
    Returns:
        Path: The actual path where the file was saved
        
    Raises:
        Exception: If there's an error saving the file
    """
    try:
        # Convert to Path object if it's a string
        filepath = Path(filepath)
        
        # Ensure the directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
            
        # Verify the file was created
        if not filepath.exists():
            raise FileNotFoundError(f"Failed to create file: {filepath}")
            
        logger.info(f"Successfully saved report to {filepath.absolute()}")
        return filepath.absolute()
        
    except Exception as e:
        error_msg = f"Error saving report to {filepath}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg)

def aggregate_analysis(ticker: str, period: str = '1y', num_articles: int = 20) -> Dict[str, Any]:
    """
    Aggregate all analysis for a given ticker and save results to reports directory.
    
    Args:
        ticker: Stock ticker symbol
        period: Time period for historical data (e.g., '1y', '6mo')
        num_articles: Number of news articles to analyze
        
    Returns:
        dict: Aggregated analysis results with 'saved_files' list and 'error' if any
    """
    logger.info(f"Starting analysis for {ticker}")
    
    # Initialize response with default values
    result = {
        'ticker': ticker.upper(),
        'timestamp': datetime.now().isoformat(),
        'price_data': None,
        'sentiment': {},
        'news': [],
        'saved_files': [],
        'error': None
    }
    
    ticker_dir = None
    try:
        # 0. Setup directories
        ticker_dir = get_company_dir(ticker.upper())
        ticker_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Fetch and save stock data
        logger.info(f"Fetching stock data for {ticker}...")
        try:
            stock_data = fetch_stock_data(ticker, period)
            if not stock_data or 'history' not in stock_data or stock_data['history'].empty:
                logger.warning(f"No price data available for {ticker}")
                result['error'] = f"No price data available for {ticker}"
            else:
                # Save price data
                price_file = ticker_dir / f"{ticker}_price_data_{timestamp}.csv"
                try:
                    # Ensure directory exists
                    price_file.parent.mkdir(parents=True, exist_ok=True)
                    # Save the file
                    stock_data['history'].to_csv(price_file, index=False)
                    # Verify it was created
                    if not price_file.exists():
                        raise FileNotFoundError(f"Failed to create price data file: {price_file}")
                    
                    saved_path = str(price_file.absolute())
                    result['saved_files'].append(saved_path)
                    result['price_data'] = stock_data['history'].to_dict(orient='records')
                    logger.info(f"Successfully saved price data to {saved_path}")
                except Exception as e:
                    error_msg = f"Failed to save price data: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    result['error'] = error_msg
        except Exception as e:
            error_msg = f"Error fetching stock data for {ticker}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result['error'] = error_msg
        
        # 2. Fetch and analyze news
        logger.info(f"Fetching news for {ticker}...")
        try:
            news = fetch_news_rss(ticker, num_articles)
            
            if not news:
                logger.warning(f"No news articles found for {ticker}")
            else:
                logger.info(f"Analyzing sentiment for {len(news)} articles...")
                analyzed_news = batch_analyze(news)
                
                if not analyzed_news:
                    logger.warning("No articles were successfully analyzed")
                else:
                    result['news'] = analyzed_news
                    result['sentiment'] = calculate_sentiment_metrics(analyzed_news)
                    
                    # Save news data
                    news_file = ticker_dir / f"{ticker}_news_{timestamp}.json"
                    try:
                        saved_path = save_report(analyzed_news, news_file)
                        result['saved_files'].append(str(saved_path))
                    except Exception as e:
                        error_msg = f"Failed to save news data: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        if not result.get('error'):
                            result['error'] = error_msg
        except Exception as e:
            error_msg = f"Error processing news for {ticker}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            if not result.get('error'):  # Only set if no previous error
                result['error'] = error_msg
        
        # 3. Always generate and save summary, even if some parts failed
        try:
            logger.info("Generating summary report...")
            summary = {
                'ticker': result['ticker'],
                'timestamp': result['timestamp'],
                'price_data_points': len(result.get('price_data', [])),
                'news_articles_analyzed': len(result.get('news', [])),
                'sentiment_summary': result.get('sentiment', {}),
                'saved_files': result.get('saved_files', []),
                'error': result.get('error')
            }
            
            summary_file = ticker_dir / f"{ticker}_summary_{timestamp}.json"
            try:
                saved_path = save_report(summary, summary_file)
                result['saved_files'].append(str(saved_path))
            except Exception as e:
                error_msg = f"Failed to save summary report: {str(e)}"
                logger.error(error_msg, exc_info=True)
                if not result.get('error'):
                    result['error'] = error_msg
            
            logger.info(f"Analysis complete. Generated {len(result['saved_files'])} report files for {ticker}")
            
        except Exception as e:
            error_msg = f"Error generating summary for {ticker}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result['error'] = error_msg
        
    except Exception as e:
        error_msg = f"Unexpected error in aggregate_analysis for {ticker}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        result['error'] = error_msg
    
    # Verify files were actually created
    verified_files = []
    for filepath in result.get('saved_files', []):
        if Path(filepath).exists():
            verified_files.append(filepath)
        else:
            logger.warning(f"Expected file not found: {filepath}")
    
    result['saved_files'] = verified_files
    
    if not verified_files and not result.get('error'):
        result['error'] = "No report files were generated. Check logs for details."
    
    return result
