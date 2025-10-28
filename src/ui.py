import os
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import sys
import time
import json

from src.aggregator import aggregate_analysis
from src.utils import (
    logger, 
    cleanup_company_reports,
    save_plot,
    save_dataframe
)
from src.config import (
    REPORTS_DIR, 
    PLOT_STYLE, 
    PLOT_FIGSIZE,
    PLOT_DPI
)

def _ensure_reports_dir(ticker: str) -> Path:
    """Ensure the reports directory exists and return its path."""
    try:
        # Ensure REPORTS_DIR is a Path object
        reports_path = Path(REPORTS_DIR) if isinstance(REPORTS_DIR, str) else REPORTS_DIR
        
        # Create reports directory if it doesn't exist
        reports_path.mkdir(parents=True, exist_ok=True)
        
        # Create company-specific subdirectory
        company_dir = reports_path / ticker.upper()
        company_dir.mkdir(parents=True, exist_ok=True)
        
        return company_dir
    except Exception as e:
        logger.error(f"Error ensuring reports directory exists: {e}")
        fallback_path = Path(REPORTS_DIR) if isinstance(REPORTS_DIR, str) else REPORTS_DIR
        return fallback_path / ticker.upper()  # Fallback path

def _save_plot(fig, filename: str, ticker: str) -> Optional[Path]:
    """Save a plot to the company's report directory."""
    try:
        # Ensure the directory exists
        company_dir = _ensure_reports_dir(ticker)
        
        # Generate file path with timestamp to avoid overwriting
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ticker}_{filename}_{timestamp}.png"
        filepath = company_dir / filename
        
        # Save the plot
        fig.savefig(filepath, dpi=PLOT_DPI, bbox_inches='tight')
        logger.info(f"Saved plot to {filepath}")
        
        # Save report as JSON
        report_path = company_dir / f"{ticker}_report_{timestamp}.json"
        with open(report_path, 'w') as f:
            json.dump({'report': 'generated'}, f, indent=2)
        logger.info(f"Saved report to {report_path}")
        
        # Save analysis results as CSV
        if 'report_df' in locals() and report_df is not None:
            csv_path = company_dir / f"{ticker}_analysis_{timestamp}.csv"
            try:
                report_df.to_csv(csv_path, index=False)
                logger.info(f"Saved analysis to {csv_path}")
            except Exception as e:
                logger.error(f"Error saving analysis CSV: {e}")
        
        # Save any additional data as needed
        if 'additional_data' in locals():
            try:
                data_path = company_dir / f"{ticker}_data_{timestamp}.json"
                with open(data_path, 'w') as f:
                    json.dump(additional_data, f, indent=2)
            except Exception as e:
                logger.error(f"Error saving additional data: {e}")
        plt.close(fig)
        return filepath
    except Exception as e:
        logger.error(f"Error saving plot {filename}: {e}", exc_info=True)
        return None

def generate_report(ticker: str, data: dict) -> dict:
    """Generate and save analysis reports."""
    # Initialize report
    report = {
        'ticker': ticker,
        'timestamp': dt.datetime.now().strftime("%Y%m%d_%H%M%S"),
        'saved_files': []
    }
    
    try:
        # Ensure the reports directory exists
        company_dir = _ensure_reports_dir(ticker)
        
        # Clean up any existing reports for this ticker
        cleanup_company_reports(ticker)
        
        # Create price chart
        if 'price_history' in data and not data['price_history'].empty:
            # Create a figure with subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
            
            # Plot price data on the first subplot
            data['price_history']['Close'].plot(ax=ax1, label='Close Price', color='tab:blue')
            if 'MA50' in data['price_history'].columns:
                data['price_history']['MA50'].plot(ax=ax1, label='50-day MA', color='tab:orange', linestyle='--')
            
            ax1.set_title(f"{ticker} Stock Price Analysis")
            ax1.set_ylabel('Price ($)', color='tab:blue')
            ax1.legend(loc='upper left')
            ax1.grid(True, linestyle='--', alpha=0.7)
            
            # Add volume as a bar chart on the second subplot if available
            if 'Volume' in data['price_history'].columns:
                ax2.bar(data['price_history'].index, 
                       data['price_history']['Volume'], 
                       color='tab:green', 
                       alpha=0.3)
                ax2.set_ylabel('Volume', color='tab:green')
                ax2.grid(True, linestyle='--', alpha=0.3)
            
            plt.tight_layout()
            
            # Save the combined plot
            plot_path = _save_plot(fig, f"{ticker}_analysis", ticker)
            if plot_path:
                report['saved_files'].append(str(plot_path))
            
            # Save the price data as CSV
            csv_path = save_dataframe(data['price_history'], f"{ticker}_price_data", ticker)
            if csv_path:
                report['saved_files'].append(str(csv_path))
        
        # Add sentiment analysis if available
        if 'sentiment_data' in data and not data['sentiment_data'].empty:
            # Create sentiment plot
            fig, ax = plt.subplots(figsize=(12, 4))
            data['sentiment_data'].plot(ax=ax, kind='bar', color='tab:purple', alpha=0.7)
            ax.set_title(f"{ticker} Sentiment Analysis")
            ax.set_xlabel('Date')
            ax.set_ylabel('Sentiment Score')
            ax.grid(True, linestyle='--', alpha=0.3)
            plt.tight_layout()
            
            # Save sentiment plot
            sent_path = _save_plot(fig, f"{ticker}_sentiment", ticker)
            if sent_path:
                report['saved_files'].append(str(sent_path))
            
            # Save sentiment data as CSV
            sent_csv_path = save_dataframe(data['sentiment_data'], f"{ticker}_sentiment_data", ticker)
            if sent_csv_path:
                report['saved_files'].append(str(sent_csv_path))
        
        logger.info(f"Generated {len(report['saved_files'])} report files for {ticker}")
        
    except Exception as e:
        logger.error(f"Error generating report for {ticker}: {e}", exc_info=True)
        report['error'] = str(e)
    
    return report

