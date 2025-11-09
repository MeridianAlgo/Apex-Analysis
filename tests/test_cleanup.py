"""
Tests for cleanup functionality (Task 1)
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from src.utils import cleanup_company_reports, get_company_dir


@pytest.fixture
def temp_reports_dir(monkeypatch):
    """Create a temporary reports directory for testing"""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    # Mock the REPORTS_DIR in config
    import src.config as config
    original_reports_dir = config.REPORTS_DIR
    config.REPORTS_DIR = temp_path
    
    # Also patch it in utils
    import src.utils as utils
    utils.REPORTS_DIR = temp_path
    
    yield temp_path
    
    # Cleanup
    config.REPORTS_DIR = original_reports_dir
    utils.REPORTS_DIR = original_reports_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_cleanup_empty_directory(temp_reports_dir):
    """Test cleanup when no reports exist"""
    ticker = "AAPL"
    
    # Should not crash even if directory doesn't exist
    cleanup_company_reports(ticker)
    
    # Directory should be created
    company_dir = temp_reports_dir / ticker
    assert company_dir.exists()


def test_cleanup_with_existing_files(temp_reports_dir):
    """Test cleanup removes existing files"""
    ticker = "MSFT"
    company_dir = temp_reports_dir / ticker
    company_dir.mkdir(parents=True, exist_ok=True)
    
    # Create some dummy files
    (company_dir / "old_report.csv").write_text("old data")
    (company_dir / "old_chart.png").write_text("old chart")
    (company_dir / "old_summary.json").write_text("{}")
    
    # Verify files exist
    assert len(list(company_dir.glob("*"))) == 3
    
    # Run cleanup
    cleanup_company_reports(ticker)
    
    # Files should be deleted
    assert len(list(company_dir.glob("*"))) == 0
    # But directory should still exist
    assert company_dir.exists()


def test_cleanup_preserves_subdirectories(temp_reports_dir):
    """Test that cleanup only removes files, not subdirectories"""
    ticker = "GOOGL"
    company_dir = temp_reports_dir / ticker
    company_dir.mkdir(parents=True, exist_ok=True)
    
    # Create files and subdirectory
    (company_dir / "report.csv").write_text("data")
    subdir = company_dir / "archive"
    subdir.mkdir()
    (subdir / "old.csv").write_text("archived")
    
    # Run cleanup
    cleanup_company_reports(ticker)
    
    # Files in main directory should be gone
    assert not (company_dir / "report.csv").exists()
    # Subdirectory should still exist (cleanup only removes files)
    assert subdir.exists()


def test_get_company_dir_creates_directory(temp_reports_dir):
    """Test that get_company_dir creates the directory if it doesn't exist"""
    ticker = "TSLA"
    
    company_dir = get_company_dir(ticker)
    
    # Should return a Path object
    assert isinstance(company_dir, Path)
    # Directory should exist
    assert company_dir.exists()
    # Should be under reports dir
    assert company_dir.parent == temp_reports_dir


def test_get_company_dir_uppercase(temp_reports_dir):
    """Test that ticker is converted to uppercase"""
    ticker = "aapl"
    
    company_dir = get_company_dir(ticker)
    
    # Directory name should be uppercase
    assert company_dir.name == "AAPL"


def test_cleanup_multiple_tickers(temp_reports_dir):
    """Test cleanup works for multiple tickers independently"""
    tickers = ["AAPL", "MSFT", "GOOGL"]
    
    # Create files for each ticker
    for ticker in tickers:
        company_dir = temp_reports_dir / ticker
        company_dir.mkdir(parents=True, exist_ok=True)
        (company_dir / f"{ticker}_report.csv").write_text("data")
    
    # Cleanup only AAPL
    cleanup_company_reports("AAPL")
    
    # AAPL files should be gone
    assert len(list((temp_reports_dir / "AAPL").glob("*"))) == 0
    # Other tickers should still have files
    assert len(list((temp_reports_dir / "MSFT").glob("*"))) == 1
    assert len(list((temp_reports_dir / "GOOGL").glob("*"))) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
