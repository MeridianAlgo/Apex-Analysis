import time
import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib import robotparser
import time
from datetime import datetime
from typing import List, Dict, Optional

from src.utils import (
    handle_errors, 
    logger, 
    clean_text, 
    load_cache, 
    cache_data
)
from src.config import (
    RESPECT_ROBOTS,
    ALLOW_PAYWALLED,
    REQUEST_TIMEOUT_SEC,
    REQUEST_DELAY_SEC,
    USER_AGENT
)

def _robots_allows(url: str) -> bool:
    """Check if robots.txt allows scraping the given URL."""
    if not RESPECT_ROBOTS:
        return True
        
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        logger.warning(f"Invalid URL format: {url}")
        return False
        
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    
    try:
        # Set a timeout for the robots.txt request
        rp.set_url(robots_url)
        rp.read()
        can_fetch = rp.can_fetch(USER_AGENT, url)
        
        if not can_fetch:
            logger.info(f"Robots.txt disallows: {url}")
            
        return can_fetch
        
    except Exception as e:
        logger.warning(f"Error checking robots.txt for {robots_url}: {str(e)}")
        # Be more conservative - if we can't check robots.txt, don't scrape
        return False

@handle_errors
def fetch_news_rss(ticker: str, num_articles: int = 20) -> list[dict]:
    """Fetch news articles for a given stock ticker from RSS feeds."""
    if not ticker or not isinstance(ticker, str):
        logger.error(f"Invalid ticker: {ticker}")
        return []
        
    ticker = ticker.strip().upper()
    cache_key = f"{ticker}_news_rss"
    
    try:
        cached = load_cache(cache_key)
        if cached is not None:
            return cached
            
        url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
        logger.info(f"Fetching RSS for {ticker}: {url}")
        
        # Set up the feedparser with custom request handling
        import socket
        import urllib.request
        
        # Create a custom request with timeout
        req = urllib.request.Request(
            url,
            headers={'User-Agent': USER_AGENT}
        )
        
        try:
            # Open URL with timeout
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as response:
                content = response.read()
                feed = feedparser.parse(content)
        except (urllib.error.URLError, socket.timeout) as e:
            logger.warning(f"Error fetching RSS feed: {e}")
            return []
        
        if feed.bozo and feed.bozo_exception:
            logger.warning(f"Error parsing RSS feed: {feed.bozo_exception}")
            return []
            
        articles = []
        for entry in feed.entries[:num_articles]:
            try:
                if not hasattr(entry, 'link') or not entry.link:
                    continue
                    
                raw_date = getattr(entry, 'published', '') or getattr(entry, 'updated', '')
                try:
                    date = datetime.strptime(raw_date, '%a, %d %b %Y %H:%M:%S %Z') if raw_date else datetime.utcnow()
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing date '{raw_date}': {e}")
                    date = datetime.utcnow()
                    
                articles.append({
                    'title': getattr(entry, 'title', 'No title'),
                    'link': entry.link,
                    'date': date,
                    'source': getattr(entry, 'source', {}).get('title', 'Unknown')
                })
                
            except Exception as e:
                logger.error(f"Error processing RSS entry: {e}", exc_info=True)
                continue
                
        if articles:
            cache_data(cache_key, articles, expire_hours=1)  # Cache for 1 hour
            
        return articles
        
    except Exception as e:
        logger.error(f"Error in fetch_news_rss for {ticker}: {e}", exc_info=True)
        return []

def _looks_paywalled(html: str) -> bool:
    low = html.lower()
    for k in ["subscribe", "paywall", "metered", "membership", "register to read"]:
        if k in low:
            return True
    return False

@handle_errors
def scrape_article_content(link: str) -> str:
    cache_key = f"article_{hash(link)}"
    cached = load_cache(cache_key)
    if cached is not None:
        return cached

    if not _robots_allows(link):
        logger.info(f"Skipping (robots.txt disallow): {link}")
        return ""

    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(link, headers=headers, timeout=REQUEST_TIMEOUT_SEC)
    time.sleep(REQUEST_DELAY_SEC)

    if resp.status_code != 200:
        logger.info(f"Skipping non-200 ({resp.status_code}): {link}")
        return ""

    if not ALLOW_PAYWALLED and _looks_paywalled(resp.text):
        logger.info(f"Skipping likely paywalled article: {link}")
        return ""

    soup = BeautifulSoup(resp.text, 'html.parser')
    body = soup.find('article') or soup.find('div', class_='article-body') or soup.find('body')
    if not body:
        return ""
    for tag in body(["script", "style", "noscript"]):
        tag.decompose()
    text = body.get_text(separator=" ")
    cleaned = clean_text(text)
    cache_data(cache_key, cleaned)
    return cleaned
