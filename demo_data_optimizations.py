"""
Demonstration of Data Handling Optimizations

Shows the benefits of:
- Data type optimization
- Compression
- Chunked loading
- Generator-based processing
- Streaming
"""
import numpy as np
import pandas as pd
from pathlib import Path
import time

from src.data_handler import (
    optimize_dataframe_dtypes,
    save_dataframe_compressed,
    load_dataframe_chunked,
    load_dataframe_optimized,
    stream_json_records,
    save_json_compressed,
    dataframe_to_dict_generator,
    get_dataframe_memory_usage,
)


def create_sample_data(rows: int = 10000) -> pd.DataFrame:
    """Create sample stock data for testing"""
    dates = pd.date_range(start='2020-01-01', periods=rows, freq='1min')

    data = {
        'Date': dates,
        'Open': np.random.randn(rows).cumsum() + 100,
        'High': np.random.randn(rows).cumsum() + 102,
        'Low': np.random.randn(rows).cumsum() + 98,
        'Close': np.random.randn(rows).cumsum() + 100,
        'Volume': np.random.randint(1000000, 10000000, rows),
        'Ticker': ['AAPL'] * rows,
        'sentiment': np.random.uniform(-1, 1, rows),
        'sentiment_confidence': np.random.uniform(0, 1, rows),
    }

    return pd.DataFrame(data)


def demo_dtype_optimization():
    """Demonstrate memory savings from dtype optimization"""
    print("\n" + "="*70)
    print("DEMONSTRATION: Data Type Optimization")
    print("="*70)

    # Create sample data
    df = create_sample_data(50000)

    # Get original memory usage
    original_usage = get_dataframe_memory_usage(df, detailed=False)
    print(f"\nOriginal DataFrame:")
    print(f"  Rows: {original_usage['rows']:,}")
    print(f"  Memory: {original_usage['total_mb']:.2f} MB")
    print(f"  Bytes per row: {original_usage['bytes_per_row']:,}")

    # Optimize dtypes
    df_optimized = optimize_dataframe_dtypes(df)

    # Get optimized memory usage
    optimized_usage = get_dataframe_memory_usage(df_optimized, detailed=False)
    reduction = (1 - optimized_usage['total_mb'] / original_usage['total_mb']) * 100

    print(f"\nOptimized DataFrame:")
    print(f"  Rows: {optimized_usage['rows']:,}")
    print(f"  Memory: {optimized_usage['total_mb']:.2f} MB")
    print(f"  Bytes per row: {optimized_usage['bytes_per_row']:,}")
    print(f"  Reduction: {reduction:.1f}%")

    print("\nData type changes:")
    for col in df.columns:
        if df[col].dtype != df_optimized[col].dtype:
            print(f"  {col}: {df[col].dtype} → {df_optimized[col].dtype}")


def demo_compression():
    """Demonstrate file size savings from compression"""
    print("\n" + "="*70)
    print("DEMONSTRATION: Compression")
    print("="*70)

    df = create_sample_data(10000)
    test_dir = Path("reports/test_compression")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Save without compression
    csv_path = test_dir / "data.csv"
    df.to_csv(csv_path, index=False)
    csv_size = csv_path.stat().st_size / 1024  # KB

    # Save with gzip
    gzip_path = save_dataframe_compressed(df, test_dir / "data_gzip", compression='gzip')
    gzip_size = gzip_path.stat().st_size / 1024  # KB

    # Save as parquet
    parquet_path = save_dataframe_compressed(df, test_dir / "data_parquet", compression='parquet')
    parquet_size = parquet_path.stat().st_size / 1024  # KB

    print(f"\nFile sizes for 10,000 rows:")
    print(f"  CSV:         {csv_size:>10.2f} KB")
    print(f"  CSV (gzip):  {gzip_size:>10.2f} KB ({(1-gzip_size/csv_size)*100:.1f}% smaller)")
    print(f"  Parquet:     {parquet_size:>10.2f} KB ({(1-parquet_size/csv_size)*100:.1f}% smaller)")

    # Cleanup
    for f in test_dir.glob("*"):
        f.unlink()
    test_dir.rmdir()


