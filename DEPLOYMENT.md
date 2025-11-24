# 🚀 Deploying Apex Analysis to Streamlit Cloud

## Quick Deploy (Recommended)

### Option 1: Streamlit Community Cloud (FREE)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add Streamlit app"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your repository: `MeridianAlgo/Apex-Analysis`
   - Main file path: `streamlit_app.py`
   - Click "Deploy"!

3. **Your app will be live at:**
   ```
   https://apex-analysis.streamlit.app
   ```

### Option 2: Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

## Features ✨

### 📊 Dashboard
- Real-time stock metrics for your watchlist
- Quick overview of price changes
- Recent analysis history

### 📈 Analysis
- **Beautiful Charts**: Candlestick and technical indicator charts
- **Smart Alerts**: Automatic detection of:
  - Moving average crossovers
  - RSI overbought/oversold conditions
  - Volume spikes
  - 52-week high/low proximity
  - MACD crossovers
  - Significant price movements
- **Technical Indicators**: RSI, MACD, Moving Averages, Bollinger Bands

### 🔄 Backtesting
- Test trading strategies on historical data
- MA Crossover, RSI Mean Reversion, MACD Momentum
- Comprehensive performance metrics:
  - Total & Annualized Returns
  - Sharpe & Sortino Ratios
  - Max Drawdown
  - Win Rate
- Visual equity curve

### ⚠️ Risk Management
- Value at Risk (VaR) at 95% and 99%
- Conditional VaR (CVaR)
- Drawdown analysis with visualization
- Returns distribution histogram
- Sharpe and Sortino ratios

### 🔔 Alerts
- Automatic alerts on analysis
- Custom alert setup:
  - Price above/below threshold
  - Percentage change alerts
  - Volume spike alerts
- Alert management dashboard

### 📥 Data Export
- Export in multiple formats:
  - **CSV**: For Excel/spreadsheets
  - **JSON**: For APIs/web apps
  - **Excel**: Native .xlsx format
  - **Parquet**: For big data tools
- Optional technical indicators inclusion
- Data preview before download

## Configuration

### Theme Customization
Edit `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#6366f1"  # Purple
backgroundColor = "#0f172a"  # Dark blue
secondaryBackgroundColor = "#1e293b"  # Lighter dark blue
textColor = "#ffffff"  # White
```

### Watchlist
Default watchlist: AAPL, GOOGL, MSFT, TSLA

Add/remove tickers in the sidebar!

## Environment Variables (Optional)

For production deployment, you can set:

```bash
# In Streamlit Cloud: Settings > Secrets
# Add to .streamlit/secrets.toml locally

[general]
cache_ttl = 3600
max_watchlist_size = 20
```

## Performance Tips

1. **Caching**: The app uses Streamlit's caching for data fetching
2. **Watchlist**: Keep watchlist under 10 tickers for faster loading
3. **Period**: Shorter periods load faster (1mo vs 5y)

## Troubleshooting

### App won't start
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Data not loading
- Check internet connection
- Verify ticker symbol is valid
- Try a different time period

### Charts not displaying
```bash
# Update plotly
pip install plotly --upgrade
```

## Support

- 📧 Email: support@apexanalysis.com
- 🐛 Issues: [GitHub Issues](https://github.com/MeridianAlgo/Apex-Analysis/issues)
- 📚 Docs: [Full Documentation](https://github.com/MeridianAlgo/Apex-Analysis)

## License

Educational use only. See LICENSE file.

---

**Made with ❤️ using Streamlit**
