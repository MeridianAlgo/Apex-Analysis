import os
from pathlib import Path
from datetime import datetime

# File paths
BASE_DIR = Path(__file__).parent.absolute()
# Put cache and reports at the repository root (one level above src)
REPO_ROOT = BASE_DIR.parent
CACHE_DIR = REPO_ROOT / 'cache'
REPORTS_DIR = REPO_ROOT / 'reports'

# Ensure directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# News API settings
NEWS_SOURCES = [
    'https://finance.yahoo.com/news/rss',
    'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',
    'https://www.investing.com/rss/news.rss'
]

RESPECT_ROBOTS = True
ALLOW_PAYWALLED = False
REQUEST_TIMEOUT_SEC = 15
REQUEST_DELAY_SEC = 1
USER_AGENT = 'ApexAnalysis/1.0 (Educational Use Only)'

# Sentiment analysis
SENTIMENT_THRESHOLD = 0.1
MIN_WORDS_FOR_ANALYSIS = 10  # Minimum words for meaningful sentiment analysis

# Data settings
CACHE_EXPIRY_DAYS = 1

# Plot settings
PLOT_STYLE = 'seaborn'
PLOT_FIGSIZE = (14, 8)
PLOT_DPI = 300

SAVE_PLOTS = True