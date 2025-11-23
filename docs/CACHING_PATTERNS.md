# Caching Patterns

The Apex Analysis stack relies on layered caching to hide network latency and smooth out heavy analytical workloads. This document explains when and how to apply each cache so you can extend the system without reintroducing expensive recomputations.

## Goals
- **Lower latency** for API consumers and dashboards by reusing recently computed summaries.
- **Reduce upstream API calls** (yfinance, news feeds) to stay within vendor rate limits.
- **Stabilize workloads** so background jobs (training, backtests) don't stampede the same resources.

## Layers
1. **In-memory (process-local)**
   - Use `functools.lru_cache` on pure functions (e.g., indicator lookups) with very hot access patterns.
   - Ideal for derived metrics inside a single worker; automatically evicted on process restart.

2. **File-based cache (`cache/` + `cache_manager.py`)**
   - Development-friendly persistence using JSON/Parquet snapshots.
   - Enables offline demos when market data is unavailable.
   - Add a short TTL (minutes-hours) and include query parameters (ticker, period, indicators) in the cache key.

3. **Distributed (Redis/Memcached)**
   - Required when scaling the FastAPI/Flask layer horizontally.
   - Set `CACHE_URL` or `REDIS_URL` env vars and let `CacheManager` hydrate connections.
   - Use hash keys such as `analysis:{ticker}:{period}` for clarity and to support targeted invalidation.

## Patterns
### Write-Through API Cache
1. Attempt to read a serialized payload (JSON) from Redis/file cache.
2. On cache miss, execute the expensive call (`fetch_stock_data`, `aggregate_analysis`).
3. Serialize, store with TTL, and return.
4. Bubble cache metadata back to the caller (e.g., `X-Cache: HIT/MISS`).

### Batch Result Cache
- When running nightly backtests or ML training, store intermediate dataframes as Parquet in `cache/backtests/`.
- Subsequent analytics jobs can reuse the pre-processed features instead of recomputing from raw quotes.

### Guarding External APIs
- Wrap outbound requests with `CacheManager.memoize()` to prevent duplicate fetches within a time window.
- Example configuration:
  ```python
  with cache_manager.memoize(key=f"news:{ticker}", ttl=900) as cached:
      if cached.hit:
          return cached.value
      payload = fetch_news(ticker)
      cached.store(payload)
      return payload
  ```

## Invalidation Strategies
- **Time-based expiration**: default for market data (e.g., 5–15 minutes).
- **Event-based invalidation**: purge `analysis:*` entries after completing a trade/alert that changes state.
- **Manual busting**: expose `/api/v1/admin/cache/clear?prefix=analysis` for administrators.

## Instrumentation
- Emit cache metrics (hit ratio, evictions, memory usage) through the logging layer.
- In production, wire Redis INFO into Prometheus/Grafana dashboards for visibility.

Following these guidelines keeps the platform responsive while ensuring deterministic analytics for end users.
