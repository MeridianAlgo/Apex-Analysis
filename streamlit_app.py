"""
Apex Analysis - Modern Live Stock Dashboard with User Authentication
Real-time data, beautiful UI, and personalized watchlists
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import json
import io
import sqlite3
import bcrypt
import time
from pathlib import Path

from src.fetch_data import fetch_stock_data
from src.backtesting import Backtester
from src.risk_management import RiskMetrics
from src.utils import logger

# ============================================================================
# Database Setup
# ============================================================================

DB_PATH = Path("data/users.db")
DB_PATH.parent.mkdir(exist_ok=True)

def init_database():
    """Initialize SQLite database for users"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Watchlists table
    c.execute('''CREATE TABLE IF NOT EXISTS watchlists
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  ticker TEXT NOT NULL,
                  added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  UNIQUE(user_id, ticker))''')
    
    # Alerts table
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  ticker TEXT NOT NULL,
                  alert_type TEXT NOT NULL,
                  threshold REAL NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_user(username, email, password):
    """Create a new user"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        password_hash = hash_password(password)
        c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                 (username, email, password_hash))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return True, user_id
    except sqlite3.IntegrityError:
        return False, None

def authenticate_user(username, password):
    """Authenticate a user"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result and verify_password(password, result[1]):
        return True, result[0]
    return False, None

def get_user_watchlist(user_id):
    """Get user's watchlist"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT ticker FROM watchlists WHERE user_id = ? ORDER BY added_at DESC", (user_id,))
    tickers = [row[0] for row in c.fetchall()]
    conn.close()
    return tickers

def add_to_watchlist(user_id, ticker):
    """Add ticker to user's watchlist"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("INSERT INTO watchlists (user_id, ticker) VALUES (?, ?)", (user_id, ticker))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def remove_from_watchlist(user_id, ticker):
    """Remove ticker from user's watchlist"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("DELETE FROM watchlists WHERE user_id = ? AND ticker = ?", (user_id, ticker))
    conn.commit()
    conn.close()

def get_user_alerts(user_id):
    """Get user's alerts"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT id, ticker, alert_type, threshold, created_at FROM alerts WHERE user_id = ?", (user_id,))
    alerts = c.fetchall()
    conn.close()
    return alerts

def add_alert(user_id, ticker, alert_type, threshold):
    """Add an alert"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("INSERT INTO alerts (user_id, ticker, alert_type, threshold) VALUES (?, ?, ?, ?)",
             (user_id, ticker, alert_type, threshold))
    conn.commit()
    conn.close()

def delete_alert(alert_id):
    """Delete an alert"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Apex Analysis - Live Stock Trading Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# Custom CSS - Enhanced Modern UI
# ============================================================================

