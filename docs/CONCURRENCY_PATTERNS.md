# Concurrency Patterns

This guide summarizes how Apex Analysis parallelizes workloads safely across CPU- and I/O-bound tasks.

## Building Blocks
- **ThreadPoolExecutor** (`src/parallel_processor.py`): hides I/O latency when fetching multiple tickers/news feeds.
- **ProcessPoolExecutor / multiprocessing**: used for CPU-heavy indicator calculations, Monte Carlo sims, and ML inference.
- **Async job queues** (RQ/Celery optional): decouple real-time API requests from long-running training/backtests.

## Recommended Patterns
### 1. Fan-out/Fan-in for Aggregations
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def aggregate_portfolio(tickers):
    with ThreadPoolExecutor(max_workers=min(8, len(tickers))) as pool:
        futures = {pool.submit(fetch_stock_data, t): t for t in tickers}
        return {ticker: fut.result() for fut, ticker in futures.items()}
```
- Keeps UI/API responsive while gathering data from multiple vendors.

### 2. Pipeline Parallelism
1. **Fetch layer** (threads) pulls raw quotes/news.
2. **Compute layer** (processes) enriches with indicators / ML features.
3. **Persistence layer** (async queue) stores artifacts or pushes alerts.
Use queues (`multiprocessing.Queue` or `asyncio.Queue`) between stages to decouple throughput.

### 3. Background Workers for Heavy Jobs
- Schedule backtests, hyper-parameter sweeps, or anomaly scans via Celery workers or `multiprocessing.Process` wrappers.
- Emit progress through Redis pub/sub or simple log polling so the UI can display status.

## Best Practices
- **Immutable payloads**: pass pandas objects via Parquet/temp files when crossing process boundaries to avoid pickling overhead.
- **CPU affinity**: cap `max_workers` to `os.cpu_count()` for processes; for threads, lean on I/O wait time to decide.
- **Graceful shutdown**: wrap workers with `try/finally` to close sessions, avoid zombie processes, and drain queues.
- **Observability**: tag logs with `job_id`/`worker_id` so you can trace work across pools.

Proper concurrency keeps the analytics responsive without overloading APIs or the database.
