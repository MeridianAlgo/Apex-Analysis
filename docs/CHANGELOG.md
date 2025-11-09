# Changelog

All notable changes to the Apex Analysis project will be documented in this file.

## [Unreleased] - 2025-11-09

### Added
- Created `docs/` directory for all documentation
- Created `tests/` directory for all test files
- Added `docs/PROJECT_STRUCTURE.md` - Complete project organization guide
- Added `docs/GETTING_STARTED.md` - Beginner-friendly setup guide for Richard
- Added `docs/CHANGELOG.md` - This file
- Added `tests/__init__.py` - Makes tests a proper Python package
- Enhanced `.gitignore` with comprehensive Python, IDE, and project-specific rules

### Changed
- Moved `CONTRIBUTORS.md` to `docs/CONTRIBUTORS.md`
- Moved `SECURITY.md` to `docs/SECURITY.md`
- Moved `test_aggregate.py` to `tests/test_aggregate.py`
- Moved `test_save_png.py` to `tests/test_save_png.py`
- Updated `tasks.md` with detailed, beginner-friendly instructions for Task #3
  - Added step-by-step instructions for auto-delete feature
  - Added comprehensive technical analysis guide with code examples
  - Added detailed UI/UX overhaul instructions with colorama and tqdm
  - Included troubleshooting sections for each step

### Removed
- Deleted duplicate `cache/` directory (using `.cache/` only)
- Deleted `src/cache/` directory (duplicate)
- Deleted `src/reports/` directory (duplicate of root `reports/`)
- Deleted `__pycache__/` directories (Python bytecode cache)
- Deleted `apex_analysis.egg-info/` (build artifacts)
- Deleted empty `__init__.py` from project root

### Project Structure
```
Before:
Apex-Analysis/
├── __pycache__/           ❌ Removed
├── cache/                 ❌ Removed (duplicate)
├── apex_analysis.egg-info/ ❌ Removed
├── src/
│   ├── __pycache__/       ❌ Removed
│   ├── cache/             ❌ Removed
│   └── reports/           ❌ Removed
├── __init__.py            ❌ Removed
├── CONTRIBUTORS.md        → Moved to docs/
├── SECURITY.md            → Moved to docs/
├── test_aggregate.py      → Moved to tests/
└── test_save_png.py       → Moved to tests/

After:
Apex-Analysis/
├── .cache/                ✅ Single cache location
├── docs/                  ✅ New - All documentation
│   ├── CONTRIBUTORS.md
│   ├── SECURITY.md
│   ├── PROJECT_STRUCTURE.md
│   ├── GETTING_STARTED.md
│   └── CHANGELOG.md
├── tests/                 ✅ New - All tests
│   ├── __init__.py
│   ├── test_aggregate.py
│   └── test_save_png.py
├── src/                   ✅ Clean source code
├── reports/               ✅ Generated reports
├── main.py
├── tasks.md               ✅ Enhanced with detailed instructions
└── ...
```

## [1.0.0] - Previous Release

### Features
- Stock price data fetching from Yahoo Finance
- News article scraping and processing
- Sentiment analysis using NLTK
- Report generation (CSV, JSON, PNG)
- Command-line interface
- Basic visualization with matplotlib

---

## Task #3 Goals (In Progress)

The following features are planned for the next release:

### Analysis Enhancements
- [ ] Auto-delete old reports before generating new ones
- [ ] Technical indicators (RSI, MACD, Bollinger Bands, Volume analysis)
- [ ] Advanced sentiment analysis with ML features
- [ ] Data export pipeline for AI training

### UI/UX Improvements
- [ ] Colored terminal output with colorama
- [ ] Progress bars with tqdm
- [ ] ASCII art logo
- [ ] Better error messages with suggestions
- [ ] Enhanced visualizations

### Project Organization
- [x] Move tests to `tests/` directory
- [x] Move docs to `docs/` directory
- [x] Clean up Python artifacts
- [x] Update .gitignore
- [ ] Restructure `src/` into logical subpackages

### Documentation
- [x] PROJECT_STRUCTURE.md
- [x] GETTING_STARTED.md
- [x] CHANGELOG.md
- [ ] AI_TRAINING.md (planned)
- [ ] ARCHITECTURE.md (planned)

---

## Notes

### Version Numbering
We follow [Semantic Versioning](https://semver.org/):
- MAJOR version for incompatible API changes
- MINOR version for new functionality (backwards compatible)
- PATCH version for bug fixes (backwards compatible)

### Commit Message Format
```
<type>: <description>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes (formatting)
- refactor: Code refactoring
- test: Adding or updating tests
- chore: Maintenance tasks
```

### Contributors
- Ishaan M - Project Lead
- Richard - Intern Developer (Task #3)

---

Last updated: 2025-11-09
