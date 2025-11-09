# Getting Started with Apex Analysis Development

## Welcome, Richard! 👋

This guide will help you get started with developing Apex Analysis. Read this before starting Task #3.

## Prerequisites

### Required Software
1. **Python 3.8 or higher**
   - Check version: `python --version`
   - Download from: https://www.python.org/downloads/

2. **Git**
   - Check version: `git --version`
   - Download from: https://git-scm.com/downloads

3. **Code Editor**
   - Recommended: VS Code (https://code.visualstudio.com/)
   - Install Python extension in VS Code

### Recommended VS Code Extensions
- Python (Microsoft)
- Pylance (Microsoft)
- GitLens
- YAML

## Initial Setup

### 1. Clone the Repository
```bash
git clone https://github.com/MeridianAlgo/Apex-Analysis.git
cd Apex-Analysis
```

### 2. Create a Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

This installs all required packages:
- yfinance (stock data)
- pandas (data manipulation)
- matplotlib (plotting)
- nltk (sentiment analysis)
- feedparser (RSS feeds)
- beautifulsoup4 (web scraping)
- colorama (colored terminal output)
- tqdm (progress bars)

### 4. Test the Installation
```bash
python main.py
```

Try analyzing a stock:
- Enter: `AAPL`
- Wait for it to complete
- Check `reports/AAPL/` for generated files

## Project Structure Quick Reference

```
Apex-Analysis/
├── src/           # All source code goes here
├── tests/         # All test files go here
├── docs/          # All documentation goes here
├── reports/       # Generated reports (auto-created, gitignored)
├── main.py        # Run this to start the program
└── tasks.md       # Your task assignments
```

## Common Commands

### Running the Program
```bash
python main.py
```

### Running Tests
```bash
# Install pytest first
pip install pytest

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run a specific test file
pytest tests/test_aggregate.py
```

### Git Workflow
```bash
# Create a new branch for your work
git checkout -b intern-advanced-features-v1.3

# Check what files you've changed
git status

# Add files to commit
git add src/utils.py
# Or add all changed files:
git add .

# Commit your changes
git commit -m "Add auto-cleanup of old reports"

# Push to GitHub
git push origin intern-advanced-features-v1.3

# Pull latest changes from main
git checkout main
git pull origin main
```

## Understanding the Code Flow

### How Analysis Works
1. **User runs** `main.py`
2. **main.py calls** `src/ui.py` (user interface)
3. **ui.py calls** `src/aggregator.py` (orchestrates everything)
4. **aggregator.py calls**:
   - `src/fetch_data.py` → Gets stock prices
   - `src/news_processor.py` → Gets news articles
   - `src/sentiment_analyzer.py` → Analyzes sentiment
5. **Results saved** to `reports/TICKER/`

### Key Files to Understand
- **src/aggregator.py**: The "brain" - coordinates everything
- **src/fetch_data.py**: Gets data from Yahoo Finance API
- **src/ui.py**: What the user sees and interacts with
- **src/utils.py**: Helper functions used everywhere

## Debugging Tips

### Print Debugging
```python
# Add print statements to see what's happening
print(f"DEBUG: ticker = {ticker}")
print(f"DEBUG: dataframe shape = {df.shape}")
print(f"DEBUG: columns = {df.columns.tolist()}")
```

### Using Python Debugger
```python
# Add this line where you want to pause
import pdb; pdb.set_trace()

# When it pauses, you can:
# - Type variable names to see their values
# - Type 'n' to go to next line
# - Type 'c' to continue
# - Type 'q' to quit
```

### Common Errors and Solutions

**Error: "ModuleNotFoundError: No module named 'X'"**
- Solution: `pip install X`
- Or: Make sure your virtual environment is activated

**Error: "No data found for ticker"**
- Solution: Check if ticker is valid on Yahoo Finance
- Try a different ticker like AAPL or MSFT

**Error: "Permission denied" when deleting files**
- Solution: Close any programs that have the files open (Excel, etc.)

**Error: "Import error" after moving files**
- Solution: Check your import statements match the new file locations

## Testing Your Changes

### Before Committing
1. **Run the program**: `python main.py`
2. **Test with multiple tickers**: AAPL, MSFT, NVDA
3. **Check generated files**: Look in `reports/`
4. **Run tests**: `pytest tests/`
5. **Check for errors**: Read any error messages carefully

### What to Test
- ✅ Program runs without crashing
- ✅ Reports are generated correctly
- ✅ CSV files can be opened in Excel
- ✅ PNG images display correctly
- ✅ Error messages are helpful
- ✅ Progress bars show up
- ✅ Colors display in terminal

## Getting Help

### When You're Stuck
1. **Read the error message** carefully - it usually tells you what's wrong
2. **Google the error** - add "python" to your search
3. **Check Stack Overflow** - someone probably had the same issue
4. **Look at similar code** in the project - see how it's done elsewhere
5. **Ask Ishaan** - text with:
   - What you're trying to do
   - What error you're getting
   - What you've already tried

### Useful Resources
- Python docs: https://docs.python.org/3/
- Pandas docs: https://pandas.pydata.org/docs/
- Stack Overflow: https://stackoverflow.com/
- Real Python tutorials: https://realpython.com/

## Task #3 Checklist

Before you start Task #3, make sure:
- [ ] You can run `python main.py` successfully
- [ ] You understand the project structure
- [ ] You've read through the existing code
- [ ] Your virtual environment is activated
- [ ] You've created your feature branch
- [ ] You've read `tasks.md` completely

## Tips for Success

1. **Work in small steps** - Don't try to do everything at once
2. **Test frequently** - Run the program after each change
3. **Commit often** - Small commits are better than big ones
4. **Read error messages** - They're trying to help you!
5. **Ask questions** - Better to ask than to be stuck for hours
6. **Take breaks** - Fresh eyes catch more bugs
7. **Document as you go** - Add comments explaining tricky parts

## Next Steps

1. Read `tasks.md` - Your task assignments
2. Read `docs/PROJECT_STRUCTURE.md` - Understand the organization
3. Start with Task #3, Step 1 - Auto-delete old reports
4. Work through each step carefully
5. Test everything thoroughly
6. Create your PR when done

Good luck! You've got this! 🚀

---

Questions? Text Ishaan M
Last updated: 2025-11-09
