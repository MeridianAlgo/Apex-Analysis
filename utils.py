import logging
import time
from functools import wraps
import pickle
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as ve:
            logger.error(f"Value error: {ve}")
            return None
        except requests.exceptions.RequestException as re:
            logger.error(f"Network error: {re}")
            time.sleep(5)  # Retry delay
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    return wrapper

def clean_text(text: str) -> str:
    return ' '.join(text.split()).strip()

def cache_data(key: str, data):
    with open(f"{key}.pkl", 'wb') as f:
        pickle.dump(data, f)

def load_cache(key: str):
    try:
        with open(f"{key}.pkl", 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None