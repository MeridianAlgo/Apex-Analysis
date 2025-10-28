# Apex Analysis

A comprehensive stock analysis tool that combines price data with news sentiment analysis to provide insights into stock performance.
# Apex Analysis

Apex Analysis is a command-line stock analysis tool that combines historical price data with news sentiment analysis and generates automated reports (CSV, JSON and PNG visualizations).

This README contains a full project overview, a complete file tree, setup and run instructions, where to find generated reports, configuration details, and links to every important file in the repository.

## Quick start

1. Clone the repository and change into it:

```bash
git clone <repo-url> apex-analysis
cd apex-analysis
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app (interactive CLI):

```bash
python main.py
```

Type a ticker symbol (for example `NVDA`, `AAPL`) and press Enter. The program will fetch price and news data, analyze sentiment, and save results in the `reports/` folder.

You can also run the package as a module:

```bash
python -m src
```

## Where reports are saved

Reports are saved under the repository root `reports/<TICKER>/`. The following file types are produced:

- CSV: price and sentiment data (e.g. `NVDA_price_data_YYYYMMDD_HHMMSS.csv`)
- JSON: structured exports and summaries (e.g. `NVDA_summary_...json`)
- PNG: visualizations (e.g. `NVDA_NVDA_analysis_...png`, `NVDA_NVDA_sentiment_...png`)

Example path inside this repo: `reports/NVDA/NVDA_price_data_2025...csv`.

## Full repository file tree

Below is the complete project structure (top-level and `src/`):

```
/ (repo root)
├── LICENSE
├── README.md
├── main.py
├── pyproject.toml
├── requirements.txt
├── setup.py
├── __init__.py
├── apex_analysis.egg-info/
├── reports/                # generated output (created at runtime)
├── cache/                  # runtime cache (may be empty)
├── test_aggregate.py       # small helper test (dev)
├── test_save_png.py        # small helper test (dev)
└── src/
      ├── __init__.py
      ├── __main__.py
      ├── aggregator.py         # orchestrates fetching, analysis & report saving
      ├── config.py             # central configuration (paths, plot settings)
      ├── fetch_data.py         # price/history fetching (yfinance)
      ├── news_processor.py     # RSS fetcher & article scraper
      ├── sentiment_analyzer.py # sentiment scoring, VADER/TextBlob
      ├── ui.py                 # command-line interface + plot generation
      ├── utils.py              # helper functions (save_plot, save_dataframe, logging)
      └── reports/              # legacy folder inside src (not used; canonical is repo-root/reports)
