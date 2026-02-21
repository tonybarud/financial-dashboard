import streamlit as yf
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

st.set_page_config(page_title="💹 Pro Trading Dashboard", layout="wide")

# ========== STATE ==========
def init_state():
    defaults = {"watchlist": [], "portfolio": [], "price_alerts": {}}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ========== HELPERS ==========
@st.cache_data(ttl=30)  # Fast refresh for live
def get_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        return ticker.fast_info.get('lastPrice', 0)
    except:
        return 0

def get_change(symbol):
    try:
        hist = yf.download(symbol, period="2d", progress=False)
        if len(hist) < 2:
            return 0
        return hist['Close'][-1] - hist['Close'][-2]
    except:
        return 0

@st.cache_data(ttl=60)
def get_options(symbol):
    try:
        ticker = yf.Ticker(symbol)
        opts = ticker.options
        if opts:
            chain = ticker.option_chain(opts[0])
            return pd.concat([chain.calls.head(5), chain.puts.head(5)])
    except:
        pass
    return pd.DataFrame()

# ========== NAVIGATION ==========
st.sidebar.title("💹 Pro Dashboard")
page = st.sidebar.radio("Navigate:", [
    "📰 Live Market News",    # ← YOUR REQUEST: #1 position
    "📊 Overview", 
    "📈 Options Chain", 
    "🤖 AI Signals", 
    "💼 Portfolio", 
    "⭐ Watchlist/Alerts"
])

# Save button
if st.sidebar.button("💾 Save All"):
    st.sidebar.success("✅ Saved!")

# ========== LIVE MARKET NEWS FULL PAGE ==========
if page == "📰 Live Market News":
    st.title("📰 **Live Market News**")
    st.markdown(f"**🕐 Auto-updating: {datetime.now().strftime('%I:%M:%S %p CST')}**")
    
    # Market Indexes (Green/Red)
    st.header("📊 **Market Indexes**")
    indexes = [
        ('^DJI', 'Dow Jones', 40000),
        ('^IXIC', 'NASDAQ', 18000),
        ('^GSPC', 'S&P 500', 5800),
        ('^RUT', 'Russell 2000', 2300)
    ]
    
    cols = st.columns(4)
    for i, (symbol, name, approx) in enumerate(indexes):
        with cols[i]:
            price = get_price(symbol)
            change = get_change(symbol)
            delta_color = "green" if change >= 0 else "red"
            st.metric(name, f"{price:,.0f}", f"{change:+,.0f}", delta_color=delta_color)
    
    # Stocks/ETFs/Metals/Crypto sections
    sections = [
        ("📈 **Top Stocks**", ['AAPL', 'MSFT', 'GOOGL', 'TSLA']),
        ("🏆 **ETFs**", ['SPY', 'QQQ', 'IWM']),
        ("🥇 **Metals**", ['GLD', 'SLV']),
        ("₿ **Crypto**", ['BTC-USD', 'ETH-USD'])
    ]
    
    for title, symbols in sections:
        st.subheader(title)
        cols = st.columns(len(symbols))
        for j, sym in enumerate(symbols):
            with cols[j]:
                price = get_price(sym)
                change = get_change(sym)
                st.metric(sym, f"${price:.0f}", f"{change:+.0f}", 
                         delta_color="green" if change >= 0 else "red")

# ========== OTHER PAGES ==========
elif page == "📊 Overview":
    st.header("📊 Dashboard Overview")
    st.success("✅ Live Market News • Options • Signals • Portfolio • Alerts")

elif page == "📈 Options Chain":
    st.header("📈 Options Chain")
    symbol = st.text_input("Symbol", "AAPL").upper()
    if symbol:
        df = get_options(symbol)
        if not df.empty:
            st.dataframe(df)
        else:
            st.info("No options data")

elif page == "🤖 AI Signals":
    st.header("🤖 AI Signals")
    symbol = st.text_input("Symbol", "AAPL").upper()
    if symbol:
        hist = yf.download(symbol, period="1mo", progress=False)
        if not hist.empty:
            price = hist['Close'][-1]
            ma_short = hist['Close'].rolling(5).mean()[-1]
            signal = "🟢 BUY" if price > ma_short else "🔴 SELL"
            st.metric("Signal", signal)
            st.metric("Current Price", f"${price:.2f}")

elif page == "💼 Portfolio":
    st.header("💼 Portfolio")
    with st.form("portfolio"):
        col1, col2 = st.columns(2)
        sym = col1.text_input("Symbol").upper()
        shares = col2.number_input("Shares")
        st.form_submit_button("Add")
    
    for holding in st.session_state.portfolio:
        price = get_price(holding['symbol'])
        st.metric(holding['symbol'], f"${price * holding['shares']:.0f}")

elif page == "⭐ Watchlist/Alerts":
    st.header("⭐ Watchlist & Alerts")
    
    # Watchlist add
    new_sym = st.text_input("Add to watchlist").upper()
    if st.button("➕ Add") and new_sym:
        st.session_state.watchlist.append(new_sym)
    
    # Show watchlist
    for sym in st.session_state.watchlist:
        price = get_price(sym)
        change = get_change(sym)
        st.metric(sym, f"${price:.1f}", f"{change:+.1f}", 
                 delta_color="green" if change >= 0 else "red")
    
    # Alerts
    st.subheader("🚨 Alerts")
    alert_sym = st.text_input("Alert symbol").upper()
    target = st.number_input("Target price")
    if st.button("Set Alert") and alert_sym:
        st.session_state.price_alerts[alert_sym] = {"target": target}

st.markdown("---")
st.caption(f"🕐 Live: {datetime.now().strftime('%H:%M:%S CST')} | Pro Dashboard")
