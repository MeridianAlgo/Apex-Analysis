# Apex Analysis - Project Structure

## Overview
This document describes the organization of the Apex Analysis project.

## Directory Structure

```
Apex-Analysis/
├── src/                    # Source code
│   ├── __init__.py
│   ├── __main__.py
│   ├── aggregator.py      # Main analysis orchestration
│   ├── config.py          # Configuration management
│   ├── fetch_data.py      # Stock data fetching
│   ├── news_processor.py  # News article processing
│   ├── sentiment_analyzer.py  # Sentiment analysis
│   ├── ui.py              # User interface and CLI
│   └── utils.py           # Utility functions
│
├── tests/                  # Test files
│   ├── __init__.py
│   ├── test_aggregate.py
│   └── test_save_png.py
│
├── docs/                   # Documentation
│   ├── CONTRIBUTORS.md
│   ├── SECURITY.md
│   └── PROJECT_STRUCTURE.md (this file)
│
├── reports/                # Generated analysis reports (gitignored)
│   └── [TICKER]/          # One folder per stock ticker
│       ├── *_price_data.csv
│       ├── *_news.json
│       ├── *_summary.json
│       └── *.png
│
├── .cache/                 # Cache directory (gitignored)
│
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── pyproject.toml         # Project metadata
├── setup.py               # Package setup
├── tasks.md               # Intern task assignments
├── README.md              # Project documentation
├── LICENSE                # MIT License
└── .gitignore             # Git ignore rules
```

## Key Files

### Source Code (`src/`)
- **aggregator.py**: Orchestrates the entire analysis pipeline
- **fetch_data.py**: Fetches stock price data from Yahoo Finance
- **news_processor.py**: Scrapes and processes news articles
- **sentiment_analyzer.py**: Analyzes sentiment of news articles
- **ui.py**: Command-line interface and visualization
- **utils.py**: Helper functions (logging, file I/O, etc.)
- **config.py**: Configuration management

### Tests (`tests/`)
- All test files should be placed here
- Use pytest for running tests: `pytest tests/`

### Documentation (`docs/`)
- **CONTRIBUTORS.md**: List of project contributors
- **SECURITY.md**: Security policy and vulnerability reporting
- **PROJECT_STRUCTURE.md**: This file

### Reports (`reports/`)
- Auto-generated analysis reports
- Organized by ticker symbol
- Automatically cleaned up on new analysis (see Task #3)
- Not tracked in git

## Recent Changes (2025-11-09)

### Cleanup Performed
1. ✅ Created `tests/` directory and moved test files
2. ✅ Created `docs/` directory and moved documentation
3. ✅ Removed duplicate `cache/` directory (using `.cache/` only)
4. ✅ Removed `__pycache__/` directories
5. ✅ Removed `apex_analysis.egg-info/`
6. ✅ Removed empty `__init__.py` from root
7. ✅ Removed `src/reports/` (duplicate of root `reports/`)
8. ✅ Removed `src/cache/` (using root `.cache/` only)
9. ✅ Updated `.gitignore` with comprehensive rules

### .gitignore Coverage
The `.gitignore` now properly excludes:
- Python artifacts (`__pycache__`, `*.pyc`, `*.egg-info`)
- Cache directories (`.cache/`, `cache/`)
- Generated reports (`reports/`)
- Virtual environments (`venv/`, `.venv/`)
- IDE files (`.vscode/`, `.idea/`)
- OS files (`.DS_Store`, `Thumbs.db`)

## Future Structure (Task #3)

The intern will reorganize `src/` into logical subpackages:

```
src/
├── data/                   # Data fetching and processing
│   ├── fetch_data.py
│   ├── news_processor.py
│   └── technical_analysis.py
│
├── analysis/               # Analysis modules
│   ├── sentiment_analyzer.py
│   ├── aggregator.py
│   └── ml_export.py
│
├── visualization/          # UI and plotting
│   └── ui.py
│
└── utils/                  # Utilities
    ├── config.py
    └── utils.py
```

## Development Workflow

1. **Create a feature branch**: `git checkout -b feature-name`
2. **Make changes** in appropriate directories
3. **Run tests**: `pytest tests/`
4. **Commit changes**: `git commit -m "Description"`
5. **Push and create PR**: `git push origin feature-name`

## Notes for Developers

- Keep `src/` for source code only
- Put all tests in `tests/`
- Put all documentation in `docs/`
- Never commit `reports/` or `.cache/` directories
- Use `main.py` as the entry point
- Follow the task assignments in `tasks.md`

---

Last updated: 2025-11-09 by Ishaan M
