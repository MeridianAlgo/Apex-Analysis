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
SAVE_PLOTS = bool(config.get("save_plots", True))

RESPECT_ROBOTS = bool(config.get("respect_robots", True))
CACHE_TTL_DAYS = int(config.get("cache_ttl_days", 1))

DAYS_BACK_PRICE = int(config.get("days_back_price", 30))
DAYS_BACK_NEWS = int(config.get("days_back_news", 7))

NEWS_SOURCES = config.get("news_sources", [])
