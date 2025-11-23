"""
Optimized Data Handling Module

Provides efficient data loading, saving, and processing for large datasets:
- Chunked loading for large files
- Efficient data type conversion
- Compression support (gzip, parquet)
- Memory-optimized generators
- Streaming support
"""
import gzip
import json
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, List, Optional, Union

import numpy as np
import pandas as pd

from src.utils import logger, safe_mkdir


# Optimal data types for common stock data columns
DTYPE_OPTIMIZATION_MAP = {
    'Open': 'float32',
    'High': 'float32',
    'Low': 'float32',
    'Close': 'float32',
    'Volume': 'int32',
    'Adj Close': 'float32',
    'sentiment': 'float32',
    'sentiment_confidence': 'float32',
    'vader_score': 'float32',
    'textblob_score': 'float32',
    'word_count': 'int16',
}


def optimize_dataframe_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize DataFrame memory usage by converting to efficient data types.

    This can reduce memory usage by 50-75% for numerical data.

    Args:
        df: Input DataFrame

    Returns:
        Optimized DataFrame with reduced memory footprint
    """
    if df.empty:
        return df

    original_memory = df.memory_usage(deep=True).sum() / 1024**2  # MB
    df_optimized = df.copy()

    for col in df_optimized.columns:
        col_type = df_optimized[col].dtype

        # Apply predefined optimizations
        if col in DTYPE_OPTIMIZATION_MAP:
            try:
                df_optimized[col] = df_optimized[col].astype(DTYPE_OPTIMIZATION_MAP[col])
                continue
            except (ValueError, TypeError):
                pass

        # Optimize integers
        if col_type == 'int64':
            c_min = df_optimized[col].min()
            c_max = df_optimized[col].max()

            if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                df_optimized[col] = df_optimized[col].astype(np.int8)
            elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                df_optimized[col] = df_optimized[col].astype(np.int16)
            elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                df_optimized[col] = df_optimized[col].astype(np.int32)

        # Optimize floats
        elif col_type == 'float64':
            df_optimized[col] = df_optimized[col].astype(np.float32)

        # Optimize objects (strings)
        elif col_type == 'object':
            num_unique = df_optimized[col].nunique()
            num_total = len(df_optimized[col])

            # Convert to category if cardinality is low
            if num_unique / num_total < 0.5:
                df_optimized[col] = df_optimized[col].astype('category')

    optimized_memory = df_optimized.memory_usage(deep=True).sum() / 1024**2  # MB
    reduction = (1 - optimized_memory / original_memory) * 100 if original_memory > 0 else 0

    logger.info(f"Memory optimization: {original_memory:.2f} MB → {optimized_memory:.2f} MB ({reduction:.1f}% reduction)")

    return df_optimized


def save_dataframe_compressed(
    df: pd.DataFrame,
    filepath: Union[str, Path],
    compression: str = 'gzip',
    optimize_dtypes: bool = True
) -> Path:
    """
    Save DataFrame with compression for reduced storage.

    Supported formats:
    - CSV with gzip compression
    - Parquet (columnar, highly compressed)

    Args:
        df: DataFrame to save
        filepath: Output file path
        compression: 'gzip' or 'parquet'
        optimize_dtypes: Whether to optimize data types before saving

    Returns:
        Path to saved file
    """
    filepath = Path(filepath)
    safe_mkdir(filepath.parent)

    if optimize_dtypes:
        df = optimize_dataframe_dtypes(df)

    if compression == 'parquet':
        # Parquet is columnar and highly compressed
        output_path = filepath.with_suffix('.parquet')
        df.to_parquet(output_path, engine='pyarrow', compression='snappy', index=False)
        logger.info(f"Saved compressed parquet: {output_path}")

    elif compression == 'gzip':
        # CSV with gzip compression
        # Handle different input filename formats
        if filepath.suffix == '.gz':
            # Already has .gz extension
            output_path = filepath
        elif filepath.suffix == '.csv':
            # Has .csv, add .gz
            output_path = Path(str(filepath) + '.gz')
        else:
            # No extension, add .csv.gz
            output_path = filepath.with_suffix('.csv.gz')

        df.to_csv(output_path, compression='gzip', index=False)
        logger.info(f"Saved compressed CSV: {output_path}")

    else:
        # Standard CSV
        output_path = filepath.with_suffix('.csv')
        df.to_csv(output_path, index=False)
        logger.info(f"Saved CSV: {output_path}")

    return output_path


def load_dataframe_chunked(
    filepath: Union[str, Path],
    chunksize: int = 10000,
    optimize_dtypes: bool = True
) -> Generator[pd.DataFrame, None, None]:
    """
    Load large CSV files in chunks to avoid memory issues.

    Usage:
        for chunk in load_dataframe_chunked('large_file.csv'):
            process(chunk)

    Args:
        filepath: Path to CSV file
        chunksize: Number of rows per chunk
        optimize_dtypes: Whether to optimize data types

    Yields:
        DataFrame chunks
    """
    filepath = Path(filepath)

    # Detect compression
    if filepath.suffix == '.gz':
        compression = 'gzip'
    elif filepath.suffix == '.parquet':
        # Parquet doesn't support chunking the same way
        # Load and yield in chunks
        df = pd.read_parquet(filepath)
        for i in range(0, len(df), chunksize):
            chunk = df.iloc[i:i + chunksize]
            if optimize_dtypes:
                chunk = optimize_dataframe_dtypes(chunk)
            yield chunk
        return
    else:
        compression = 'infer'

    # Read CSV in chunks
    for chunk in pd.read_csv(filepath, chunksize=chunksize, compression=compression):
        if optimize_dtypes:
            chunk = optimize_dataframe_dtypes(chunk)
        yield chunk


def load_dataframe_optimized(
    filepath: Union[str, Path],
    optimize_dtypes: bool = True,
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load DataFrame with automatic optimization.

    Handles:
    - Compressed files (.gz, .parquet)
    - Data type optimization
    - Column selection for memory efficiency

    Args:
        filepath: Path to file
        optimize_dtypes: Whether to optimize data types
        columns: Specific columns to load (None = all)

    Returns:
        Optimized DataFrame
    """
    filepath = Path(filepath)

    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return pd.DataFrame()

    # Load based on file type
    if filepath.suffix == '.parquet':
        df = pd.read_parquet(filepath, columns=columns)
    elif filepath.suffix == '.gz':
        df = pd.read_csv(filepath, compression='gzip', usecols=columns)
    else:
        df = pd.read_csv(filepath, usecols=columns)

    if optimize_dtypes:
        df = optimize_dataframe_dtypes(df)

    logger.info(f"Loaded {filepath.name}: {len(df)} rows, {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    return df


def stream_json_records(filepath: Union[str, Path]) -> Generator[Dict[str, Any], None, None]:
    """
    Stream JSON records one at a time for memory efficiency.

    Supports:
    - JSON arrays: [{"a": 1}, {"a": 2}]
    - JSON lines: {"a": 1}\n{"a": 2}
    - Compressed JSON (.gz)

    Args:
        filepath: Path to JSON file

    Yields:
        Individual JSON objects
    """
    filepath = Path(filepath)

    # Handle compression
    if filepath.suffix == '.gz':
        open_func = gzip.open
    else:
        open_func = open

    with open_func(filepath, 'rt', encoding='utf-8') as f:
        first_char = f.read(1)
        f.seek(0)

        if first_char == '[':
            # JSON array - load and yield
            data = json.load(f)
            for record in data:
                yield record
        else:
            # JSON lines - one object per line
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)


