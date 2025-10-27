import time
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse
from urllib import robotparser
from utils import handle_errors, logger, clean_text, load_cache, cache_data
from config import (
    RESPECT_ROBOTS, ALLOW_PAYWALLED, REQUEST_TIMEOUT_SEC,
    REQUEST_DELAY_SEC, USER_AGENT
)

def _robots_allows(url: str) -> bool:
    if not RESPECT_ROBOTS:
        return True
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        logger.info(f"Could not read robots.txt; disallowing: {robots_url}")
        return False

@handle_errors
def fetch_news_rss(ticker: str, num_articles: int = 20) -> list[dict]:
    cache_key = f"{ticker}_news_rss"
    cached = load_cache(cache_key)
    if cached is not None:
        return cached
    url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
    logger.info(f"Fetching RSS for {ticker}: {url}")
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:num_articles]:
        raw_date = getattr(entry, 'published', '') or getattr(entry, 'updated', '')
        try:
            date = datetime.strptime(raw_date, '%a, %d %b %Y %H:%M:%S %Z') if raw_date else datetime.utcnow()
        except ValueError:
            date = datetime.utcnow()
        articles.append({'title': entry.title, 'link': entry.link, 'date': date})
    cache_data(cache_key, articles)
    return articles

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
