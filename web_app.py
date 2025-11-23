"""
Apex Analysis REST API with Authentication and Rate Limiting

Features:
- JWT authentication
- API key authentication
- Rate limiting
- API versioning (v1)
- Swagger/OpenAPI documentation
- CORS support
"""
from flask import Flask, render_template, jsonify, request
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flasgger import Swagger
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
from functools import wraps

from src.fetch_data import fetch_stock_data
from src.backtesting import Backtester
from src.risk_management import RiskMetrics
from src.auth import auth_manager, create_token_payload
from src.utils import logger

# ============================================================================
# Flask App Configuration
# ============================================================================

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['JWT_SECRET_KEY'] = 'your-jwt-secret-key-change-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Swagger configuration
app.config['SWAGGER'] = {
    'title': 'Apex Analysis API',
    'uiversion': 3,
    'version': '1.0.0',
    'description': 'Stock analysis and trading platform API with ML-powered insights',
    'securityDefinitions': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"'
        },
        'ApiKey': {
            'type': 'apiKey',
            'name': 'X-API-Key',
            'in': 'header',
            'description': 'API Key for authentication'
        }
    },
    'security': [
        {'Bearer': []},
        {'ApiKey': []}
    ]
}

# Initialize extensions
jwt = JWTManager(app)
CORS(app)
swagger = Swagger(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


# ============================================================================
# Authentication Decorators
# ============================================================================

def api_key_required(f):
    """Decorator for API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key is required'}), 401

        user = auth_manager.authenticate_api_key(api_key)
        if not user:
            return jsonify({'error': 'Invalid API key'}), 401

        # Add user to request context
        request.current_user = user
        return f(*args, **kwargs)

    return decorated_function


def role_required(role: str):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            user_id = get_jwt_identity()
            user = auth_manager.get_user_by_id(user_id)

            if not user or not user.has_role(role):
                return jsonify({'error': f'Role {role} required'}), 403

            request.current_user = user
            return f(*args, **kwargs)

        return decorated_function
    return decorator


# ============================================================================
# Routes - Pages (Public)
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/analysis')
def analysis_page():
    """Stock analysis page"""
    return render_template('analysis.html')


@app.route('/backtest')
def backtest_page():
    """Backtesting page"""
    return render_template('backtest.html')


@app.route('/risk')
def risk_page():
    """Risk management page"""
    return render_template('risk.html')


@app.route('/docs')
def docs_redirect():
    """Redirect to API documentation"""
    return jsonify({
        'message': 'API Documentation',
        'swagger_ui': '/apidocs',
        'openapi_spec': '/apispec_1.json'
    })


# ============================================================================
# API v1 - Authentication Endpoints
# ============================================================================

@app.route('/api/v1/auth/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              example: "johndoe"
            email:
              type: string
              example: "john@example.com"
            password:
              type: string
              example: "SecurePass123"
    responses:
      201:
        description: User created successfully
        schema:
          type: object
          properties:
            message:
              type: string
            user:
              type: object
            api_key:
              type: string
      400:
        description: Invalid input or user already exists
    """
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not all([username, email, password]):
            return jsonify({'error': 'Username, email, and password required'}), 400

        # Check if user exists
        if auth_manager.get_user_by_username(username):
            return jsonify({'error': 'Username already exists'}), 400

        # Create user
        user = auth_manager.create_user(username, email, password)

        return jsonify({
            'message': 'User created successfully',
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email
            },
            'api_key': user.api_key
        }), 201

    except Exception as e:
        logger.error(f"Error registering user: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """
    Login and get JWT tokens
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              example: "admin"
            password:
              type: string
              example: "admin123"
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            access_token:
              type: string
            refresh_token:
              type: string
            user:
              type: object
      401:
        description: Invalid credentials
    """
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not all([username, password]):
            return jsonify({'error': 'Username and password required'}), 400

        # Authenticate user
        user = auth_manager.authenticate_user(username, password)
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        # Create tokens
        access_token = create_access_token(
            identity=user.user_id,
            additional_claims=create_token_payload(user)
        )
        refresh_token = create_refresh_token(identity=user.user_id)

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'roles': user.roles
            }
        })

    except Exception as e:
        logger.error(f"Error logging in: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Token refreshed successfully
        schema:
          type: object
          properties:
            access_token:
              type: string
    """
    user_id = get_jwt_identity()
    user = auth_manager.get_user_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    access_token = create_access_token(
        identity=user_id,
        additional_claims=create_token_payload(user)
    )

    return jsonify({'access_token': access_token})


@app.route('/api/v1/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user information
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: User information
        schema:
          type: object
      401:
        description: Not authenticated
    """
    user_id = get_jwt_identity()
    user = auth_manager.get_user_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'user_id': user.user_id,
        'username': user.username,
        'email': user.email,
        'roles': user.roles,
        'api_key': user.api_key,
        'created_at': user.created_at.isoformat() if isinstance(user.created_at, datetime) else user.created_at
    })


# ============================================================================
# API v1 - Stock Analysis Endpoints
# ============================================================================


def _log_user_action(action: str):
    """Utility to log actions with awareness of authenticated users."""
    user = getattr(request, 'current_user', None)
    username = getattr(user, 'username', 'anonymous')
    logger.info(f"{action} (User: {username})")


def _handle_analysis_request():
    """Shared implementation for stock analysis endpoints."""
    try:
        data = request.get_json(silent=True) or {}
        ticker = data.get('ticker', 'AAPL').upper()
        period = data.get('period', '1y')

        _log_user_action(f"Analyzing {ticker} for period {period}")

        stock_data = fetch_stock_data(ticker, period)
        if not stock_data or stock_data['history'].empty:
            return jsonify({'error': 'No data available'}), 404

        df = stock_data['history']
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        summary = {
            'ticker': ticker,
            'current_price': float(latest['Close']),
            'price_change': float(latest['Close'] - prev['Close']),
            'price_change_pct': float((latest['Close'] - prev['Close']) / prev['Close'] * 100),
            'volume': int(latest['Volume']),
            'high_52w': float(df['High'].tail(252).max()) if len(df) >= 252 else float(df['High'].max()),
            'low_52w': float(df['Low'].tail(252).min()) if len(df) >= 252 else float(df['Low'].min()),
        }

        if 'RSI' in df.columns:
            summary['rsi'] = float(latest['RSI'])
        if 'MACD' in df.columns:
            summary['macd'] = float(latest['MACD'])
            summary['macd_signal'] = float(latest['MACD_Signal'])

        return jsonify(summary)

    except Exception as exc:
        logger.error(f"Error analyzing stock: {exc}", exc_info=True)
        return jsonify({'error': str(exc)}), 500


def _handle_chart_request(ticker: str):
    """Shared implementation for chart data endpoints."""
    try:
        period = request.args.get('period', '1y')
        chart_type = request.args.get('type', 'candlestick')

        stock_data = fetch_stock_data(ticker, period)
        if not stock_data or stock_data['history'].empty:
            return jsonify({'error': 'No data available'}), 404

        df = stock_data['history'].reset_index()

        if chart_type == 'candlestick':
            fig = create_candlestick_chart(df, ticker)
        elif chart_type == 'line':
            fig = create_line_chart(df, ticker)
        elif chart_type == 'volume':
            fig = create_volume_chart(df, ticker)
        elif chart_type == 'indicators':
            fig = create_indicators_chart(df, ticker)
        else:
            fig = create_candlestick_chart(df, ticker)

        return jsonify(json.loads(fig.to_json()))

    except Exception as exc:
        logger.error(f"Error getting chart data: {exc}", exc_info=True)
        return jsonify({'error': str(exc)}), 500


def _handle_backtest_request():
    """Shared implementation for backtest endpoints."""
    try:
        data = request.get_json(silent=True) or {}
        ticker = data.get('ticker', 'AAPL')
        period = data.get('period', '1y')
        initial_capital = float(data.get('initial_capital', 100000))

        stock_data = fetch_stock_data(ticker, period)
        df = stock_data['history']

        def ma_crossover(dataframe, short=20, long=50):
            signals = pd.Series(0, index=dataframe.index)
            short_ma = dataframe['Close'].rolling(short).mean()
            long_ma = dataframe['Close'].rolling(long).mean()
            signals[short_ma > long_ma] = 1
            signals[short_ma < long_ma] = -1
            return signals

        bt = Backtester(initial_capital=initial_capital)
        results = bt.run(df, ma_crossover)

        equity_df = results['equity_curve']
        equity_chart = {
            'dates': equity_df['date'].astype(str).tolist(),
            'values': equity_df['total_value'].tolist()
        }

        return jsonify({
            'metrics': {
                'total_return': results['total_return'],
                'annualized_return': results['annualized_return'],
                'sharpe_ratio': results['sharpe_ratio'],
                'sortino_ratio': results['sortino_ratio'],
                'max_drawdown': results['max_drawdown'],
                'total_trades': results['total_trades'],
                'win_rate': results['win_rate']
            },
            'equity_curve': equity_chart
        })

    except Exception as exc:
        logger.error(f"Error running backtest: {exc}", exc_info=True)
        return jsonify({'error': str(exc)}), 500


def _handle_risk_request(ticker: str):
    """Shared implementation for risk metric endpoints."""
    try:
        period = request.args.get('period', '1y')

        stock_data = fetch_stock_data(ticker, period)
        df = stock_data['history']

        returns = df['Close'].pct_change().dropna()
        equity_curve = (1 + returns).cumprod() * 100000

        var_95 = RiskMetrics.calculate_var(returns, 0.95)
        var_99 = RiskMetrics.calculate_var(returns, 0.99)
        cvar_95 = RiskMetrics.calculate_cvar(returns, 0.95)

        dd_stats = RiskMetrics.get_drawdown_stats(equity_curve)
        risk_adj = RiskMetrics.calculate_risk_adjusted_returns(returns)

        return jsonify({
            'var_95': var_95,
            'var_99': var_99,
            'cvar_95': cvar_95,
            'max_drawdown': dd_stats['max_drawdown'],
            'current_drawdown': dd_stats['current_drawdown'],
            'sharpe_ratio': risk_adj['sharpe_ratio'],
            'sortino_ratio': risk_adj['sortino_ratio'],
            'volatility': risk_adj['annualized_volatility']
        })

    except Exception as exc:
        logger.error(f"Error calculating risk metrics: {exc}", exc_info=True)
        return jsonify({'error': str(exc)}), 500

@app.route('/api/v1/analyze', methods=['POST'])
@limiter.limit("30 per minute")
@api_key_required
def analyze_stock_v1():
    """
    Analyze a stock ticker
    ---
    tags:
      - Stock Analysis
    security:
      - ApiKey: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - ticker
          properties:
            ticker:
              type: string
              example: "AAPL"
            period:
              type: string
              example: "1y"
              default: "1y"
    responses:
      200:
        description: Stock analysis data
        schema:
          type: object
          properties:
            ticker:
              type: string
            current_price:
              type: number
            price_change:
              type: number
            volume:
              type: integer
            rsi:
              type: number
      404:
        description: No data available
    """
    return _handle_analysis_request()


@app.route('/api/v1/chart/<ticker>')
@limiter.limit("20 per minute")
@api_key_required
def get_chart_data_v1(ticker):
    """
    Get chart data for a ticker
    ---
    tags:
      - Stock Analysis
    security:
      - ApiKey: []
    parameters:
      - name: ticker
        in: path
        type: string
        required: true
        example: "AAPL"
      - name: period
        in: query
        type: string
        default: "1y"
      - name: type
        in: query
        type: string
        default: "candlestick"
        enum: ["candlestick", "line", "volume", "indicators"]
    responses:
      200:
        description: Chart data in Plotly format
      404:
        description: No data available
    """
    return _handle_chart_request(ticker)


@app.route('/api/v1/backtest', methods=['POST'])
@limiter.limit("10 per hour")
@jwt_required()
def run_backtest_v1():
    """
    Run a backtest
    ---
    tags:
      - Backtesting
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            ticker:
              type: string
              example: "AAPL"
            period:
              type: string
              example: "1y"
            initial_capital:
              type: number
              example: 100000
    responses:
      200:
        description: Backtest results
        schema:
          type: object
          properties:
            metrics:
              type: object
            equity_curve:
              type: object
    """
    return _handle_backtest_request()


@app.route('/api/v1/risk/<ticker>')
@limiter.limit("30 per minute")
@api_key_required
def get_risk_metrics_v1(ticker):
    """
    Get risk metrics for a ticker
    ---
    tags:
      - Risk Management
    security:
      - ApiKey: []
    parameters:
      - name: ticker
        in: path
        type: string
        required: true
      - name: period
        in: query
        type: string
        default: "1y"
    responses:
      200:
        description: Risk metrics
        schema:
          type: object
          properties:
            var_95:
              type: number
            var_99:
              type: number
            sharpe_ratio:
              type: number
            volatility:
              type: number
    """
    return _handle_risk_request(ticker)


# ============================================================================
# Legacy Unversioned Endpoints (Dashboard compatibility)
# ============================================================================

@app.route('/api/analyze', methods=['POST'])
@limiter.limit("30 per minute")
def analyze_stock_legacy():
    """Legacy endpoint retained for the existing dashboard."""
    return _handle_analysis_request()


@app.route('/api/chart/<ticker>')
@limiter.limit("20 per minute")
def get_chart_data_legacy(ticker):
    """Legacy endpoint retained for the existing dashboard."""
    return _handle_chart_request(ticker)


@app.route('/api/backtest', methods=['POST'])
@limiter.limit("10 per hour")
def run_backtest_legacy():
    """Legacy endpoint retained for the existing dashboard."""
    return _handle_backtest_request()


@app.route('/api/risk/<ticker>')
@limiter.limit("30 per minute")
def get_risk_metrics_legacy(ticker):
    """Legacy endpoint retained for the existing dashboard."""
    return _handle_risk_request(ticker)


# ============================================================================
# Admin Endpoints (Admin role required)
# ============================================================================

@app.route('/api/v1/admin/users', methods=['GET'])
@role_required('admin')
def list_users():
    """
    List all users (admin only)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    responses:
      200:
        description: List of users
        schema:
          type: array
          items:
            type: object
    """
    users = auth_manager.list_users()
    return jsonify(users)


@app.route('/api/v1/admin/users/<user_id>/regenerate-key', methods=['POST'])
@role_required('admin')
def regenerate_user_api_key(user_id):
    """
    Regenerate API key for a user (admin only)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: New API key
        schema:
          type: object
          properties:
            api_key:
              type: string
    """
    new_key = auth_manager.regenerate_api_key(user_id)
    if not new_key:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'api_key': new_key})


# ============================================================================
# Chart Creation Functions (from original web_app.py)
# ============================================================================

def create_candlestick_chart(df, ticker):
    """Create candlestick chart with volume"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(f'{ticker} Price', 'Volume')
    )

    fig.add_trace(
        go.Candlestick(
            x=df['Date'] if 'Date' in df.columns else df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='OHLC'
        ),
        row=1, col=1
    )

    colors = ['red' if row['Close'] < row['Open'] else 'green' for _, row in df.iterrows()]
    fig.add_trace(
        go.Bar(
            x=df['Date'] if 'Date' in df.columns else df.index,
            y=df['Volume'],
            name='Volume',
            marker_color=colors
        ),
        row=2, col=1
    )

    fig.update_layout(
        title=f'{ticker} Stock Price',
        yaxis_title='Price ($)',
        yaxis2_title='Volume',
        xaxis_rangeslider_visible=False,
        height=600,
        template='plotly_white'
    )

    return fig


def create_line_chart(df, ticker):
    """Create line chart with moving averages"""
    fig = go.Figure()

    x = df['Date'] if 'Date' in df.columns else df.index

    fig.add_trace(go.Scatter(
        x=x, y=df['Close'],
        mode='lines',
        name='Close Price',
        line=dict(color='blue', width=2)
    ))

    if 'SMA_20' in df.columns:
        fig.add_trace(go.Scatter(
            x=x, y=df['SMA_20'],
            mode='lines',
            name='SMA 20',
            line=dict(color='orange', width=1, dash='dash')
        ))

    if 'SMA_50' in df.columns:
        fig.add_trace(go.Scatter(
            x=x, y=df['SMA_50'],
            mode='lines',
            name='SMA 50',
            line=dict(color='red', width=1, dash='dash')
        ))

    fig.update_layout(
        title=f'{ticker} Price Chart',
        yaxis_title='Price ($)',
        xaxis_title='Date',
        height=500,
        template='plotly_white'
    )

    return fig


def create_volume_chart(df, ticker):
    """Create volume chart"""
    fig = go.Figure()

    colors = ['red' if row['Close'] < row['Open'] else 'green' for _, row in df.iterrows()]

    fig.add_trace(go.Bar(
        x=df['Date'] if 'Date' in df.columns else df.index,
        y=df['Volume'],
        name='Volume',
        marker_color=colors
    ))

    fig.update_layout(
        title=f'{ticker} Volume',
        yaxis_title='Volume',
        xaxis_title='Date',
        height=400,
        template='plotly_white'
    )

    return fig


def create_indicators_chart(df, ticker):
    """Create technical indicators chart"""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=('Price', 'RSI', 'MACD')
    )

    x = df['Date'] if 'Date' in df.columns else df.index

    fig.add_trace(
        go.Scatter(x=x, y=df['Close'], mode='lines', name='Close'),
        row=1, col=1
    )

    if 'RSI' in df.columns:
        fig.add_trace(
            go.Scatter(x=x, y=df['RSI'], mode='lines', name='RSI'),
            row=2, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    if 'MACD' in df.columns:
        fig.add_trace(
            go.Scatter(x=x, y=df['MACD'], mode='lines', name='MACD'),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=x, y=df['MACD_Signal'], mode='lines', name='Signal'),
            row=3, col=1
        )

    fig.update_layout(
        height=800,
        title=f'{ticker} Technical Indicators',
        template='plotly_white'
    )

    return fig


# ============================================================================
# Run App
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Starting Apex Analysis REST API v2")
    print("="*60)
    print("\nFeatures:")
    print("  ✓ JWT Authentication")
    print("  ✓ API Key Authentication")
    print("  ✓ Rate Limiting")
    print("  ✓ API Versioning (v1)")
    print("  ✓ Swagger Documentation")
    print("\nEndpoints:")
    print("  Dashboard: http://localhost:5001")
    print("  API Docs:  http://localhost:5001/apidocs")
    print("  API v1:    http://localhost:5001/api/v1/")
    print("\nDefault Credentials:")
    print("  Admin: username='admin', password='admin123'")
    print("  Demo:  username='demo', password='demo123'")
    print("\nPress Ctrl+C to stop the server\n")

    app.run(debug=True, host='0.0.0.0', port=5001)
