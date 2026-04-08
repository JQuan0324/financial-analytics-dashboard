"""
pages/options.py — Options Analytics Dashboard
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import norm
from datetime import datetime


# ── Black-Scholes functions
def bs_price(S, K, T, r, sigma, option_type="call"):
    if T <= 0 or sigma <= 0:
        return max(0, S - K) if option_type == "call" else max(0, K - S)
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == "call":
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def bs_greeks(S, K, T, r, sigma, option_type="call"):
    if T <= 0 or sigma <= 0:
        return {"Delta": 0, "Gamma": 0, "Theta": 0, "Vega": 0, "Rho": 0}
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    pdf_d1 = norm.pdf(d1)

    delta = norm.cdf(d1) if option_type == "call" else norm.cdf(d1) - 1
    gamma = pdf_d1 / (S * sigma * np.sqrt(T))
    theta_call = (-(S * pdf_d1 * sigma) / (2 * np.sqrt(T))
                  - r * K * np.exp(-r * T) * norm.cdf(d2))
    theta_put = (-(S * pdf_d1 * sigma) / (2 * np.sqrt(T))
                 + r * K * np.exp(-r * T) * norm.cdf(-d2))
    theta = theta_call / 365 if option_type == "call" else theta_put / 365
    vega = S * pdf_d1 * np.sqrt(T) / 100
    rho_call = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
    rho_put = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
    rho = rho_call if option_type == "call" else rho_put

    return {"Delta": delta, "Gamma": gamma, "Theta": theta, "Vega": vega, "Rho": rho}


def render():
    st.title("⚡ Options Analytics")
    st.markdown("Black-Scholes pricing, Greeks, and payoff diagrams for any option.")

    st.markdown("---")
    st.subheader("Option Parameters")

    col1, col2, col3 = st.columns(3)

    with col1:
        ticker_input = st.text_input("Ticker (for live price)", value="AAPL")
        use_live = st.checkbox("Use live spot price", value=True)
        if use_live:
            try:
                with st.spinner("Fetching price..."):
                    tk = yf.Ticker(ticker_input.upper())
                    S = float(tk.fast_info.last_price)
                st.success(f"Live price: ${S:.2f}")
            except Exception:
                S = 150.0
                st.warning("Could not fetch live price. Using $150.")
        else:
            S = st.number_input("Spot Price ($)", value=150.0, min_value=0.01)

    with col2:
        K = st.number_input("Strike Price ($)", value=float(round(S / 5) * 5) if use_live else 150.0, min_value=0.01, max_value=99999.0, step=1.0)
        T_days = st.number_input("Days to Expiry", value=30, min_value=1, max_value=730)
        T = T_days / 365
        option_type = st.selectbox("Option Type", ["call", "put"])

    with col3:
        sigma = st.slider("Implied Volatility (%)", 5, 150, 30) / 100
        r = st.slider("Risk-Free Rate (%)", 0, 10, 5) / 100

    # ── Pricing output
    price = bs_price(S, K, T, r, sigma, option_type)
    greeks = bs_greeks(S, K, T, r, sigma, option_type)
    intrinsic = max(0, S - K) if option_type == "call" else max(0, K - S)
    time_value = price - intrinsic

    st.markdown("---")
    st.subheader("Pricing Output")
    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("Option Price", f"${price:.4f}")
    p2.metric("Intrinsic Value", f"${intrinsic:.4f}")
    p3.metric("Time Value", f"${time_value:.4f}")
    moneyness = "ITM" if intrinsic > 0 else ("ATM" if abs(S - K) / S < 0.01 else "OTM")
    p4.metric("Moneyness", moneyness)
    p5.metric("IV", f"{sigma:.0%}")

    # ── Greeks
    st.markdown("---")
    st.subheader("Greeks")
    g1, g2, g3, g4, g5 = st.columns(5)
    g1.metric("Delta (Δ)", f"{greeks['Delta']:.4f}", help="Price sensitivity to $1 move in spot")
    g2.metric("Gamma (Γ)", f"{greeks['Gamma']:.4f}", help="Rate of change of Delta")
    g3.metric("Theta (Θ)", f"{greeks['Theta']:.4f}", help="Daily time decay")
    g4.metric("Vega (ν)", f"{greeks['Vega']:.4f}", help="Sensitivity to 1% change in IV")
    g5.metric("Rho (ρ)", f"{greeks['Rho']:.4f}", help="Sensitivity to 1% change in rates")

    # ── Payoff diagram
    st.markdown("---")
    st.subheader("Payoff Diagram at Expiry")

    spot_range = np.linspace(S * 0.5, S * 1.5, 200)
    if option_type == "call":
        payoff = np.maximum(spot_range - K, 0) - price
    else:
        payoff = np.maximum(K - spot_range, 0) - price

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=spot_range, y=payoff,
        mode="lines",
        name="P&L at Expiry",
        line=dict(color="#00C9A7", width=2),
        fill="tozeroy",
        fillcolor="rgba(0,201,167,0.1)",
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    fig.add_vline(x=S, line_dash="dash", line_color="#FFD166", annotation_text="Spot")
    fig.add_vline(x=K, line_dash="dash", line_color="#EF476F", annotation_text="Strike")

    fig.update_layout(
        template="plotly_dark", height=400,
        xaxis_title="Spot Price at Expiry ($)",
        yaxis_title="P&L ($)",
        margin=dict(l=40, r=20, t=20, b=40),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── IV surface (sensitivity table)
    st.markdown("---")
    st.subheader("Price Sensitivity Table")
    st.caption("Option price across different spot prices and IVs")

    spot_steps = np.linspace(S * 0.8, S * 1.2, 7)
    iv_steps = [0.15, 0.20, 0.25, 0.30, 0.40, 0.50]

    table = pd.DataFrame(index=[f"{iv:.0%}" for iv in iv_steps],
                         columns=[f"${s:.0f}" for s in spot_steps])
    for iv in iv_steps:
        for s in spot_steps:
            table.loc[f"{iv:.0%}", f"${s:.0f}"] = round(bs_price(s, K, T, r, iv, option_type), 2)

    st.dataframe(table, use_container_width=True)
