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


def save_dataframe(
    df: pd.DataFrame,
    filename: str,
    ticker: Optional[str] = None,
    compress: bool = False,
    optimize: bool = True
) -> Path:
    """
    Save DataFrame with optional compression and optimization.

    Args:
        df: DataFrame to save
        filename: Output filename
        ticker: Optional ticker for organized storage
        compress: Whether to use compression (parquet or gzip)
        optimize: Whether to optimize data types before saving

    Returns:
        Path to saved file
    """
    if ticker:
        base_dir = get_company_dir(ticker)
    else:
        base_dir = REPORTS_DIR

    # Import here to avoid circular dependency
    if compress and optimize:
        try:
            from src.data_handler import save_dataframe_compressed
            path = base_dir / filename
            return save_dataframe_compressed(df, path, compression='gzip', optimize_dtypes=True)
        except ImportError:
            logger.warning("data_handler not available, using standard save")

    # Optimize dtypes if requested
    if optimize:
        try:
            from src.data_handler import optimize_dataframe_dtypes
            df = optimize_dataframe_dtypes(df)
        except ImportError:
            pass

    # Standard CSV save
    if not filename.lower().endswith(".csv"):
        filename += ".csv"

    path = base_dir / filename
    safe_mkdir(path.parent)

    if compress:
        path = path.with_suffix('.csv.gz')
        df.to_csv(path, index=False, compression='gzip')
    else:
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


def memoize_dataframe(func: Callable) -> Callable:
    """
    Decorator to cache DataFrame operations using a combination of
    hash-based caching for DataFrames and function arguments.
    """
    cache: Dict[str, Any] = {}

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create cache key from function name and arguments
        key_parts = [func.__name__]

        for arg in args:
            if isinstance(arg, pd.DataFrame):
                # For DataFrames, use shape and column names as part of key
                key_parts.append(f"df_{arg.shape}_{tuple(arg.columns)}")
            else:
                key_parts.append(str(arg))

        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")

        cache_key_str = "_".join(str(p) for p in key_parts)

        if cache_key_str in cache:
            return cache[cache_key_str]

        result = func(*args, **kwargs)
        cache[cache_key_str] = result

        # Limit cache size to prevent memory issues
        if len(cache) > 100:
            # Remove oldest entry (simple FIFO)
            cache.pop(next(iter(cache)))

        return result

    return wrapper
