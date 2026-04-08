"""
pages/screener.py — Stock Screener
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px


SP500_SAMPLE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
    "UNH", "JNJ", "JPM", "V", "PG", "MA", "HD", "CVX", "MRK", "ABBV",
    "PEP", "KO", "BAC", "PFE", "TMO", "COST", "DIS", "CSCO", "WMT",
    "ABT", "MCD", "NEE", "ACN", "LIN", "DHR", "NKE", "ADBE", "CRM",
    "TXN", "PM", "ORCL", "QCOM", "AMD", "INTC", "AMGN", "HON", "IBM",
]


@st.cache_data(ttl=3600)
def fetch_screener_data(tickers, period="1y"):
    rows = []
    progress = st.progress(0, text="Fetching stock data...")
    for i, ticker in enumerate(tickers):
        try:
            raw = yf.download(ticker, period=period, progress=False, auto_adjust=True)
            if raw.empty:
                continue
            close = raw["Close"].squeeze()
            if len(close) < 2:
                continue

            returns = close.pct_change().dropna()
            total_ret = float((close.iloc[-1] / close.iloc[0]) - 1)
            volatility = float(returns.std() * np.sqrt(252))
            sharpe = float((returns.mean() * 252 - 0.04) / volatility) if volatility != 0 else 0

            roll_max = close.cummax()
            max_dd = float(((close - roll_max) / roll_max).min())
            avg_vol = float(raw["Volume"].squeeze().mean())

            rows.append({
                "Ticker": ticker,
                "Price": round(float(close.iloc[-1]), 2),
                "1Y Return": total_ret,
                "Volatility": volatility,
                "Sharpe": sharpe,
                "Max Drawdown": max_dd,
                "Avg Volume (M)": round(avg_vol / 1e6, 2),
                "Market Cap (B)": None,
            })
        except Exception:
            pass
        progress.progress((i + 1) / len(tickers), text=f"Fetching {ticker}...")

    progress.empty()
    return pd.DataFrame(rows)


def render():
    st.title("🔍 Stock Screener")
    st.markdown("Screen stocks by return, volatility, and risk-adjusted performance.")

    # ── Controls
    col1, col2 = st.columns([2, 1])
    with col1:
        custom_input = st.text_input(
            "Custom tickers (leave blank to use S&P 500 sample)",
            placeholder="e.g. AAPL, TSLA, NVDA, MSFT",
        )
    with col2:
        period = st.selectbox("Lookback Period", ["6mo", "1y", "2y", "3y"], index=1)

    tickers = (
        [t.strip().upper() for t in custom_input.split(",") if t.strip()]
        if custom_input else SP500_SAMPLE
    )

    if st.button("Run Screener", type="primary"):
        df = fetch_screener_data(tickers, period)

        if df.empty:
            st.error("No data returned.")
            return

        filtered = df.copy()

        st.caption(f"Showing {len(filtered)} of {len(df)} stocks")

        # ── Scatter: Return vs Volatility
        st.markdown("---")
        st.subheader("Return vs. Volatility")
        if not filtered.empty:
            fig = px.scatter(
                filtered,
                x="Volatility", y="1Y Return",
                text="Ticker",
                color="Sharpe",
                size="Avg Volume (M)",
                color_continuous_scale="RdYlGn",
                hover_data=["Price", "Market Cap (B)", "Max Drawdown"],
            )
            fig.update_traces(textposition="top center", textfont_size=10)
            fig.update_layout(
                template="plotly_dark", height=500,
                xaxis_tickformat=".0%", yaxis_tickformat=".0%",
                margin=dict(l=40, r=20, t=20, b=40),
            )
            fig.add_hline(y=0, line_dash="dot", line_color="gray")
            st.plotly_chart(fig, use_container_width=True)

        # ── Table
        st.markdown("---")
        st.subheader("Screener Results")

        display = filtered.copy()
        display["1Y Return"] = display["1Y Return"].map("{:+.2%}".format)
        display["Volatility"] = display["Volatility"].map("{:.2%}".format)
        display["Sharpe"] = display["Sharpe"].map("{:.2f}".format)
        display["Max Drawdown"] = display["Max Drawdown"].map("{:.2%}".format)

        st.dataframe(
            display.sort_values("Sharpe", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

        # ── Top performers bar chart
        st.markdown("---")
        st.subheader("Top 10 by Sharpe Ratio")
        top10 = filtered.nlargest(10, "Sharpe")
        fig_bar = px.bar(
            top10, x="Ticker", y="Sharpe",
            color="Sharpe", color_continuous_scale="Teal",
            text="Sharpe",
        )
        fig_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_bar.update_layout(template="plotly_dark", height=350,
                              margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)
