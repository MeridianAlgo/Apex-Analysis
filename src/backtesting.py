"""
Event-Driven Backtesting Framework

Implements:
- Event-driven backtesting engine
- Performance metrics (Sharpe, Sortino, Calmar ratios)
- Walk-forward optimization
- Transaction cost modeling
- Portfolio tracking
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from datetime import datetime

from src.utils import logger


@dataclass
class Trade:
    """Individual trade record"""
    date: datetime
    symbol: str
    action: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    commission: float = 0.0

    @property
    def value(self) -> float:
        return self.quantity * self.price + self.commission


@dataclass
class Position:
    """Current position in a symbol"""
    symbol: str
    quantity: int
    avg_price: float

    @property
    def value(self) -> float:
        return self.quantity * self.avg_price

    def update(self, quantity: int, price: float):
        """Update position with new trade"""
        total_value = self.value + (quantity * price)
        self.quantity += quantity
        if self.quantity != 0:
            self.avg_price = total_value / self.quantity


class Portfolio:
    """Portfolio state tracker"""

    def __init__(self, initial_capital: float = 100000.0, commission: float = 0.001):
        """
        Args:
            initial_capital: Starting cash
            commission: Commission per trade (0.001 = 0.1%)
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_rate = commission
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []

    def execute_trade(self, date: datetime, symbol: str, action: str, quantity: int, price: float) -> bool:
        """Execute a trade"""
        commission = abs(quantity * price * self.commission_rate)

        if action == 'BUY':
            cost = quantity * price + commission
            if cost > self.cash:
                logger.warning(f"Insufficient cash for {symbol}: need {cost:.2f}, have {self.cash:.2f}")
                return False

            self.cash -= cost

            if symbol in self.positions:
                self.positions[symbol].update(quantity, price)
            else:
                self.positions[symbol] = Position(symbol, quantity, price)

        elif action == 'SELL':
            if symbol not in self.positions or self.positions[symbol].quantity < quantity:
                logger.warning(f"Insufficient shares of {symbol}")
                return False

            proceeds = quantity * price - commission
            self.cash += proceeds

            self.positions[symbol].update(-quantity, price)

            # Remove position if fully sold
            if self.positions[symbol].quantity == 0:
                del self.positions[symbol]

        # Record trade
        trade = Trade(date, symbol, action, quantity, price, commission)
        self.trades.append(trade)

        return True

    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """Get total portfolio value"""
        positions_value = sum(
            pos.quantity * current_prices.get(pos.symbol, pos.avg_price)
            for pos in self.positions.values()
        )
        return self.cash + positions_value

    def record_equity(self, date: datetime, current_prices: Dict[str, float]):
        """Record equity curve point"""
        total_value = self.get_total_value(current_prices)

        self.equity_curve.append({
            'date': date,
            'total_value': total_value,
            'cash': self.cash,
            'positions_value': total_value - self.cash,
            'returns': (total_value - self.initial_capital) / self.initial_capital
        })

    def get_equity_curve(self) -> pd.DataFrame:
        """Get equity curve as DataFrame"""
        return pd.DataFrame(self.equity_curve)


class Backtester:
    """Event-driven backtesting engine"""

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.001
    ):
        """
        Args:
            initial_capital: Starting capital
            commission: Commission rate (0.001 = 0.1%)
            slippage: Slippage per trade (0.001 = 0.1%)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.portfolio = None
        self.results = None

    def run(
        self,
        data: pd.DataFrame,
        strategy: Callable,
        **strategy_params
    ) -> Dict:
        """
        Run backtest

        Args:
            data: Price data with OHLCV columns
            strategy: Strategy function that returns signals
            strategy_params: Parameters for strategy

        Returns:
            Backtest results dictionary
        """
        self.portfolio = Portfolio(self.initial_capital, self.commission)

        # Generate signals
        signals = strategy(data, **strategy_params)

        # Execute trades
        for date, row in data.iterrows():
            signal = signals.loc[date] if date in signals.index else 0

            current_prices = {'stock': row['Close']}

            if signal > 0:  # Buy signal
                # Buy with available cash
                shares = int(self.portfolio.cash / (row['Close'] * (1 + self.slippage)))
                if shares > 0:
                    price = row['Close'] * (1 + self.slippage)
                    self.portfolio.execute_trade(date, 'stock', 'BUY', shares, price)

            elif signal < 0:  # Sell signal
                # Sell all shares
                if 'stock' in self.portfolio.positions:
                    shares = self.portfolio.positions['stock'].quantity
                    price = row['Close'] * (1 - self.slippage)
                    self.portfolio.execute_trade(date, 'stock', 'SELL', shares, price)

            # Record equity
            self.portfolio.record_equity(date, current_prices)

        # Calculate metrics
        self.results = self._calculate_metrics()

        return self.results

    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        equity_curve = self.portfolio.get_equity_curve()

        if equity_curve.empty:
            return {}

        # Returns
        equity_curve['daily_returns'] = equity_curve['total_value'].pct_change()

        # Total return
        total_return = (equity_curve['total_value'].iloc[-1] - self.initial_capital) / self.initial_capital

        # Annualized return
        days = len(equity_curve)
        years = days / 252  # Trading days
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        # Volatility
        volatility = equity_curve['daily_returns'].std() * np.sqrt(252)

        # Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0

        # Sortino ratio (downside deviation)
        downside_returns = equity_curve['daily_returns'][equity_curve['daily_returns'] < 0]
        downside_std = downside_returns.std() * np.sqrt(252)
        sortino_ratio = annualized_return / downside_std if downside_std > 0 else 0

        # Max drawdown
        cumulative = (1 + equity_curve['daily_returns']).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # Calmar ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Win rate
        trades = self.portfolio.trades
        winning_trades = sum(1 for t in trades[1::2] if len(trades) > 1)  # Simplified
        win_rate = winning_trades / (len(trades) / 2) if len(trades) > 1 else 0

        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'final_value': equity_curve['total_value'].iloc[-1],
            'equity_curve': equity_curve
        }

    def get_summary(self) -> str:
        """Get formatted summary"""
        if not self.results:
            return "No backtest results available"

        summary = f"""
