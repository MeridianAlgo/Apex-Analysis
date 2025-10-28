### Task Assignment: Enhance and Deploy Apex Analysis (Intern Task #2)

**Hello Richard,**

Welcome to your second task with MeridianAlgo! Building on your first task (where you set up the basic project structure for Apex Analysis), this one focuses on **improving the codebase and README** based on recent feedback. The goal is to make Apex Analysis more robust, user-friendly, and production-ready. This will involve code enhancements, testing, and documentation—great practice for modular Python development.

By the end of this, you'll have:
- A refactored codebase with better error handling, caching, and configuration.
- An updated README that's more scannable and engaging.
- Passing tests and a GitHub PR ready for review.

**Estimated Time:** 6-8 hours (spread over 2-3 days). 

**Why this task?** Apex Analysis is a core prototype for our stock sentiment tools. Polishing it now sets a strong foundation for future ML integrations (like the PyTorch framework we discussed last week).

---

#### **Prerequisites**
Before starting:
1. Ensure you have:
   - Python 3.8+ installed (use `python --version` to check).
   - Git installed and configured (with your GitHub account).
   - A code editor like VS Code (with Python and YAML extensions).
2. Clone the repo if you haven't:
   ```bash
   git clone https://github.com/MeridianAlgo/Apex-Analysis.git  
   cd apex-analysis
   git pull origin main
   ```
3. Create a feature branch:
   ```bash
   git checkout -b intern-enhance-v1.1
   git push origin intern-enhance-v1.1
   ```
   (This keeps your work isolated.)

If anything's missing, ping me ASAP.

---

#### **Step 1: Review Current State (30-45 mins)**
Get familiar with the baseline:
1. **Run the existing code:**
   - Install deps: `pip install -r requirements.txt`
   - Run interactively: `python main.py`
     - Enter `NVDA` as ticker. Check if reports generate in `reports/NVDA/` (CSV, JSON, PNGs).
   - Run non-interactively: `printf "AAPL\nquit\n" | python main.py`
   - Note any issues (e.g., errors, missing files) in your log.
2. **Read key files:**
   - Skim the README.md for overview.
   - Review `src/` modules: Focus on `aggregator.py` (main flow), `utils.py` (helpers), and `ui.py` (CLI/plots).
   - Check `test_aggregate.py` and `test_save_png.py`—run them manually.

---

#### **Step 2: Update Dependencies and Config (45-60 mins)**
Make the project more maintainable.
1. **Enhance requirements.txt:**
   
3. **Switch to YAML config:**
   - Create `src/config.yaml` with this content (new file):
     ```yaml
     reports_dir: ./reports
     plot_dpi: 300
     plot_figsize: [12, 8]
     save_plots: true
     respect_robots: true
     news_sources:
       - url: https://feeds.finance.yahoo.com/rss/2.0/headline
         name: Yahoo Finance
       - url: https://rss.cnn.com/rss/money_latest.rss  # Add more as needed
         name: CNN Money
     cache_ttl_days: 1
     days_back_price: 30
     days_back_news: 7
     ```
   - Update `src/config.py` to load it:
     ```python
     import os
     import yaml
     from pathlib import Path

     CONFIG_FILE = Path(__file__).parent / 'config.yaml'

     def load_config():
         if not CONFIG_FILE.exists():
             raise FileNotFoundError("Create src/config.yaml with defaults.")
         with open(CONFIG_FILE, 'r') as f:
             return yaml.safe_load(f)

     config = load_config()  # Global for simplicity
     ```
   - Test: In a Python shell (`python`), run `from src.config import config; print(config['plot_dpi'])`—should output 300.
   - Commit: `git add src/config* && git commit -m "Migrate config to YAML for easier editing"`

**Tip:** If YAML parsing fails, check indentation (use 2 spaces).

---

#### **Step 3: Refactor Core Modules (2-3 hours)**
Implement key enhancements one file at a time. Use the provided code snippets as templates—copy, paste, and adapt. Test after each file.

