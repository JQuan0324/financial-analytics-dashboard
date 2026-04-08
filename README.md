# 📊 Financial Analytics Dashboard

A multi-page Streamlit dashboard for portfolio analysis, stock screening, and options pricing — built for traders, analysts, and finance professionals.

**Live Demo:** *(deploy link here)*

---

## Features

### 📂 Portfolio Analyzer
- Input any set of tickers with custom weights
- Performance metrics: Annual Return, Volatility, Sharpe Ratio, Max Drawdown, VaR (95%)
- Interactive equity curve and drawdown chart
- Correlation heatmap across holdings
- Per-stock performance breakdown table

### 🔍 Stock Screener
- Screen from S&P 500 sample or enter custom tickers
- Filter by return, volatility, and Sharpe ratio
- Return vs. Volatility scatter plot (bubble size = trading volume)
- Sortable results table with full metrics
- Top 10 by Sharpe bar chart

### ⚡ Options Analytics
- Black-Scholes pricing with live spot price (via yfinance)
- Full Greeks: Delta, Gamma, Theta, Vega, Rho
- Interactive payoff diagram at expiry
- Price sensitivity table across spot prices and implied volatilities

---

## Quickstart

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## Project Structure

```
finance_dashboard/
├── app.py                  # Main app + navigation
├── pages/
│   ├── portfolio.py        # Portfolio Analyzer
│   ├── screener.py         # Stock Screener
│   └── options.py          # Options Analytics
├── requirements.txt
└── README.md
```

---

## Deployment (Streamlit Cloud)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set main file as `app.py`
4. Deploy — free hosting, public URL

---

## Tech Stack

- **Streamlit** — UI framework
- **yfinance** — Market data
- **Plotly** — Interactive charts
- **SciPy** — Black-Scholes calculations
- **pandas / numpy** — Data processing

---

## License

MIT