def demo_chunked_loading():
    """Demonstrate chunked loading for large files"""
    print("\n" + "="*70)
    print("DEMONSTRATION: Chunked Loading")
    print("="*70)

    # Create and save large dataset
    large_df = create_sample_data(100000)
    test_dir = Path("reports/test_chunking")
    test_dir.mkdir(parents=True, exist_ok=True)

    test_file = test_dir / "large_data.csv.gz"
    save_dataframe_compressed(large_df, test_file, compression='gzip')

    print(f"\nProcessing {len(large_df):,} rows in chunks...")

    # Process in chunks
    chunk_count = 0
    row_count = 0
    start_time = time.time()

    for chunk in load_dataframe_chunked(test_file, chunksize=10000):
        chunk_count += 1
        row_count += len(chunk)
        # Simulate processing
        _ = chunk['Close'].mean()

    elapsed = time.time() - start_time

    print(f"\nResults:")
    print(f"  Total chunks: {chunk_count}")
    print(f"  Total rows: {row_count:,}")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Throughput: {row_count/elapsed:,.0f} rows/sec")

    # Cleanup
    for f in test_dir.glob("*"):
        f.unlink()
    test_dir.rmdir()


def demo_generator_efficiency():
    """Demonstrate memory efficiency of generators"""
    print("\n" + "="*70)
    print("DEMONSTRATION: Generator vs List for Large Data")
    print("="*70)

    df = create_sample_data(50000)

    # Method 1: to_dict (loads all into memory)
    print("\nMethod 1: df.to_dict('records')")
    start = time.time()
    records_list = df.to_dict('records')
    list_time = time.time() - start
    print(f"  Time: {list_time:.4f}s")
    print(f"  Memory: ~{len(records_list) * 500 / 1024:.2f} KB (estimated)")

    # Method 2: Generator (memory efficient)
    print("\nMethod 2: dataframe_to_dict_generator()")
    start = time.time()
    records_gen = dataframe_to_dict_generator(df)
    # Process generator (doesn't load all into memory)
    count = sum(1 for _ in records_gen)
    gen_time = time.time() - start
    print(f"  Time: {gen_time:.4f}s")
    print(f"  Memory: ~constant (iterates one at a time)")
    print(f"  Processed: {count:,} records")


def demo_json_streaming():
    """Demonstrate JSON streaming"""
    print("\n" + "="*70)
    print("DEMONSTRATION: JSON Streaming")
    print("="*70)

    # Create test data
    test_data = [{'id': i, 'value': np.random.random()} for i in range(10000)]
    test_dir = Path("reports/test_json")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Save compressed JSON
    json_file = save_json_compressed(test_data, test_dir / "data", compression=True)

    print(f"\nStreaming {len(test_data):,} records from compressed JSON...")

    # Stream records one at a time
    start = time.time()
    count = 0
    for record in stream_json_records(json_file):
        count += 1
        # Process record without loading entire file into memory

    elapsed = time.time() - start

    print(f"\nResults:")
    print(f"  Records streamed: {count:,}")
    print(f"  Time: {elapsed:.4f}s")
    print(f"  File size: {json_file.stat().st_size / 1024:.2f} KB")

    # Cleanup
    json_file.unlink()
    test_dir.rmdir()


def main():
    """Run all demonstrations"""
    print("\n" + "="*70)
    print("DATA HANDLING OPTIMIZATIONS - DEMONSTRATION SUITE")
    print("="*70)

    demo_dtype_optimization()
    demo_compression()
    demo_chunked_loading()
    demo_generator_efficiency()
    demo_json_streaming()

    print("\n" + "="*70)
    print("All demonstrations complete!")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
