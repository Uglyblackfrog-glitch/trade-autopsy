import streamlit as st
import requests
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Trade Postmortem | Live Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CREDENTIALS ---
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except:
    st.error("⚠️ Add HF_TOKEN to Streamlit Secrets.")
    st.stop()

# --- 3. STYLES ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #e6edf3; }
    .price-card {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 15px;
        text-align: center;
    }
    .big-price { font-size: 2.5rem; font-weight: 800; }
    .green { color: #00e272; }
    .red { color: #fa4d56; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ROBUST DATA FETCHER (THE FIX) ---
def get_live_data(symbol):
    # 1. Clean the input
    clean_symbol = symbol.upper().strip().replace(" ", "")
    
    # 2. Add .NS if missing (default to NSE)
    # logic: if it doesn't have a dot (like .NS or .BO), add .NS
    if "." not in clean_symbol:
        clean_symbol += ".NS"

    stock = yf.Ticker(clean_symbol)
    
    # 3. Try fetching Intraday Data (Best for Live Terminal)
    # We fetch 5 days of 5-minute data
    df = stock.history(period="5d", interval="5m")
    
    # 4. FALLBACK: If Intraday is empty (common error), fetch Daily Data
    if df.empty:
        df = stock.history(period="1y")
    
    # 5. If STILL empty, then the stock name is truly wrong
    if df.empty:
        return None, clean_symbol, 0, 0

    # 6. Calculate Stats
    current_price = df['Close'].iloc[-1]
    
    # Safe previous close calculation
    if len(df) > 1:
        prev_close = df['Close'].iloc[-2] # Last candle close
        # Ideally we want yesterday's close, but for live chart, previous candle is okay for momentum
        # Better: Get 'previousClose' from info if available
        info = stock.info
        if 'previousClose' in info and info['previousClose'] is not None:
             real_prev_close = info['previousClose']
             change = current_price - real_prev_close
             change_pct = (change / real_prev_close) * 100
        else:
             change = current_price - prev_close
             change_pct = (change / prev_close) * 100
    else:
        change = 0
        change_pct = 0
        
    # Add Indicators for AI
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['SMA_50'] = ta.sma(df['Close'], length=50)
    
    return df, clean_symbol, current_price, change_pct

def plot_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name=symbol)])

    fig.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=30, b=0),
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        plot_bgcolor="#000000",
        paper_bgcolor="#000000",
        title=f"{symbol} PRICE ACTION"
    )
    return fig

# =========================================================
#                       APP UI
# =========================================================

# --- SESSION STATE ---
if 'symbol' not in st.session_state:
    st.session_state.symbol = "ZOMATO" # Default working stock

st.title("⚡ LIVE TERMINAL")

# --- CONTROLS ---
col_search, col_buttons = st.columns([1, 2])

with col_search:
    # Text Input updates Session State
    user_input = st.text_input("SEARCH STOCK", value=st.session_state.symbol)
    if st.button("SEARCH"):
        st.session_state.symbol = user_input
        st.rerun()

with col_buttons:
    st.write("Quick Picks:")
    b1, b2, b3, b4 = st.columns(4)
    if b1.button("RELIANCE"): st.session_state.symbol = "RELIANCE"; st.rerun()
    if b2.button("TATA MOTORS"): st.session_state.symbol = "TATAMOTORS"; st.rerun()
    if b3.button("ZOMATO"): st.session_state.symbol = "ZOMATO"; st.rerun()
    if b4.button("NIFTY 50"): st.session_state.symbol = "^NSEI"; st.rerun()

# --- MAIN DISPLAY ---
try:
    df, ticker, price, change = get_live_data(st.session_state.symbol)

    if df is not None:
        # Price Card
        color = "green" if change >= 0 else "red"
        st.markdown(f"""
        <div class="price-card">
            <h2 style='color: white; margin:0;'>{ticker}</h2>
            <div class="big-price {color}">₹{price:,.2f}</div>
            <div style="font-size: 1.2rem; color: { '#00e272' if change >=0 else '#fa4d56' };">
                {change:+.2f} ({change_pct:+.2f}%)
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Chart
        st.plotly_chart(plot_chart(df, ticker), use_container_width=True)
        
        # AI Button
        if st.button("🤖 ASK AI ANALYST"):
            with st.spinner("AI is analyzing the chart..."):
                # Mock AI call (Replace with your Router if needed, kept simple for stability)
                prompt = f"Stock: {ticker}, Price: {price}, RSI: {df['RSI'].iloc[-1]:.2f}. Trend is {'Up' if change > 0 else 'Down'}."
                
                payload = {
                    "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                    "messages": [{"role": "user", "content": f"Analyze this stock data briefly: {prompt}"}],
                    "max_tokens": 200
                }
                
                headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                try:
                    res = requests.post(API_URL, headers=headers, json=payload).json()
                    st.success(res['choices'][0]['message']['content'])
                except:
                    st.error("AI Busy. Try again.")

    else:
        st.error(f"❌ '{st.session_state.symbol}' not found. Check spelling.")

except Exception as e:
    st.error(f"System Error: {e}")
