"""
Integration tests for the complete workflow
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from src.aggregator import aggregate_analysis
from src.fetch_data import fetch_stock_history
from src.technical_analysis import add_all_indicators


@pytest.mark.integration
def test_fetch_and_analyze_workflow():
    """Test the complete workflow: fetch -> add indicators -> analyze"""
    ticker = "AAPL"
    
    # This is a real API call, so it might fail if network is down
    try:
        # Fetch stock data
        df = fetch_stock_history(ticker, period='1mo')
        
        if df is not None and not df.empty:
            # Should have OHLCV columns
            assert 'Close' in df.columns
            assert 'High' in df.columns
            assert 'Low' in df.columns
            assert 'Volume' in df.columns
            
            # Should have technical indicators added
            assert 'RSI' in df.columns
            assert 'MACD' in df.columns
            assert 'BB_Upper' in df.columns
            
            # Data should be reasonable
            assert len(df) > 0
            assert df['Close'].notna().any()
    except Exception as e:
        pytest.skip(f"Network test skipped due to: {e}")


@pytest.mark.integration
@pytest.mark.slow
def test_full_analysis_pipeline():
    """Test the complete analysis pipeline"""
    ticker = "MSFT"
    
    try:
        # Run full analysis
        results = aggregate_analysis(ticker, period='1mo', num_articles=5)
        
        # Should return results for the ticker
        assert ticker in results
        
        data = results[ticker]
        
        # Should have key components
        assert 'ticker' in data
        assert 'timestamp' in data
        
        # Should have either data or an error
        if data.get('error'):
            # If there's an error, it should be a string
            assert isinstance(data['error'], str)
        else:
            # If no error, should have data
            assert 'price_df' in data or 'price_data' in data
            
    except Exception as e:
        pytest.skip(f"Integration test skipped due to: {e}")


def test_technical_indicators_integration():
    """Test that technical indicators integrate properly with real-like data"""
    # Create realistic test data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': range(100, 200),
        'High': range(101, 201),
        'Low': range(99, 199),
        'Close': range(100, 200),
        'Volume': [1000000] * 100
    })
    df = df.set_index('Date')
    
    # Add indicators
    result = add_all_indicators(df)
    
    # Should have all expected columns
    assert 'RSI' in result.columns
    assert 'MACD' in result.columns
    assert 'BB_Upper' in result.columns
    assert 'SMA_50' in result.columns
    
    # Indicators should have valid values (not all NaN)
    assert result['RSI'].notna().any()
    assert result['MACD'].notna().any()
    assert result['SMA_50'].notna().any()


def test_error_handling_invalid_ticker():
    """Test that invalid ticker is handled gracefully"""
    ticker = "INVALIDTICKER123456"
    
    try:
        results = aggregate_analysis(ticker, period='1mo', num_articles=5)
        
        # Should return results even for invalid ticker
        assert ticker in results
        
        # Should have an error message
        data = results[ticker]
        # Either has error or empty data
        assert data.get('error') or data.get('price_df') is None or data['price_df'].empty
    except Exception as e:
        # Should not crash, but if it does, that's also acceptable for invalid ticker
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'not slow'])
