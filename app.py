import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

st.set_page_config(page_title="Pro Trading Dashboard 💹", layout="wide")

# ========== INITIALIZE STATE SAFELY ==========
@st.cache_data
def init_session_state():
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = []
    if "price_alerts" not in st.session_state:
        st.session_state.price_alerts = {}
    if "loaded" not in st.session_state:
        st.session_state.loaded = True

init_session_state()

# JSON persistence
def save_state():
    try:
        os.makedirs(".streamlit", exist_ok=True)
        with open(".streamlit/state.json", "w") as f:
            json.dump({
                "watchlist": st.session_state.watchlist,
                "portfolio": st.session_state.portfolio, 
                "price_alerts": st.session_state.price_alerts
            }, f)
    except:
        pass

# ========== DATA HELPERS ==========
@st.cache_data(ttl=120)
def get_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        return ticker.fast_info.get('lastPrice', 0) or ticker.history(period="1d")['Close'][-1]
    except:
        return 0

@st.cache_data(ttl=120)
def get_options(symbol):
    try:
        ticker = yf.Ticker(symbol)
        chain = ticker.option_chain(ticker.options[0])
        return pd.concat([chain.calls.head(5), chain.puts.head(5)])
    except:
        return pd.DataFrame()

def get_signals(symbol):
    try:
        hist = yf.download(symbol, period="3mo", progress=False)
        if hist.empty:
            return {}
        ma_short = hist['Close'].rolling(10).mean().iloc[-1]
        ma_long = hist['Close'].rolling(30).mean().iloc[-1]
        price = hist['Close'].iloc[-1]
        signal = "Buy" if price > ma_short > ma_long else "Sell" if price < ma_long else "Hold"
        return {"signal": signal, "price": price, "ma_short": ma_short, "ma_long": ma_long}
    except:
        return {}

# ========== ALERTS (SAFE VERSION) ==========
def check_alerts():
    if not isinstance(st.session_state.price_alerts, dict):
        return
    
    for symbol, alert in list(st.session_state.price_alerts.items()):
        if not isinstance(alert, dict):
            continue
            
        price = get_price(symbol)
        if price == 0:
            continue
            
        target = alert.get('target', 0)
        direction = alert.get('direction', 'above')
        hit = alert.get('hit', False)
        
        triggered = False
        if direction == 'above' and price >= target:
            triggered = True
        elif direction == 'below' and price <= target:
            triggered = True
            
        if triggered and not hit:
            alert['hit'] = True
            st.error(f"🚨 {symbol}: ${price:.2f} {'↑' if direction=='above' else '↓'} ${target:.2f}")
            # Beep sound
            st.components.v1.html("""
            <audio autoplay>
                <source src="data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhQd+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+Dyvm
