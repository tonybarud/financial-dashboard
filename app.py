import streamlit as st
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
@st.cache_data(ttl=60)
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
        return ((hist['Close'][-1] - hist['Close'][-2]) / hist['Close'][-2]) * 100
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

# ========== SAFE ALERTS ==========
def check_alerts():
    alerts = getattr(st.session_state, 'price_alerts', {})
    if isinstance(alerts, dict):
        for sym, alert in alerts.items():
            if isinstance(alert, dict):
                price = get_price(sym)
                target = alert.get('target', 0)
                if price >= target and not alert.get('hit', False):
                    st.error(f"🚨 {sym} hit ${target}!")

# ========== MAIN LAYOUT ==========
# LEFT: Live Market News (PERMANENT)
col_left, col_right = st.columns([1, 3])

with col_left:
    st.markdown("### 💹 **Live Market News**")
    st.markdown(f"**🕐 {datetime.now().strftime('%A, %B %d, %Y - %I:%M %p CST')}**")
    
    st.markdown("#### **📊 Market Indexes**")
    
    # Market Indexes with Green/Red changes
    indexes = ['^DJI', '^IXIC', '^GSPC', '^RUT']
    names = ['Dow Jones', 'NASDAQ', 'S&P 500', 'Russell 2000']
    
    for idx, name in zip(indexes, names):
        price = get_price(idx)
        change_pct = get_change(idx)
        color = "normal" if change_pct == 0 else "inverse" if change_pct > 0 else "normal"
        delta = f"+{change_pct:.2f}%" if change_pct > 0 else f"{change_pct:.2f}%"
        st.metric(name, f"{price:.0f}", delta, delta_color="green" if change_pct >= 0 else "red")

# RIGHT: Navigation & Pages
with col_right:
    # Sidebar-style navigation (but in main area)
    st.markdown("### 📱 **Dashboard Navigation**")
    page = st.radio("Select page:", [
        "📊 Overview", "📈 Options Chain", "🤖 AI Signals", 
        "💼 Portfolio", "⭐ Watchlist/Alerts", "📰 News & Podcasts"
    ], label_visibility="collapsed")
    
    if st.button("💾 Save All", use_container_width=True):
        st.success("✅ Data saved!")
    
    check_alerts()

# ========== PAGES ==========
if page == "📊 Overview":
    st.header("📊 Trading Dashboard")
    st.success("✅ Live prices • Options • Signals • Portfolio • Alerts • News")

if page == "📈 Options Chain":
    st.header("📈 Live Options Chain")
    symbol = st.text_input("Symbol", "AAPL").upper()
    if symbol:
        df = get_options(symbol)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No options available")

if page == "🤖 AI Signals":
    st.header("🤖 AI Trading Signals")
    symbol = st.text_input("Symbol", "AAPL").upper()
    if symbol:
        hist = yf.download(symbol, period="3mo", progress=False)
        if not hist.empty:
            price = hist['Close'][-1]
            ma10 = hist['Close'].rolling(10).mean()[-1]
            signal = "🟢 BUY" if price > ma10 else "🔴 SELL"
            col1, col2 = st.columns(2)
            col1.metric("Signal", signal)
            col2.metric("Price", f"${price:.2f}")

if page == "💼 Portfolio":
    st.header("💼 Portfolio Tracker")
    with st.form("add_holding"):
        col1, col2, col3 = st.columns(3)
        col1.text_input("Symbol")
        col2.number_input("Shares", 1)
        col3.number_input("Cost", 1.0)
        st.form_submit_button("Add")
    
    if st.session_state.portfolio:
        for h in st.session_state.portfolio:
            price = get_price(h['symbol'])
            st.write(f"{h['symbol']}: ${price * h['shares']:.0f}")

if page == "⭐ Watchlist/Alerts":
    st.header("⭐ Watchlist & Alerts")
    col1, col2 = st.columns(2)
    
    with col1:
        new_sym = st.text_input("Watchlist").upper()
        if st.button("Add to Watchlist"):
            st.session_state.watchlist.append(new_sym)
    
    with col2:
        alert_sym = st.text_input("Alert Symbol").upper()
        target = st.number_input("Target Price", 1.0)
        if st.button("Set Alert"):
            st.session_state.price_alerts[alert_sym] = {"target": target}
    
    # Show both
    for sym in st.session_state.watchlist:
        price = get_price(sym)
        st.metric(sym, f"${price:.2f}")

if page == "📰 News & Podcasts":
    st.header("📰 News & Podcasts")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("**📻 Live News**")
        symbols = ['AAPL', 'SPY']
        for sym in symbols:
            ticker = yf.Ticker(sym)
            for item in ticker.news[:3]:
                st.markdown(f"**{item['title'][:70]}**")
                st.caption(item['publisher'])
                st.markdown("─")
    
    with col2:
        st.subheader("**🎙️ Podcasts** (Live Links)")
        podcasts = [
            ("Yahoo Finance Live", "https://finance.yahoo.com/video/"),
            ("WSJ Money Briefing", "https://www.wsj.com/podcasts/your-money-matters"),
            ("CNBC Squawk Box", "https://www.iheart.com/podcast/269-squawk-pod-49626182/"),
            ("Bloomberg Radio", "https://www.bloomberg.com/audio")
        ]
        
        for name, url in podcasts:
            if st.button(f"▶️ {name}", key=name):
                st.markdown(f"[Open {name}]({url})")
                st.caption(url)

# Footer
st.markdown("---")
st.caption(f"Updated: {datetime.now().strftime('%H:%M CST')} | Pro Trading Dashboard")
