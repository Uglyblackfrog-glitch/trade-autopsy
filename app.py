import streamlit as st
import requests
import base64
import json
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from PIL import Image
import io

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="StockPostmortem.ai",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# 2. SECURE CREDENTIALS
# =========================================================
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except Exception:
    st.error("🔑 HF_TOKEN missing in Streamlit Secrets!")
    st.stop()

# =========================================================
# 3. PIXEL-PERFECT CSS ENGINE
# =========================================================
st.markdown("""
    <style>
    /* --------------------------------------------------------
       FONTS & GLOBAL RESET
    -------------------------------------------------------- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,600;0,800;1,800&display=swap');
    
    .stApp {
        background-color: #0f171c;
        font-family: 'Inter', sans-serif;
        color: #e2e8f0;
    }
    
    /* Hide Streamlit Default Header/Footer */
    header[data-testid="stHeader"] {display: none;}
    footer {display: none;}
    #MainMenu {display: none;}
    
    /* --------------------------------------------------------
       NAVBAR
    -------------------------------------------------------- */
    .navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 0;
        border-bottom: 1px solid #1f2e38;
        margin-bottom: 40px;
    }
    .nav-logo {
        font-size: 24px;
        font-weight: 800;
        color: #fff;
        letter-spacing: -1px;
    }
    .nav-logo span { color: #ff4d4d; }
    
    .nav-links {
        display: flex;
        gap: 30px;
        font-size: 14px;
        font-weight: 600;
        color: #cbd5e1;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* --------------------------------------------------------
       HERO SECTION
    -------------------------------------------------------- */
    .hero-title {
        font-size: 64px;
        font-weight: 800;
        font-style: italic;
        text-align: center;
        margin-bottom: 10px;
        line-height: 1.1;
        color: #fff;
    }
    .hero-sub {
        text-align: center;
        color: #94a3b8;
        font-size: 18px;
        max-width: 700px;
        margin: 0 auto 40px auto;
        line-height: 1.6;
    }

    /* --------------------------------------------------------
       UPLOAD ZONE (DASHED BOX)
    -------------------------------------------------------- */
    .upload-container {
        border: 2px dashed #334155;
        border-radius: 16px;
        background-color: rgba(31, 46, 56, 0.4);
        padding: 50px 20px;
        text-align: center;
        max-width: 800px;
        margin: 0 auto 60px auto;
        transition: all 0.3s ease;
    }
    .upload-container:hover {
        border-color: #ff4d4d;
        background-color: rgba(31, 46, 56, 0.6);
    }
    .upload-icon {
        font-size: 40px;
        color: #ff4d4d;
        margin-bottom: 15px;
    }
    .upload-text {
        font-size: 20px;
        font-weight: 700;
        color: #fff;
        margin-bottom: 8px;
    }
    .upload-sub {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 25px;
    }

    /* Override Streamlit File Uploader to fit design */
    [data-testid="stFileUploader"] {
        max-width: 400px;
        margin: 0 auto;
    }
    section[data-testid="stFileUploaderDropzone"] {
        background-color: transparent;
        border: 1px solid #334155;
    }

    /* --------------------------------------------------------
       FEATURE GRID
    -------------------------------------------------------- */
    .feature-card {
        background-color: #1f2e38;
        padding: 30px;
        border-radius: 12px;
        height: 100%;
        border: 1px solid #2d4250;
    }
    .feature-title {
        color: #fff;
        font-weight: 700;
        font-size: 18px;
        margin-bottom: 10px;
    }
    .feature-desc {
        color: #94a3b8;
        font-size: 14px;
        line-height: 1.5;
    }

    /* --------------------------------------------------------
       UI ELEMENTS (Buttons & Inputs)
    -------------------------------------------------------- */
    .stButton>button {
        background-color: #ff4d4d;
        color: white;
        border: none;
        padding: 12px 30px;
        border-radius: 6px;
        font-weight: 700;
        transition: 0.3s;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #ff3333;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 77, 77, 0.3);
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        justify-content: center;
        border-bottom: 1px solid #1f2e38;
        padding-bottom: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border: none;
        color: #64748b;
        font-weight: 600;
        font-size: 14px;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #ff4d4d;
        border-bottom: 2px solid #ff4d4d;
    }
    
    /* Inputs */
    .stTextInput input {
        background-color: #1f2e38;
        color: white;
        border: 1px solid #334155;
        border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 4. BACKEND LOGIC (EXACT COPY)
# =========================================================

def query_router(payload):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
        "X-Wait-For-Model": "true" 
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        return response
    except Exception as e:
        return None

def get_stock_data(symbol):
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        symbol += ".NS"
    
    stock = yf.Ticker(symbol)
    df = stock.history(period="2y") # 2 years for 200 SMA
    
    if df.empty: return None, None, None
    
    try:
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
    except:
        df['RSI'] = 50; df['SMA_50'] = 0; df['SMA_200'] = 0
        
    df = df.fillna(0)
    current_price = df['Close'].iloc[-1]
    
    if len(df) > 1:
        prev_close = df['Close'].iloc[-2]
        change_pct = ((current_price - prev_close) / prev_close) * 100
    else:
        change_pct = 0.0
        
    tech_summary = (
        f"Symbol: {symbol}. Price: {current_price:.2f}. "
        f"RSI: {df['RSI'].iloc[-1]:.2f}. SMA50: {df['SMA_50'].iloc[-1]:.2f}. "
        f"Trend: {'Bullish' if current_price > df['SMA_50'].iloc[-1] else 'Bearish'}."
    )
    return df.tail(126), tech_summary, change_pct

def render_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name=symbol)])
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        plot_bgcolor="#0f171c",
        paper_bgcolor="#0f171c",
        height=500,
        margin=dict(l=0, r=0, t=30, b=0),
        title=f"{symbol} - Daily Chart"
    )
    return fig

# =========================================================
# 5. UI LAYOUT & NAVIGATION
# =========================================================

# --- NAVBAR HTML ---
st.markdown("""
    <div class="navbar">
        <div class="nav-logo">STOCK<span>POSTMORTEM</span>.AI</div>
        <div class="nav-links">
            <span>Analyze</span>
            <span>Case Studies</span>
            <span>Pricing</span>
            <span style="background:#ff4d4d; color:white; padding:8px 20px; border-radius:50px;">Get Started</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- MAIN TABS ---
tab1, tab2 = st.tabs(["HOME / AUDIT", "LIVE TERMINAL"])

# =========================================================
# TAB 1: THE LANDING PAGE / AUDIT UI
# =========================================================
with tab1:
    # 1. HERO TEXT
    st.markdown('<div class="hero-title">STOP BLEEDING CAPITAL.</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="hero-sub">
            Upload your losing trade screenshots. Our AI identifies psychological traps,
            technical failures, and provides a surgical path to recovery.
        </div>
    """, unsafe_allow_html=True)

    # 2. UPLOAD ZONE
    # We wrap the Streamlit uploader in our custom CSS container
    st.markdown('<div class="upload-container">', unsafe_allow_html=True)
    st.markdown('<div class="upload-icon">☁️</div>', unsafe_allow_html=True)
    st.markdown('<div class="upload-text">Drop your P&L or Chart screenshot here</div>', unsafe_allow_html=True)
    st.markdown('<div class="upload-sub">Supports PNG, JPG (Max 10MB). Encrypted & Deleted after analysis.</div>', unsafe_allow_html=True)
    
    file = st.file_uploader("", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    
    if file:
        st.success("File Successfully Loaded")
        if st.button("INITIATE SURGICAL ANALYSIS"):
            with st.spinner("Running Forensic Algorithms..."):
                image = Image.open(file)
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                
                system_logic = (
                    "ACT AS: A Senior Financial Auditor. "
                    "TASK: Analyze the portfolio/chart screenshot. Identify psychological errors (FOMO, Revenge Trading) and Technical failures."
                    "OUTPUT: Provide a brutal, honest assessment and a recovery plan."
                )
                
                payload = {
                    "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                    "messages": [
                        {"role": "user", "content": [
                            {"type": "text", "text": system_logic},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                        ]}
                    ],
                    "max_tokens": 1000
                }
                
                res = query_router(payload)
                if res and res.status_code == 200:
                    analysis = res.json()['choices'][0]['message']['content']
                    st.markdown(f"""
                    <div style="background:#1f2e38; border-left:4px solid #ff4d4d; padding:20px; border-radius:8px; margin-top:20px;">
                        {analysis}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("Analysis Failed. Check Connection.")
    
    st.markdown('</div>', unsafe_allow_html=True) # End Upload Container

    # 3. FEATURE GRID
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">Pattern Recognition</div>
            <div class="feature-desc">Did you buy the top? We identify if you're falling for FOMO or revenge trading.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">Risk Autopsy</div>
            <div class="feature-desc">Calculates if your stop-loss was too tight or if your position sizing was reckless.</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">Recovery Plan</div>
            <div class="feature-desc">Step-by-step technical adjustments to ensure the next trade is a winner.</div>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# TAB 2: LIVE TERMINAL (SAME LOGIC, MATCHING THEME)
# =========================================================
with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # SEARCH BAR
    col_search, col_space = st.columns([1, 2])
    with col_search:
        if 'selected_stock' not in st.session_state: st.session_state.selected_stock = "RELIANCE"
        search_query = st.text_input("SEARCH TICKER", value=st.session_state.selected_stock)
        if st.button("LOAD CHART"): st.session_state.selected_stock = search_query.upper()

    # FETCH DATA
    try:
        df, tech_summary, change = get_stock_data(st.session_state.selected_stock)
        
        if df is not None:
            # METRICS CARD
            cur_price = df['Close'].iloc[-1]
            color = "#00ff41" if change >= 0 else "#ff4d4d"
            
            st.markdown(f"""
            <div style="background:#1f2e38; padding:20px; border-radius:12px; border:1px solid #2d4250; margin-bottom:20px; display:flex; align-items:center; gap:20px;">
                <div>
                    <span style="color:#94a3b8; font-size:14px;">{st.session_state.selected_stock}.NS</span><br>
                    <span style="color:white; font-size:32px; font-weight:800;">₹{cur_price:,.2f}</span>
                </div>
                <div style="color:{color}; font-size:20px; font-weight:700;">
                    {change:+.2f}%
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # CHART & AI
            c_chart, c_ai = st.columns([3, 1])
            
            with c_chart:
                st.plotly_chart(render_chart(df, st.session_state.selected_stock), use_container_width=True)
                
            with c_ai:
                st.markdown('<div class="feature-card" style="height:auto;">', unsafe_allow_html=True)
                st.markdown('<div class="feature-title">AI Analyst</div>', unsafe_allow_html=True)
                if st.button("GENERATE SIGNAL", key="sig_btn"):
                    with st.spinner("Analyzing..."):
                        prompt = f"ACT AS: Trader. DATA: {tech_summary}. TASK: Buy/Sell/Wait signal + 1 sentence reason."
                        payload = {
                            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 200
                        }
                        res = query_router(payload)
                        if res:
                            st.info(res.json()['choices'][0]['message']['content'])
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("Stock not found.")
            
    except Exception as e:
        st.error(f"Error: {e}")
