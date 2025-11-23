# Risk Management Approach

Risk management in Apex Analysis combines statistical measures with deterministic guardrails exposed via `/api/v1/risk/<ticker>` and the dashboard.

## Core Metrics
- **Value at Risk (VaR)**: parametric and historical methods at 95% and 99% confidence (`RiskMetrics.calculate_var`).
- **Conditional VaR (CVaR)**: expected shortfall beyond the VaR threshold (`calculate_cvar`).
- **Drawdowns**: max/current drawdown from the equity curve.
- **Volatility**: annualized standard deviation of returns.
- **Sharpe / Sortino**: risk-adjusted performance across full sample.

## Process
1. Fetch ticker history for the requested period.
2. Compute log/percent returns, drop NaNs.
3. Generate a synthetic equity curve (baseline 100k) to visualize drawdowns.
4. Run calculations listed above and return JSON to the UI/API.

## Operational Guardrails
- **Position Sizing**: integrate `RiskManager` to cap exposure per trade based on volatility and configurable stop levels.
- **Alerting**: pair with the front-end alert system to raise warnings when VaR or drawdown exceeds thresholds.
- **Scenario Testing**: extend metrics with stress scenarios (e.g., ±5σ shocks) for portfolios.

## Extensibility
- Plug in alternative distributions (e.g., Cornish-Fisher) when modeling fat tails.
- Add portfolio-level metrics by aggregating correlated tickers before running stats.
- Export risk snapshots via the Data Export card or `/api/v1/risk` for audit trails.

Follow these steps to deliver consistent risk insights across API, UI, and automation.
