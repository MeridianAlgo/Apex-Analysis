"""
Parallel Processing Module

Implements:
- Multiprocessing for CPU-bound tasks
- Threading for I/O-bound operations
- Job queues with progress tracking
- Worker pools with error handling
"""
import multiprocessing as mp
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from queue import Queue, Empty
from typing import Any, Callable, Iterable, List, Optional, Union
import time

from tqdm import tqdm
from src.utils import logger


@dataclass
class JobResult:
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0


class ProgressTracker:
    """Thread-safe progress tracker"""

    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.completed = 0
        self.failed = 0
        self.lock = threading.Lock()
        self.pbar = tqdm(total=total, desc=description)

    def update(self, success: bool = True):
        with self.lock:
            self.completed += 1
            if not success:
                self.failed += 1
            self.pbar.update(1)

    def close(self):
        self.pbar.close()

    def get_stats(self) -> dict:
        with self.lock:
            return {
                'total': self.total,
                'completed': self.completed,
                'failed': self.failed,
                'success_rate': (self.completed - self.failed) / self.completed * 100 if self.completed > 0 else 0
            }


class ParallelProcessor:
    """Base class for parallel processing"""

    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or mp.cpu_count()

    def _execute_safe(self, func: Callable, item: Any) -> JobResult:
        """Execute function with error handling and timing"""
        start_time = time.time()
        try:
            result = func(item)
            return JobResult(
                success=True,
                result=result,
                execution_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"Error processing item: {e}", exc_info=True)
            return JobResult(
                success=False,
                error=e,
                execution_time=time.time() - start_time
            )


class MultiprocessingPool(ParallelProcessor):
    """Process pool for CPU-bound tasks"""

    def map(
        self,
        func: Callable,
        items: Iterable,
        show_progress: bool = True,
        chunksize: Optional[int] = None
    ) -> List[JobResult]:
        """
        Map function across items using multiprocessing

        Best for: CPU-intensive operations (data processing, calculations)
        """
        items_list = list(items)
        total = len(items_list)

        results = []
        tracker = ProgressTracker(total, "CPU-bound tasks") if show_progress else None

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._execute_safe, func, item): item for item in items_list}

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                if tracker:
                    tracker.update(result.success)

        if tracker:
            tracker.close()
            logger.info(f"Multiprocessing complete: {tracker.get_stats()}")

        return results

    def starmap(
        self,
        func: Callable,
        items: Iterable[tuple],
        show_progress: bool = True
    ) -> List[JobResult]:
        """Map function with multiple arguments"""
        items_list = list(items)
        total = len(items_list)

        results = []
        tracker = ProgressTracker(total, "CPU-bound tasks") if show_progress else None

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._execute_safe_star, func, *args): args for args in items_list}

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                if tracker:
                    tracker.update(result.success)

        if tracker:
            tracker.close()

        return results

    def _execute_safe_star(self, func: Callable, *args) -> JobResult:
        """Execute function with multiple args"""
        start_time = time.time()
        try:
            result = func(*args)
            return JobResult(
                success=True,
                result=result,
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return JobResult(
                success=False,
                error=e,
                execution_time=time.time() - start_time
            )


class ThreadingPool(ParallelProcessor):
    """Thread pool for I/O-bound tasks"""

    def map(
        self,
        func: Callable,
        items: Iterable,
        show_progress: bool = True
    ) -> List[JobResult]:
        """
        Map function across items using threading

        Best for: I/O operations (API calls, file operations, web scraping)
        """
        items_list = list(items)
        total = len(items_list)

        results = []
        tracker = ProgressTracker(total, "I/O-bound tasks") if show_progress else None

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._execute_safe, func, item): item for item in items_list}

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                if tracker:
                    tracker.update(result.success)

        if tracker:
            tracker.close()
            logger.info(f"Threading complete: {tracker.get_stats()}")

        return results

    def starmap(
        self,
        func: Callable,
        items: Iterable[tuple],
        show_progress: bool = True
    ) -> List[JobResult]:
        """Map function with multiple arguments"""
        items_list = list(items)
        total = len(items_list)

        results = []
        tracker = ProgressTracker(total, "I/O-bound tasks") if show_progress else None

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(func, *args): args for args in items_list}

            for future in as_completed(futures):
                try:
                    result = future.result()
                    job_result = JobResult(success=True, result=result)
                except Exception as e:
                    job_result = JobResult(success=False, error=e)

                results.append(job_result)

                if tracker:
                    tracker.update(job_result.success)

        if tracker:
            tracker.close()

        return results


