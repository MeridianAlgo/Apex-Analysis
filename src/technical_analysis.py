"""
Technical Analysis Module
Calculates trading indicators for stock price data
"""
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def calculate_rsi(df, period=14):
    """
    Calculate Relative Strength Index (RSI)
    
    RSI measures momentum - is the stock overbought or oversold?
    - RSI > 70: Overbought (might go down soon)
    - RSI < 30: Oversold (might go up soon)
    
    Args:
        df: DataFrame with 'Close' column
        period: Number of days to calculate over (default 14)
    
    Returns:
        DataFrame with new 'RSI' column added
    """
    # Calculate price changes
    delta = df['Close'].diff()
    
    # Separate gains and losses
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Calculate RS and RSI
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    logger.info(f"✓ Calculated RSI (period={period})")
    return df


def calculate_macd(df, fast=12, slow=26, signal=9):
    """
    Calculate MACD (Moving Average Convergence Divergence)
    
    MACD shows trend direction and momentum
    - MACD line above signal line: Bullish (upward trend)
    - MACD line below signal line: Bearish (downward trend)
    
    Args:
        df: DataFrame with 'Close' column
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line period (default 9)
    
    Returns:
        DataFrame with 'MACD', 'MACD_Signal', 'MACD_Hist' columns
    """
    # Calculate exponential moving averages
    exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
    
    # MACD line
    df['MACD'] = exp1 - exp2
    
    # Signal line
    df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
    
    # Histogram (difference between MACD and signal)
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    logger.info(f"✓ Calculated MACD ({fast}/{slow}/{signal})")
    return df


def calculate_bollinger_bands(df, period=20, std_dev=2):
    """
    Calculate Bollinger Bands
    
    Shows price volatility and potential reversal points
    - Price near upper band: Might be overbought
    - Price near lower band: Might be oversold
    - Bands widening: Increasing volatility
    
    Args:
        df: DataFrame with 'Close' column
        period: Moving average period (default 20)
        std_dev: Standard deviations for bands (default 2)
    
    Returns:
        DataFrame with 'BB_Middle', 'BB_Upper', 'BB_Lower' columns
    """
    # Middle band is simple moving average
    df['BB_Middle'] = df['Close'].rolling(window=period).mean()
    
    # Calculate standard deviation
    std = df['Close'].rolling(window=period).std()
    
    # Upper and lower bands
    df['BB_Upper'] = df['BB_Middle'] + (std * std_dev)
    df['BB_Lower'] = df['BB_Middle'] - (std * std_dev)
    
    # Band width (measures volatility)
    df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
    
    logger.info(f"✓ Calculated Bollinger Bands (period={period})")
    return df


def calculate_volume_indicators(df):
    """
    Calculate volume-based indicators
    
    Volume shows how much interest there is in a stock
    - High volume + price up: Strong buying
    - High volume + price down: Strong selling
    
    Args:
        df: DataFrame with 'Volume' column
    
    Returns:
        DataFrame with volume indicators
    """
    # Volume moving averages
    df['Volume_MA_10'] = df['Volume'].rolling(window=10).mean()
    df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()
    
    # Volume ratio (current vs average)
    df['Volume_Ratio'] = df['Volume'] / df['Volume_MA_20']
    
    logger.info("✓ Calculated volume indicators")
    return df


def calculate_volatility(df, period=20):
    """
    Calculate volatility metrics
    
    Volatility measures how much the price jumps around
    - High volatility: Risky, big price swings
    - Low volatility: Stable, small price changes
    
    Args:
        df: DataFrame with 'Close' and 'High'/'Low' columns
        period: Period for calculations (default 20)
    
    Returns:
        DataFrame with volatility metrics
    """
    # Standard deviation of returns
    df['Returns'] = df['Close'].pct_change()
    df['Volatility'] = df['Returns'].rolling(window=period).std()
    
    # Average True Range (ATR)
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(period).mean()
    
    logger.info(f"✓ Calculated volatility (period={period})")
    return df


def add_all_indicators(df):
    """
    Add ALL technical indicators to the dataframe
    
    This is the main function you'll call from other modules.
    It runs all the indicator calculations in sequence.
    
    Args:
        df: DataFrame with OHLCV data (Open, High, Low, Close, Volume)
    
    Returns:
        DataFrame with all indicators added as new columns
    """
    logger.info("📊 Adding technical indicators...")
    
    # Make a copy so we don't modify the original
    df = df.copy()
    
    # Check if required columns exist
    required_cols = ['Close', 'High', 'Low', 'Volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.warning(f"Missing columns for technical analysis: {missing_cols}")
        return df
    
    # Add each indicator
    df = calculate_rsi(df)
    df = calculate_macd(df)
    df = calculate_bollinger_bands(df)
    df = calculate_volume_indicators(df)
    df = calculate_volatility(df)
    
    # Add simple moving averages (commonly used)
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    logger.info(f"✅ Added {len(df.columns)} total columns (including indicators)")
    
    return df
