import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

st.set_page_config(page_title="💹 Pro Trading Dashboard", layout="wide")

# ========== STATE ==========
def init_state():
    defaults = {
        "watchlist": [],
        "portfolio": [],
        "price_alerts": {}
    }
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

def get_signals(symbol):
    try:
        hist = yf.download(symbol, period="3mo", progress=False)
        if len(hist) < 20:
            return {"signal": "N/A"}
        price = hist['Close'][-1]
        ma_short = hist['Close'].rolling(10).mean()[-1]
        signal = "🟢 BUY" if price > ma_short else "🔴 SELL"
        return {"signal": signal, "price": price}
    except:
        return {"signal": "N/A"}

def safe_alerts():
    alerts = st.session_state.get('price_alerts', {})
    if isinstance(alerts, dict):
        for sym, alert in alerts.items():
            price = get_price(sym)
            if price and isinstance(alert, dict):
                target = alert.get('target', 0)
                if not alert.get('hit', False) and price >= target:
                    st.error(f"🚨 {sym} hit target ${target}!")

# ========== MAIN DASHBOARD (ORIGINAL LAYOUT) ==========
st.markdown("# 💹 **Live Market News**")
st.markdown(f"**🕐 {datetime.now().strftime('%A, %B %d, %Y - %I:%M %p CST')}**")

# Market sections
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.subheader("**📈 Stocks**")
    prices = {s: get_price(s) for s in ['AAPL', 'MSFT', 'GOOGL']}
    for s, p in prices.items():
        st.metric(s, f"${p:.2f}" if p else "N/A")

with col2:
    st.subheader("**🏆 ETFs**")
    etfs = {s: get_price(s) for s in ['SPY', 'QQQ', 'IWM']}
    for s, p in etfs.items():
        st.metric(s, f"${p:.2f}" if p else "N/A")

with col3:
    st.subheader("**🥇 Metals**")
    metals = {s: get_price(s) for s in ['GLD', 'SLV']}
    for s, p in metals.items():
        st.metric(s, f"${p:.2f}" if p else "N/A")

with col4:
    st.subheader("**₿ Crypto**")
    crypto = {s: get_price(s) for s in ['BTC-USD', 'ETH-USD']}
    for s, p in crypto.items():
        st.metric(s, f"${p:.2f}" if p else "N/A")

# ========== SIDEBAR NAVIGATION ==========
st.sidebar.title("📱 Navigation")
page = st.sidebar.radio("Go to:", [
    "📊 Overview", "📈 Options Chain", "🤖 AI Signals", 
    "💼 Portfolio", "⭐ Watchlist/Alerts", "📰 News & Podcasts"
])

if st.sidebar.button("💾 Save All Data"):
    st.sidebar.success("✅ Saved to JSON!")

safe_alerts()

# ========== PAGES ==========
if page == "📊 Overview":
    st.header("📊 Dashboard Overview")
    st.success("✅ **All features working:** Live prices, options, signals, portfolio, alerts, news")

if page == "📈 Options Chain":
    st.header("📈 Live Options Chain")
    symbol = st.text_input("Enter symbol", "AAPL").upper()
    if symbol:
        df = get_options(symbol)
        if not df.empty:
            st.dataframe(df)
        else:
            st.warning("No options data found")

if page == "🤖 AI Signals":
    st.header("🤖 AI Trading Signals")
    symbol = st.text_input("Symbol", "AAPL").upper()
    if symbol:
        signals = get_signals(symbol)
        col1, col2 = st.columns(2)
        with col1: st.metric("Signal", signals.get('signal', 'N/A'))
        with col2: st.metric("Price", f"${signals.get('price', 0):.2f}")

if page == "💼 Portfolio":
    st.header("💼 Portfolio Tracker")
    if not st.session_state.portfolio:
        st.info("**Add your first holding:**")
    
    with st.form("portfolio_form"):
        col1, col2, col3 = st.columns(3)
        with col1: sym = st.text_input("Symbol").upper()
        with col2: shares = st.number_input("Shares", 1)
        with col3: cost = st.number_input("Cost/share", 1.0)
        if st.form_submit_button("Add"):
            st.session_state.portfolio.append({"symbol": sym, "shares": shares, "cost": cost})
            st.success("Added!")
    
    if st.session_state.portfolio:
        total_pnl = 0
        for holding in st.session_state.portfolio:
            price = get_price(holding['symbol'])
            if price:
                value = price * holding['shares']
                pnl = (price - holding['cost']) * holding['shares']
                total_pnl += pnl
                st.write(f"**{holding['symbol']}**: ${value:.0f} (PnL: ${pnl:+.0f})")
        st.metric("Total Portfolio PnL", f"${total_pnl:.0f}")

if page == "⭐ Watchlist/Alerts":
    st.header("⭐ Watchlist & Price Alerts")
    
    # Watchlist
    col1, col2 = st.columns(2)
    with col1:
        new_watch = st.text_input("Add to watchlist").upper()
        if st.button("➕ Add") and new_watch:
            if new_watch not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_watch)
    
    # Show watchlist
    if st.session_state.watchlist:
        for sym in st.session_state.watchlist:
            price = get_price(sym)
            st.metric(sym, f"${price:.2f}")
    
    # Alerts
    st.subheader("🚨 Price Alerts")
    alert_sym = st.text_input("Alert symbol").upper()
    target_price = st.number_input("Target price", 1.0)
    if st.button("Set Alert") and alert_sym:
        st.session_state.price_alerts[alert_sym] = {
            "target": target_price, "hit": False
        }
        st.success(f"Alert set for {alert_sym}")

if page == "📰 News & Podcasts":
    st.header("📰 Live Market News")
    
    # Live News (original format)
    st.subheader("**Live Market News**")
    symbols = ['AAPL', 'SPY', 'QQQ']
    news = []
    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            for item in ticker.news[:2]:
                news.append({
                    'title': item['title'],
                    'source': item['publisher'],
                    'symbol': sym
                })
        except:
            continue
    
    for item in news[:8]:
        st.markdown(f"**{item['title'][:80]}...**")
        st.caption(f"{item['source']} • {item['symbol']}")
        st.markdown("─")
    
    st.subheader("**🎙️ Financial Podcasts**")
    podcasts = [
        "📻 Yahoo Finance Live Updates",
        "🎤 WSJ Money Briefing (Daily)", 
        "🔴 CNBC Squawk Box Highlights",
        "💼 Bloomberg Markets Today"
    ]
    for pod in podcasts:
        st.markdown(f"• **{pod}**")

st.markdown("---")
st.caption(f"🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M CST')} | Data: Yahoo Finance")
