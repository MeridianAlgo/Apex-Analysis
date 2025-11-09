"""
Tests for technical analysis indicators
"""
import pytest
import pandas as pd
import numpy as np
from src.technical_analysis import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_volume_indicators,
    calculate_volatility,
    add_all_indicators
)


@pytest.fixture
def sample_stock_data():
    """Create sample stock data for testing"""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    
    # Generate realistic price data
    close_prices = 100 + np.cumsum(np.random.randn(100) * 2)
    high_prices = close_prices + np.random.rand(100) * 2
    low_prices = close_prices - np.random.rand(100) * 2
    open_prices = close_prices + np.random.randn(100)
    volumes = np.random.randint(1000000, 10000000, 100)
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': open_prices,
        'High': high_prices,
        'Low': low_prices,
        'Close': close_prices,
        'Volume': volumes
    })
    
    return df


def test_calculate_rsi(sample_stock_data):
    """Test RSI calculation"""
    df = sample_stock_data.copy()
    result = calculate_rsi(df, period=14)
    
    # Check that RSI column was added
    assert 'RSI' in result.columns
    
    # RSI should be between 0 and 100
    valid_rsi = result['RSI'].dropna()
    assert (valid_rsi >= 0).all()
    assert (valid_rsi <= 100).all()
    
    # First few values should be NaN (not enough data)
    assert result['RSI'].iloc[:13].isna().all()


def test_calculate_macd(sample_stock_data):
    """Test MACD calculation"""
    df = sample_stock_data.copy()
    result = calculate_macd(df, fast=12, slow=26, signal=9)
    
    # Check that MACD columns were added
    assert 'MACD' in result.columns
    assert 'MACD_Signal' in result.columns
    assert 'MACD_Hist' in result.columns
    
    # MACD histogram should be difference between MACD and signal
    valid_idx = result['MACD_Hist'].notna()
    expected_hist = result.loc[valid_idx, 'MACD'] - result.loc[valid_idx, 'MACD_Signal']
    np.testing.assert_array_almost_equal(
        result.loc[valid_idx, 'MACD_Hist'].values,
        expected_hist.values,
        decimal=5
    )


def test_calculate_bollinger_bands(sample_stock_data):
    """Test Bollinger Bands calculation"""
    df = sample_stock_data.copy()
    result = calculate_bollinger_bands(df, period=20, std_dev=2)
    
    # Check that BB columns were added
    assert 'BB_Middle' in result.columns
    assert 'BB_Upper' in result.columns
    assert 'BB_Lower' in result.columns
    assert 'BB_Width' in result.columns
    
    # Upper band should be above middle, middle above lower
    valid_idx = result['BB_Middle'].notna()
    assert (result.loc[valid_idx, 'BB_Upper'] >= result.loc[valid_idx, 'BB_Middle']).all()
    assert (result.loc[valid_idx, 'BB_Middle'] >= result.loc[valid_idx, 'BB_Lower']).all()
    
    # Width should be positive
    assert (result.loc[valid_idx, 'BB_Width'] > 0).all()


def test_calculate_volume_indicators(sample_stock_data):
    """Test volume indicators calculation"""
    df = sample_stock_data.copy()
    result = calculate_volume_indicators(df)
    
    # Check that volume columns were added
    assert 'Volume_MA_10' in result.columns
    assert 'Volume_MA_20' in result.columns
    assert 'Volume_Ratio' in result.columns
    
    # Volume ratio should be positive
    valid_idx = result['Volume_Ratio'].notna()
    assert (result.loc[valid_idx, 'Volume_Ratio'] > 0).all()


def test_calculate_volatility(sample_stock_data):
    """Test volatility calculation"""
    df = sample_stock_data.copy()
    result = calculate_volatility(df, period=20)
    
    # Check that volatility columns were added
    assert 'Returns' in result.columns
    assert 'Volatility' in result.columns
    assert 'ATR' in result.columns
    
    # Volatility should be non-negative
    valid_idx = result['Volatility'].notna()
    assert (result.loc[valid_idx, 'Volatility'] >= 0).all()
    
    # ATR should be positive
    valid_atr = result['ATR'].dropna()
    assert (valid_atr > 0).all()


def test_add_all_indicators(sample_stock_data):
    """Test adding all indicators at once"""
    df = sample_stock_data.copy()
    original_cols = len(df.columns)
    
    result = add_all_indicators(df)
    
    # Should have more columns than original
    assert len(result.columns) > original_cols
    
    # Check that key indicators are present
    expected_indicators = [
        'RSI', 'MACD', 'MACD_Signal', 'MACD_Hist',
        'BB_Middle', 'BB_Upper', 'BB_Lower', 'BB_Width',
        'Volume_MA_10', 'Volume_MA_20', 'Volume_Ratio',
        'Returns', 'Volatility', 'ATR',
        'SMA_10', 'SMA_20', 'SMA_50'
    ]
    
    for indicator in expected_indicators:
        assert indicator in result.columns, f"Missing indicator: {indicator}"


def test_add_all_indicators_missing_columns():
    """Test that function handles missing columns gracefully"""
    # Create dataframe with only Close column
    df = pd.DataFrame({
        'Close': [100, 101, 102, 103, 104]
    })
    
    result = add_all_indicators(df)
    
    # Should return dataframe without crashing
    assert isinstance(result, pd.DataFrame)
    # Should have original columns
    assert 'Close' in result.columns


def test_indicators_with_insufficient_data():
    """Test indicators with very small dataset"""
    df = pd.DataFrame({
        'Open': [100, 101, 102],
        'High': [101, 102, 103],
        'Low': [99, 100, 101],
        'Close': [100, 101, 102],
        'Volume': [1000, 1100, 1200]
    })
    
    result = add_all_indicators(df)
    
    # Should not crash
    assert isinstance(result, pd.DataFrame)
    # Most indicators will be NaN due to insufficient data
    assert result['RSI'].isna().all()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