class JobQueue:
    """Background job queue with worker threads"""

    def __init__(self, num_workers: int = 4):
        self.queue = Queue()
        self.results = {}
        self.num_workers = num_workers
        self.workers = []
        self.running = False
        self.job_counter = 0
        self.lock = threading.Lock()

    def start(self):
        """Start worker threads"""
        self.running = True
        for i in range(self.num_workers):
            worker = threading.Thread(target=self._worker, daemon=True, name=f"Worker-{i}")
            worker.start()
            self.workers.append(worker)
        logger.info(f"Started {self.num_workers} worker threads")

    def stop(self, wait: bool = True):
        """Stop worker threads"""
        self.running = False

        if wait:
            # Wait for queue to empty
            self.queue.join()

        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=1.0)

        logger.info("Stopped worker threads")

    def _worker(self):
        """Worker thread main loop"""
        while self.running:
            try:
                job_id, func, args, kwargs = self.queue.get(timeout=0.5)

                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    job_result = JobResult(
                        success=True,
                        result=result,
                        execution_time=time.time() - start_time
                    )
                except Exception as e:
                    logger.error(f"Job {job_id} failed: {e}", exc_info=True)
                    job_result = JobResult(
                        success=False,
                        error=e,
                        execution_time=time.time() - start_time
                    )

                with self.lock:
                    self.results[job_id] = job_result

                self.queue.task_done()

            except Empty:
                continue

    def submit(self, func: Callable, *args, **kwargs) -> int:
        """Submit job to queue"""
        with self.lock:
            self.job_counter += 1
            job_id = self.job_counter

        self.queue.put((job_id, func, args, kwargs))
        return job_id

    def get_result(self, job_id: int, timeout: Optional[float] = None) -> Optional[JobResult]:
        """Get job result (blocking if not ready)"""
        start_time = time.time()

        while True:
            with self.lock:
                if job_id in self.results:
                    return self.results.pop(job_id)

            if timeout and (time.time() - start_time) > timeout:
                return None

            time.sleep(0.1)

    def get_queue_size(self) -> int:
        """Get number of pending jobs"""
        return self.queue.qsize()


def parallel_map(
    func: Callable,
    items: Iterable,
    mode: str = 'auto',
    max_workers: Optional[int] = None,
    show_progress: bool = True
) -> List[Any]:
    """
    Convenience function for parallel mapping

    Args:
        func: Function to apply
        items: Items to process
        mode: 'cpu', 'io', or 'auto' (default)
        max_workers: Max parallel workers
        show_progress: Show progress bar

    Returns:
        List of results (in original order)
    """
    items_list = list(items)

    if len(items_list) == 0:
        return []

    # Auto-detect mode
    if mode == 'auto':
        # Simple heuristic: if function is I/O bound, use threads
        # For now, default to threads for small datasets, processes for large
        mode = 'io' if len(items_list) < 100 else 'cpu'

    if mode == 'cpu':
        processor = MultiprocessingPool(max_workers=max_workers)
    else:
        processor = ThreadingPool(max_workers=max_workers)

    results = processor.map(func, items_list, show_progress=show_progress)

    # Extract successful results (maintain order)
    return [r.result for r in results if r.success]


def batch_process(
    items: Iterable,
    func: Callable,
    batch_size: int = 100,
    mode: str = 'io',
    show_progress: bool = True
) -> List[Any]:
    """
    Process items in batches with parallel processing

    Useful for: API rate limiting, memory management
    """
    items_list = list(items)
    total_items = len(items_list)
    all_results = []

    # Create batches
    batches = [items_list[i:i + batch_size] for i in range(0, total_items, batch_size)]

    tracker = ProgressTracker(len(batches), "Batch processing") if show_progress else None

    for batch in batches:
        batch_results = parallel_map(batch, func, mode=mode, show_progress=False)
        all_results.extend(batch_results)

        if tracker:
            tracker.update(True)

    if tracker:
        tracker.close()

    return all_results
