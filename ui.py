import os
import datetime as dt
import matplotlib.pyplot as plt
from aggregator import aggregate_analysis
from utils import logger
from config import SAVE_PLOTS, REPORTS_DIR

def _ensure_reports_dir():
    if SAVE_PLOTS and not os.path.isdir(REPORTS_DIR):
        os.makedirs(REPORTS_DIR, exist_ok=True)

def _save_fig(name_prefix: str):
    if not SAVE_PLOTS:
        return
    _ensure_reports_dir()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(REPORTS_DIR, f"{name_prefix}-{stamp}.png")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    logger.info(f"Saved plot: {path}")

def run_cli():
    while True:
        ticker = input("Enter stock ticker (e.g., AAPL) or 'quit' to exit: ").strip().upper()
        if ticker == 'QUIT':
            break
        analysis = aggregate_analysis(ticker)
        if not analysis:
            print("Failed to analyze ticker.")
            continue

        print("\nApex Analysis Report:")
        print(analysis['report_df'].to_string(index=False))

        print("\nStock Info (key fields):")
        info = analysis['stock_data'].get('info', {}) or {}
        for key in ['longName', 'sector', 'industry', 'marketCap', 'beta', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow']:
            if key in info:
                print(f"  {key}: {info.get(key)}")

        
        history = analysis['stock_data'].get('history')
        if history is not None and not history.empty:
            plt.figure(figsize=(10, 5))
            plt.plot(history.index, history['Close'], label='Close Price')
            if 'MA50' in history.columns:
                plt.plot(history.index, history['MA50'], label='50-Day MA')
            plt.title(f"{ticker} Price Trend")
            plt.xlabel('Date')
            plt.ylabel('Price')
            plt.legend()
            _save_fig(f"{ticker}-price")
            plt.show()

        
        if analysis['news']:
            dates = [a['date'] for a in analysis['news']]
            sents = [a['sentiment'] for a in analysis['news']]
            plt.figure(figsize=(10, 5))
            plt.bar(dates, sents, width=0.5)
            plt.title(f"{ticker} News Sentiment Over Time")
            plt.xlabel('Date')
            plt.ylabel('Sentiment Score')
            _save_fig(f"{ticker}-sentiment")
            plt.show()

        out_csv = f"{ticker}_report.csv"
        analysis['report_df'].to_csv(out_csv, index=False)
        logger.info(f"Report saved to {out_csv}")
