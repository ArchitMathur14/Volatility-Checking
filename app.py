import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from gs_quant.timeseries import volatility, Window

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="GS-Quant Market Analyzer", layout="wide")

# --- HEADER ---
st.title("⚡ Market Regime Analyzer")
st.markdown("""
**Powered by Goldman Sachs `gs-quant`**
This tool analyzes the "Volatility Regime" of an asset to determine if the market is currently in a state of *Panic* or *Stability*.
""")

# --- SIDEBAR INPUTS ---
st.sidebar.header("Configuration")
ticker = st.sidebar.text_input("Ticker Symbol", value="SPY", help="Enter a valid Yahoo Finance ticker (e.g., AAPL, BTC-USD, TSLA)")
period = st.sidebar.selectbox("Lookback Period", ["1y", "2y", "5y", "10y"], index=1)
vol_threshold = st.sidebar.slider("Volatility Alert Threshold (%)", 10, 50, 20)

# --- CACHED DATA FUNCTION (Speeds up the app) ---
@st.cache_data
def get_data(ticker, period):
    data = yf.download(ticker, period=period, progress=False)
    return data['Adj Close']

# --- MAIN ANALYTICS ---
try:
    # 1. Fetch Data
    with st.spinner(f"Fetching data for {ticker}..."):
        prices = get_data(ticker, period)

    # 2. Apply GS-Quant Logic
    # Calculate Rolling Volatility (22-day window ~ 1 trading month)
    vol_series = volatility(prices, Window(22, 0))
    
    # Get latest values for metrics
    current_price = prices.iloc[-1]
    current_vol = vol_series.iloc[-1] * 100 # Convert to percentage
    
    # 3. Display Key Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Price", f"${current_price:.2f}")
    col2.metric("30-Day Volatility", f"{current_vol:.2f}%", delta_color="inverse")
    
    # Determine Regime
    if current_vol > vol_threshold:
        status = "🔴 HIGH VOLATILITY (Defensive)"
        col3.error(status)
    else:
        status = "🟢 NORMAL VOLATILITY (Stable)"
        col3.success(status)

    # 4. Visualization (The Dual-Axis Chart)
    st.subheader("Price vs. Volatility Regime")
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot Price (Left Axis)
    color_price = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price ($)', color=color_price)
    ax1.plot(prices.index, prices, color=color_price, label="Asset Price")
    ax1.tick_params(axis='y', labelcolor=color_price)
    ax1.grid(True, alpha=0.3)

    # Plot Volatility (Right Axis)
    ax2 = ax1.twinx()
    color_vol = 'tab:red'
    ax2.set_ylabel('Annualized Volatility (%)', color=color_vol)
    ax2.plot(vol_series.index, vol_series * 100, color=color_vol, linestyle='--', label="Volatility (GS Model)")
    ax2.tick_params(axis='y', labelcolor=color_vol)
    
    # Add a horizontal line for the threshold
    ax2.axhline(y=vol_threshold, color='gray', linestyle=':', alpha=0.5, label=f"Threshold ({vol_threshold}%)")

    st.pyplot(fig)

    # 5. Data View (Optional expansion)
    with st.expander("View Raw Data"):
        st.dataframe(prices.tail(30))

except Exception as e:
    st.error(f"Error: Could not fetch data for ticker '{ticker}'. Please check the symbol.")
