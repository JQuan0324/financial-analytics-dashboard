"""
app.py — Financial Analytics Dashboard
---------------------------------------
Run with:
    streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Financial Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar navigation
st.sidebar.title("📊 Financial Dashboard")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate",
    ["Portfolio Analyzer", "Stock Screener", "Options Analytics"],
    index=0,
)
st.sidebar.markdown("---")
st.sidebar.caption("Built with Python · yfinance · Streamlit")

# ── Page routing
if page == "Portfolio Analyzer":
    from pages.portfolio import render
    render()
elif page == "Stock Screener":
    from pages.screener import render
    render()
elif page == "Options Analytics":
    from pages.options import render
    render()
