"""
Parallel Aggregator

Optimized version of aggregator.py with:
- Parallel ticker processing
- Smart caching
- Progress tracking
"""
from datetime import datetime
from typing import Any, Dict, List, Union

from src.aggregator import (
    _analyze_single_ticker,
    _normalize_tickers,
)
from src.parallel_processor import parallel_map, ThreadingPool
from src.cache_manager import get_cache, cache_result
from src.utils import logger


def aggregate_analysis_parallel(
    tickers: Union[str, List[str]],
    period: str = "1y",
    num_articles: int = 20,
    use_cache: bool = True,
    max_workers: int = 4
) -> Dict[str, Any]:
    """
    Parallel version of aggregate_analysis

    Processes multiple tickers concurrently with caching

    Args:
        tickers: Ticker symbol(s)
        period: Time period for stock data
        num_articles: Number of news articles
        use_cache: Use caching for API responses
        max_workers: Number of parallel workers

    Returns:
        Dict of ticker results
    """
    symbols = _normalize_tickers(tickers)

    if len(symbols) == 0:
        return {}

    logger.info(f"Analyzing {len(symbols)} tickers in parallel with {max_workers} workers")

    cache = get_cache()

    def process_ticker(ticker: str) -> tuple[str, Dict[str, Any]]:
        """Process single ticker with caching"""
        cache_key = f"{ticker}:{period}:{num_articles}"

        # Try cache first
        if use_cache:
            cached_result = cache.get(cache_key, prefix="ticker_analysis")
            if cached_result is not None:
                logger.info(f"Cache hit for {ticker}")
                return ticker, cached_result

        # Analyze ticker
        logger.info(f"Analyzing {ticker}...")
        result = _analyze_single_ticker(ticker, period=period, num_articles=num_articles)

        # Cache result (1 hour TTL)
        if use_cache:
            cache.set(cache_key, result, ttl=3600, prefix="ticker_analysis")

        return ticker, result

    # Process tickers in parallel
    pool = ThreadingPool(max_workers=max_workers)
    job_results = pool.map(process_ticker, symbols, show_progress=True)

    # Build results dict
    results = {}
    for job_result in job_results:
        if job_result.success:
            ticker, data = job_result.result
            results[ticker] = data
        else:
            logger.error(f"Failed to analyze ticker: {job_result.error}")

    logger.info(f"Completed analysis of {len(results)}/{len(symbols)} tickers")

    return results


def batch_analyze_tickers(
    tickers: List[str],
    period: str = "1y",
    num_articles: int = 20,
    batch_size: int = 5
) -> Dict[str, Any]:
    """
    Batch process tickers to avoid API rate limits

    Args:
        tickers: List of ticker symbols
        period: Time period
        num_articles: Articles per ticker
        batch_size: Tickers per batch

    Returns:
        Dict of ticker results
    """
    all_results = {}

    # Process in batches
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        logger.info(f"Processing batch {i // batch_size + 1}: {batch}")

        batch_results = aggregate_analysis_parallel(
            batch,
            period=period,
            num_articles=num_articles,
            max_workers=min(batch_size, 4)
        )

        all_results.update(batch_results)

    return all_results


def clear_ticker_cache(ticker: Optional[str] = None):
    """
    Clear cached ticker analysis

    Args:
        ticker: Specific ticker to clear (None = all)
    """
    cache = get_cache()

    if ticker:
        count = cache.clear(prefix=f"ticker_analysis:{ticker}")
        logger.info(f"Cleared cache for {ticker}: {count} entries")
    else:
        count = cache.clear(prefix="ticker_analysis")
        logger.info(f"Cleared all ticker cache: {count} entries")

    return count
