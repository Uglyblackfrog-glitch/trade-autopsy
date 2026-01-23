import streamlit as st
import requests
import base64
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from PIL import Image
import io
import time  # <--- NEW: Required for Live Loop

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Trade Postmortem | Live Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed" # Wider view for charts
)

# --- 2. CREDENTIALS ---
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except:
    st.error("⚠️ Add HF_TOKEN to Streamlit Secrets.")
    st.stop()

# --- 3. STYLING (The "Terminal" Look) ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #e6edf3; } /* Pitch Black Background */
    
    /* LIVE TICKER STYLE */
    .live-badge {
        background-color: #ff0000;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }

    /* PRICE CARDS */
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
    
    /* SEARCH BAR */
    .stTextInput>div>div>input {
        background-color: #161b22;
        color: white;
        border: 1px solid #30363d;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNCTIONS ---

def query_ai(payload):
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
    try:
        return requests.post(API_URL, headers=headers, json=payload).json()
    except:
        return None

def get_live_data(symbol):
    # Intelligent Symbol Handling
    clean_symbol = symbol.upper().replace(" ", "")
    if not clean_symbol.endswith(".NS") and not clean_symbol.endswith(".BO"):
        clean_symbol += ".NS" # Default to NSE
    
    # 1. Get Live Price (Fastest)
    stock = yf.Ticker(clean_symbol)
    
    # We use 'fast_info' for real-time price if available, else history
    try:
        # Fetching 1 day history (1m interval) is best for "Live" charts
        # Note: 1m data is only available for the last 7 days
        df = stock.history(period="5d", interval="5m")
        
        if df.empty:
            return None, None, 0, 0
            
        current_price = df['Close'].iloc[-1]
        prev_close = stock.info.get('previousClose', df['Close'].iloc[0])
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100
        
        # Add Technicals
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        
        return df, clean_symbol, current_price, change_pct
        
    except Exception as e:
        return None, None, 0, 0

def plot_live_chart(df, symbol):
    # Professional Candle Chart
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name=symbol)])

    fig.update_layout(
        height=550,
        margin=dict(l=0, r=0, t=20, b=0),
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        plot_bgcolor="#000000",
        paper_bgcolor="#000000",
        font=dict(color="#b0b0b0")
    )
    return fig

# =========================================================
#                       APP LAYOUT
# =========================================================

# --- HEADER & LIVE CONTROLS ---
c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    st.title("⚡ LIVE TERMINAL")
with c3:
    # THE MAGIC SWITCH: Enables Auto-Refresh
    st.write("")
    st.write("")
    live_mode = st.toggle("🔴 LIVE DATA STREAM", value=False)

# --- SESSION STATE FOR SEARCH ---
if 'symbol' not in st.session_state:
    st.session_state.symbol = "RELIANCE"

# --- TABS ---
tab_terminal, tab_audit = st.tabs(["📈 MARKET TERMINAL", "⚖️ AUDIT ROOM"])

# =========================================================
# TAB 1: REAL-TIME MARKET TERMINAL
# =========================================================
with tab_terminal:
    # 1. SEARCH BAR (Acts as the main controller)
    col_search, col_quick = st.columns([1, 2])
    with col_search:
        query = st.text_input("SEARCH TICKER (Hit Enter)", value=st.session_state.symbol)
        if query != st.session_state.symbol:
            st.session_state.symbol = query
            st.rerun() # Force reload immediately on enter
            
    with col_quick:
        st.write("Trending:")
        # Quick Buttons that update state
        b1, b2, b3, b4, b5 = st.columns(5)
        if b1.button("NIFTY"): st.session_state.symbol = "^NSEI"; st.rerun()
        if b2.button("BANKNIFTY"): st.session_state.symbol = "^NSEBANK"; st.rerun()
        if b3.button("TATA"): st.session_state.symbol = "TATAMOTORS"; st.rerun()
        if b4.button("ADANI"): st.session_state.symbol = "ADANIENT"; st.rerun()
        if b5.button("ZOMATO"): st.session_state.symbol = "ZOMATO"; st.rerun()

    # 2. FETCH DATA
    df, clean_sym, price, change = get_live_data(st.session_state.symbol)

    if df is not None:
        # 3. BIG METRIC DISPLAY
        color = "green" if change >= 0 else "red"
        sign = "+" if change >= 0 else ""
        
        st.markdown(f"""
        <div class="price-card">
            <div style="font-size: 1.2rem; color: #888;">{clean_sym} <span class="live-badge">LIVE</span></div>
            <div class="big-price {color}">₹{price:,.2f}</div>
            <div style="font-size: 1.5rem;" class="{color}">{sign}{change:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

        # 4. CHART & AI
        c_chart, c_ai = st.columns([3, 1])
        
        with c_chart:
            fig = plot_live_chart(df, clean_sym)
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{time.time()}") # Unique key forces redraw

        with c_ai:
            st.markdown("### 🤖 AI FORECAST")
            st.info("Based on 5-min Momentum")
            
            if st.button("SCAN NOW"):
                # Prepare Technical Data for AI
                tech_data = f"""
                STOCK: {clean_sym}
                PRICE: {price}
                RSI (14): {df['RSI'].iloc[-1]:.2f}
                Trend (Last 5 candles): {df['Close'].tail(5).tolist()}
                """
                
                with st.spinner("AI Scanning..."):
                    payload = {
                        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                        "messages": [{
                            "role": "user", 
                            "content": f"Analyze this technical data short term. Buy/Sell/Wait? Keep it super short.\n{tech_data}"
                        }],
                        "max_tokens": 200
                    }
                    res = query_ai(payload)
                    if res:
                        st.success(res['choices'][0]['message']['content'])

    else:
        st.error(f"❌ Could not find live data for '{st.session_state.symbol}'. Try checking the spelling.")

    # 5. AUTO-REFRESH LOGIC
    if live_mode:
        time.sleep(2) # Wait 2 seconds
        st.rerun()    # Reload the page automatically

# =========================================================
# TAB 2: AUDIT ROOM (Your Original Code)
# =========================================================
with tab_audit:
    st.header("Forensic Trade Auditor")
    # ... (Your existing audit upload logic here)
    # Re-pasted purely for completeness
    file = st.file_uploader("Upload P&L Screenshot", type=["png", "jpg"])
    if file and st.button("Analyze Loss"):
        st.warning("AI Analysis requires image processing (same as previous version).")
