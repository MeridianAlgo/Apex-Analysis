import logging
import time
import os
import shutil
from pathlib import Path
from functools import wraps
import pickle
import requests
from typing import Optional, Any, Dict, List

from src.config import REPORTS_DIR  # centralize reports dir in config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cache directory
CACHE_DIR = Path('.cache')

# Ensure directories exist
# REPORTS_DIR is created by src.config; ensure cache exists here
CACHE_DIR.mkdir(exist_ok=True, parents=True)

def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as ve:
            logger.error(f"Value error: {ve}", exc_info=True)
            return None
        except requests.exceptions.RequestException as re:
            logger.error(f"Network error: {re}", exc_info=True)
            time.sleep(5)  # Retry delay
            return None
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            return None
    return wrapper

def clean_text(text: str) -> str:
    """Clean and normalize text by removing extra whitespace."""
    return ' '.join(str(text).split()).strip()

def get_company_dir(ticker: str) -> Path:
    """Get or create a directory for a company's reports."""
    company_dir = Path(REPORTS_DIR) / ticker.upper()
    company_dir.mkdir(exist_ok=True, parents=True)
    return company_dir

def cleanup_company_reports(ticker: str) -> None:
    """Remove all existing report files for a company."""
    company_dir = get_company_dir(ticker)
    if company_dir.exists():
        for file in company_dir.glob('*.*'):
            try:
                if file.is_file():
                    file.unlink()
            except Exception as e:
                logger.error(f"Error deleting {file}: {e}")

def save_plot(fig, filename: str, ticker: str) -> Optional[Path]:
    """Save a matplotlib figure as PNG in the company's report directory."""
    try:
        if not filename.lower().endswith('.png'):
            filename += '.png'
            
        company_dir = get_company_dir(ticker)
        filepath = company_dir / filename
        
        # Ensure the directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the figure
        fig.savefig(filepath, bbox_inches='tight', dpi=300)
        logger.info(f"Saved plot to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error saving plot {filename}: {e}")
        return None

def save_dataframe(df, filename: str, ticker: str) -> Optional[Path]:
    """Save a pandas DataFrame as CSV in the company's report directory."""
    try:
        if not filename.lower().endswith('.csv'):
            filename += '.csv'
            
        company_dir = get_company_dir(ticker)
        filepath = company_dir / filename
        
        # Ensure the directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the DataFrame
        df.to_csv(filepath, index=False)
        logger.info(f"Saved data to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error saving DataFrame {filename}: {e}")
        return None

def cache_data(key: str, data: Any, expire_hours: int = 24) -> None:
    """
    Cache data - DISABLED
    This function is kept for API compatibility but doesn't cache anything.
    """
    # Completely disable caching
    return

def load_cache(key: str) -> Optional[Any]:
    """Load data from cache - DISABLED"""
    # Always return None to force fresh data
    return None

def clear_all_cache() -> None:
    """Clear all cached data - DISABLED"""
    # No-op since caching is disabled
    return

def get_latest_report(ticker: str) -> Optional[Dict[str, Path]]:
    """Get the paths to the latest report files for a ticker."""
    company_dir = get_company_dir(ticker)
    if not company_dir.exists():
        return None
        
    report_files = {}
    for ext in ['.csv', '.png', '.json']:
        files = list(company_dir.glob(f'*{ext}'))
        if files:
            # Get the most recently modified file of this type
            latest = max(files, key=lambda f: f.stat().st_mtime)
            report_files[ext[1:]] = latest
            
    return report_files if report_files else None