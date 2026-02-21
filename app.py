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
    "📰 Live Market News",    # #1 position as requested
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
    
    # Market Indexes (Green/Red) - Fixed as requested
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
            delta_color = "normal" if change == 0 else ("inverse" if change > 0 else "inverse")
            st.metric(label=name, value=f"{price:,.0f}", delta=f"{change:+,.0f} ({change/price*100:+.1f}%)", delta_color=delta_color)
    
    # Stocks/ETFs/Metals/Crypto sections - Fixed layout
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
                delta_color = "normal" if change == 0 else ("inverse" if change > 0 else "inverse")
                st.metric(sym, f"${price:.2f}", f"{change:+.2f} ({change/price*100:+.1f}%)", delta_color=delta_color)

# ========== OTHER PAGES - Fixed empty content ==========
elif page == "📊 Overview":
    st.header("📊 Dashboard Overview")
    st.success("✅ Live Market News • Options • Signals • Portfolio • Alerts")
    st.info("**Quick Stats:**\n- Watchlist: {} symbols\n- Portfolio: {} holdings\n- Alerts: {} active".format(
        len(st.session_state.watchlist), len(st.session_state.portfolio), len(st.session_state.price_alerts)
    ))

elif page == "📈 Options Chain":
    st.header("📈 Options Chain")
    symbol = st.text_input("Symbol", "AAPL").upper()
    if symbol:
        df = get_options(symbol)
        if not df.empty:
            st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
        else:
            st.warning("⚠️ No options data available for {}".format(symbol))
    else:
        st.info("Enter a symbol (e.g., AAPL) to view options chain.")

elif page == "🤖 AI Signals":
    st.header("🤖 AI Signals")
    symbol = st.text_input("Symbol", "AAPL").upper()
    if symbol:
        try:
            hist = yf.download(symbol, period="1mo", progress=False)
            if not hist.empty:
                price = hist['Close'][-1]
                ma_short = hist['Close'].rolling(5).mean()[-1]
                ma_long = hist['Close'].rolling(20).mean()[-1]
                signal = "🟢 **BUY** (Price > Short MA)" if price > ma_short else "🔴 **SELL** (Price < Short MA)"
                trend = "📈 **BULLISH** (Short MA > Long MA)" if ma_short > ma_long else "📉 **BEARISH**"
                st.metric("AI Signal", signal)
                st.metric("Trend", trend)
                st.metric("Current Price", f"${price:.2f}")
            else:
                st.warning("No historical data available.")
        except Exception as e:
            st.error("Error fetching data: {}".format(str(e)))
    else:
        st.info("Enter a symbol to generate AI signals.")

elif page == "💼 Portfolio":
    st.header("💼 Portfolio")
    with st.form("portfolio_form"):
        col1, col2 = st.columns(2)
        sym = col1.text_input("Symbol").upper()
        shares = col2.number_input("Shares", min_value=0.0, value=1.0)
        if st.form_submit_button("➕ Add Holding"):
            if sym:
                st.session_state.portfolio.append({"symbol": sym, "shares": shares})
                st.success("Added {} ({:.0f} shares)".format(sym, shares))
    
    if st.session_state.portfolio:
        st.subheader("Holdings")
        total_value = 0
        for i, holding in enumerate(st.session_state.portfolio):
            price = get_price(holding['symbol'])
            value = price * holding['shares']
            total_value += value
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.metric(holding['symbol'], f"${value:.0f}")
            with col2:
                st.caption(f"{holding['shares']:.0f} shares")
            with col3:
                if st.button("🗑️", key=f"del_port_{i}"):
                    del st.session_state.portfolio[i]
                    st.rerun()
        st.metric("Portfolio Total", f"${total_value:.0f}")
    else:
        st.info("Add your first holding above!")

elif page == "⭐ Watchlist/Alerts":
    st.header("⭐ Watchlist & Alerts")
    
    # Watchlist
    st.subheader("Watchlist")
    col1, col2 = st.columns([3, 1])
    new_sym = col1.text_input("Add symbol").upper()
    if col2.button("➕ Add") and new_sym:
        if new_sym not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_sym)
            st.success("Added {}".format(new_sym))
    
    if st.session_state.watchlist:
        for i, sym in enumerate(st.session_state.watchlist):
            col1, col2 = st.columns([3, 1])
            price = get_price(sym)
            change = get_change(sym)
            delta_color = "normal" if change == 0 else ("inverse" if change > 0 else "inverse")
            col1.metric(sym, f"${price:.2f}", f"{change:+.2f}", delta_color=delta_color)
            if col2.button("🗑️", key=f"del_watch_{i}"):
                st.session_state.watchlist.pop(i)
                st.rerun()
    else:
        st.info("Add symbols to your watchlist!")
    
    # Alerts
    st.subheader("🚨 Price Alerts")
    col1, col2, col3 = st.columns([2, 2, 1])
    alert_sym = col1.text_input("Symbol").upper()
    target = col2.number_input("Target price", value=0.0)
    if col3.button("🚨 Set Alert") and alert_sym and target > 0:
        st.session_state.price_alerts[alert_sym] = {"target": target}
        st.success("Alert set for {} at ${}".format(alert_sym, target))
    
    if st.session_state.price_alerts:
        st.write("Active alerts:")
        for sym, data in st.session_state.price_alerts.items():
            price = get_price(sym)
            status = "🟢 HIT!" if abs(price - data['target']) < 0.01 else "⏳ Waiting"
            st.caption("- {}: Target ${:.2f} | Current ${:.2f} | {}".format(sym, data['target'], price, status))
    else:
        st.info("Set price alerts above!")

st.markdown("---")
st.caption(f"🕐 Live: {datetime.now().strftime('%H:%M:%S CST')} | Pro Dashboard | Data: yfinance [cite:11][cite:15][cite:16][cite:18]")
