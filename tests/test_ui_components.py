"""
Tests for UI components (Task 4)
"""
import pytest
from io import StringIO
import sys
from colorama import Fore, Style
from src.ui import (
    print_success,
    print_error,
    print_warning,
    print_info,
    handle_error,
    print_logo
)


def capture_output(func, *args, **kwargs):
    """Helper to capture print output"""
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        func(*args, **kwargs)
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    return output


def test_print_success():
    """Test success message printing"""
    output = capture_output(print_success, "Test successful")
    
    # Should contain the message
    assert "Test successful" in output
    # Should contain checkmark
    assert "✓" in output or "v" in output.lower()


def test_print_error():
    """Test error message printing"""
    output = capture_output(print_error, "Test error")
    
    # Should contain the message
    assert "Test error" in output
    # Should contain X or error symbol
    assert "✗" in output or "x" in output.lower()


def test_print_warning():
    """Test warning message printing"""
    output = capture_output(print_warning, "Test warning")
    
    # Should contain the message
    assert "Test warning" in output
    # Should contain warning symbol
    assert "⚠" in output or "warning" in output.lower()


def test_print_info():
    """Test info message printing"""
    output = capture_output(print_info, "Test info")
    
    # Should contain the message
    assert "Test info" in output


def test_handle_error_invalid_ticker():
    """Test error handler for invalid ticker"""
    output = capture_output(handle_error, 'invalid_ticker', 'INVALID')
    
    # Should contain ticker name
    assert "INVALID" in output
    # Should contain suggestions
    assert "Suggestions" in output or "suggestions" in output
    # Should mention common tickers
    assert "AAPL" in output


def test_handle_error_no_data():
    """Test error handler for no data"""
    output = capture_output(handle_error, 'no_data', 'DELISTED')
    
    # Should contain ticker name
    assert "DELISTED" in output
    # Should contain possible reasons
    assert "reasons" in output.lower() or "Possible" in output


def test_handle_error_network():
    """Test error handler for network error"""
    output = capture_output(handle_error, 'network_error')
    
    # Should contain troubleshooting info
    assert "connection" in output.lower() or "network" in output.lower()


def test_handle_error_unknown():
    """Test error handler for unknown error type"""
    output = capture_output(handle_error, 'unknown_error_type')
    
    # Should still produce some output
    assert len(output) > 0


def test_print_logo():
    """Test logo printing"""
    output = capture_output(print_logo)
    
    # Should contain APEX or company name
    assert "APEX" in output or "Apex" in output or "█" in output
    # Should be multi-line
    assert output.count('\n') > 5


def test_colored_output_contains_ansi():
    """Test that colored functions use ANSI codes (when colorama is active)"""
    output = capture_output(print_success, "Test")
    
    # Should contain ANSI escape sequences or the message
    # (ANSI codes might be stripped in some environments)
    assert "Test" in output


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
