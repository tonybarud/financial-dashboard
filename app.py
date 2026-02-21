import streamlit as st
import yfinance as yf
import pyttsx3
import datetime
import pandas as pd
import numpy as np
from zoneinfo import ZoneInfo

from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    layout="wide",
    page_title="Tony Market Pulse",
    page_icon="📈"
)

# ---------------- CONFIG ----------------
YAHOO_NEWS_TICKER = "^GSPC"
MAX_NEWS_ITEMS = 6

# Remove top spacing + improve dark mode
st.markdown("""
<style>
    div.block-container { padding-top: 1rem !important; }
    div.stAppViewBlockContainer { padding-top: 1rem !important; }
    section[data-testid="stAppViewContainer"] { background-color: #0e1117; }
    section[data-testid="stSidebar"] { background-color: #1e1e1e; }
</style>
""", unsafe_allow_html=True)

st_autorefresh(interval=60 * 1000, key="app_autorefresh")

# ---------------- LIVE MARKET NEWS ----------------
def fetch_market_news(ticker=YAHOO_NEWS_TICKER, limit=MAX_NEWS_ITEMS):
    try:
        t = yf.Ticker(ticker)
        news = t.news or []
        return news[:limit]
    except Exception:
        return []

def render_live_news():
    now_ct = datetime.datetime.now(ZoneInfo("America/Chicago"))
    news_items = fetch_market_news()

    st.markdown(
        """
        <div style="background-color:#111; padding:10px 15px; border-radius:8px; margin-bottom:10px;">
            <h2 style="color:#f1c40f; margin:0; font-size:24px;">Live Market News</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<p style='font-weight:bold; color:#ffffff; text-shadow: 1px 1px 2px #000000; font-size:16px; margin:5px 0;'>{now_ct.strftime('%A, %B %d, %Y - %I:%M:%S %p CT')}</p>",
        unsafe_allow_html=True,
    )

    if not news_items:
        st.write("No news available at the moment.")
        return

    if all((not item.get("title")) or item.get("title", "").strip().lower() == "untitled" for item in news_items):
        st.write("No readable headlines returned.")
        return

    st.markdown("---")

    for item in news_items:
        title = item.get("title")
        if not title or title.strip().lower() == "untitled":
            continue

        link = item.get("link") or item.get("url")
        is_important = any(kw in title.lower() for kw in [
            "fed", "inflation", "rate hike", "crash", "plunge", "surge", "recession",
            "jobs report", "earnings miss", "dow falls", "s&p 500 falls", "nasdaq tumbles"
        ])
        color = "#e74c3c" if is_important else "#ffffff"

        if link:
            st.markdown(
                f"- <span style='color:{color}; font-size:14px;'>"
                f"<a href='{link}' target='_blank' style='color:{color}; text-decoration:none;'>{title}</a>"
                f"</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f"- <span style='color:{color}; font-size:14px;'>{title}</span>", unsafe_allow_html=True)

# ---------------- SESSION-STATE WATCHLISTS ----------------
def init_watchlist(key, default_list):
    if key not in st.session_state:
        st.session_state[key] = default_list[:]

init_watchlist("indexes", ["^GSPC", "^DJI", "^IXIC", "^RUT"])
init_watchlist("stocks", ["AAPL", "TSLA", "NVDA"])
init_watchlist("etfs", ["SPY", "QQQ", "DIA"])
init_watchlist("metals", ["GLD", "SLV", "GDX", "GC=F", "SI=F"])
init_watchlist("crypto", ["BTC-USD", "ETH-USD"])
init_watchlist("portfolio", {"AAPL": 100, "TSLA": 50})  # Feature 4

# ---------------- SIDEBAR ----------------
st.sidebar.title("📈 Tony Market Pulse")
page = st.sidebar.radio("", ["Dashboard", "Options Chain", "AI Signals", "Portfolio"], key="nav_radio")
st.sidebar.markdown("---")

st.sidebar.subheader("Customize Watchlists")
def watchlist_editor(label, key):
    items = st.session_state[key]
    st.sidebar.markdown(f"**{label}**")
    st.sidebar.write(", ".join(items))

    new_key = f"{key}_new"
    del_key = f"{key}_del"
    if new_key not in st.session_state:
        st.session_state[new_key] = ""

    st.sidebar.text_input(f"Add {label[:-1]}", key=new_key)
    
    def add_item():
        sym = st.session_state[new_key].strip().upper()
        if sym and sym not in items:
            items.append(sym)
        st.session_state[new_key] = ""
    
    st.sidebar.button(f"Add", key=f"{key}_add", on_click=add_item)
    
    st.sidebar.selectbox(f"Delete", [""] + items, key=del_key)
    
    def delete_item():
        choice = st.session_state[del_key]
        if choice in items:
            items.remove(choice)
    
    st.sidebar.button(f"Delete", key=f"{key}_del", on_click=delete_item)

for label, key in [("Indexes", "indexes"), ("Stocks", "stocks"), ("ETFs", "etfs"), ("Metals", "metals"), ("Crypto", "crypto")]:
    watchlist_editor(label, key)

indexes = st.session_state["indexes"]
stocks = st.session_state["stocks"]
etfs = st.session_state["etfs"]
metals = st.session_state["metals"]
crypto = st.session_state["crypto"]
portfolio = st.session_state["portfolio"]

# ---------------- DATA FUNCTIONS ----------------
INDEX_NAMES = {"^GSPC": "S&P 500", "^DJI": "Dow Jones", "^IXIC": "Nasdaq", "^RUT": "Russell 2000"}

def get_price(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1d")
        price = data["Close"].iloc[-1]
        openp = data["Open"].iloc[-1]
        change = price - openp
        pct = (change / openp) * 100
        return price, change, pct
    except:
        return None, None, None

def card(ticker, show_name=False):
    price, change, pct = get_price(ticker)
    if price is None:
        st.markdown(f"""
        <div style="border-radius: 10px; padding: 10px; margin
