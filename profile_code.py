import cProfile
import pstats
import io
from pathlib import Path
import sys

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.aggregator import aggregate_analysis, calculate_sentiment_metrics, _analyze_single_ticker
from src.technical_analysis import add_all_indicators
from src.sentiment_analyzer import batch_analyze, SentimentAnalyzer
import pandas as pd
import numpy as np


def profile_technical_analysis():
    print("\n" + "="*60)
    print("PROFILING: Technical Analysis")
    print("="*60)

    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
    sample_data = pd.DataFrame({
        'Close': np.random.randn(len(dates)).cumsum() + 100,
        'High': np.random.randn(len(dates)).cumsum() + 102,
        'Low': np.random.randn(len(dates)).cumsum() + 98,
        'Volume': np.random.randint(1000000, 10000000, len(dates)),
        'Open': np.random.randn(len(dates)).cumsum() + 99,
    }, index=dates)

    profiler = cProfile.Profile()
    profiler.enable()

    result = add_all_indicators(sample_data)

    profiler.disable()

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)
    print(s.getvalue())

    return profiler


def profile_sentiment_analysis():
    print("\n" + "="*60)
    print("PROFILING: Sentiment Analysis")
    print("="*60)

    sample_articles = []
    for i in range(100):
        sample_articles.append({
            'title': f'Stock {i % 10} shows strong growth and positive momentum in market rally',
            'content': 'The stock market experienced significant gains today with strong buying pressure. Analysts are optimistic about future growth potential. Earnings beat expectations and revenue increased substantially.',
            'date': '2024-01-01',
            'source': 'Test Source'
    })

    profiler = cProfile.Profile()
    profiler.enable()

    result = batch_analyze(sample_articles)

    profiler.disable()

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)
    print(s.getvalue())

    return profiler


def profile_sentiment_metrics():
    print("\n" + "="*60)
    print("PROFILING: Sentiment Metrics Calculation")
    print("="*60)

    sample_rows = []
    for i in range(1000):
        sample_rows.append({
            'sentiment': np.random.uniform(-1, 1),
            'sentiment_keywords': ['growth', 'positive', 'momentum'] if i % 2 == 0 else ['decline', 'negative']
    })

    profiler = cProfile.Profile()
    profiler.enable()

    for _ in range(10):
        result = calculate_sentiment_metrics(sample_rows)

    profiler.disable()

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)
    print(s.getvalue())

    return profiler


def save_profile_results():
    print("\n" + "="*80)
    print("APEX ANALYSIS PERFORMANCE PROFILING")
    print("="*80)

    profiles = {
        'technical_analysis': profile_technical_analysis(),
        'sentiment_analysis': profile_sentiment_analysis(),
        'sentiment_metrics': profile_sentiment_metrics(),
    }

    report_path = Path('profile_results.txt')
    with open(report_path, 'w') as f:
        f.write("="*80 + "\n")
        f.write("APEX ANALYSIS - DETAILED PERFORMANCE PROFILE\n")
        f.write("="*80 + "\n\n")

        for name, profiler in profiles.items():
            f.write(f"\n{'='*80}\n")
            f.write(f"{name.upper().replace('_', ' ')}\n")
            f.write(f"{'='*80}\n\n")

            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(30)
            f.write(s.getvalue())
            f.write("\n\n")

    print(f"\n✓ Detailed profile results saved to: {report_path}")
    print("\nTop optimization opportunities will be identified in the next step.")


if __name__ == '__main__':
    save_profile_results()
