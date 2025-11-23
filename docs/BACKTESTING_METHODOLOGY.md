# Backtesting Methodology

The `src/backtesting.Backtester` class powers strategy evaluations across the UI and REST API. This document describes the methodology so results remain auditable.

## Data Handling
- Use split-adjusted close prices from `fetch_stock_data()`.
- Apply indicator functions before running the simulation to avoid re-computation in the loop.
- Drop rows with incomplete indicators to prevent look-ahead bias.

## Strategy Interface
```python
def strategy(dataframe):
    signals = pd.Series(0, index=dataframe.index)
    signals[dataframe['SMA_20'] > dataframe['SMA_50']] = 1
    signals[dataframe['SMA_20'] < dataframe['SMA_50']] = -1
    return signals
```
- Return `1` for long, `-1` for short, `0` for flat.
- The Backtester will translate positions into trades and PnL.

## Evaluation Metrics
- **Total Return / CAGR**: growth of the equity curve.
- **Sharpe / Sortino**: risk-adjusted returns using daily log returns.
- **Max Drawdown & Depth**: computed via `RiskMetrics.get_drawdown_stats()`.
- **Win Rate / Trade Count**: basic hit ratios.

## Advanced Modes
- **Walk-forward**: run `Backtester.walk_forward()` with rolling windows for robustness.
- **Transaction Costs**: set `Backtester(transaction_cost=0.0005)` to simulate fees/slippage.
- **Position sizing**: plug `RiskManager` callbacks to scale trade sizes based on volatility or Kelly fractions.

## Reporting
- Persist equity curves + trades to `cache/backtests/{strategy}_{timestamp}.parquet`.
- Surface summary JSON to the API/UI for visualization (Plotly equity curve + stats table).
- Log metadata (strategy name, params, sample start/end, data source) for reproducibility.

By standardizing on this pipeline, strategy comparisons remain fair and traceable.
