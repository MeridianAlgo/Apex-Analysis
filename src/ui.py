import os
import sys
import time
import itertools

import matplotlib.pyplot as plt
import pandas as pd
from colorama import Fore, Back, Style, init
from tqdm import tqdm

from src.aggregator import aggregate_analysis
from src.utils import logger, cleanup_company_reports, save_plot
from src.config import PLOT_FIGSIZE

# Initialize colorama (needed for Windows)
init(autoreset=True)


def print_logo():
    """Display the Apex Analysis ASCII logo"""
    logo = f"""
{Fore.CYAN}╔═══════════════════════════════════════════╗
║                                           ║
║     {Fore.YELLOW}█████╗ ██████╗ ███████╗██╗  ██╗{Fore.CYAN}     ║
║    {Fore.YELLOW}██╔══██╗██╔══██╗██╔════╝╚██╗██╔╝{Fore.CYAN}     ║
║    {Fore.YELLOW}███████║██████╔╝█████╗   ╚███╔╝{Fore.CYAN}      ║
║    {Fore.YELLOW}██╔══██║██╔═══╝ ██╔══╝   ██╔██╗{Fore.CYAN}      ║
║    {Fore.YELLOW}██║  ██║██║     ███████╗██╔╝ ██╗{Fore.CYAN}     ║
║    {Fore.YELLOW}╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝{Fore.CYAN}     ║
║                                           ║
║        {Fore.GREEN}Stock Analysis & AI Training{Fore.CYAN}        ║
║              {Fore.WHITE}MeridianAlgo 2025{Fore.CYAN}              ║
║                                           ║
╚═══════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(logo)


BANNER = f"""
{Fore.CYAN}{'='*50}
{Fore.YELLOW}Enter one or more tickers (e.g. AAPL or GOOGL,AAPL)
{Fore.WHITE}Type 'help' for commands, 'quit' or 'exit' to close
{Fore.CYAN}{'='*50}{Style.RESET_ALL}
"""


def _clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def _print_header():
    print_logo()
    print(BANNER)


def print_success(message):
    """Print a success message in green"""
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def print_error(message):
    """Print an error message in red"""
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")


def print_warning(message):
    """Print a warning message in yellow"""
    print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


def print_info(message):
    """Print an info message in cyan"""
    print(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}")


def print_header_section(message):
    """Print a section header"""
    print(f"\n{Fore.MAGENTA}{'='*50}")
    print(f"{Fore.MAGENTA}{message.center(50)}")
    print(f"{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}\n")


def handle_error(error_type, ticker=None):
    """Display helpful error messages with suggestions"""
    
    error_messages = {
        'invalid_ticker': f"""
{Fore.RED}✗ Invalid ticker symbol: {ticker}{Style.RESET_ALL}

{Fore.YELLOW}Suggestions:{Style.RESET_ALL}
• Make sure the ticker is correct (e.g., AAPL, MSFT, GOOGL)
• Check if the company is publicly traded
• Try searching on Yahoo Finance first

{Fore.CYAN}Common tickers:{Style.RESET_ALL}
• AAPL (Apple)
• MSFT (Microsoft)
• GOOGL (Google)
• TSLA (Tesla)
• NVDA (NVIDIA)
""",
        
        'no_data': f"""
{Fore.RED}✗ No data available for {ticker}{Style.RESET_ALL}

{Fore.YELLOW}Possible reasons:{Style.RESET_ALL}
• The ticker might be delisted
• Market might be closed
• API rate limit reached (wait a few minutes)

{Fore.CYAN}What to do:{Style.RESET_ALL}
• Try a different ticker
• Check your internet connection
• Wait 5 minutes and try again
""",
        
        'network_error': f"""
{Fore.RED}✗ Network connection error{Style.RESET_ALL}

{Fore.YELLOW}Troubleshooting:{Style.RESET_ALL}
• Check your internet connection
• Try again in a few moments
• Check if Yahoo Finance is accessible
"""
    }
    
    print(error_messages.get(error_type, f"{Fore.RED}An error occurred{Style.RESET_ALL}"))


def _print_help():
    print(f"""
{Fore.CYAN}Commands:{Style.RESET_ALL}
  {Fore.GREEN}help{Style.RESET_ALL}        Show this message
  {Fore.GREEN}clear{Style.RESET_ALL}       Clear the screen
  {Fore.GREEN}quit/exit{Style.RESET_ALL}   Exit the application

