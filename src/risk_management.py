"""
Risk Management Module

Implements:
- Value at Risk (VaR) calculations
- Expected Shortfall (Conditional VaR)
- Position sizing strategies
- Drawdown analysis
- Risk-adjusted metrics
"""
import numpy as np
import pandas as pd
from typing import Optional, Dict, Tuple
from scipy import stats

from src.utils import logger


class RiskMetrics:
    """Calculate various risk metrics"""

    @staticmethod
    def calculate_var(
        returns: pd.Series,
        confidence_level: float = 0.95,
        method: str = 'historical'
    ) -> float:
        """
        Calculate Value at Risk

        Args:
            returns: Returns series
            confidence_level: Confidence level (0.95 = 95%)
            method: 'historical', 'parametric', or 'monte_carlo'

        Returns:
            VaR value (positive number)
        """
        if method == 'historical':
            return -np.percentile(returns.dropna(), (1 - confidence_level) * 100)

        elif method == 'parametric':
            mean = returns.mean()
            std = returns.std()
            z_score = stats.norm.ppf(1 - confidence_level)
            return -(mean + z_score * std)

        elif method == 'monte_carlo':
            # Monte Carlo simulation
            mean = returns.mean()
            std = returns.std()
            simulations = np.random.normal(mean, std, 10000)
            return -np.percentile(simulations, (1 - confidence_level) * 100)

        else:
            raise ValueError(f"Unknown method: {method}")

    @staticmethod
    def calculate_cvar(
        returns: pd.Series,
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall)

        Average loss beyond VaR threshold

        Args:
            returns: Returns series
            confidence_level: Confidence level

        Returns:
            CVaR value (positive number)
        """
        var = RiskMetrics.calculate_var(returns, confidence_level, 'historical')
        threshold = -var

        # Get returns worse than VaR
        tail_losses = returns[returns <= threshold]

        if len(tail_losses) == 0:
            return var

        return -tail_losses.mean()

    @staticmethod
    def calculate_drawdown(equity_curve: pd.Series) -> pd.DataFrame:
        """
        Calculate drawdown series

        Args:
            equity_curve: Equity curve series

        Returns:
            DataFrame with drawdown metrics
        """
        cumulative = equity_curve / equity_curve.iloc[0]
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        dd_df = pd.DataFrame({
            'equity': equity_curve,
            'cumulative': cumulative,
            'running_max': running_max,
            'drawdown': drawdown,
            'drawdown_pct': drawdown * 100
        })

        return dd_df

    @staticmethod
    def get_drawdown_stats(equity_curve: pd.Series) -> Dict:
        """Get drawdown statistics"""
        dd_df = RiskMetrics.calculate_drawdown(equity_curve)
        drawdown = dd_df['drawdown']

        # Find drawdown periods
        is_dd = (drawdown < 0).astype(bool)
        is_dd_shifted_back = is_dd.shift(-1).fillna(False).astype(bool)
        is_dd_shifted_forward = is_dd.shift(1).fillna(False).astype(bool)

        dd_starts = (~is_dd & is_dd_shifted_back)
        dd_ends = (is_dd & ~is_dd_shifted_back)

        drawdown_periods = []
        start_idx = None

        for i, is_start in enumerate(dd_starts):
            if is_start:
                start_idx = i
            elif dd_ends.iloc[i] and start_idx is not None:
                dd_period = drawdown.iloc[start_idx:i+1]
                drawdown_periods.append({
                    'start': dd_period.index[0],
                    'end': dd_period.index[-1],
                    'max_dd': dd_period.min(),
                    'duration': len(dd_period)
                })
                start_idx = None

        stats_dict = {
            'max_drawdown': drawdown.min(),
            'max_drawdown_pct': drawdown.min() * 100,
            'current_drawdown': drawdown.iloc[-1],
            'num_drawdown_periods': len(drawdown_periods),
            'avg_drawdown': np.mean([p['max_dd'] for p in drawdown_periods]) if drawdown_periods else 0,
            'avg_duration': np.mean([p['duration'] for p in drawdown_periods]) if drawdown_periods else 0,
            'drawdown_periods': drawdown_periods
        }

        return stats_dict

    @staticmethod
    def calculate_risk_adjusted_returns(
        returns: pd.Series,
        risk_free_rate: float = 0.02
    ) -> Dict:
        """
        Calculate risk-adjusted return metrics

        Args:
            returns: Returns series
            risk_free_rate: Annual risk-free rate

        Returns:
            Dictionary of metrics
        """
        # Annualize
        periods_per_year = 252  # Trading days
        mean_return = returns.mean() * periods_per_year
        std_return = returns.std() * np.sqrt(periods_per_year)

        # Sharpe Ratio
        sharpe = (mean_return - risk_free_rate) / std_return if std_return > 0 else 0

        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(periods_per_year)
        sortino = (mean_return - risk_free_rate) / downside_std if downside_std > 0 else 0

        # Calmar Ratio
        equity_curve = (1 + returns).cumprod()
        dd_stats = RiskMetrics.get_drawdown_stats(equity_curve)
        max_dd = abs(dd_stats['max_drawdown'])
        calmar = mean_return / max_dd if max_dd > 0 else 0

        return {
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'annualized_return': mean_return,
            'annualized_volatility': std_return,
            'max_drawdown': max_dd
        }


class PositionSizer:
    """Position sizing strategies"""

    @staticmethod
    def fixed_fraction(
        capital: float,
        risk_per_trade: float = 0.02,
        stop_loss_pct: float = 0.05,
        price: float = 100.0
    ) -> int:
        """
        Fixed fractional position sizing

        Args:
            capital: Available capital
            risk_per_trade: Risk per trade (0.02 = 2%)
            stop_loss_pct: Stop loss percentage
            price: Current price

        Returns:
            Number of shares
        """
        risk_amount = capital * risk_per_trade
        shares = int(risk_amount / (price * stop_loss_pct))
        return max(shares, 0)

    @staticmethod
    def kelly_criterion(
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        capital: float,
        fraction: float = 0.25
    ) -> float:
        """
        Kelly Criterion position sizing

        Args:
            win_rate: Historical win rate
            avg_win: Average winning return
            avg_loss: Average losing return (positive)
            capital: Available capital
            fraction: Fraction of Kelly to use (0.25 = quarter-Kelly)

        Returns:
            Position size in dollars
        """
        if avg_loss == 0:
            return 0

        b = avg_win / avg_loss  # Win/loss ratio
        p = win_rate  # Probability of win
        q = 1 - p  # Probability of loss

        kelly_pct = (b * p - q) / b

        # Use fractional Kelly for safety
        kelly_pct = max(min(kelly_pct * fraction, 1.0), 0.0)

        return capital * kelly_pct

    @staticmethod
    def volatility_based(
        capital: float,
        target_volatility: float = 0.15,
        realized_volatility: float = 0.20,
        price: float = 100.0
    ) -> int:
        """
        Volatility-based position sizing

        Args:
            capital: Available capital
            target_volatility: Target portfolio volatility
            realized_volatility: Stock's realized volatility
            price: Current price

        Returns:
            Number of shares
        """
        if realized_volatility == 0:
            return 0

        position_value = capital * (target_volatility / realized_volatility)
        shares = int(position_value / price)

        return max(shares, 0)

    @staticmethod
    def risk_parity(
        capital: float,
        volatilities: Dict[str, float],
        prices: Dict[str, float]
    ) -> Dict[str, int]:
        """
        Risk parity allocation across multiple assets

        Args:
            capital: Total capital
            volatilities: Dict of asset volatilities
            prices: Dict of asset prices

        Returns:
            Dict of share quantities per asset
        """
        # Inverse volatility weights
        inv_vols = {k: 1/v if v > 0 else 0 for k, v in volatilities.items()}
        total_inv_vol = sum(inv_vols.values())

        if total_inv_vol == 0:
            return {k: 0 for k in prices.keys()}

        # Normalize weights
        weights = {k: v/total_inv_vol for k, v in inv_vols.items()}

        # Calculate shares
        shares = {}
        for asset, weight in weights.items():
            position_value = capital * weight
            shares[asset] = int(position_value / prices[asset])

        return shares


class RiskManager:
    """Comprehensive risk management"""

    def __init__(
        self,
        max_position_size: float = 0.1,
        max_portfolio_var: float = 0.02,
        max_drawdown: float = 0.20
    ):
        """
        Args:
            max_position_size: Max position as fraction of portfolio (0.1 = 10%)
            max_portfolio_var: Max daily VaR (0.02 = 2%)
            max_drawdown: Max acceptable drawdown (0.20 = 20%)
        """
        self.max_position_size = max_position_size
        self.max_portfolio_var = max_portfolio_var
        self.max_drawdown = max_drawdown

    def check_position_limits(
        self,
        position_value: float,
        portfolio_value: float
    ) -> bool:
        """Check if position size is within limits"""
        position_fraction = position_value / portfolio_value

        if position_fraction > self.max_position_size:
            logger.warning(f"Position size {position_fraction:.1%} exceeds limit {self.max_position_size:.1%}")
            return False

        return True

    def check_var_limit(
        self,
        portfolio_returns: pd.Series,
        confidence: float = 0.95
    ) -> bool:
        """Check if portfolio VaR is within limits"""
        var = RiskMetrics.calculate_var(portfolio_returns, confidence)

        if var > self.max_portfolio_var:
            logger.warning(f"Portfolio VaR {var:.2%} exceeds limit {self.max_portfolio_var:.2%}")
            return False

        return True

    def check_drawdown_limit(self, equity_curve: pd.Series) -> bool:
        """Check if drawdown is within limits"""
        dd_stats = RiskMetrics.get_drawdown_stats(equity_curve)
        current_dd = abs(dd_stats['current_drawdown'])

        if current_dd > self.max_drawdown:
            logger.warning(f"Current drawdown {current_dd:.2%} exceeds limit {self.max_drawdown:.2%}")
            return False

        return True

    def get_risk_report(
        self,
        returns: pd.Series,
        equity_curve: pd.Series,
        confidence: float = 0.95
    ) -> Dict:
        """Generate comprehensive risk report"""
        # VaR metrics
        var_historical = RiskMetrics.calculate_var(returns, confidence, 'historical')
        var_parametric = RiskMetrics.calculate_var(returns, confidence, 'parametric')
        cvar = RiskMetrics.calculate_cvar(returns, confidence)

        # Drawdown analysis
        dd_stats = RiskMetrics.get_drawdown_stats(equity_curve)

        # Risk-adjusted returns
        risk_adjusted = RiskMetrics.calculate_risk_adjusted_returns(returns)

        report = {
            'var_95_historical': var_historical,
            'var_95_parametric': var_parametric,
            'cvar_95': cvar,
            'max_drawdown': dd_stats['max_drawdown'],
            'current_drawdown': dd_stats['current_drawdown'],
            'avg_drawdown': dd_stats['avg_drawdown'],
            'num_drawdown_periods': dd_stats['num_drawdown_periods'],
            **risk_adjusted,
            'within_limits': {
                'var': var_historical <= self.max_portfolio_var,
                'drawdown': abs(dd_stats['current_drawdown']) <= self.max_drawdown
            }
        }

        return report

    def format_risk_report(self, report: Dict) -> str:
        """Format risk report as string"""
        output = f"""
Risk Management Report
{'='*60}

Value at Risk (95% confidence)
    Historical VaR:        {report['var_95_historical']:.2%}
    Parametric VaR:        {report['var_95_parametric']:.2%}
    Expected Shortfall:    {report['cvar_95']:.2%}

Drawdown Analysis
    Max Drawdown:          {report['max_drawdown']:.2%}
    Current Drawdown:      {report['current_drawdown']:.2%}
    Avg Drawdown:          {report['avg_drawdown']:.2%}
    Drawdown Periods:      {report['num_drawdown_periods']}

Risk-Adjusted Returns
    Sharpe Ratio:          {report['sharpe_ratio']:.2f}
    Sortino Ratio:         {report['sortino_ratio']:.2f}
    Calmar Ratio:          {report['calmar_ratio']:.2f}
    Ann. Return:           {report['annualized_return']:.2%}
    Ann. Volatility:       {report['annualized_volatility']:.2%}

Risk Limit Status
    VaR within limit:      {report['within_limits']['var']}
    DD within limit:       {report['within_limits']['drawdown']}
        """

        return output
