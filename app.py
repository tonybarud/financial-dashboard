import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime, timedelta
import feedparser  # NEW: pip install feedparser

# ========== BASIC APP CONFIG ==========
st.set_page_config(
    page_title="Pro Trading Dashboard",
    page_icon="💹",
    layout="wide"  # Better for news cards
)

# ========== RSS NEWS SOURCES (WORKING FEB 2026) ==========
NEWS_FEEDS = {
    "Yahoo Finance Top Stories": "https://finance.yahoo.com/rss/topstories",
    "Yahoo Markets": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=m",
    "Bloomberg Markets": "https://feeds.bloomberg.com/markets/news.rss",
    "Bloomberg Economy": "https://feeds.bloomberg.com/markets/economics.rss"
}

PODCASTS = {
    "Yahoo Finance Presents": "https://rss.art19.com/yahoofinancepresents",
    "WSJ Money Briefing": "https://video-api.wsj.com/podcast/rss/wsj/your-money-matters",
    "CNBC Squawk Box": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100006121"
}

@st.cache_data(ttl=300)  # 5min cache
def fetch_news():
    all_news = []
    for name, url in NEWS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:  # Top 5 per source
                all_news.append({
                    'title': entry.get('title', 'No title'),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': name,
                    'summary': entry.get('summary', '')[:200] + '...'
                })
        except:
            continue
    return sorted(all_news, key=lambda x: x['published'], reverse=True)[:12]

@st.cache_data(ttl=3600)  # 1hr cache
def fetch_podcasts():
    all_pod = []
    for name, url in PODCASTS.items():
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                latest = feed.entries[0]
                all_pod.append({
                    'title': latest.get('title', 'No title'),
                    'link': latest.get('link', ''),
                    'pubDate': latest.get('published', ''),
                    'source': name,
                    'description': latest.get('description', '')[:150] + '...'
                })
        except:
            continue
    return all_pod[:6]

# ========== [ALL PREVIOUS CODE REMAINS IDENTICAL UNTIL SIDEBAR] ==========
# ... (portfolio, options, signals code stays exactly the same - just skip to sidebar changes)

# ========== GLOBAL STATE HELPERS ==========
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []
if "price_alerts" not in st.session_state:
    st.session_state.price_alerts = {}
if "last_alert_check" not in st.session_state:
    st.session_state.last_alert_check = None

WATCHLIST_FILE = "watchlist.json"
PORTFOLIO_FILE = "portfolio.json"
ALERTS_FILE = "alerts.json"

def load_json_safe(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            return default
    return default

def save_json_safe(path, obj):
    try:
        with open(path, "w") as f:
            json.dump(obj, f, indent=2)
    except:
        pass

load_state_from_files = lambda: [
    setattr(st.session_state, 'watchlist', load_json_safe(WATCHLIST_FILE, [])),
    setattr(st.session_state, 'portfolio', load_json_safe(PORTFOLIO_FILE, [])),
    setattr(st.session_state, 'price_alerts', load_json_safe(ALERTS_FILE, {}))
][0]

if "loaded_files" not in st.session_state:
    load_state_from_files()
    st.session_state.loaded_files = True

# [ALL data helpers, signals, alerts functions stay EXACTLY the same as previous version]
# ... (get_price_history, options_chain, compute_ai_signals, get_live_price, play_beep, check_price_targets)

# ========== NEW SIDEBAR WITH NEWS ==========
st.sidebar.title("💹 Pro Trading Dashboard")
page = st.sidebar.radio(
    "Navigate", 
    ["Overview", "Options Chain", "AI Signals", "Portfolio", "Watchlist & Alerts", "News & Podcasts"]  # NEW!
)

st.sidebar.markdown("---")
if st.sidebar.button("💾 Save All"):
    save_json_safe(WATCHLIST_FILE, st.session_state.watchlist)
    save_json_safe(PORTFOLIO_FILE, st.session_state.portfolio)
    save_json_safe(ALERTS_FILE, st.session_state.price_alerts)
    st.sidebar.success("✅ Saved")

# ========== PREVIOUS 5 PAGES EXACTLY SAME ==========
# [Overview, Options, Signals, Portfolio, Watchlist pages - copy from previous version exactly]
# ... (keep all previous page code unchanged)

# ========== NEW PAGE: NEWS & PODCASTS ==========
if page == "News & Podcasts":
    st.title("📰 News & Podcasts")
    
    tab1, tab2 = st.tabs(["Live News", "Podcast Briefs"])
    
    with tab1:
        st.subheader("🔥 Top Financial Headlines")
        news = fetch_news()
        
        if news:
            cols = st.columns(2)
            for i, article in enumerate(news):
                with cols[i % 2]:
                    with st.container():
                        st.markdown(f"**{article['title']}**")
                        st.caption(f"{article['source']} • {article['published'][:16]}")
                        if article['summary']:
                            st.markdown(f"*{article['summary']}*")
                        if st.button("Read ▶️", key=f"news_{i}"):
                            st.markdown(f"[Open article]({article['link']})")
                        st.markdown("---")
        else:
            st.info("📡 Fetching live news... (refresh page)")
    
    with tab2:
        st.subheader("🎙️ Latest Podcast Episodes")
        podcasts = fetch_podcasts()
        
        if podcasts:
            for i, pod in enumerate(podcasts):
                with st.container():
                    st.markdown(f"**{pod['title']}**")
                    st.caption(f"{pod['source']} • {pod['pubDate'][:16]}")
                    st.markdown(f"*{pod['description']}*")
                    if st.button("Listen ▶️", key=f"pod_{i}"):
                        st.markdown(f"[Play episode]({pod['link']})")
                    st.markdown("---")
        else:
            st.info("📡 Loading podcasts...")

    check_price_targets()  # Keep alerts working everywhere

# [Rest of previous pages: Overview, Options, etc. - paste exactly from previous app.py]
