# 🎯 Apex Analysis - Quick Reference

## 🚀 Starting the App

### Windows
```bash
# Double-click this file:
run_app.bat

# Or run manually:
streamlit run streamlit_app.py
```

### Mac/Linux
```bash
streamlit run streamlit_app.py
```

**Dashboard URL:** http://localhost:8501

---

## 📊 Dashboard Pages

| Page | Purpose | Key Features |
|------|---------|--------------|
| 📊 Dashboard | Overview | Watchlist, quick stats, history |
| 📈 Analysis | Stock analysis | Charts, alerts, indicators |
| 🔄 Backtesting | Strategy testing | Performance metrics, equity curve |
| ⚠️ Risk | Risk metrics | VaR, CVaR, drawdowns |
| 🔔 Alerts | Alert management | Custom alerts, notifications |
| 📥 Export | Data export | CSV, JSON, Excel, Parquet |

---

## 🔔 Smart Alerts (Automatic)

The app automatically detects:

✅ **Bullish Signals**
- Price above MA20 & MA50
- RSI oversold (<30)
- MACD bullish crossover
- Near 52-week high

⚠️ **Bearish Signals**
- Price below MA20 & MA50
- RSI overbought (>70)
- MACD bearish crossover
- Near 52-week low

📢 **Other Alerts**
- Volume spikes (>1.5x average)
- Significant price moves (>3%)

---

## 📈 Technical Indicators

| Indicator | What it shows | Signal |
|-----------|---------------|--------|
| **RSI** | Momentum | >70 overbought, <30 oversold |
| **MACD** | Trend | Crossover = buy/sell signal |
| **MA20** | Short-term trend | Price above = bullish |
| **MA50** | Medium-term trend | Price above = bullish |
| **Bollinger Bands** | Volatility | Price at bands = reversal |
| **Volume** | Activity | High volume = strong move |

---

## 📥 Export Formats

| Format | Best For | File Size |
|--------|----------|-----------|
| **CSV** | Excel, spreadsheets | Medium |
| **JSON** | APIs, web apps | Medium |
| **Excel** | Business reports | Large |
| **Parquet** | Big data, Python | Small |

---

## ⚙️ Customization

### Add to Watchlist
1. Go to sidebar
2. Enter ticker (e.g., AAPL)
3. Click "➕ Add to Watchlist"

### Set Custom Alert
1. Go to 🔔 Alerts page
2. Enter ticker and threshold
3. Click "➕ Add Alert"

### Change Theme
Edit `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#6366f1"
backgroundColor = "#0f172a"
```

---

## 🎓 Tips & Tricks

💡 **Performance**
- Keep watchlist under 10 tickers
- Use shorter time periods for faster loading
- Data is cached for 5 minutes

💡 **Analysis**
- Start with 1y period for best balance
- Use "Indicators" chart for detailed analysis
- Check alerts before making decisions

💡 **Backtesting**
- Test multiple strategies
- Compare Sharpe ratios (>1 is good)
- Watch for max drawdown (<20% ideal)

💡 **Risk Management**
- VaR shows potential losses
- CVaR shows worst-case scenarios
- Monitor drawdowns regularly

---

## 🚀 Deployment to Cloud

### Streamlit Cloud (FREE)
1. Push to GitHub
2. Go to share.streamlit.io
3. Connect repository
4. Deploy!

See [DEPLOYMENT.md](DEPLOYMENT.md) for details.

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| App won't start | `pip install -r requirements.txt` |
| No data loading | Check internet, verify ticker |
| Charts not showing | `pip install plotly --upgrade` |
| Slow performance | Reduce watchlist size |

---

## 📚 Resources

- 📖 Full Documentation: [README.md](README.md)
- 🚀 Deployment Guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- 🐛 Report Issues: GitHub Issues
- 💬 Support: meridianaglo@gmail.com

---

**Made with ❤️ by MeridianAlgo**