def save_json_compressed(
    data: Any,
    filepath: Union[str, Path],
    compression: bool = True
) -> Path:
    """
    Save JSON with optional compression.

    Args:
        data: Data to save (dict, list, etc.)
        filepath: Output path
        compression: Whether to use gzip compression

    Returns:
        Path to saved file
    """
    filepath = Path(filepath)
    safe_mkdir(filepath.parent)

    if compression:
        output_path = filepath.with_suffix('.json.gz')
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, default=str)
    else:
        output_path = filepath.with_suffix('.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    logger.info(f"Saved JSON: {output_path}")
    return output_path


def dataframe_to_dict_generator(df: pd.DataFrame) -> Generator[Dict[str, Any], None, None]:
    """
    Convert DataFrame to dict records using a generator for memory efficiency.

    More memory efficient than df.to_dict('records') for large DataFrames.

    Args:
        df: Input DataFrame

    Yields:
        Dict records
    """
    columns = df.columns.tolist()
    for row in df.itertuples(index=False, name=None):
        yield dict(zip(columns, row))


def process_large_dataframe(
    df: pd.DataFrame,
    process_func: callable,
    chunksize: int = 1000
) -> pd.DataFrame:
    """
    Process large DataFrame in chunks to reduce memory pressure.

    Args:
        df: Input DataFrame
        process_func: Function to apply to each chunk
        chunksize: Rows per chunk

    Returns:
        Processed DataFrame
    """
    chunks = []
    total_rows = len(df)

    for i in range(0, total_rows, chunksize):
        chunk = df.iloc[i:i + chunksize].copy()
        processed_chunk = process_func(chunk)
        chunks.append(processed_chunk)

        if (i + chunksize) % 10000 == 0:
            logger.info(f"Processed {min(i + chunksize, total_rows)}/{total_rows} rows")

    result = pd.concat(chunks, ignore_index=True)
    logger.info(f"Completed processing {total_rows} rows")

    return result


# Memory usage utilities

def get_dataframe_memory_usage(df: pd.DataFrame, detailed: bool = False) -> Dict[str, Any]:
    """
    Get detailed memory usage information for a DataFrame.

    Args:
        df: DataFrame to analyze
        detailed: Include per-column breakdown

    Returns:
        Memory usage statistics
    """
    total_bytes = df.memory_usage(deep=True).sum()
    total_mb = total_bytes / 1024**2

    stats = {
        'total_bytes': int(total_bytes),
        'total_mb': round(total_mb, 2),
        'rows': len(df),
        'columns': len(df.columns),
        'bytes_per_row': int(total_bytes / len(df)) if len(df) > 0 else 0
    }

    if detailed:
        column_usage = df.memory_usage(deep=True)
        stats['column_usage'] = {
            col: {
                'bytes': int(column_usage[col]),
                'mb': round(column_usage[col] / 1024**2, 2),
                'dtype': str(df[col].dtype)
            }
            for col in df.columns
        }

    return stats
