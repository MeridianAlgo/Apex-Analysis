"""
Demo: ML Models, Backtesting & Risk Management

Comprehensive demonstration of:
- Machine Learning models (Random Forest, XGBoost, Anomaly Detection)
- Backtesting framework with performance metrics
- Risk management (VaR, drawdowns, position sizing)
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from src.ml_models import TrendClassifier, AnomalyDetector, XGBOOST_AVAILABLE
if XGBOOST_AVAILABLE:
    from src.ml_models import XGBoostPredictor
from src.backtesting import Backtester, WalkForwardOptimizer
from src.risk_management import RiskMetrics, PositionSizer, RiskManager
from src.utils import logger


def create_sample_data(n_days: int = 500) -> pd.DataFrame:
    """Create realistic stock price data"""
    np.random.seed(42)

    dates = pd.date_range(start='2022-01-01', periods=n_days, freq='D')

    # Generate returns with trend and volatility
    trend = 0.0005
    volatility = 0.02
    returns = np.random.normal(trend, volatility, n_days)

    # Add some market regimes
    returns[100:150] += 0.01  # Bull market
    returns[300:350] -= 0.015  # Bear market

    # Generate OHLCV data
    close = 100 * np.exp(np.cumsum(returns))
    high = close * (1 + np.random.uniform(0, 0.02, n_days))
    low = close * (1 - np.random.uniform(0, 0.02, n_days))
    open_price = close * (1 + np.random.uniform(-0.01, 0.01, n_days))
    volume = np.random.randint(1000000, 10000000, n_days)

    df = pd.DataFrame({
        'Open': open_price,
        'High': high,
        'Low': low,
        'Close': close,
        'Volume': volume
    }, index=dates)

    return df


def demo_trend_classification():
    """Demo: Random Forest trend classification"""
    print("\n" + "="*70)
    print("DEMO: Random Forest Trend Classification")
    print("="*70)

    df = create_sample_data(500)

    # Train classifier
    clf = TrendClassifier(n_estimators=100)
    metrics = clf.train(df, forward_days=5, test_size=0.2)

    print(f"\nModel Performance:")
    print(f"  Train Accuracy: {metrics['train_accuracy']:.3f}")
    print(f"  Test Accuracy:  {metrics['test_accuracy']:.3f}")

    # Feature importance
    importance = clf.get_feature_importance()
    print(f"\nTop 5 Important Features:")
    for idx, row in importance.head(5).iterrows():
        print(f"  {row['feature']:20s}: {row['importance']:.4f}")

    # Make predictions
    predictions = clf.predict(df.tail(100))
    print(f"\nRecent Predictions (last 10 days):")
    labels = {0: 'Down', 1: 'Neutral', 2: 'Up'}
    for i, pred in enumerate(predictions[-10:]):
        print(f"  Day {i+1}: {labels[pred]}")


def demo_xgboost():
    """Demo: XGBoost for returns prediction"""
    print("\n" + "="*70)
    print("DEMO: XGBoost Returns Prediction")
    print("="*70)

    if not XGBOOST_AVAILABLE:
        print("\nXGBoost not available. Install with: pip install xgboost")
        print("Skipping XGBoost demo...")
        return

    df = create_sample_data(500)

    # Train XGBoost
    xgb_model = XGBoostPredictor(n_estimators=100, learning_rate=0.1)
    metrics = xgb_model.train(df, forward_days=1, test_size=0.2)

    print(f"\nModel Performance:")
    print(f"  Train R²: {metrics['train_r2']:.3f}")
    print(f"  Test R²:  {metrics['test_r2']:.3f}")

    # Feature importance
    importance = xgb_model.get_feature_importance()
    print(f"\nTop 5 Important Features:")
    for idx, row in importance.head(5).iterrows():
        print(f"  {row['feature']:20s}: {row['importance']:.4f}")


def demo_anomaly_detection():
    """Demo: Anomaly detection"""
    print("\n" + "="*70)
    print("DEMO: Anomaly Detection")
    print("="*70)

    df = create_sample_data(500)

    # Add some artificial anomalies
    df.loc[df.index[200], 'Close'] *= 1.10  # +10% spike
    df.loc[df.index[350], 'Close'] *= 0.85  # -15% drop

    # Fit detector
    detector = AnomalyDetector(contamination=0.05)
    detector.fit(df)

    # Detect anomalies
    anomalies = detector.get_anomalies(df, top_n=5)

    print(f"\nTop 5 Anomalous Days:")
    for idx, row in anomalies.iterrows():
        print(f"  {row['date'].strftime('%Y-%m-%d')}: "
              f"Return={row['returns']*100:+.2f}%, "
              f"Score={row['anomaly_score']:.3f}")


def simple_ma_crossover(data: pd.DataFrame, short_window: int = 20, long_window: int = 50):
    """Simple moving average crossover strategy"""
    signals = pd.Series(0, index=data.index)

    # Calculate moving averages
    short_ma = data['Close'].rolling(window=short_window).mean()
    long_ma = data['Close'].rolling(window=long_window).mean()

    # Generate signals
    signals[short_ma > long_ma] = 1   # Buy
    signals[short_ma < long_ma] = -1  # Sell

    return signals


def demo_backtesting():
    """Demo: Backtesting framework"""
    print("\n" + "="*70)
    print("DEMO: Backtesting Framework")
    print("="*70)

    df = create_sample_data(500)

    # Run backtest
    bt = Backtester(
        initial_capital=100000,
        commission=0.001,
        slippage=0.001
    )

    results = bt.run(df, simple_ma_crossover, short_window=20, long_window=50)

    print(bt.get_summary())


def demo_risk_metrics():
    """Demo: Risk metrics calculation"""
    print("\n" + "="*70)
    print("DEMO: Risk Metrics")
    print("="*70)

    df = create_sample_data(500)
    returns = df['Close'].pct_change().dropna()
    equity_curve = (1 + returns).cumprod() * 100000

    # Calculate VaR
    var_95 = RiskMetrics.calculate_var(returns, 0.95, 'historical')
    var_99 = RiskMetrics.calculate_var(returns, 0.99, 'historical')
    cvar_95 = RiskMetrics.calculate_cvar(returns, 0.95)

    print(f"\nValue at Risk:")
    print(f"  95% VaR:  {var_95:.2%}")
    print(f"  99% VaR:  {var_99:.2%}")
    print(f"  95% CVaR: {cvar_95:.2%}")

    # Drawdown analysis
    dd_stats = RiskMetrics.get_drawdown_stats(equity_curve)

    print(f"\nDrawdown Analysis:")
    print(f"  Max Drawdown:     {dd_stats['max_drawdown_pct']:.2f}%")
    print(f"  Current Drawdown: {dd_stats['current_drawdown']*100:.2f}%")
    print(f"  Avg Drawdown:     {dd_stats['avg_drawdown']*100:.2f}%")
    print(f"  # DD Periods:     {dd_stats['num_drawdown_periods']}")

    # Risk-adjusted returns
    risk_adj = RiskMetrics.calculate_risk_adjusted_returns(returns)

    print(f"\nRisk-Adjusted Metrics:")
    print(f"  Sharpe Ratio:  {risk_adj['sharpe_ratio']:.2f}")
    print(f"  Sortino Ratio: {risk_adj['sortino_ratio']:.2f}")
    print(f"  Calmar Ratio:  {risk_adj['calmar_ratio']:.2f}")


def demo_position_sizing():
    """Demo: Position sizing strategies"""
    print("\n" + "="*70)
    print("DEMO: Position Sizing Strategies")
    print("="*70)

    capital = 100000
    price = 150

    # Fixed fraction
    shares_fixed = PositionSizer.fixed_fraction(
        capital=capital,
        risk_per_trade=0.02,
        stop_loss_pct=0.05,
        price=price
    )

    print(f"\nFixed Fraction (2% risk, 5% stop):")
    print(f"  Shares: {shares_fixed}")
    print(f"  Position value: ${shares_fixed * price:,.2f}")
    print(f"  % of capital: {shares_fixed * price / capital * 100:.1f}%")

    # Kelly Criterion
    position_kelly = PositionSizer.kelly_criterion(
        win_rate=0.55,
        avg_win=0.10,
        avg_loss=0.05,
        capital=capital,
        fraction=0.25
    )

    print(f"\nKelly Criterion (quarter-Kelly):")
    print(f"  Position value: ${position_kelly:,.2f}")
    print(f"  % of capital: {position_kelly / capital * 100:.1f}%")

    # Volatility-based
    shares_vol = PositionSizer.volatility_based(
        capital=capital,
        target_volatility=0.15,
        realized_volatility=0.25,
        price=price
    )

    print(f"\nVolatility-Based (15% target vol):")
    print(f"  Shares: {shares_vol}")
    print(f"  Position value: ${shares_vol * price:,.2f}")
    print(f"  % of capital: {shares_vol * price / capital * 100:.1f}%")


def demo_risk_management():
    """Demo: Comprehensive risk management"""
    print("\n" + "="*70)
    print("DEMO: Risk Management System")
    print("="*70)

    df = create_sample_data(500)
    returns = df['Close'].pct_change().dropna()
    equity_curve = (1 + returns).cumprod() * 100000

    # Create risk manager
    risk_mgr = RiskManager(
        max_position_size=0.10,
        max_portfolio_var=0.02,
        max_drawdown=0.20
    )

    # Generate report
    report = risk_mgr.get_risk_report(returns, equity_curve, confidence=0.95)

    print(risk_mgr.format_risk_report(report))


def main():
    """Run all demonstrations"""
    print("\n" + "="*70)
    print("ML MODELS, BACKTESTING & RISK MANAGEMENT")
    print("="*70)

    demo_trend_classification()
    demo_xgboost()
    demo_anomaly_detection()
    demo_backtesting()
    demo_risk_metrics()
    demo_position_sizing()
    demo_risk_management()

    print("\n" + "="*70)
    print("All demonstrations complete!")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
