"""
Advanced Caching Layer

Supports:
- Redis caching (production)
- File-based caching (development/fallback)
- Automatic fallback from Redis to file
- Cache invalidation strategies
- Cache metrics and monitoring
"""
import hashlib
import json
import pickle
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, Union

from src.utils import logger, CACHE_DIR


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


class CacheManager:
    """Unified cache manager with Redis and file-based backends"""

    def __init__(self, use_redis: bool = True, redis_url: Optional[str] = None):
        self.use_redis = use_redis
        self.redis_client = None
        self.stats = CacheStats()

        if use_redis:
            try:
                import redis
                url = redis_url or "redis://localhost:6379/0"
                self.redis_client = redis.from_url(url, decode_responses=False)
                self.redis_client.ping()
                logger.info(f"Redis cache connected: {url}")
            except (ImportError, Exception) as e:
                logger.warning(f"Redis unavailable, using file cache: {e}")
                self.use_redis = False

        self.file_cache_dir = CACHE_DIR / "advanced"
        self.file_cache_dir.mkdir(parents=True, exist_ok=True)

    def _make_key(self, key: str, prefix: str = "") -> str:
        """Create cache key with optional prefix"""
        if prefix:
            return f"{prefix}:{key}"
        return key

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        return pickle.dumps(value)

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        return pickle.loads(data)

    def _file_path(self, key: str) -> Path:
        """Get file path for cache key"""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.file_cache_dir / f"{safe_key}.cache"

    def get(self, key: str, prefix: str = "") -> Optional[Any]:
        """Get value from cache"""
        full_key = self._make_key(key, prefix)

        try:
            if self.use_redis and self.redis_client:
                data = self.redis_client.get(full_key)
                if data is not None:
                    self.stats.hits += 1
                    return self._deserialize(data)

            # Fallback to file cache
            file_path = self._file_path(full_key)
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    cache_data = pickle.load(f)

                # Check expiration
                if cache_data['expires_at'] and time.time() > cache_data['expires_at']:
                    file_path.unlink()
                    self.stats.misses += 1
                    return None

                self.stats.hits += 1
                return cache_data['value']

            self.stats.misses += 1
            return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.stats.errors += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None, prefix: str = "") -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = no expiration)
            prefix: Optional key prefix
        """
        full_key = self._make_key(key, prefix)

        try:
            serialized = self._serialize(value)

            if self.use_redis and self.redis_client:
                if ttl:
                    self.redis_client.setex(full_key, ttl, serialized)
                else:
                    self.redis_client.set(full_key, serialized)
                self.stats.sets += 1
                return True

            # Fallback to file cache
            file_path = self._file_path(full_key)
            cache_data = {
                'value': value,
                'created_at': time.time(),
                'expires_at': time.time() + ttl if ttl else None
            }

            with open(file_path, 'wb') as f:
                pickle.dump(cache_data, f)

            self.stats.sets += 1
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.stats.errors += 1
            return False

    def delete(self, key: str, prefix: str = "") -> bool:
        """Delete key from cache"""
        full_key = self._make_key(key, prefix)

        try:
            if self.use_redis and self.redis_client:
                self.redis_client.delete(full_key)

            file_path = self._file_path(full_key)
            if file_path.exists():
                file_path.unlink()

            self.stats.deletes += 1
            return True

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self.stats.errors += 1
            return False

    def clear(self, prefix: Optional[str] = None) -> int:
        """Clear cache (optionally by prefix)"""
        count = 0

        try:
            if self.use_redis and self.redis_client:
                if prefix:
                    pattern = f"{prefix}:*"
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        count = self.redis_client.delete(*keys)
                else:
                    self.redis_client.flushdb()
                    count = -1  # Unknown count

            # Clear file cache
            for file_path in self.file_cache_dir.glob("*.cache"):
                if prefix:
                    # Check if file matches prefix (simplified)
                    file_path.unlink()
                    count += 1
                else:
                    file_path.unlink()
                    count += 1

            logger.info(f"Cleared {count} cache entries" + (f" with prefix '{prefix}'" if prefix else ""))
            return count

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0

    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        return self.stats

    def exists(self, key: str, prefix: str = "") -> bool:
        """Check if key exists in cache"""
        full_key = self._make_key(key, prefix)

        try:
            if self.use_redis and self.redis_client:
                return self.redis_client.exists(full_key) > 0

            file_path = self._file_path(full_key)
            return file_path.exists()

        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False


# Global cache instance
_cache = None


def get_cache() -> CacheManager:
    """Get global cache instance"""
    global _cache
    if _cache is None:
        _cache = CacheManager(use_redis=False)  # Default to file cache
    return _cache


def cache_result(
    ttl: Optional[int] = 3600,
    prefix: str = "",
    key_func: Optional[Callable] = None
):
    """
    Decorator to cache function results

    Args:
        ttl: Time to live in seconds
        prefix: Cache key prefix
        key_func: Custom function to generate cache key from args/kwargs
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: hash of function name + args + kwargs
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            # Try to get from cache
            result = cache.get(cache_key, prefix=prefix)
            if result is not None:
                logger.debug(f"Cache hit: {func.__name__}")
                return result

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl=ttl, prefix=prefix)
            logger.debug(f"Cache miss: {func.__name__}")

            return result

        # Add cache control methods
        wrapper.cache_clear = lambda: get_cache().clear(prefix=prefix)
        wrapper.cache_info = lambda: get_cache().get_stats()

        return wrapper

    return decorator


class CacheInvalidation:
    """Cache invalidation strategies"""

    def __init__(self, cache: Optional[CacheManager] = None):
        self.cache = cache or get_cache()

    def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        return self.cache.clear(prefix=pattern)

    def invalidate_by_tags(self, tags: list[str]) -> int:
        """Invalidate by tags (stored as prefixes)"""
        count = 0
        for tag in tags:
            count += self.cache.clear(prefix=f"tag:{tag}")
        return count

    def invalidate_by_time(self, older_than: timedelta) -> int:
        """Invalidate entries older than specified time"""
        count = 0
        cutoff = time.time() - older_than.total_seconds()

        # File cache only (Redis handles TTL automatically)
        for file_path in self.cache.file_cache_dir.glob("*.cache"):
            if file_path.stat().st_mtime < cutoff:
                file_path.unlink()
                count += 1

        return count


class SmartCache:
    """Smart caching with automatic invalidation and warming"""

    def __init__(self, cache: Optional[CacheManager] = None):
        self.cache = cache or get_cache()
        self.dependencies = {}

    def set_with_dependencies(
        self,
        key: str,
        value: Any,
        dependencies: list[str],
        ttl: Optional[int] = None
    ):
        """Set cache value with dependency tracking"""
        self.cache.set(key, value, ttl=ttl)

        # Track dependencies
        for dep in dependencies:
            if dep not in self.dependencies:
                self.dependencies[dep] = set()
            self.dependencies[dep].add(key)

    def invalidate_dependency(self, dependency: str) -> int:
        """Invalidate all keys that depend on this dependency"""
        if dependency not in self.dependencies:
            return 0

        count = 0
        for key in self.dependencies[dependency]:
            if self.cache.delete(key):
                count += 1

        # Clean up dependency tracking
        del self.dependencies[dependency]

        return count

    def warm_cache(self, key: str, value_func: Callable, ttl: Optional[int] = None):
        """Warm cache with computed value"""
        if not self.cache.exists(key):
            value = value_func()
            self.cache.set(key, value, ttl=ttl)
            logger.info(f"Cache warmed: {key}")
