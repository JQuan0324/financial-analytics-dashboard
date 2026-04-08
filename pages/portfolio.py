"""
pages/portfolio.py — Portfolio Analyzer
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


def get_data(tickers, start, end):
    raw = yf.download(tickers, start=start, end=end, progress=False, auto_adjust=True)
    if len(tickers) == 1:
        prices = raw[["Close"]].copy()
        prices.columns = tickers
    else:
        prices = raw["Close"].copy()
    prices.dropna(how="all", inplace=True)
    return prices


def calc_metrics(returns, weights, rf=0.04):
    weights = np.array(weights)
    port_returns = returns @ weights

    ann_return = port_returns.mean() * 252
    ann_vol = port_returns.std() * np.sqrt(252)
    sharpe = (ann_return - rf) / ann_vol if ann_vol != 0 else 0

    cumulative = (1 + port_returns).cumprod()
    roll_max = cumulative.cummax()
    drawdown = (cumulative - roll_max) / roll_max
    max_dd = drawdown.min()

    # VaR 95%
    var_95 = np.percentile(port_returns, 5)

    return {
        "Annual Return": ann_return,
        "Annual Volatility": ann_vol,
        "Sharpe Ratio": sharpe,
        "Max Drawdown": max_dd,
        "VaR (95%, daily)": var_95,
        "port_returns": port_returns,
        "cumulative": cumulative,
        "drawdown": drawdown,
    }


def render():
    st.title("📂 Portfolio Analyzer")
    st.markdown("Enter your portfolio holdings to analyze risk, return, and diversification.")

    # ── Input section
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Holdings")
        default_tickers = "AAPL, MSFT, GOOGL, NVDA, SPY"
        ticker_input = st.text_input(
            "Tickers (comma-separated)",
            value=default_tickers,
            help="Enter Yahoo Finance ticker symbols separated by commas"
        )

    with col2:
        st.subheader("Period")
        start_date = st.date_input("Start Date", value=pd.to_datetime("2020-01-01"))
        end_date = st.date_input("End Date", value=pd.to_datetime("2024-12-31"))

    tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

    if not tickers:
        st.warning("Enter at least one ticker.")
        return

    # ── Weights
    st.subheader("Weights")
    st.caption("Adjust portfolio weights (must sum to 100%)")

    weight_cols = st.columns(len(tickers))
    weights = []
    equal_w = round(100 / len(tickers), 1)

    for i, (col, ticker) in enumerate(zip(weight_cols, tickers)):
        w = col.number_input(ticker, min_value=0.0, max_value=100.0, value=equal_w, step=0.5)
        weights.append(w)

    total_weight = sum(weights)
    if abs(total_weight - 100) > 0.1:
        st.error(f"Weights sum to {total_weight:.1f}% — must equal 100%")
        return

    weights_norm = [w / 100 for w in weights]

    # ── Run analysis
    if st.button("Analyze Portfolio", type="primary"):
        with st.spinner("Fetching data..."):
            try:
                prices = get_data(tickers, str(start_date), str(end_date))
            except Exception as e:
                st.error(f"Failed to fetch data: {e}")
                return

        missing = [t for t in tickers if t not in prices.columns]
        if missing:
            st.warning(f"Could not fetch: {', '.join(missing)}")
            tickers = [t for t in tickers if t in prices.columns]
            weights_norm = weights_norm[:len(tickers)]

        if not tickers:
            st.error("No valid tickers.")
            return

        prices = prices[tickers].dropna()
        returns = prices.pct_change().dropna()

        metrics = calc_metrics(returns, weights_norm)

        # ── Metrics row
        st.markdown("---")
        st.subheader("Performance Summary")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Annual Return", f"{metrics['Annual Return']:+.2%}")
        m2.metric("Annual Volatility", f"{metrics['Annual Volatility']:.2%}")
        m3.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
        m4.metric("Max Drawdown", f"{metrics['Max Drawdown']:.2%}")
        m5.metric("VaR (95%)", f"{metrics['VaR (95%, daily)']:.2%}")

        # ── Charts
        st.markdown("---")
        chart_col1, chart_col2 = st.columns([3, 1])

        with chart_col1:
            # Equity curve
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                row_heights=[0.65, 0.35],
                                subplot_titles=["Portfolio Cumulative Return", "Drawdown (%)"],
                                vertical_spacing=0.08)

            fig.add_trace(go.Scatter(
                x=metrics["cumulative"].index,
                y=metrics["cumulative"],
                name="Portfolio",
                line=dict(color="#00C9A7", width=2),
            ), row=1, col=1)

            fig.add_trace(go.Scatter(
                x=metrics["drawdown"].index,
                y=metrics["drawdown"] * 100,
                name="Drawdown",
                fill="tozeroy",
                line=dict(color="#FF6B6B", width=1),
                fillcolor="rgba(255,107,107,0.3)",
            ), row=2, col=1)

            fig.update_layout(
                template="plotly_dark", height=450,
                margin=dict(l=40, r=20, t=40, b=20),
                hovermode="x unified", showlegend=False,
            )
            fig.update_yaxes(title_text="Growth of $1", row=1, col=1)
            fig.update_yaxes(title_text="Drawdown %", row=2, col=1)
            st.plotly_chart(fig, use_container_width=True)

        with chart_col2:
            # Allocation pie
            fig_pie = px.pie(
                names=tickers,
                values=weights,
                title="Allocation",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            fig_pie.update_layout(
                template="plotly_dark", height=450,
                margin=dict(l=20, r=20, t=40, b=20),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # ── Correlation heatmap
        st.markdown("---")
        st.subheader("Correlation Matrix")
        corr = returns.corr()
        fig_corr = px.imshow(
            corr,
            color_continuous_scale="RdYlGn",
            zmin=-1, zmax=1,
            text_auto=".2f",
        )
        fig_corr.update_layout(template="plotly_dark", height=350,
                               margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_corr, use_container_width=True)

        # ── Individual stock performance table
        st.markdown("---")
        st.subheader("Individual Stock Performance")
        rows = []
        for ticker in tickers:
            r = returns[ticker]
            total_ret = (1 + r).prod() - 1
            vol = r.std() * np.sqrt(252)
            sharpe = (r.mean() * 252 - 0.04) / vol if vol != 0 else 0
            rows.append({
                "Ticker": ticker,
                "Total Return": f"{total_ret:+.2%}",
                "Ann. Volatility": f"{vol:.2%}",
                "Sharpe": f"{sharpe:.2f}",
                "Weight": f"{weights_norm[tickers.index(ticker)]:.1%}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
