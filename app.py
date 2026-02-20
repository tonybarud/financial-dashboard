import streamlit as st
import yfinance as yf
import pyttsx3
import datetime
from zoneinfo import ZoneInfo

from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    layout="wide",
    page_title="Tony Market Pulse", 
    page_icon="💰"  # Money bag icon
)

# ---------------- CONFIG ----------------
YAHOO_NEWS_TICKER = "^GSPC"  # broad market symbol for general headlines
MAX_NEWS_ITEMS = 6           # number of headlines to show

# Remove top spacing + improve dark mode compatibility
st.markdown("""
<style>
    /* Remove top padding */
    div.block-container { padding-top: 1rem !important; }
    div.stAppViewBlockContainer { padding-top: 1rem !important; }
    
    /* Dark mode background */
    section[data-testid="stAppViewContainer"] {
        background-color: #0e1117;
    }
    
    /* Ensure sidebar is dark */
    section[data-testid="stSidebar"] {
        background-color: #1e1e1e;
    }
</style>
""", unsafe_allow_html=True)

# Auto-refresh every 60 seconds (60,000 ms)
st_autorefresh(interval=60 * 1000, key="app_autorefresh")

# ---------------- LIVE MARKET NEWS ----------------
def fetch_market_news(ticker=YAHOO_NEWS_TICKER, limit=MAX_NEWS_ITEMS):
    """
    Use yfinance's news attribute to fetch recent Yahoo Finance headlines.
    """
    try:
        t = yf.Ticker(ticker)
        news = t.news or []
        return news[:limit]
    except Exception:
        return []


