import streamlit as st
import requests
import base64
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from PIL import Image
import io
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="StockPostmortem.ai",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CREDENTIALS ---
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except:
    # Fail gracefully if secrets missing for UI demo
    HF_TOKEN = ""
    API_URL = ""

# --- 3. THE "STOCKPOSTMORTEM" UI ENGINE (CSS) ---
st.markdown("""
    <style>
    /* IMPORT INTER FONT */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* GLOBAL RESET */
    .stApp {
        background-color: #0f171c; /* Deep Navy/Black */
        font-family: 'Inter', sans-serif;
        color: #e2e8f0;
    }
    
    /* HIDE STREAMLIT DEFAULT ELEMENTS */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* CUSTOM NAVBAR STYLING */
    .nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 1px solid #2d4250;
        margin-bottom: 2rem;
    }
    .nav-logo {
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: -0.05em;
        color: white;
    }
    .accent-red { color: #ff4d4d; }
    
    /* GLASS CARDS */
    .glass-card {
        background: rgba(31, 46, 56, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* BUTTON OVERRIDES */
    .stButton>button {
        background-color: #ff4d4d; /* Brand Red */
        color: white;
        border: none;
        border-radius: 50px;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #ff1a1a;
        transform: scale(1.02);
    }
    
    /* SECONDARY BUTTON (Gray) */
    div[data-testid="column"] .stButton>button {
        background-color: #1f2e38;
        border: 1px solid #2d4250;
    }
    div[data-testid="column"] .stButton>button:hover {
        border-color: #ff4d4d;
        color: #ff4d4d;
    }

    /* INPUT FIELDS */
    .stTextInput>div>div>input {
        background-color: #1f2e38;
        color: white;
        border: 1px solid #2d4250;
        border-radius: 8px;
    }
    .stTextInput>div>div>input:focus {
        border-color: #ff4d4d;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border: none;
        color: #64748b;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #ff4d4d;
        border-bottom: 2px solid #ff4d4d;
    }
    
    /* METRIC TEXT */
    .big-stat { font-size: 2.5rem; font-weight: 800; line-height: 1; }
    .stat-label { color: #94a3b8; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. BACKEND LOGIC (The "Invincible" Fetcher) ---

def get_live_data(symbol):
    clean_symbol = symbol.upper().strip().replace(" ", "")
    if "." not in clean_symbol:
        clean_symbol += ".NS"

    try:
        stock = yf.Ticker(clean_symbol)
        # Try Intraday First (5m)
        df = stock.history(period="5d", interval="5m")
        
        # Fallback to Daily if Intraday fails
        if df.empty:
            df = stock.history(period="1y")
            
        if df.empty:
            return None, clean_symbol, 0, 0

        # Calculations
        current_price = df['Close'].iloc[-1]
        
        if len(df) > 1:
            prev_close = df['Close'].iloc[-2]
            # Try to get real previous close for accurate %
            info = stock.info
            if 'previousClose' in info and info['previousClose']:
                real_prev = info['previousClose']
                change = current_price - real_prev
                change_pct = (change / real_prev) * 100
            else:
                change = current_price - prev_close
                change_pct = (change / prev_close) * 100
        else:
            change = 0; change_pct = 0
            
        # Indicators
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        
        return df, clean_symbol, current_price, change_pct
    except Exception:
        return None, clean_symbol, 0, 0

def plot_chart(df, symbol):
    # Match the HTML Dark Theme
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name=symbol)])
    
    fig.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=10, b=0),
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        plot_bgcolor="rgba(0,0,0,0)", # Transparent
        paper_bgcolor="rgba(0,0,0,0)", # Transparent
        font=dict(color="#94a3b8", family="Inter")
    )
    return fig

# =========================================================
#                       UI LAYOUT
# =========================================================

# --- 1. CUSTOM NAVBAR ---
st.markdown("""
<div class="nav-container">
    <div class="nav-logo">STOCK<span class="accent-red">POSTMORTEM</span>.AI</div>
    <div>
        <span style="color:#64748b; font-size:0.9rem; margin-right:15px;">v2.0 BETA</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 2. HEADER SECTION ---
st.markdown("""
<div style="text-align:center; margin-bottom: 40px;">
    <h1 style="font-size: 3rem; font-weight: 800; font-style: italic; margin-bottom: 10px;">
        STOP BLEEDING <span class="accent-red">CAPITAL</span>.
    </h1>
    <p style="color: #94a3b8; max-width: 600px; margin: 0 auto;">
        Surgical analysis of your trading mistakes & real-time market intelligence.
    </p>
</div>
""", unsafe_allow_html=True)

# --- 3. MAIN TABS ---
tab_terminal, tab_audit = st.tabs(["📉 LIVE TERMINAL", "🩸 LOSS AUTOPSY"])

# ---------------------------------------------------------
# TAB 1: LIVE TERMINAL
# ---------------------------------------------------------
with tab_terminal:
    # Initialize State
    if 'symbol' not in st.session_state:
        st.session_state.symbol = "ZOMATO"

    # Top Control Bar (Glass Card)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        query = st.text_input("SEARCH TICKER", value=st.session_state.symbol)
        if st.button("LOAD CHART"):
            st.session_state.symbol = query
            st.rerun()
    with c2:
        st.caption("QUICK PICKS")
        bc1, bc2, bc3 = st.columns(3)
        if bc1.button("NIFTY"): st.session_state.symbol = "^NSEI"; st.rerun()
        if bc2.button("TATA"): st.session_state.symbol = "TATAMOTORS"; st.rerun()
        if bc3.button("ADANI"): st.session_state.symbol = "ADANIENT"; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Data Fetching
    df, ticker, price, change = get_live_data(st.session_state.symbol)

    if df is not None:
        # Metrics Row
        col_metric, col_chart = st.columns([1, 3])
        
        with col_metric:
            color = "#00e272" if change >= 0 else "#ff4d4d"
            st.markdown(f"""
            <div class="glass-card" style="text-align:center; height: 500px; display:flex; flex-direction:column; justify-content:center;">
                <div class="stat-label">{ticker}</div>
                <div class="big-stat" style="color: white;">₹{price:,.2f}</div>
                <div style="color: {color}; font-weight:bold; font-size:1.2rem; margin-top:10px;">
                    {change:+.2f} ({change_pct:+.2f}%)
                </div>
                <hr style="border-color:#2d4250; margin: 20px 0;">
                <div style="text-align:left; padding: 0 10px;">
                    <p style="margin:5px 0; color:#94a3b8;">RSI (14): <span style="color:white; float:right;">{df['RSI'].iloc[-1]:.1f}</span></p>
                    <p style="margin:5px 0; color:#94a3b8;">50 SMA: <span style="color:white; float:right;">{df['SMA_50'].iloc[-1]:.1f}</span></p>
                    <p style="margin:5px 0; color:#94a3b8;">Vol: <span style="color:white; float:right;">{df['Volume'].iloc[-1]/1000:.0f}K</span></p>
                </div>
                <div style="margin-top:auto;">
                     <button style="background:transparent; border:1px solid #ff4d4d; color:#ff4d4d; width:100%; padding:10px; border-radius:8px;">GENERATE SIGNAL</button>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_chart:
            # Chart Container
            st.markdown('<div class="glass-card" style="height: 500px; padding:10px;">', unsafe_allow_html=True)
            st.plotly_chart(plot_chart(df, ticker), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
    else:
        st.error(f"Could not load data for {st.session_state.symbol}. Check spelling.")

# ---------------------------------------------------------
# TAB 2: LOSS AUTOPSY (Replicating the HTML Upload Section)
# ---------------------------------------------------------
with tab_audit:
    c_upload, c_info = st.columns([1, 1])
    
    with c_upload:
        st.markdown("""
        <div class="glass-card" style="text-align:center; border: 2px dashed #475569; padding: 40px;">
            <div style="font-size: 3rem; margin-bottom: 20px;">📂</div>
            <h3 style="font-weight:600; margin-bottom:10px;">Drop your P&L Screenshot</h3>
            <p style="color:#64748b; font-size:0.9rem; margin-bottom:20px;">Supports PNG, JPG. Data is processed locally.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # We place the widget "under" the visual card functionality
        file = st.file_uploader("Upload File", type=["png", "jpg"], label_visibility="collapsed")
        
        if file:
            st.success("File Received. Ready to Audit.")
            if st.button("EXECUTE FORENSIC ANALYSIS"):
                # (Your existing AI Analysis Logic)
                if not HF_TOKEN:
                    st.error("AI Token Missing.")
                else:
                    with st.spinner("Diagnosing Trading Errors..."):
                        # Image Processing
                        image = Image.open(file)
                        buf = io.BytesIO()
                        image.save(buf, format="PNG")
                        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                        
                        payload = {
                            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                            "messages": [
                                {"role": "user", "content": [
                                    {"type": "text", "text": "ACT AS: Brutal Trading Coach. Analyze this P&L. Identify FOMO, sizing errors, and suggest a fix."},
                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                                ]}
                            ],
                            "max_tokens": 800
                        }
                        
                        # Call API
                        headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                        try:
                            res = requests.post(API_URL, headers=headers, json=payload).json()
                            analysis = res['choices'][0]['message']['content']
                            st.markdown(f'<div class="glass-card">{analysis}</div>', unsafe_allow_html=True)
                        except:
                            st.error("AI Service Busy.")

    with c_info:
        # The Info Grid from your HTML
        st.markdown("""
        <div style="display:grid; gap:20px;">
            <div class="glass-card">
                <h4 style="font-weight:bold; color:#e2e8f0; margin-bottom:5px;">🧠 Pattern Recognition</h4>
                <p style="font-size:0.85rem; color:#94a3b8;">Detects if you are revenge trading or catching falling knives.</p>
            </div>
            <div class="glass-card">
                <h4 style="font-weight:bold; color:#e2e8f0; margin-bottom:5px;">💀 Risk Autopsy</h4>
                <p style="font-size:0.85rem; color:#94a3b8;">Calculates if your stop-loss was too tight or position size too big.</p>
            </div>
            <div class="glass-card">
                <h4 style="font-weight:bold; color:#e2e8f0; margin-bottom:5px;">💊 Recovery Plan</h4>
                <p style="font-size:0.85rem; color:#94a3b8;">Actionable steps to ensure your next trade isn't a disaster.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
