import yaml
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.yaml"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Missing config file: {CONFIG_FILE}. "
            f"Create it using src/config.yaml template."
        )
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


config = load_config()

REPORTS_DIR = Path(config.get("reports_dir", "./reports")).resolve()
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

PLOT_DPI = int(config.get("plot_dpi", 300))
PLOT_FIGSIZE = tuple(config.get("plot_figsize", [12, 8]))
PLOT_STYLE = config.get("plot_style", "ggplot")
SAVE_PLOTS = bool(config.get("save_plots", True))

RESPECT_ROBOTS = bool(config.get("respect_robots", True))
CACHE_TTL_DAYS = int(config.get("cache_ttl_days", 1))
ALLOW_PAYWALLED = bool(config.get("allow_paywalled", False))
REQUEST_TIMEOUT_SEC = int(config.get("request_timeout_sec", 10))
REQUEST_DELAY_SEC = float(config.get("request_delay_sec", 1.0))
USER_AGENT = config.get(
    "user_agent",
    "Mozilla/5.0 (compatible; ApexAnalysisBot/1.0; +https://example.com/bot)",
)

DAYS_BACK_PRICE = int(config.get("days_back_price", 30))
DAYS_BACK_NEWS = int(config.get("days_back_news", 7))
MIN_WORDS_FOR_ANALYSIS = int(config.get("min_words_for_analysis", 40))

NEWS_SOURCES = config.get("news_sources", [])