{Fore.CYAN}Examples:{Style.RESET_ALL}
  {Fore.YELLOW}AAPL{Style.RESET_ALL}
  {Fore.YELLOW}MSFT{Style.RESET_ALL}
  {Fore.YELLOW}GOOGL,AAPL{Style.RESET_ALL}
""")


def _print_ticker_summary(ticker, data):
    print(f"\n{Fore.CYAN}" + "=" * 60 + Style.RESET_ALL)
    print(f"{Fore.YELLOW}[{ticker}]{Style.RESET_ALL}")

    err = data.get("error")
    if err:
        print_error(f"Error: {err}")
        print(f"{Fore.CYAN}" + "=" * 60 + Style.RESET_ALL)
        return

    price_df = data.get("price_df")
    if not isinstance(price_df, pd.DataFrame):
        price_df = pd.DataFrame(data.get("price_data") or [])

    news = data.get("news") or []
    sentiment = data.get("sentiment_summary") or {}
    saved = data.get("saved_files") or []

    if not price_df.empty:
        print(f"  {Fore.GREEN}Price points:{Style.RESET_ALL} {len(price_df)}")
    else:
        print(f"  {Fore.RED}Price points:{Style.RESET_ALL} 0")

    print(f"  {Fore.GREEN}News articles analyzed:{Style.RESET_ALL} {len(news)}")

    if sentiment:
        avg = sentiment.get("average", 0.0)
        color = Fore.GREEN if avg > 0 else Fore.RED if avg < 0 else Fore.YELLOW
        print(f"  {Fore.GREEN}Avg sentiment:{Style.RESET_ALL} {color}{avg:.3f}{Style.RESET_ALL}")
    else:
        print(f"  {Fore.YELLOW}Avg sentiment:{Style.RESET_ALL} n/a")

    if isinstance(news, pd.DataFrame):
        rows = news.to_dict(orient="records")
    else:
        rows = news

    if rows:
        print(f"  {Fore.CYAN}Headlines:{Style.RESET_ALL}")
        for i, art in enumerate(rows[:3], 1):
            title = art.get("title") or ""
            print(f"    {Fore.WHITE}{i}.{Style.RESET_ALL} {title[:100]}")
    else:
        print_warning("  No recent news used for sentiment.")

    if saved:
        print(f"  {Fore.CYAN}Files:{Style.RESET_ALL}")
        for p in saved:
            print(f"    {Fore.GREEN}-{Style.RESET_ALL} {p}")

    print(f"{Fore.CYAN}" + "=" * 60 + Style.RESET_ALL)



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
        print_info(f"Analyzing {tickers_input}...")

        try:
            symbols = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
            
            # Cleanup old reports with progress bar
            print_info("Cleaning up old reports...")
            for t in tqdm(symbols, desc="Cleanup", colour="yellow"):
                try:
                    cleanup_company_reports(t)
                except Exception:
                    logger.exception("Failed to cleanup reports for %s", t)

            # Run analysis with progress indication
            print_info("Fetching and analyzing data...")
            done = False
            results = {}

            def _run():
                nonlocal results, done
                results = aggregate_analysis(tickers_input)
                done = True

            import threading

            thread = threading.Thread(target=_run, daemon=True)
            thread.start()

            # Show spinner while processing
            spinner = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
            while not done and thread.is_alive():
                sys.stdout.write(f"\r{Fore.CYAN}{next(spinner)} Processing...{Style.RESET_ALL}")
                sys.stdout.flush()
                time.sleep(0.1)

            sys.stdout.write("\r" + " " * 40 + "\r")
            sys.stdout.flush()

            if not isinstance(results, dict):
                print_error("Unexpected result from analysis. Check logs.")
                continue

            # Generate reports with progress bar
            print_info("Generating reports...")
            for t in tqdm(symbols, desc="Reports", colour="green"):
                data = results.get(t)
                if not data:
                    print_error(f"{t}: no result (see logs).")
                    continue

                generate_report(t, data)
                _print_ticker_summary(t, data)
                if not data.get("error"):
                    print_success(f"Report for {t} saved successfully!")
                else:
                    print_error(f"Report for {t} had errors.")
        except Exception as e:
            logger.error("Unexpected error in CLI loop: %s", e, exc_info=True)
            print_error(f"Unexpected error: {e}")
            handle_error('network_error')
        finally:
            plt.close("all")
