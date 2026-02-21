import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

# ========== CONFIG ==========
st.set_page_config(page_title="Pro Trading Dashboard", page_icon="💹", layout="wide")

# [KEEP ALL PREVIOUS STATE/HELPER FUNCTIONS EXACTLY SAME - just add this NEW page]

# ========== SIDEBAR WITH NEWS ==========
st.sidebar.title("💹 Pro Trading Dashboard")
page = st.sidebar.radio(
    "Navigate", 
    ["Overview", "Options Chain", "AI Signals", "Portfolio", "Watchlist & Alerts", "News & Podcasts"]
)

# ========== NEWS & PODCASTS (NO EXTERNAL LIBRARIES) ==========
if page == "News & Podcasts":
    st.title("📰 News & Podcasts")
    
    # Use yfinance news (BUILT-IN, no extra libraries!)
    symbols = ["AAPL", "SPY", "QQQ", "TSLA", "NVDA"]
    all_news = []
    
    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            news = ticker.news[:3]  # Get 3 latest per symbol
            for item in news:
                all_news.append({
                    'title': item.get('title', 'News'),
                    'link': item.get('link', ''),
                    'publisher': item.get('publisher', sym),
                    'symbol': sym
                })
        except:
            continue
    
    tab1, tab2 = st.tabs(["📈 Market News", "🎙️ Top Headlines"])
    
    with tab1:
        st.subheader("🔥 Live Market News (via Yahoo Finance)")
        if all_news:
            for i, news_item in enumerate(all_news[:12]):
                col1, col2 = st.columns([3,1])
                with col1:
                    st.markdown(f"**{news_item['title']}**")
                    st.caption(f"{news_item['publisher']} • {news_item['symbol']}")
                with col2:
                    if st.button("Read", key=f"news{i}"):
                        st.markdown(f"[Open]({news_item['link']})")
                st.markdown("---")
        else:
            st.info("📡 Loading market news...")
    
    with tab2:
        st.subheader("🎙️ Featured Podcasts & Briefs")
        podcasts = [
            {"title": "Yahoo Finance: Market Open Update", "link": "https://finance.yahoo.com/video/"},
            {"title": "WSJ Money Briefing (Daily)", "link": "https://www.wsj.com/podcasts/your-money-matters"},
            {"title": "CNBC Squawk Box Highlights", "link": "https://www.cnbc.com/squawk-box/"},
            {"title": "Bloomberg Markets Today", "link": "https://www.bloomberg.com/podcasts"},
        ]
        
        for pod in podcasts:
            col1, col2 = st.columns([3,1])
            with col1:
                st.markdown(f"**{pod['title']}**")
            with col2:
                st.markdown(f"[Listen]({pod['link']})")
            st.markdown("---")

# [PASTE ALL YOUR PREVIOUS PAGES HERE EXACTLY - Overview, Options, etc.]
# Keep everything else from your working app.py
