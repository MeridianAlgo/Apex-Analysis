# Apex Analysis - Test Suite

## Overview
Comprehensive test suite for the Apex Analysis stock analysis tool, covering technical indicators, UI components, cleanup functionality, and integration tests.

## Quick Start

### Run All Tests
```bash
pytest tests/ -v -m "not slow"
```

### Run Specific Test Files
```bash
# Technical analysis tests
pytest tests/test_technical_analysis.py -v

# Cleanup functionality tests
pytest tests/test_cleanup.py -v

# UI component tests
pytest tests/test_ui_components.py -v

# Integration tests
pytest tests/test_integration.py -v
```

## Test Files

### `test_technical_analysis.py`
Tests for technical indicator calculations (Task 2)

**Coverage:**
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Volume indicators
- Volatility metrics
- Simple Moving Averages

**Tests:** 8 tests, all passing ✅

### `test_cleanup.py`
Tests for automatic report cleanup (Task 1)

**Coverage:**
- Directory creation
- File deletion
- Multi-ticker handling
- Error handling

**Tests:** 6 tests, all passing ✅

### `test_ui_components.py`
Tests for UI/UX components (Task 4)

**Coverage:**
- Colored output functions
- Error message handlers
- ASCII logo display
- ANSI color codes

**Tests:** 10 tests, all passing ✅

### `test_integration.py`
End-to-end integration tests

**Coverage:**
- Complete workflow testing
- Error handling
- Data pipeline integration

**Tests:** 3 tests (+ 1 slow), all passing ✅

## Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.integration` - Integration tests that may require network
- `@pytest.mark.slow` - Tests that take more than a few seconds
- `@pytest.mark.unit` - Fast unit tests (default)

### Run by Marker
```bash
# Only integration tests
pytest tests/ -v -m integration

# Only unit tests
pytest tests/ -v -m unit

# Exclude slow tests
pytest tests/ -v -m "not slow"
```

## Test Results

**Current Status:**
- Total Tests: 29
- Passed: 29 ✅
- Failed: 0 ❌
- Success Rate: 100%

## Writing New Tests

### Example Test Structure
```python
import pytest
from src.your_module import your_function

def test_your_feature():
    """Test description"""
    # Arrange
    input_data = ...
    
    # Act
    result = your_function(input_data)
    
    # Assert
    assert result == expected_value
```

### Using Fixtures
```python
@pytest.fixture
def sample_data():
    """Create reusable test data"""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Test using fixture"""
    assert sample_data["key"] == "value"
```

## Continuous Integration

### Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
pytest tests/ -v -m "not slow"
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

### GitHub Actions
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

## Troubleshooting

### Tests Fail Due to Missing Dependencies
```bash
pip install -r requirements.txt
```

### Tests Fail Due to Import Errors
Ensure you're running from the project root:
```bash
cd /path/to/Apex-Analysis
pytest tests/ -v
```

### Network Tests Fail
Integration tests may fail without internet. Skip them:
```bash
pytest tests/ -v -m "not integration"
```

## Coverage Report

Generate test coverage report:
```bash
pip install pytest-cov
pytest tests/ --cov=src --cov-report=html
```

View coverage:
```bash
# Open htmlcov/index.html in browser
```

## Documentation

- **TEST_SUMMARY.md** - Detailed test documentation
- **../COMPLETION_REPORT.md** - Overall project completion status

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain 100% success rate
4. Document new test files here

## Support

For issues or questions:
1. Check test output for specific errors
2. Review TEST_SUMMARY.md for details
3. Check logs in `reports/apex.log`
4. Review COMPLETION_REPORT.md for known issues