st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main container */
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(99, 102, 241, 0.3);
        text-align: center;
    }
    
    .main-header h1 {
        color: white;
        font-size: 3rem;
        font-weight: 900;
        margin: 0;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
        letter-spacing: -1px;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.95);
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
        font-weight: 300;
    }
    
    /* Live indicator */
    .live-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        background: #10b981;
        border-radius: 50%;
        animation: pulse 2s infinite;
        margin-right: 8px;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Metric cards */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
        border-color: rgba(99, 102, 241, 0.6);
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 0.75rem;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.5);
    }
    
    /* Watchlist cards */
    .watchlist-card {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .watchlist-card:hover {
        border-color: rgba(99, 102, 241, 0.5);
        transform: translateX(5px);
    }
    
    /* Alert cards */
    .alert-card {
        padding: 1rem;
        border-radius: 0.75rem;
        margin: 0.5rem 0;
        border-left: 4px solid;
        animation: slideIn 0.3s ease;
        backdrop-filter: blur(10px);
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .alert-success {
        background: rgba(16, 185, 129, 0.15);
        border-color: #10b981;
        color: #10b981;
    }
    
    .alert-warning {
        background: rgba(245, 158, 11, 0.15);
        border-color: #f59e0b;
        color: #f59e0b;
    }
    
    .alert-danger {
        background: rgba(239, 68, 68, 0.15);
        border-color: #ef4444;
        color: #ef4444;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        border-right: 1px solid rgba(99, 102, 241, 0.2);
    }
    
    /* Input fields */
    .stTextInput>div>div>input {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 0.5rem;
        color: white;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(30, 41, 59, 0.6);
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        color: white;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Session State & Database Initialization
# ============================================================================

init_database()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# ============================================================================
# Helper Functions
# ============================================================================

@st.cache_data(ttl=1)  # Cache for 1 second for TRUE live updates
def get_live_price(ticker):
    """Get live price for a ticker"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period='1d', interval='1m')
        if not data.empty:
            current_price = data['Close'].iloc[-1]
            prev_close = stock.info.get('previousClose', data['Close'].iloc[0])
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100
            return {
                'price': current_price,
                'change': change,
                'change_pct': change_pct,
                'volume': data['Volume'].iloc[-1]
            }
    except:
        pass
    return None

def create_price_chart(df, ticker):
    """Create enhanced candlestick chart with full-length MAs"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(f'{ticker} - Live Price Action', 'Volume')
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
            increasing_line_color='#10b981',
            decreasing_line_color='#ef4444'
        ),
        row=1, col=1
    )
    
    # Moving averages - FULL LENGTH
    if len(df) >= 20:
        ma20 = df['Close'].rolling(window=20).mean()
        # Plot from first valid point to end
        valid_ma20 = ma20.dropna()
        fig.add_trace(
            go.Scatter(
                x=valid_ma20.index, 
                y=valid_ma20, 
                name='MA20',
                line=dict(color='#f59e0b', width=2),
                mode='lines'
            ),
            row=1, col=1
        )
    
    if len(df) >= 50:
        ma50 = df['Close'].rolling(window=50).mean()
        valid_ma50 = ma50.dropna()
        fig.add_trace(
            go.Scatter(
                x=valid_ma50.index, 
                y=valid_ma50, 
                name='MA50',
                line=dict(color='#6366f1', width=2),
                mode='lines'
            ),
            row=1, col=1
        )
    
    # Volume
    colors = ['#10b981' if df['Close'].iloc[i] >= df['Open'].iloc[i] 
              else '#ef4444' for i in range(len(df))]
    
    fig.add_trace(
        go.Bar(x=df.index, y=df['Volume'], name='Volume', 
               marker_color=colors, showlegend=False),
        row=2, col=1
    )
    
    fig.update_layout(
        template='plotly_dark',
        height=700,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        plot_bgcolor='rgba(15, 23, 42, 0.8)',
        paper_bgcolor='rgba(15, 23, 42, 0.8)',
        font=dict(color='white', size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(99, 102, 241, 0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(99, 102, 241, 0.1)')
    
    return fig

def create_indicators_chart(df, ticker):
    """Create technical indicators chart"""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=(f'{ticker} Price', 'RSI', 'MACD')
    )
    
    # Price with Bollinger Bands
    fig.add_trace(
        go.Scatter(x=df.index, y=df['Close'], name='Close', 
                  line=dict(color='#6366f1', width=2)),
        row=1, col=1
    )
    
    if 'BB_Upper' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['BB_Upper'], name='BB Upper',
                      line=dict(color='rgba(99, 102, 241, 0.3)', width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['BB_Lower'], name='BB Lower',
                      line=dict(color='rgba(99, 102, 241, 0.3)', width=1),
                      fill='tonexty', fillcolor='rgba(99, 102, 241, 0.1)'),
            row=1, col=1
        )
    
    # RSI
    if 'RSI' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['RSI'], name='RSI',
                      line=dict(color='#f59e0b', width=2)),
            row=2, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#10b981", row=2, col=1)
    
    # MACD
    if 'MACD' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MACD'], name='MACD',
                      line=dict(color='#10b981', width=2)),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MACD_Signal'], name='Signal',
                      line=dict(color='#ef4444', width=2)),
            row=3, col=1
        )
        
        if 'MACD_Hist' in df.columns:
            colors = ['#10b981' if val >= 0 else '#ef4444' for val in df['MACD_Hist']]
            fig.add_trace(
                go.Bar(x=df.index, y=df['MACD_Hist'], name='Histogram',
                      marker_color=colors),
                row=3, col=1
            )
    
    fig.update_layout(
        template='plotly_dark',
        height=800,
        showlegend=True,
        hovermode='x unified',
        plot_bgcolor='rgba(15, 23, 42, 0.8)',
        paper_bgcolor='rgba(15, 23, 42, 0.8)',
        font=dict(color='white')
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(99, 102, 241, 0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(99, 102, 241, 0.1)')
    
    return fig

def check_price_alerts(ticker, current_price, df):
    """Check for price alerts"""
    alerts = []
    
    if len(df) >= 20:
        ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        ma50 = df['Close'].rolling(window=50).mean().iloc[-1] if len(df) >= 50 else None
        
        if ma50 is not None:
            if current_price > ma20 > ma50:
                alerts.append({
                    'type': 'success',
                    'title': '🚀 Bullish Signal',
                    'message': f'{ticker} is above both MA20 (${ma20:.2f}) and MA50 (${ma50:.2f})'
                })
            elif current_price < ma20 < ma50:
                alerts.append({
                    'type': 'danger',
                    'title': '⚠️ Bearish Signal',
                    'message': f'{ticker} is below both MA20 (${ma20:.2f}) and MA50 (${ma50:.2f})'
                })
    
    if 'RSI' in df.columns:
        rsi = df['RSI'].iloc[-1]
        if rsi > 70:
            alerts.append({
                'type': 'warning',
                'title': '📊 Overbought',
                'message': f'RSI is {rsi:.2f} - Stock may be overbought'
            })
        elif rsi < 30:
            alerts.append({
                'type': 'success',
                'title': '📊 Oversold',
                'message': f'RSI is {rsi:.2f} - Potential buying opportunity'
            })
    
    avg_volume = df['Volume'].tail(20).mean()
    current_volume = df['Volume'].iloc[-1]
    if current_volume > avg_volume * 1.5:
        alerts.append({
            'type': 'warning',
            'title': '📢 High Volume',
            'message': f'Volume is {(current_volume/avg_volume):.1f}x above 20-day average'
        })
    
    price_change_pct = ((current_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
    if abs(price_change_pct) > 3:
        alert_type = 'success' if price_change_pct > 0 else 'danger'
        alerts.append({
            'type': alert_type,
            'title': '💰 Significant Price Move',
            'message': f'{ticker} moved {price_change_pct:+.2f}% today'
        })
    
    high_52w = df['High'].tail(252).max() if len(df) >= 252 else df['High'].max()
    low_52w = df['Low'].tail(252).min() if len(df) >= 252 else df['Low'].min()
    
    if current_price >= high_52w * 0.98:
        alerts.append({
            'type': 'success',
            'title': '🎯 Near 52-Week High',
            'message': f'{ticker} is trading near its 52-week high of ${high_52w:.2f}'
        })
    elif current_price <= low_52w * 1.02:
        alerts.append({
            'type': 'warning',
            'title': '⚠️ Near 52-Week Low',
            'message': f'{ticker} is trading near its 52-week low of ${low_52w:.2f}'
        })
    
    if 'MACD' in df.columns and 'MACD_Signal' in df.columns and len(df) >= 2:
        macd_current = df['MACD'].iloc[-1]
        signal_current = df['MACD_Signal'].iloc[-1]
        macd_prev = df['MACD'].iloc[-2]
        signal_prev = df['MACD_Signal'].iloc[-2]
        
        if macd_prev < signal_prev and macd_current > signal_current:
            alerts.append({
                'type': 'success',
                'title': '📈 MACD Bullish Crossover',
                'message': 'MACD crossed above signal line - Potential buy signal'
            })
        elif macd_prev > signal_prev and macd_current < signal_current:
            alerts.append({
                'type': 'danger',
                'title': '📉 MACD Bearish Crossover',
                'message': 'MACD crossed below signal line - Potential sell signal'
            })
    
    return alerts

def export_data(df, ticker, format='csv'):
    """Export data in various formats"""
    if format == 'csv':
        return df.to_csv().encode('utf-8')
    elif format == 'json':
        return df.to_json(orient='records', date_format='iso').encode('utf-8')
    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=ticker)
        return output.getvalue()
    elif format == 'parquet':
        output = io.BytesIO()
        df.to_parquet(output)
        return output.getvalue()

# ============================================================================
# Authentication Pages
# ============================================================================

def show_login():
    """Login page"""
    st.markdown("""
    <div class="main-header">
        <h1>📈 Apex Analysis</h1>
        <p>Professional Live Stock Trading Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with tab1:
            st.markdown("### Welcome Back!")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", type="primary", use_container_width=True):
                if username and password:
                    success, user_id = authenticate_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.success("✅ Login successful!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("⚠️ Please enter both username and password")
        
        with tab2:
            st.markdown("### Create Account")
            new_username = st.text_input("Username", key="signup_username")
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            
            if st.button("Sign Up", type="primary", use_container_width=True):
                if new_username and new_email and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("❌ Passwords don't match")
                    elif len(new_password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    else:
                        success, user_id = create_user(new_username, new_email, new_password)
                        if success:
                            # Auto-login after successful signup
                            st.session_state.logged_in = True
                            st.session_state.user_id = user_id
                            st.session_state.username = new_username
                            st.success(f"✅ Account created! Welcome, {new_username}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Username or email already exists")
                else:
                    st.warning("⚠️ Please fill in all fields")


# ============================================================================
# Main App
# ============================================================================

def main():
    if not st.session_state.logged_in:
        show_login()
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); border-radius: 1rem; margin-bottom: 1rem;'>
            <h3 style='color: white; margin: 0;'>👤 {st.session_state.username}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🎯 Navigation")
        page = st.radio(
            "Select Page",
            ["📈 Analysis", "🔄 Backtesting", "⚠️ Risk Management", 
             "🔔 Alerts", "📥 Data Export"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Logic for 1-second updates (Only on Analysis)
        if page == "📈 Analysis":
            if time.time() - st.session_state.last_refresh > 1:
                st.session_state.last_refresh = time.time()
                st.rerun()
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📈 Apex Analysis</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Route to pages
    if page == "📈 Analysis":
        show_analysis()
    elif page == "🔄 Backtesting":
        show_backtesting()
    elif page == "⚠️ Risk Management":
        show_risk_management()
    elif page == "🔔 Alerts":
        show_alerts()
    elif page == "📥 Data Export":
        show_data_export()

def show_analysis():
    """Stock analysis page"""
    st.markdown("## 📈 Live Stock Analysis")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        ticker = st.text_input("Enter Stock Ticker", value="AAPL", 
                              placeholder="e.g., AAPL, GOOGL, MSFT").upper()
    
    with col2:
        period = st.selectbox("Time Period", 
                             ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"],
                             index=5)
    
    with col3:
        chart_type = st.selectbox("Chart Type", 
                                 ["Candlestick", "Indicators"])
    
    if st.button("🔍 Analyze", type="primary", use_container_width=True):
        with st.spinner(f"Analyzing {ticker}..."):
            try:
                stock_data = fetch_stock_data(ticker, period)
                
                if not stock_data or stock_data['history'].empty:
                    st.error(f"No data available for {ticker}")
                    return
                
                df = stock_data['history']
                
                # Get live price
                live_data = get_live_price(ticker)
                if live_data:
                    current_price = live_data['price']
                    price_change = live_data['change']
                    price_change_pct = live_data['change_pct']
                else:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2]
                    current_price = latest['Close']
                    price_change = current_price - prev['Close']
                    price_change_pct = (price_change / prev['Close']) * 100
                
                # Key metrics
                st.markdown("### 📊 Live Metrics")
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("💰 Live Price", f"${current_price:.2f}",
                            f"{price_change_pct:+.2f}%")
                
                with col2:
                    volume = live_data['volume'] if live_data else df['Volume'].iloc[-1]
                    st.metric("📊 Volume", f"{volume:,.0f}")
                
                with col3:
                    high_52w = df['High'].tail(252).max() if len(df) >= 252 else df['High'].max()
                    st.metric("📈 52W High", f"${high_52w:.2f}")
                
                with col4:
                    low_52w = df['Low'].tail(252).min() if len(df) >= 252 else df['Low'].min()
                    st.metric("📉 52W Low", f"${low_52w:.2f}")
                
                with col5:
                    if 'RSI' in df.columns:
                        st.metric("📊 RSI", f"{df['RSI'].iloc[-1]:.2f}")
                
                # Price alerts
                alerts = check_price_alerts(ticker, current_price, df)
                if alerts:
                    st.markdown("### 🔔 Active Alerts")
                    for alert in alerts:
                        alert_class = f"alert-{alert['type']}"
                        st.markdown(f"""
                        <div class="alert-card {alert_class}">
                            <strong>{alert['title']}</strong><br>
                            {alert['message']}
                        </div>
                        """, unsafe_allow_html=True)
                
                # Chart
                st.markdown("### 📈 Price Chart")
                if chart_type == "Candlestick":
                    fig = create_price_chart(df, ticker)
                else:
                    fig = create_indicators_chart(df, ticker)
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Technical indicators table
                st.markdown("### 📊 Technical Indicators")
                indicators_data = {
                    'Indicator': [],
                    'Value': [],
                    'Signal': []
                }
                
                if 'RSI' in df.columns:
                    rsi = df['RSI'].iloc[-1]
                    signal = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
                    indicators_data['Indicator'].append('RSI')
                    indicators_data['Value'].append(f"{rsi:.2f}")
                    indicators_data['Signal'].append(signal)
                
                if 'MACD' in df.columns:
                    macd = df['MACD'].iloc[-1]
                    signal_line = df['MACD_Signal'].iloc[-1]
                    signal = "Bullish" if macd > signal_line else "Bearish"
                    indicators_data['Indicator'].append('MACD')
                    indicators_data['Value'].append(f"{macd:.4f}")
                    indicators_data['Signal'].append(signal)
                
                if len(df) >= 20:
                    ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
                    signal = "Above" if current_price > ma20 else "Below"
                    indicators_data['Indicator'].append('MA20')
                    indicators_data['Value'].append(f"${ma20:.2f}")
                    indicators_data['Signal'].append(signal)
                
                if len(df) >= 50:
                    ma50 = df['Close'].rolling(window=50).mean().iloc[-1]
                    signal = "Above" if current_price > ma50 else "Below"
                    indicators_data['Indicator'].append('MA50')
                    indicators_data['Value'].append(f"${ma50:.2f}")
                    indicators_data['Signal'].append(signal)
                
                st.dataframe(pd.DataFrame(indicators_data), use_container_width=True, hide_index=True)
                
            except Exception as e:
                st.error(f"Error analyzing {ticker}: {str(e)}")
                logger.error(f"Analysis error: {e}", exc_info=True)

def show_backtesting():
    """Backtesting page with Custom Code support"""
    st.markdown("## 🔄 Strategy Backtesting")
    
    # Tabs for different backtesting modes
    mode = st.radio("Mode", ["📚 Standard Strategies", "🐍 Custom Python Code", "🌲 PineScript (Beta)"], 
                    horizontal=True, label_visibility="collapsed")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ticker = st.text_input("Ticker", value="AAPL").upper()
    
    with col2:
        period = st.selectbox("Period", ["1y", "2y", "5y"], index=0)
    
    with col3:
        initial_capital = st.number_input("Initial Capital ($)", 
                                         min_value=1000, value=100000, step=1000)
    
    if mode == "📚 Standard Strategies":
        strategies = [
            "MA Crossover (20/50)", "SMA 50/200 (Golden Cross)", "EMA Crossover (12/26)",
            "RSI Mean Reversion (30/70)", "RSI Trend Following (>50/<50)",
            "MACD Signal Crossover", "MACD Zero Cross",
            "Bollinger Bands Mean Reversion", "Bollinger Bands Breakout",
            "Stochastic Oscillator (20/80)", "Williams %R",
            "CCI Mean Reversion", "CCI Trend Following",
            "Momentum (ROC 10)", "Price Channel Breakout (20d)",
            "Volume Spike Reversal", "OBV Trend", "MFI Overbought/Oversold",
            "Simple Mean Reversion (Price vs SMA20)", "Consecutive Up/Down Days",
            "Inside Bar Breakout", "Three White Soldiers/Black Crows", "ATR Breakout"
        ]
        strategy = st.selectbox("Select Strategy", strategies)
        
        if st.button("🚀 Run Backtest", type="primary", use_container_width=True):
            run_standard_backtest(ticker, period, initial_capital, strategy)
            
    elif mode == "🐍 Custom Python Code":
        with st.expander("📚 Documentation & Examples", expanded=False):
            st.markdown("""
            ### 🐍 How to Write a Python Strategy
            
            You must define a function named `strategy(df)` that takes a pandas DataFrame and returns a pandas Series of signals.
            
            #### **Input Data (`df`)**
            The `df` contains historical stock data with these columns:
            - `Open`, `High`, `Low`, `Close` (Prices)
            - `Volume` (Number of shares)
            - The index is a `DatetimeIndex`.
            
            #### **Output Signal**
            Return a `pd.Series` with the same index as `df` containing:
            - `1`: **Buy** (Long)
            - `-1`: **Sell** (Short/Close)
            - `0`: **Hold** (No action)
            
            #### **Example 1: Simple MA Crossover**
            ```python
            def strategy(df):
                # Calculate indicators
                short_ma = df['Close'].rolling(20).mean()
                long_ma = df['Close'].rolling(50).mean()
                
                # Generate signals
                signals = pd.Series(0, index=df.index)
                signals[short_ma > long_ma] = 1
                signals[short_ma < long_ma] = -1
                return signals
            ```
            
            #### **Example 2: RSI Strategy**
            ```python
            def strategy(df):
                # Calculate RSI manually
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                
                signals = pd.Series(0, index=df.index)
                signals[rsi < 30] = 1  # Buy oversold
                signals[rsi > 70] = -1 # Sell overbought
                return signals
            ```
            """)
        
        default_code = """def strategy(df):
    # 💡 TIP: Use df['Close'], df['Volume'], etc.
    
    # 1. Calculate Indicators
    sma_20 = df['Close'].rolling(20).mean()
    
    # 2. Define Signals
    signals = pd.Series(0, index=df.index)
    
    # Buy when price is above SMA 20
    signals[df['Close'] > sma_20] = 1
    
    # Sell when price is below SMA 20
    signals[df['Close'] < sma_20] = -1
    
    return signals"""
        
        code = st.text_area("Python Strategy Code", value=default_code, height=350)
        
        if st.button("🚀 Run Custom Backtest", type="primary", use_container_width=True):
            run_custom_backtest(ticker, period, initial_capital, code)

    elif mode == "🌲 PineScript (Beta)":
        with st.expander("📚 PineScript Guide", expanded=False):
            st.markdown("""
            ### 🌲 PineScript Converter Guide
            
            This tool attempts to convert **TradingView PineScript** logic into Python for backtesting. 
            
            #### **Supported Functions**
            - `sma(source, length)` - Simple Moving Average
            - `ema(source, length)` - Exponential Moving Average
            - `crossover(a, b)` - When A crosses over B
            - `crossunder(a, b)` - When A crosses under B
            - `close`, `open`, `high`, `low`, `volume` - Price data
            
            #### **Limitations**
            - Complex logic, custom functions, and plotting are **not** supported.
            - This is a heuristic converter, meaning it guesses the logic. Always check the generated Python code!
            
            #### **Example Code**
            ```pinescript
            //@version=4
            study("My Strategy")
            long = crossover(sma(close, 14), sma(close, 28))
            short = crossunder(sma(close, 14), sma(close, 28))
            ```
            """)
            
        st.warning("⚠️ PineScript support is experimental. It works best with simple crossover strategies.")
        
        pine_code = st.text_area("Paste PineScript Code", height=300, 
                                placeholder="// Example PineScript\nstudy('Simple MA Cross')\nfast = sma(close, 20)\nslow = sma(close, 50)\nlong = crossover(fast, slow)\nshort = crossunder(fast, slow)")
        
        if st.button("🔄 Convert & Run", type="primary", use_container_width=True):
            st.info("ℹ️ Converting PineScript to Python logic...")
            python_code = convert_pinescript_to_python(pine_code)
            st.code(python_code, language='python')
            run_custom_backtest(ticker, period, initial_capital, python_code)

def run_standard_backtest(ticker, period, initial_capital, strategy_name):
    with st.spinner(f"Running {strategy_name}..."):
        try:
            stock_data = fetch_stock_data(ticker, period)
            df = stock_data['history']
            
            # --- Strategy Logic Definitions ---
            def get_strategy_signals(df, name):
                signals = pd.Series(0, index=df.index)
                close = df['Close']
                high = df['High']
                low = df['Low']
                volume = df['Volume']
                
                # Helper for RSI
                def calc_rsi(series, period=14):
                    delta = series.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
                    rs = gain / loss
                    return 100 - (100 / (1 + rs))

                if name == "MA Crossover (20/50)":
                    ma20 = close.rolling(20).mean()
                    ma50 = close.rolling(50).mean()
                    signals[ma20 > ma50] = 1
                    signals[ma20 < ma50] = -1
                    
                elif name == "SMA 50/200 (Golden Cross)":
                    ma50 = close.rolling(50).mean()
                    ma200 = close.rolling(200).mean()
                    signals[ma50 > ma200] = 1
                    signals[ma50 < ma200] = -1
                    
                elif name == "EMA Crossover (12/26)":
                    ema12 = close.ewm(span=12, adjust=False).mean()
                    ema26 = close.ewm(span=26, adjust=False).mean()
                    signals[ema12 > ema26] = 1
                    signals[ema12 < ema26] = -1
                    
                elif name == "RSI Mean Reversion (30/70)":
                    rsi = calc_rsi(close)
                    signals[rsi < 30] = 1
                    signals[rsi > 70] = -1
                    
                elif name == "RSI Trend Following (>50/<50)":
                    rsi = calc_rsi(close)
                    signals[rsi > 50] = 1
                    signals[rsi < 50] = -1
                    
                elif name == "MACD Signal Crossover":
                    ema12 = close.ewm(span=12, adjust=False).mean()
                    ema26 = close.ewm(span=26, adjust=False).mean()
                    macd = ema12 - ema26
                    signal = macd.ewm(span=9, adjust=False).mean()
                    signals[macd > signal] = 1
                    signals[macd < signal] = -1
                    
                elif name == "MACD Zero Cross":
                    ema12 = close.ewm(span=12, adjust=False).mean()
                    ema26 = close.ewm(span=26, adjust=False).mean()
                    macd = ema12 - ema26
                    signals[macd > 0] = 1
                    signals[macd < 0] = -1
                    
                elif name == "Bollinger Bands Mean Reversion":
                    ma20 = close.rolling(20).mean()
                    std20 = close.rolling(20).std()
                    upper = ma20 + (std20 * 2)
                    lower = ma20 - (std20 * 2)
                    signals[close < lower] = 1
                    signals[close > upper] = -1
                    
                elif name == "Bollinger Bands Breakout":
                    ma20 = close.rolling(20).mean()
                    std20 = close.rolling(20).std()
                    upper = ma20 + (std20 * 2)
                    lower = ma20 - (std20 * 2)
                    signals[close > upper] = 1
                    signals[close < lower] = -1
                    
                elif name == "Stochastic Oscillator (20/80)":
                    # Simple Fast Stochastic
                    low14 = low.rolling(14).min()
                    high14 = high.rolling(14).max()
                    k = 100 * ((close - low14) / (high14 - low14))
                    signals[k < 20] = 1
                    signals[k > 80] = -1
                    
                elif name == "Williams %R":
                    low14 = low.rolling(14).min()
                    high14 = high.rolling(14).max()
                    r = -100 * ((high14 - close) / (high14 - low14))
                    signals[r < -80] = 1
                    signals[r > -20] = -1
                    
                elif name == "Momentum (ROC 10)":
                    roc = close.pct_change(10)
                    signals[roc > 0] = 1
                    signals[roc < 0] = -1
                    
                elif name == "Price Channel Breakout (20d)":
                    high20 = high.rolling(20).max().shift(1)
                    low20 = low.rolling(20).min().shift(1)
                    signals[close > high20] = 1
                    signals[close < low20] = -1
                    
                elif name == "Volume Spike Reversal":
                    vol_ma = volume.rolling(20).mean()
                    # Spike = 2x average volume
                    spike = volume > (vol_ma * 2)
                    # Contrarian: Sell on up spike, Buy on down spike
                    signals[(spike) & (close < close.shift(1))] = 1
                    signals[(spike) & (close > close.shift(1))] = -1
                    
                elif name == "Simple Mean Reversion (Price vs SMA20)":
                    sma20 = close.rolling(20).mean()
                    signals[close > sma20] = 1
                    signals[close < sma20] = -1
                    
                elif name == "Consecutive Up/Down Days":
                    # Buy after 3 down days, Sell after 3 up days
                    diff = close.diff()
                    down3 = (diff < 0) & (diff.shift(1) < 0) & (diff.shift(2) < 0)
                    up3 = (diff > 0) & (diff.shift(1) > 0) & (diff.shift(2) > 0)
                    signals[down3] = 1
                    signals[up3] = -1
                
                # Default fallback
                else:
                    sma20 = close.rolling(20).mean()
                    signals[close > sma20] = 1
                    signals[close < sma20] = -1
                    
                return signals

            # Wrapper for the backtester
            def strategy_wrapper(df):
                return get_strategy_signals(df, strategy_name)
            
            bt = Backtester(initial_capital=initial_capital)
            results = bt.run(df, strategy_wrapper)
            display_backtest_results(results)
            
        except Exception as e:
            st.error(f"Error running backtest: {str(e)}")

def run_custom_backtest(ticker, period, initial_capital, code_str):
    with st.spinner("Executing custom strategy..."):
        try:
            stock_data = fetch_stock_data(ticker, period)
            df = stock_data['history']
            
            if df.empty:
                st.error("❌ No data found for this ticker.")
                return

            # Safe execution environment
            local_scope = {'pd': pd, 'np': np}
            
            # Execute user code
            try:
                exec(code_str, globals(), local_scope)
            except SyntaxError as e:
                st.error(f"❌ Syntax Error in your code: line {e.lineno}")
                st.code(e.text)
                return
            except Exception as e:
                st.error(f"❌ Error executing code: {str(e)}")
                return
            
            if 'strategy' not in local_scope:
                st.error("❌ Function `strategy(df)` not found! Please define it.")
                return
                
            strategy_func = local_scope['strategy']
            
            # Wrapper to validate output
            def wrapped_strategy(dataframe):
                try:
                    signals = strategy_func(dataframe)
                except Exception as e:
                    raise RuntimeError(f"Error inside strategy function: {str(e)}")
                
                if not isinstance(signals, pd.Series):
                    raise ValueError(f"Strategy must return a pandas Series, got {type(signals)}")
                
                if len(signals) != len(dataframe):
                    raise ValueError(f"Signal length ({len(signals)}) does not match data length ({len(dataframe)})")
                    
                return signals
            
            bt = Backtester(initial_capital=initial_capital)
            results = bt.run(df, wrapped_strategy)
            display_backtest_results(results)
            
        except ValueError as ve:
            st.error(f"❌ Validation Error: {str(ve)}")
        except RuntimeError as re:
            st.error(f"❌ Runtime Error: {str(re)}")
        except Exception as e:
            st.error(f"❌ Unexpected Error: {str(e)}")

def convert_pinescript_to_python(pine_code):
    """Heuristic converter for PineScript to Python"""
    python_code = "def strategy(df):\n    # Generated from PineScript\n    import pandas as pd\n    import numpy as np\n    \n    # Data aliases\n    close = df['Close']\n    open_ = df['Open']\n    high = df['High']\n    low = df['Low']\n    volume = df['Volume']\n    \n    signals = pd.Series(0, index=df.index)\n"
    
    lines = pine_code.split('\n')
    
    # Track variables created
    vars_created = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('//') or line.startswith('study') or line.startswith('//@'):
            continue
            
        # Handle SMA: x = sma(close, 20)
        if 'sma(' in line:
            import re
            # Regex to capture variable name and params
            match = re.match(r'(\w+)\s*=\s*sma\(([^,]+),\s*(\d+)\)', line)
            if match:
                var_name, src, length = match.groups()
                src = src.replace('close', "df['Close']") # Simple replace
                python_code += f"    {var_name} = {src}.rolling({length}).mean()\n"
                vars_created.append(var_name)
                continue
                
        # Handle EMA: x = ema(close, 20)
        if 'ema(' in line:
            import re
            match = re.match(r'(\w+)\s*=\s*ema\(([^,]+),\s*(\d+)\)', line)
            if match:
                var_name, src, length = match.groups()
                src = src.replace('close', "df['Close']")
                python_code += f"    {var_name} = {src}.ewm(span={length}, adjust=False).mean()\n"
                vars_created.append(var_name)
                continue
    
    # Logic for crossovers (heuristic)
    # If we see 'crossover(a, b)', we assume it's a buy signal
    if 'crossover' in pine_code:
        python_code += "\n    # Logic for Crossover (Buy)\n"
        import re
        matches = re.findall(r'crossover\((\w+),\s*(\w+)\)', pine_code)
        for a, b in matches:
            python_code += f"    signals[{a} > {b}] = 1\n"
            
    if 'crossunder' in pine_code:
        python_code += "\n    # Logic for Crossunder (Sell)\n"
        import re
        matches = re.findall(r'crossunder\((\w+),\s*(\w+)\)', pine_code)
        for a, b in matches:
            python_code += f"    signals[{a} < {b}] = -1\n"
            
    python_code += "\n    return signals"
    return python_code

def display_backtest_results(results):
    st.markdown("### 📊 Performance Metrics")
    
    # Show Data Range
    if 'equity_curve' in results and not results['equity_curve'].empty:
        start_date = results['equity_curve']['date'].iloc[0].strftime('%Y-%m-%d')
        end_date = results['equity_curve']['date'].iloc[-1].strftime('%Y-%m-%d')
        duration = len(results['equity_curve'])
        st.caption(f"📅 Simulation Period: **{start_date}** to **{end_date}** ({duration} trading days)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Return", f"{results['total_return']:.2f}%",
                delta=f"{results['total_return']:.2f}%")
    
    with col2:
        st.metric("Annual Return", f"{results['annualized_return']:.2f}%")
    
    with col3:
        st.metric("Sharpe Ratio", f"{results['sharpe_ratio']:.2f}")
    
    with col4:
        st.metric("Max Drawdown", f"{results['max_drawdown']:.2f}%")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Trades", f"{results['total_trades']}")
    
    with col2:
        st.metric("Win Rate", f"{results['win_rate']:.2f}%")
    
    with col3:
        st.metric("Sortino Ratio", f"{results['sortino_ratio']:.2f}")
    
    st.markdown("### 📈 Equity Curve")
    equity_df = results['equity_curve']
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=equity_df['date'],
        y=equity_df['total_value'],
        mode='lines',
        name='Portfolio Value',
        line=dict(color='#6366f1', width=3),
        fill='tozeroy',
        fillcolor='rgba(99, 102, 241, 0.2)'
    ))
    
    fig.update_layout(
        template='plotly_dark',
        height=500,
        hovermode='x unified',
        plot_bgcolor='rgba(15, 23, 42, 0.8)',
        paper_bgcolor='rgba(15, 23, 42, 0.8)',
        font=dict(color='white'),
        xaxis_title='Date',
        yaxis_title='Portfolio Value ($)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    if 'trades' in results and len(results['trades']) > 0:
        st.markdown("### 📝 Trade History")
        trades_df = pd.DataFrame(results['trades'])
        st.dataframe(trades_df, use_container_width=True, hide_index=True)

def show_risk_management():
    """Risk management page"""
    st.markdown("## ⚠️ Risk Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ticker = st.text_input("Ticker", value="AAPL").upper()
    
    with col2:
        period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=3)
    
    if st.button("📊 Calculate Risk Metrics", type="primary", use_container_width=True):
        with st.spinner("Calculating risk metrics..."):
            try:
                stock_data = fetch_stock_data(ticker, period)
                df = stock_data['history']
                
                returns = df['Close'].pct_change().dropna()
                equity_curve = (1 + returns).cumprod() * 100000
                
                var_95 = RiskMetrics.calculate_var(returns, 0.95)
                var_99 = RiskMetrics.calculate_var(returns, 0.99)
                cvar_95 = RiskMetrics.calculate_cvar(returns, 0.95)
                dd_stats = RiskMetrics.get_drawdown_stats(equity_curve)
                risk_adj = RiskMetrics.calculate_risk_adjusted_returns(returns)
                
                st.markdown("### 📊 Risk Metrics")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("VaR (95%)", f"{var_95:.2%}")
                    st.metric("VaR (99%)", f"{var_99:.2%}")
                
                with col2:
                    st.metric("CVaR (95%)", f"{cvar_95:.2%}")
                    st.metric("Max Drawdown", f"{dd_stats['max_drawdown']:.2%}")
                
                with col3:
                    st.metric("Sharpe Ratio", f"{risk_adj['sharpe_ratio']:.2f}")
                    st.metric("Sortino Ratio", f"{risk_adj['sortino_ratio']:.2f}")
                
                st.markdown("### 📉 Drawdown Analysis")
                drawdowns = (equity_curve / equity_curve.cummax() - 1) * 100
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=drawdowns,
                    mode='lines',
                    name='Drawdown',
                    line=dict(color='#ef4444', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(239, 68, 68, 0.3)'
                ))
                
                fig.update_layout(
                    template='plotly_dark',
                    height=400,
                    hovermode='x unified',
                    plot_bgcolor='rgba(15, 23, 42, 0.8)',
                    paper_bgcolor='rgba(15, 23, 42, 0.8)',
                    font=dict(color='white'),
                    xaxis_title='Date',
                    yaxis_title='Drawdown (%)'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("### 📊 Returns Distribution")
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=returns * 100,
                    nbinsx=50,
                    name='Returns',
                    marker_color='#6366f1'
                ))
                
                fig.update_layout(
                    template='plotly_dark',
                    height=400,
                    plot_bgcolor='rgba(15, 23, 42, 0.8)',
                    paper_bgcolor='rgba(15, 23, 42, 0.8)',
                    font=dict(color='white'),
                    xaxis_title='Daily Returns (%)',
                    yaxis_title='Frequency'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error calculating risk metrics: {str(e)}")
                logger.error(f"Risk calculation error: {e}", exc_info=True)

def show_alerts():
    """Alerts management page"""
    st.markdown("## 🔔 Price Alerts & Signals")
    
    st.info("💡 Alerts are automatically generated when you analyze a stock. Check the Analysis page!")
    
    st.markdown("### ⚙️ Set Custom Alert")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        alert_ticker = st.text_input("Ticker", placeholder="e.g., AAPL").upper()
    
    with col2:
        alert_type = st.selectbox("Alert Type", 
                                 ["Price Above", "Price Below", "% Change", "Volume Spike"])
    
    with col3:
        alert_value = st.number_input("Threshold", value=0.0)
    
    if st.button("➕ Add Alert", type="primary", use_container_width=True):
        if alert_ticker:
            add_alert(st.session_state.user_id, alert_ticker, alert_type, alert_value)
            st.success(f"✅ Alert added for {alert_ticker}!")
            time.sleep(0.5)
            st.rerun()
    
    # Display user's alerts
    user_alerts = get_user_alerts(st.session_state.user_id)
    if user_alerts:
        st.markdown("### 📋 Your Active Alerts")
        for alert in user_alerts:
            alert_id, ticker, alert_type, threshold, created_at = alert
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                **{ticker}** - {alert_type}: {threshold}  
                *Created: {created_at}*
                """)
            with col2:
                if st.button("🗑️ Remove", key=f"alert_{alert_id}", use_container_width=True):
                    delete_alert(alert_id)
                    st.rerun()
    else:
        st.info("No custom alerts set. Add one above!")

def show_data_export():
    """Data export page"""
    st.markdown("## 📥 Data Export")
    
    st.markdown("""
    Export stock data in multiple formats for further analysis or integration with other tools.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_ticker = st.text_input("Ticker", value="AAPL").upper()
    
    with col2:
        export_period = st.selectbox("Period", 
                                    ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
                                    index=3)
    
    export_format = st.selectbox("Export Format", 
                                ["CSV", "JSON", "Excel", "Parquet"])
    
    include_indicators = st.checkbox("Include Technical Indicators", value=True)
    
    if st.button("📥 Generate Export", type="primary", use_container_width=True):
        with st.spinner("Preparing data..."):
            try:
                stock_data = fetch_stock_data(export_ticker, export_period)
                df = stock_data['history'].copy()
                
                if not include_indicators:
                    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                
                st.markdown("### 👀 Data Preview")
                st.dataframe(df.head(10), use_container_width=True)
                
                st.markdown(f"**Total Records:** {len(df)}")
                st.markdown(f"**Date Range:** {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
                
                format_lower = export_format.lower()
                file_data = export_data(df, export_ticker, format_lower)
                
                file_extension = {
                    'csv': 'csv',
                    'json': 'json',
                    'excel': 'xlsx',
                    'parquet': 'parquet'
                }[format_lower]
                
                mime_type = {
                    'csv': 'text/csv',
                    'json': 'application/json',
                    'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'parquet': 'application/octet-stream'
                }[format_lower]
                
                filename = f"{export_ticker}_{export_period}_{datetime.now().strftime('%Y%m%d')}.{file_extension}"
                
                st.download_button(
                    label=f"⬇️ Download {export_format}",
                    data=file_data,
                    file_name=filename,
                    mime=mime_type,
                    type="primary",
                    use_container_width=True
                )
                
                st.success(f"✅ Data ready for download! Click the button above to save {filename}")
                
            except Exception as e:
                st.error(f"Error exporting data: {str(e)}")
                logger.error(f"Export error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
