"""
Demo: Caching and Parallel Processing

Demonstrates:
- Cache hit/miss patterns
- Parallel vs sequential performance
- Job queues
- Progress tracking
"""
import time
import numpy as np
from src.cache_manager import CacheManager, cache_result, get_cache
from src.parallel_processor import (
    parallel_map,
    MultiprocessingPool,
    ThreadingPool,
    JobQueue
)


def demo_basic_caching():
    """Basic caching demonstration"""
    print("\n" + "="*70)
    print("DEMO: Basic Caching")
    print("="*70)

    cache = CacheManager(use_redis=False)

    # Set values
    cache.set("user:1", {"name": "Alice", "age": 30}, ttl=60)
    cache.set("user:2", {"name": "Bob", "age": 25}, ttl=60)

    # Get values
    user1 = cache.get("user:1")
    user2 = cache.get("user:2")
    user3 = cache.get("user:3")  # Miss

    print(f"\nCache operations:")
    print(f"  user:1 = {user1}")
    print(f"  user:2 = {user2}")
    print(f"  user:3 = {user3} (miss)")

    stats = cache.get_stats()
    print(f"\nCache stats:")
    print(f"  Hits: {stats.hits}")
    print(f"  Misses: {stats.misses}")
    print(f"  Hit rate: {stats.hit_rate:.1f}%")


def demo_decorator_caching():
    """Function caching with decorator"""
    print("\n" + "="*70)
    print("DEMO: Decorator-based Caching")
    print("="*70)

    call_count = 0

    @cache_result(ttl=60, prefix="expensive_func")
    def expensive_computation(n):
        nonlocal call_count
        call_count += 1
        time.sleep(0.1)  # Simulate expensive work
        return n ** 2

    # First calls (cache miss)
    print("\nFirst calls (cache miss):")
    start = time.time()
    results = [expensive_computation(i) for i in range(5)]
    miss_time = time.time() - start
    print(f"  Results: {results}")
    print(f"  Time: {miss_time:.3f}s")
    print(f"  Function called: {call_count} times")

    # Second calls (cache hit)
    print("\nSecond calls (cache hit):")
    call_count = 0
    start = time.time()
    results = [expensive_computation(i) for i in range(5)]
    hit_time = time.time() - start
    print(f"  Results: {results}")
    print(f"  Time: {hit_time:.3f}s")
    print(f"  Function called: {call_count} times")

    print(f"\nSpeedup: {miss_time/hit_time:.1f}x faster with cache")


def cpu_bound_task(n):
    """Simulate CPU-intensive work"""
    result = 0
    for i in range(n):
        result += i ** 2
    return result


def io_bound_task(delay):
    """Simulate I/O operation"""
    time.sleep(delay)
    return delay * 2


def demo_multiprocessing():
    """Multiprocessing for CPU-bound tasks"""
    print("\n" + "="*70)
    print("DEMO: Multiprocessing (CPU-bound)")
    print("="*70)

    tasks = [1000000] * 8

    # Sequential
    print("\nSequential processing:")
    start = time.time()
    results = [cpu_bound_task(n) for n in tasks]
    seq_time = time.time() - start
    print(f"  Time: {seq_time:.3f}s")

    # Parallel
    print("\nParallel processing:")
    start = time.time()
    results = parallel_map(cpu_bound_task, tasks, mode='cpu', show_progress=True)
    par_time = time.time() - start
    print(f"  Time: {par_time:.3f}s")

    print(f"\nSpeedup: {seq_time/par_time:.2f}x with multiprocessing")


def demo_threading():
    """Threading for I/O-bound tasks"""
    print("\n" + "="*70)
    print("DEMO: Threading (I/O-bound)")
    print("="*70)

    tasks = [0.1] * 20

    # Sequential
    print("\nSequential processing:")
    start = time.time()
    results = [io_bound_task(delay) for delay in tasks]
    seq_time = time.time() - start
    print(f"  Time: {seq_time:.3f}s")

    # Parallel
    print("\nParallel processing:")
    start = time.time()
    results = parallel_map(io_bound_task, tasks, mode='io', show_progress=True)
    par_time = time.time() - start
    print(f"  Time: {par_time:.3f}s")

    print(f"\nSpeedup: {seq_time/par_time:.2f}x with threading")


def demo_job_queue():
    """Background job queue"""
    print("\n" + "="*70)
    print("DEMO: Background Job Queue")
    print("="*70)

    queue = JobQueue(num_workers=4)
    queue.start()

    # Submit jobs
    print("\nSubmitting jobs...")
    job_ids = []
    for i in range(10):
        job_id = queue.submit(cpu_bound_task, 100000)
        job_ids.append(job_id)

    print(f"Submitted {len(job_ids)} jobs")
    print(f"Queue size: {queue.get_queue_size()}")

    # Wait for results
    print("\nWaiting for results...")
    results = []
    for job_id in job_ids:
        result = queue.get_result(job_id, timeout=10)
        if result and result.success:
            results.append(result)

    queue.stop()

    print(f"\nCompleted: {len(results)}/{len(job_ids)} jobs")
    if results:
        avg_time = sum(r.execution_time for r in results) / len(results)
        print(f"Average execution time: {avg_time:.3f}s")
    else:
        print("No results to report")


def demo_combined():
    """Combined caching + parallel processing"""
    print("\n" + "="*70)
    print("DEMO: Combined Caching + Parallel Processing")
    print("="*70)

    @cache_result(ttl=300, prefix="combined_demo")
    def cached_task(n):
        time.sleep(0.05)  # Simulate work
        return n ** 2

    tasks = list(range(20))

    # First run (cache miss)
    print("\nFirst run (cache miss):")
    start = time.time()
    results = parallel_map(cached_task, tasks, mode='io', show_progress=True)
    first_time = time.time() - start
    print(f"  Time: {first_time:.3f}s")

    # Second run (cache hit)
    print("\nSecond run (cache hit):")
    start = time.time()
    results = parallel_map(cached_task, tasks, mode='io', show_progress=True)
    second_time = time.time() - start
    print(f"  Time: {second_time:.3f}s")

    print(f"\nSpeedup: {first_time/second_time:.2f}x with caching")


def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("CACHING & PARALLEL PROCESSING DEMONSTRATIONS")
    print("="*70)

    demo_basic_caching()
    demo_decorator_caching()
    demo_multiprocessing()
    demo_threading()
    demo_job_queue()
    demo_combined()

    print("\n" + "="*70)
    print("All demonstrations complete!")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