1. **Update src/utils.py (Add logging, saving, retries):**
   - Replace with the enhanced version (includes `logging`, `save_dataframe`, `save_plot`, `@retry` decorator, `@lru_cache`).
   - Test: Run `python -c "from src.utils import save_plot; print('OK')"` (won't save but imports).

2. **Enhance src/fetch_data.py (Retries & caching):**
   - Add the `@retry` and cache key.
   - Test: `python -c "from src.fetch_data import fetch_price_history; df = fetch_price_history('NVDA'); print(df.shape)"`—should fetch ~30 rows.

3. **Improve src/news_processor.py (Multi-source, robots.txt):**
   - Use BeautifulSoup for scraping (import in file).
   - Limit to 10 articles/source.
   - Test: `python -c "from src.news_processor import fetch_news; df = fetch_news('AAPL'); print(len(df))"`—expect 5-20 rows.

4. **Refine src/sentiment_analyzer.py (Batch averaging):**
   - Keep simple; ensure NLTK download is quiet.
   - Test: Create a dummy DF `pd.DataFrame({'summary': ['Great stock!']})` and run `batch_analyze`—score should be positive (~0.5+).

5. **Overhaul src/aggregator.py (Batch support, merging):**
   - Handle list of tickers; attach DFs to results.
   - Use new utils for saving.
   - Test: `python -c "from src.aggregator import aggregate_analysis; res = aggregate_analysis(['NVDA']); print(res['saved_files'])"`—should list 2 files.

6. **Polish src/ui.py (CLI loop, plots):**
   - Add `generate_report` using Matplotlib (price + sentiment subplots).
   - Support batch in CLI (e.g., comma-separated input).
   - Test full flow: Run `python main.py`, enter `GOOGL,AAPL`, check PNGs.

After each change:
- Run `python main.py` end-to-end.
- Fix errors (e.g., import issues) and log them.
- Commit per file: `git add src/[file].py && git commit -m "Enhance [file]: Add retries/caching"`

**Pro Tip:** Use `black` or any color for formatting (`pip install black; black src/`) and `flake8` for linting (`pip install flake8; flake8 src/`).

---

#### **Step 4: Add/Convert Tests (45-60 mins)**
Shift from helper scripts to proper tests.
1. **Create tests/ directory and __init__.py.**
2. **Convert helpers to pytest:**
   - Rename `test_aggregate.py` and `test_save_png.py` to `test_aggregator.py` and `test_utils.py`.
   - Update to use `@pytest.fixture` and `assert` (use the sample from Grok's review).
   - Add a smoke test: Verify PNG creation for 'AAPL'.
3. **Run tests:** `pytest tests/ -v --tb=short`
   - Aim for 100% pass; fix failures.
4. **Commit:** `git add tests/ && git commit -m "Add pytest suite with coverage"`

(Optional extension: Install `pytest-cov` and run `pytest --cov=src/` for a report—share screenshot.)

---

#### **Step 5: Revise README.md (45-60 mins)**
Make it shine based on feedback.
1. **Apply structure:**
   - Add badges (Python, MIT) at top.
   - Merge intro; add TOC.
   - Use tables for reports/config.
   - Shorten sections; add emojis.
   - Include your changes (e.g., "New: YAML config and batch mode").
2. **Test rendering:** Preview on GitHub (commit a draft first).
3. **Commit:** `git add README.md && git commit -m "Polish README: Add TOC, tables, badges"`

---

#### **Step 6: Finalize and Submit (30 mins)**
1. **Full smoke test:**
   - Run for 2-3 tickers (e.g., NVDA, TSLA).
   - Verify outputs: CSVs load in Excel, PNGs plot correctly, no crashes.
2. **Push and PR:**
   ```bash
   git push origin intern-enhance-v1.1
   ```
   - Create PR on GitHub: Title "Intern Task #2: Enhance Apex with robustness & polish".
   - Description: Link your log, summarize changes (e.g., "Added retries, YAML, tests—see diff"), add screenshots of a generated report.
   - Assign to me for review.
3. **Tag release:** After merge, `git tag v1.1 && git push --tags`.

**What if stuck?** 
- Check logs (now in utils).
- Search Stack Overflow for errors (e.g., "yfinance empty dataframe").
- Message me with: Error message + file/line + what you tried.

**Success Metrics:**
- Code runs without errors for batch tickers.
- Tests pass 100%.
- PR merged within a week.

Great work on Task #1—this builds directly on it. Excited to see your enhancements! Questions? text me.

**Best,**  
Ishaan M
MeridianAlgo Lead  

---