```

Files of interest and where to find them
- `src/config.py` — central location for `REPORTS_DIR`, `PLOT_DPI`, `SAVE_PLOTS`, and other settings.
- `src/aggregator.py` — main logic that fetches price and news, runs sentiment analysis and writes JSON/CSV results. It now attaches pandas DataFrames (`price_history`, `sentiment_data`) to the returned result so `ui.generate_report()` can create PNGs.
- `src/ui.py` — builds matplotlib figures and saves PNGs to `reports/<TICKER>/` (calls internal helpers but could be refactored to use `utils.save_plot()` centrally).
- `src/utils.py` — central helper functions for file I/O and logging; uses `REPORTS_DIR` from `src/config.py` to ensure all files are written to the same place.
- `src/fetch_data.py` — handles yfinance calls and prepares the `history` DataFrame used for plotting.
- `src/news_processor.py` — fetches RSS feeds and scrapes article content when allowed (respects robots.txt by default).
- `src/sentiment_analyzer.py` — analyzes article text using NLTK VADER and TextBlob and returns scores used in plots and reports.

## How it works (high level)

1. User enters a ticker in the CLI (`ui.run_cli`).
2. `aggregator.aggregate_analysis()` fetches price data via `fetch_data`, fetches news via `news_processor`, then runs `sentiment_analyzer.batch_analyze()`.
3. Aggregator saves CSV/JSON outputs to `reports/<TICKER>/` and attaches DataFrames to its return value.
4. `ui.generate_report()` builds plots from `price_history` and `sentiment_data` (if present) and saves PNGs to the same directory.

## Configuring behavior

Open `src/config.py` to change behavior. Important options:

- `REPORTS_DIR` — path where reports are written (default: repo root `reports/`).
- `PLOT_DPI`, `PLOT_FIGSIZE`, `PLOT_STYLE` — Matplotlib settings for saved figures.
- `SAVE_PLOTS` — whether to save PNGs (if False, PNG saving will be skipped where respected).
- `RESPECT_ROBOTS` — respect `robots.txt` when scraping articles (recommended True).

To change the reports path, edit `REPORTS_DIR` in `src/config.py`. The code will create the directory automatically.

## Running non-interactively (examples)

Generate a single analysis run for `NVDA` and exit:

```bash
printf "NVDA\nquit\n" | python3 main.py
```

Run the aggregator directly from a script (useful for automation):

```python
from src.aggregator import aggregate_analysis
res = aggregate_analysis('NVDA')
print(res['saved_files'])
```

## Tests & dev helpers

There are two small helper scripts used during development:

- `test_save_png.py` — small script that uses `src.utils.save_plot()` to verify PNG saving.
- `test_aggregate.py` — runs `aggregate_analysis('TEST')` to exercise the main flow.

These are convenience scripts and not full unit tests. If you want, we can convert them to pytest tests and add a CI workflow.

## Troubleshooting

- If nothing appears in `reports/<TICKER>/`:
   - Verify `src/config.py:REPORTS_DIR` points to the expected path.
   - Check log messages (stdout/stderr) for exceptions printed by `src.utils.logger`.
   - Ensure dependencies are installed (`pip install -r requirements.txt`).

- If PNGs are not produced but CSV/JSON are:
   - Make sure `aggregate_analysis` returned `price_history` and/or `sentiment_data` DataFrames (these are required for plotting).
   - Check `src/ui.py` to confirm `generate_report()` is being called.

## Contributing

1. Fork the repo and create a branch for your changes.
2. Run and verify the app locally.
3. Open a PR with a clear description and any relevant screenshots or logs.

If you'd like, I can add:
- a pytest-based test that asserts PNG files are created for a known ticker (smoke test),
- a GitHub Actions workflow to run basic tests on push,
- or unify plot saving to use `src.utils.save_plot()` only (less duplication).

## License

This project is distributed under the MIT License — see `LICENSE` for details.

## Contact

If you have questions or want help extending the project, open an issue or PR in the repository.

## Credits

This project was originally designed, completed, and tested by Richard Zhu and was later co-edited by Ishaan Manoor, Tanish Patel, and Dennis Talpa. 

## About MeridianAlgo

This repository is maintained under the MeridianAlgo initiative. MeridianAlgo focuses on algorithmic research and applied data science in finance and related fields. For inquiries, collaborations, or support, contact:

- Email: meridianaglo@gmail.com
- Website: https://meridianalgo.org

MeridianAlgo provides educational resources and prototypes; this project is provided for educational and research use.

## Project policies and contributors

- See `CONTRIBUTORS.md` for a full list of contributors, contribution guidelines, and acknowledgements.
- See `SECURITY.md` for the project's security and vulnerability disclosure policy.

Both files are included at the repository root and linked here for quick access.

### Quick links to important files

Below are direct links to the key source files used by this project. Click the filename to jump to the file in the repository viewer.

- [main.py](main.py) — application entry point
- [src/config.py](src/config.py) — central config and paths
- [src/aggregator.py](src/aggregator.py) — coordinates data fetching, analysis, and saving
- [src/fetch_data.py](src/fetch_data.py) — price/history fetching (yfinance)
- [src/news_processor.py](src/news_processor.py) — RSS and article scraping
- [src/sentiment_analyzer.py](src/sentiment_analyzer.py) — sentiment scoring logic
- [src/ui.py](src/ui.py) — CLI UI and plotting
- [src/utils.py](src/utils.py) — helper functions for saving/loading and logging
- [CONTRIBUTORS.md](CONTRIBUTORS.md) — contributor list & contribution guidelines
- [SECURITY.md](SECURITY.md) — vulnerability disclosure policy


