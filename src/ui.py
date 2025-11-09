import os
import sys
import time
import itertools

import matplotlib.pyplot as plt
import pandas as pd

from src.aggregator import aggregate_analysis
from src.utils import logger, cleanup_company_reports, save_plot
from src.config import PLOT_FIGSIZE


BANNER = r"""
==================================================
                 APEX ANALYSIS CLI
==================================================
Enter one or more tickers (e.g. AAPL or GOOGL,AAPL)
Type 'help' for commands, 'quit' or 'exit' to close
"""


def _clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def _print_header():
    print(BANNER)


def _print_help():
    print(
        """
Commands:
  help        Show this message
  clear       Clear the screen
  quit/exit   Exit the application

Examples:
  AAPL
  MSFT
  GOOGL,AAPL
"""
    )


def _print_ticker_summary(ticker, data):
    print("\n" + "=" * 60)
    print(f"[{ticker}]")

    err = data.get("error")
    if err:
        print(f"  Error: {err}")
        print("=" * 60)
        return

    price_df = data.get("price_df")
    if not isinstance(price_df, pd.DataFrame):
        price_df = pd.DataFrame(data.get("price_data") or [])

    news = data.get("news") or []
    sentiment = data.get("sentiment_summary") or {}
    saved = data.get("saved_files") or []

    if not price_df.empty:
        print(f"  Price points: {len(price_df)}")
    else:
        print("  Price points: 0")

    print(f"  News articles analyzed: {len(news)}")

    if sentiment:
        avg = sentiment.get("average", 0.0)
        print(f"  Avg sentiment: {avg:.3f}")
    else:
        print("  Avg sentiment: n/a")

    if isinstance(news, pd.DataFrame):
        rows = news.to_dict(orient="records")
    else:
        rows = news

    if rows:
        print("  Headlines:")
        for i, art in enumerate(rows[:3], 1):
            title = art.get("title") or ""
            print(f"    {i}. {title[:100]}")
    else:
        print("  No recent news used for sentiment.")

    if saved:
        print("  Files:")
        for p in saved:
            print(f"    - {p}")

    print("=" * 60)



def generate_report(ticker, data):
    t = ticker.upper()
    price_df = data.get("price_df")
    if price_df is None and data.get("price_data"):
        price_df = pd.DataFrame(data["price_data"])
    if price_df is None:
        price_df = pd.DataFrame()

    sent_df = data.get("sentiment_df")
    if sent_df is None and data.get("news"):
        rows = []
        for a in data["news"]:
            ts = a.get("date") or a.get("published") or a.get("analysis_timestamp")
            rows.append(
                {
                    "date": ts,
                    "sentiment": a.get("sentiment", 0.0),
                }
            )
        if rows:
            sent_df = pd.DataFrame(rows)
            sent_df["date"] = pd.to_datetime(sent_df["date"], errors="coerce")
            if sent_df["date"].notna().any():
                sent_df = sent_df.set_index("date").sort_index()
        else:
            sent_df = pd.DataFrame()
    if sent_df is None:
        sent_df = pd.DataFrame()

    if price_df.empty and sent_df.empty:
        return

    if "Date" in price_df.columns:
        price_df = price_df.set_index("Date")
    if not isinstance(price_df.index, pd.DatetimeIndex):
        try:
            price_df.index = pd.to_datetime(price_df.index)
        except Exception:
            pass

    if not sent_df.empty and not isinstance(sent_df.index, pd.DatetimeIndex):
        if "date" in sent_df.columns:
            sent_df = sent_df.set_index("date")
            try:
                sent_df.index = pd.to_datetime(sent_df.index)
            except Exception:
                pass

    if not sent_df.empty and "sentiment" not in sent_df.columns and "compound" in sent_df.columns:
        sent_df["sentiment"] = sent_df["compound"]

    has_sentiment = not sent_df.empty and "sentiment" in sent_df.columns

    if has_sentiment:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=PLOT_FIGSIZE, sharex=True)
    else:
        fig, ax1 = plt.subplots(1, 1, figsize=PLOT_FIGSIZE)
        ax2 = None

    if not price_df.empty and "Close" in price_df.columns:
        ax1.plot(price_df.index, price_df["Close"])
        ax1.set_ylabel("Price")
        ax1.set_title(f"{t} Price & Sentiment")
        ax1.grid(True, alpha=0.3)

    if has_sentiment and ax2 is not None:
        s = sent_df["sentiment"]
        ax2.plot(s.index, s, marker="o", linestyle="-")
        ax2.axhline(0.0, linestyle="--", linewidth=0.7)
        ax2.set_ylabel("Sentiment")
        ax2.grid(True, alpha=0.3)

    fig.autofmt_xdate()
    path = save_plot(f"{t}_analysis", t, fig)
    data.setdefault("saved_files", []).append(str(path))


def run_cli():
    _clear_screen()
    _print_header()

    while True:
        try:
            raw = input("Enter ticker(s) or command: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not raw:
            continue

        cmd = raw.lower()
        if cmd in ("quit", "exit"):
            print("Goodbye.")
            break
        if cmd == "help":
            _print_help()
            continue
        if cmd == "clear":
            _clear_screen()
            _print_header()
            continue

        tickers_input = raw
        print(f"\nAnalyzing {tickers_input} ...\n")

        try:
            symbols = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
            for t in symbols:
                try:
                    cleanup_company_reports(t)
                except Exception:
                    logger.exception("Failed to cleanup reports for %s", t)

            spinner = itertools.cycle(["-", "\\", "|", "/"])
            done = False
            results = {}

            def _run():
                nonlocal results, done
                results = aggregate_analysis(tickers_input)
                done = True

            import threading

            thread = threading.Thread(target=_run, daemon=True)
            thread.start()

            while not done and thread.is_alive():
                sys.stdout.write("\rProcessing " + next(spinner))
                sys.stdout.flush()
                time.sleep(0.1)

            sys.stdout.write("\r" + " " * 40 + "\r")
            sys.stdout.flush()

            if not isinstance(results, dict):
                print("Unexpected result from analysis. Check logs.")
                continue

            for t in symbols:
                data = results.get(t)
                if not data:
                    print(f"\n{t}: no result (see logs).")
                    continue

                generate_report(t, data)
                _print_ticker_summary(t, data)
                if not data.get("error"):
                    print(f"Report for {t} saved.")
                else:
                    print(f"Report for {t} had errors.")
        except Exception as e:
            logger.error("Unexpected error in CLI loop: %s", e, exc_info=True)
            print(f"Error: {e}")
        finally:
            plt.close("all")