def render_live_news():
    # Recompute time on every rerun
    now_ct = datetime.datetime.now(ZoneInfo("America/Chicago"))
    news_items = fetch_market_news()

    # Header bar
    st.markdown(
        """
        <div style="background-color:#111; padding:10px 15px; border-radius:8px; margin-bottom:10px;">
            <h2 style="color:#f1c40f; margin:0; font-size:24px;">Live Market News</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Bold CT date/time - WHITE with shadow for dark mode visibility
    st.markdown(
        f"<p style='font-weight:bold; color:#ffffff; text-shadow: 1px 1px 2px #000000; font-size:16px; margin:5px 0;'>{now_ct.strftime('%A, %B %d, %Y - %I:%M:%S %p CT')}</p>",
        unsafe_allow_html=True,
    )

    if not news_items:
        st.write("No news available at the moment (data source returned empty).")
        return

    # If all items are untitled, show message and stop
    if all(
        (not item.get("title")) or item.get("title", "").strip().lower() == "untitled"
        for item in news_items
    ):
        st.write("No readable headlines returned by the news source.")
        return

    st.markdown("---")

    for item in news_items:
        title = item.get("title")
        if not title or title.strip().lower() == "untitled":
            continue  # skip unreadable items

        link = item.get("link") or item.get("url")

        # Heuristic: mark important headlines red
        is_important = any(
            kw in title.lower()
            for kw in [
                "fed",
                "inflation",
                "rate hike",
                "crash",
                "plunge",
                "surge",
                "recession",
                "jobs report",
                "earnings miss",
                "dow falls",
                "s&p 500 falls",
                "nasdaq tumbles",
            ]
        )
        color = "#e74c3c" if is_important else "#ffffff"  # red or white for dark bg

        if link:
            st.markdown(
                f"- <span style='color:{color}; font-size:14px;'>"
                f"<a href='{link}' target='_blank' "
                f"style='color:{color}; text-decoration:none;'>{title}</a>"
                f"</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"- <span style='color:{color}; font-size:14px;'>{title}</span>",
                unsafe_allow_html=True,
            )


# ---------------- SIDEBAR NAVIGATION ----------------
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "",
    ["Dashboard", "Options Chain Viewer", "AI Trade Signals"],
    key="nav_radio",
)
st.sidebar.markdown("---")


# ---------------- SESSION-STATE WATCHLISTS ----------------
def init_watchlist(key, default_list):
    if key not in st.session_state:
        st.session_state[key] = default_list[:]


init_watchlist("indexes", ["^GSPC", "^DJI", "^IXIC", "^RUT"])
init_watchlist("stocks", ["AAPL", "TSLA", "NVDA"])
init_watchlist("etfs", ["SPY", "QQQ", "DIA"])
init_watchlist("metals", ["GLD", "SLV", "GDX", "GC=F", "SI=F"])
init_watchlist("crypto", ["BTC-USD", "ETH-USD"])

st.sidebar.subheader("Customize Watchlists")


def watchlist_editor(label, key):
    items = st.session_state[key]

    st.sidebar.markdown(f"**{label}**")
    st.sidebar.write(", ".join(items))

    new_key = f"{key}_new"
    del_key = f"{key}_del"

    if new_key not in st.session_state:
        st.session_state[new_key] = ""

    # Text input for new item
    st.sidebar.text_input(f"Add {label[:-1]}", key=new_key)

    # Add callback
    def add_item():
        sym = st.session_state[new_key].strip().upper()
        if sym and sym not in items:
            items.append(sym)
        st.session_state[new_key] = ""  # clear

    st.sidebar.button(f"Add to {label}", key=f"{key}_add_btn", on_click=add_item)

    # Delete controls
    st.sidebar.selectbox(
        f"Delete from {label}",
        [""] + items,
        key=del_key,
    )

    def delete_item():
        choice = st.session_state[del_key]
        if choice in items:
            items.remove(choice)

    st.sidebar.button(f"Delete from {label}", key=f"{key}_del_btn", on_click=delete_item)


watchlist_editor("Market Indexes", "indexes")
watchlist_editor("Stocks", "stocks")
watchlist_editor("ETFs", "etfs")
watchlist_editor("Metals", "metals")
watchlist_editor("Crypto", "crypto")

indexes = st.session_state["indexes"]
stocks = st.session_state["stocks"]
etfs = st.session_state["etfs"]
metals = st.session_state["metals"]
crypto = st.session_state["crypto"]


# ---------------- INDEX NAME MAP ----------------
INDEX_NAMES = {
    "^GSPC": "S&P 500",
    "^DJI": "Dow Jones",
    "^IXIC": "Nasdaq",
    "^RUT": "Russell 2000",
}


# ---------------- CSS STYLE ----------------
st.markdown(
    """
    <style>
    /* Additional custom CSS if needed */
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------- DATA FUNCTION ----------------
def get_price(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1d")
        price = data["Close"].iloc[-1]
        openp = data["Open"].iloc[-1]
        change = price - openp
        pct = (change / openp) * 100
        return price, change, pct
    except Exception:
        return None, None, None


# ---------------- CARD FUNCTION ----------------
def card(ticker, show_name=False):
    price, change, pct = get_price(ticker)
    if price is None:
        st.markdown(
            f"""
            <div style="border-radius: 10px; padding: 10px; margin: 5px; background-color: #333; color: white;">
                <h4>{ticker}</h4>
                <p>Data not available</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    color = "#2ecc71" if change >= 0 else "#e74c3c"
    name = INDEX_NAMES.get(ticker, ticker) if show_name else ticker

    st.markdown(
        f"""
        <div style="border-radius: 10px; padding: 10px; margin: 5px; background-color: #222; color: white;">
            <h4>{name}</h4>
            <p style="font-size: 20px;">{price:.2f}</p>
            <p style="color: {color};">
                {change:+.2f} ({pct:+.2f}%)
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =================== MAIN LAYOUT ===================

# Live Market News always at top; time updates each rerun
render_live_news()
st.write("---")

if page == "Dashboard":
    st.header("Dashboard")

    cols = st.columns(len(indexes) or 1)
    for col, idx in zip(cols, indexes):
        with col:
            card(idx, show_name=True)

    st.write("---")
    st.subheader("Stocks")
    cols = st.columns(min(len(stocks), 4) or 1)
    for i, ticker in enumerate(stocks):
        with cols[i % len(cols)]:
            card(ticker)

    st.write("---")
    st.subheader("ETFs")
    cols = st.columns(min(len(etfs), 4) or 1)
    for i, ticker in enumerate(etfs):
        with cols[i % len(cols)]:
            card(ticker)

    st.write("---")
    st.subheader("Metals")
    cols = st.columns(min(len(metals), 4) or 1)
    for i, ticker in enumerate(metals):
        with cols[i % len(cols)]:
            card(ticker)

    st.write("---")
    st.subheader("Crypto")
    cols = st.columns(min(len(crypto), 4) or 1)
    for i, ticker in enumerate(crypto):
        with cols[i % len(cols)]:
            card(ticker)

elif page == "Options Chain Viewer":
    st.header("Options Chain Viewer")
    # your existing implementation here

elif page == "AI Trade Signals":
    st.header("AI Trade Signals")
    # your existing implementation here