def _print_header():
    """Print the application header."""
    print("""
==================================================
               APEX STOCK ANALYSIS               
==================================================\033[0m
\033[1mEnter a stock ticker (e.g., AAPL, MSFT, GOOGL) to analyze
Type 'help' for commands, 'quit' or 'exit' to close\033[0m
""")

def _print_help():
    """Print help information."""
    print("""
\033[1mAvailable Commands:
  help     - Show this help message
  exit/quit - Exit the application
  clear    - Clear the screen
  list     - List recently analyzed stocks (coming soon)

Examples:
  AAPL     - Analyze Apple Inc.
  MSFT     - Analyze Microsoft
  GOOGL    - Analyze Alphabet (Google)
  AMZN     - Analyze Amazon
  TSLA     - Analyze Tesla\033[0m
""")

def _clear_screen():
    """Clear the terminal screen."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def _print_stock_info(ticker: str, result: dict):
    """Print stock information."""
    stock_data = result.get('stock_data', {})
    info = stock_data.get('info', {})
    
    print(f"\n\033[1;34m{'='*50}\033[0m")
    print(f"\033[1;36m{'APEX ANALYSIS REPORT':^50}\033[0m")
    print(f"\033[1;34m{'='*50}\033[0m\n")
    
    if 'error' in result and result['error']:
        print(f"\033[1;31mError: {result['error']}\033[0m\n")
        return
    
    # Basic stock info
    print(f"\033[1mStock:\033[0m {ticker.upper()}")
    if info:
        print(f"\033[1mCompany:\033[0m {info.get('longName', 'N/A')}")
        print(f"\033[1mSector:\033[0m {info.get('sector', 'N/A')}")
        print(f"\033[1mIndustry:\033[0m {info.get('industry', 'N/A')}")
        print(f"\033[1mCurrent Price:\033[0m ${info.get('currentPrice', 'N/A')}")
        print(f"\033[1mMarket Cap:\033[0m ${info.get('marketCap', 'N/A'):,}")
    
    # Analysis results
    print("\n\033[1mAnalysis Results:\033[0m")
    if 'report_df' in result and not result['report_df'].empty:
        print("\n" + str(result['report_df']))
    
    # News summary
    if 'news' in result and result['news']:
        print(f"\n\033[1mLatest News Headlines ({min(3, len(result['news']))} of {len(result['news'])}):\033[0m")
        for i, article in enumerate(result['news'][:3], 1):
            print(f"{i}. {article.get('title', 'No title')}")
    else:
        print("\n\033[1mNo recent news found.\033[0m")
    
    print("\n\033[1;34m" + "="*50 + "\033[0m\n")

def run_cli():
    """Run the command line interface."""
    from datetime import datetime
    
    _clear_screen()
    _print_header()
    
    while True:
        try:
            user_input = input("\n\033[1mEnter stock ticker or command: ").strip()
            
            # Handle commands
            if not user_input:
                continue
                
            if user_input.lower() in ('quit', 'exit'):
                print("\nThank you for using Apex Analysis. Goodbye!")
                break
                
            if user_input.lower() == 'help':
                _print_help()
                continue
                
            if user_input.lower() == 'clear':
                _clear_screen()
                _print_header()
                continue
            
            ticker = user_input.upper()
            print("\n\033[1;33m" + "="*50)
            print(f"ANALYZING {ticker} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*50 + "\033[0m\n")
            
            # Show a simple spinner while processing
            import itertools
            import sys
            import time
            
            spinner = itertools.cycle(['-', '/', '|', '\\'])
            start_time = time.time()
            
            # Start analysis in a separate thread
            from threading import Thread
            
            result = {}
            def analyze():
                nonlocal result
                result = aggregate_analysis(ticker)
            
            thread = Thread(target=analyze)
            thread.start()
            
            # Show spinner while processing
            while thread.is_alive():
                sys.stdout.write(f"\rProcessing {next(spinner)}  ")
                sys.stdout.flush()
                time.sleep(0.1)
                if time.time() - start_time > 30:  # 30 second timeout
                    print("\n\n\033[1;31mAnalysis is taking longer than expected. Please wait...\033[0m")
                    start_time = time.time()  # Reset timer
            
            # Clear spinner
            sys.stdout.write("\r" + " "*50 + "\r")
            
            # Print results
            _print_stock_info(ticker, result)
            
            # Save report if analysis was successful
            if 'error' not in result or not result['error']:
                try:
                    generate_report(ticker, result)
                    print("\033[1;32m✓ Report saved successfully!\033[0m")
                except Exception as e:
                    logger.error(f"Error generating report: {e}", exc_info=True)
                    print("\033[1;33m⚠ Could not save report. Check logs for details.\033[0m")
            
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            break
            
        except Exception as e:
            logger.error(f"Unexpected error in CLI: {e}", exc_info=True)
            print(f"\n\033[1;31mAn unexpected error occurred: {e}\033[0m")
            print("Please check the logs for more details or try again later.")
            logger.error(f"Error in main loop: {str(e)}", exc_info=True)
            print(f"\nAn error occurred: {str(e)}")
            print("Please try again or check the logs for more details.")
            
        finally:
            plt.close('all')  # Ensure all plots are closed