Backtest Results
{'='*50}
Initial Capital:     ${self.initial_capital:,.2f}
Final Value:         ${self.results['final_value']:,.2f}
Total Return:        {self.results['total_return']*100:.2f}%
Annualized Return:   {self.results['annualized_return']*100:.2f}%

Risk Metrics
{'='*50}
Volatility:          {self.results['volatility']*100:.2f}%
Max Drawdown:        {self.results['max_drawdown']*100:.2f}%
Sharpe Ratio:        {self.results['sharpe_ratio']:.2f}
Sortino Ratio:       {self.results['sortino_ratio']:.2f}
Calmar Ratio:        {self.results['calmar_ratio']:.2f}

Trading Activity
{'='*50}
Total Trades:        {self.results['total_trades']}
Win Rate:            {self.results['win_rate']*100:.1f}%
        """

        return summary


class WalkForwardOptimizer:
    """Walk-forward optimization for strategy parameters"""

    def __init__(
        self,
        train_periods: int = 252,
        test_periods: int = 63,
        step_size: int = 21
    ):
        """
        Args:
            train_periods: Training window size (252 = 1 year)
            test_periods: Test window size (63 = 3 months)
            step_size: Step size for rolling window (21 = 1 month)
        """
        self.train_periods = train_periods
        self.test_periods = test_periods
        self.step_size = step_size

    def optimize(
        self,
        data: pd.DataFrame,
        strategy: Callable,
        param_grid: Dict,
        metric: str = 'sharpe_ratio'
    ) -> Dict:
        """
        Perform walk-forward optimization

        Args:
            data: Price data
            strategy: Strategy function
            param_grid: Parameter ranges to test
            metric: Metric to optimize ('sharpe_ratio', 'total_return', etc.)

        Returns:
            Optimization results
        """
        results = []

        total_length = len(data)
        start_idx = 0

        while start_idx + self.train_periods + self.test_periods <= total_length:
            # Define windows
            train_end = start_idx + self.train_periods
            test_end = train_end + self.test_periods

            train_data = data.iloc[start_idx:train_end]
            test_data = data.iloc[train_end:test_end]

            # Optimize on training data
            best_params = self._optimize_window(train_data, strategy, param_grid, metric)

            # Test on out-of-sample data
            bt = Backtester()
            test_results = bt.run(test_data, strategy, **best_params)

            results.append({
                'train_start': data.index[start_idx],
                'train_end': data.index[train_end - 1],
                'test_start': data.index[train_end],
                'test_end': data.index[test_end - 1],
                'best_params': best_params,
                'test_performance': test_results.get(metric, 0)
            })

            logger.info(f"Walk-forward window complete: {metric}={test_results.get(metric, 0):.3f}")

            # Move forward
            start_idx += self.step_size

        return {
            'windows': results,
            'avg_performance': np.mean([r['test_performance'] for r in results]),
            'std_performance': np.std([r['test_performance'] for r in results])
        }

    def _optimize_window(
        self,
        data: pd.DataFrame,
        strategy: Callable,
        param_grid: Dict,
        metric: str
    ) -> Dict:
        """Optimize parameters on a single window"""
        from itertools import product

        # Generate parameter combinations
        keys = param_grid.keys()
        values = param_grid.values()
        combinations = [dict(zip(keys, v)) for v in product(*values)]

        best_score = -np.inf
        best_params = {}

        for params in combinations:
            bt = Backtester()
            results = bt.run(data, strategy, **params)
            score = results.get(metric, -np.inf)

            if score > best_score:
                best_score = score
                best_params = params

        return best_params
