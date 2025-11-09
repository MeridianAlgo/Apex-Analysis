import json
import logging
import pickle
import re
import time
from datetime import date, datetime
from dataclasses import dataclass
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import matplotlib.pyplot as plt
import pandas as pd

from src.config import REPORTS_DIR, PLOT_DPI, PLOT_FIGSIZE, SAVE_PLOTS, CACHE_TTL_DAYS


LOG_FILE = REPORTS_DIR / "apex.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("apex")
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_CACHE_TTL_SEC = CACHE_TTL_DAYS * 24 * 60 * 60


def handle_errors(
    func: Optional[Callable] = None,
    *,
    default: Optional[Any] = None,
    reraise: bool = False,
) -> Callable:
    """
    Decorator that logs and optionally swallows exceptions.
    Usage: @handle_errors or @handle_errors(default=my_default)
    """

    def decorator(inner: Callable) -> Callable:
        @wraps(inner)
        def wrapper(*args, **kwargs):
            try:
                return inner(*args, **kwargs)
            except Exception as exc:
                logger.error("Error in %s: %s", inner.__name__, exc, exc_info=True)
                if reraise:
                    raise
                return default() if callable(default) else default

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


def safe_mkdir(path: Path) -> Path:
    """Create directory (and parents) if needed, return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_company_dir(ticker: str) -> Path:
    """Per-ticker reports directory under REPORTS_DIR."""
    ticker = str(ticker).upper()
    company_dir = REPORTS_DIR / ticker
    safe_mkdir(company_dir)
    return company_dir


def cleanup_company_reports(ticker: str) -> None:
    """Delete existing report files for a ticker (non-fatal on error)."""
    company_dir = get_company_dir(ticker)
    for f in company_dir.glob("*"):
        try:
            if f.is_file():
                f.unlink()
        except Exception as e:
            logger.error("Error deleting %s: %s", f, e)


def get_latest_report(ticker: str) -> Optional[Dict[str, Path]]:
    """
    Return latest files for a ticker, grouped by extension.
    Example: {"csv": Path(...), "png": Path(...), "json": Path(...)}
    """
    company_dir = get_company_dir(ticker)
    if not company_dir.exists():
        return None

    report_files: Dict[str, Path] = {}

    for ext in (".csv", ".png", ".json"):
        files = list(company_dir.glob(f"*{ext}"))
        if not files:
            continue
        latest = max(files, key=lambda f: f.stat().st_mtime)
        report_files[ext.lstrip(".")] = latest

    return report_files or None


def save_json(path: Path, data: Any) -> Path:
    safe_mkdir(path.parent)

    def _default(o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, pd.Timestamp):
            return o.isoformat()
        return str(o)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=_default)

    logger.info("Saved JSON: %s", path)
    return path


def save_dataframe(df: pd.DataFrame, filename: str, ticker: Optional[str] = None) -> Path:
    """
    Save DataFrame as CSV.
    If ticker is provided, file goes under that ticker's report dir.
    """
    if not filename.lower().endswith(".csv"):
        filename += ".csv"

    if ticker:
        base_dir = get_company_dir(ticker)
    else:
        base_dir = REPORTS_DIR

    path = base_dir / filename
    safe_mkdir(path.parent)
    df.to_csv(path, index=False)
    logger.info("Saved CSV: %s (rows=%s)", path, len(df))
    return path


def save_plot(
    filename: str,
    ticker: Optional[str] = None,
    fig: Optional[plt.Figure] = None,
) -> Path:
    """
    Save current or given matplotlib figure as PNG.
    If ticker is provided, file goes under that ticker's report dir.
    """
    if not SAVE_PLOTS:
        # still return the intended path for consistency
        if not filename.lower().endswith(".png"):
            filename += ".png"
        base_dir = get_company_dir(ticker) if ticker else REPORTS_DIR
        path = base_dir / filename
        logger.info("Skipping plot save (SAVE_PLOTS=false): %s", path)
        return path

    if not filename.lower().endswith(".png"):
        filename += ".png"

    if ticker:
        base_dir = get_company_dir(ticker)
    else:
        base_dir = REPORTS_DIR

    path = base_dir / filename
    safe_mkdir(path.parent)

    if fig is None:
        fig = plt.gcf()

    fig.set_size_inches(*PLOT_FIGSIZE)
    fig.savefig(path, dpi=PLOT_DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved plot: %s", path)
    return path


def _cache_path(key: str) -> Path:
    safe_key = re.sub(r"[^A-Za-z0-9_.-]+", "_", key)
    return CACHE_DIR / f"{safe_key}.pkl"


def cache_data(key: str, data: Any, *, expire_hours: Optional[float] = None) -> Path:
    """Persist arbitrary Python data to disk cache."""
    payload = {
        "timestamp": time.time(),
        "ttl": expire_hours * 3600 if expire_hours else None,
        "data": data,
    }
    path = _cache_path(key)
    with path.open("wb") as fh:
        pickle.dump(payload, fh)
    logger.debug("Cached data %s -> %s", key, path)
    return path


def load_cache(key: str, *, max_age_hours: Optional[float] = None) -> Optional[Any]:
    """Retrieve cached payload if it exists and is still fresh."""
    path = _cache_path(key)
    if not path.exists():
        return None

    try:
        with path.open("rb") as fh:
            payload = pickle.load(fh)
    except Exception as exc:
        logger.warning("Failed to read cache %s: %s", path, exc)
        path.unlink(missing_ok=True)
        return None

    timestamp = payload.get("timestamp", 0)
    ttl_override = payload.get("ttl")
    ttl_sec = (
        max_age_hours * 3600
        if max_age_hours is not None
        else ttl_override
        if ttl_override is not None
        else DEFAULT_CACHE_TTL_SEC
    )

    if ttl_sec is not None and time.time() - timestamp > ttl_sec:
        logger.debug("Cache expired %s", path)
        path.unlink(missing_ok=True)
        return None

    return payload.get("data")


def clean_text(text: str) -> str:
    """Normalize whitespace and strip article text."""
    if not text:
        return ""
    collapsed = re.sub(r"\s+", " ", text)
    return collapsed.strip()


@dataclass
class RetryConfig:
    attempts: int = 3
    backoff_sec: float = 1.0


def retry(config: RetryConfig = RetryConfig()) -> Callable:
    """
    Decorator for simple retry logic.
    Use for network / API calls (not for programmer errors).
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for i in range(config.attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:  # Keep broad here; callers decide usage.
                    last_exc = e
                    logger.warning(
                        "Retry %s/%s failed for %s: %s",
                        i + 1,
                        config.attempts,
                        func.__name__,
                        e,
                    )
                    time.sleep(config.backoff_sec * (i + 1))
            logger.error("All retries failed for %s", func.__name__, exc_info=last_exc)
            raise last_exc

        return wrapper

    return decorator


@lru_cache(maxsize=256)
def cache_key(key: str) -> str:
    """
    Simple cache key wrapper so we can use @lru_cache in fetchers.
    This doesn't store payloads on disk; it just normalizes keys.
    """
    return key
