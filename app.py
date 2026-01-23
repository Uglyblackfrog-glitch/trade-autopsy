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

# --- 1. PAGE CONFIGURATION --- 
st.set_page_config( 
    page_title="StockPostmortem.ai | Forensic Analysis", 
    page_icon="🔬", 
    layout="wide", 
    initial_sidebar_state="collapsed" 
) 

# --- 2. SECURE CREDENTIALS --- 
try: 
    HF_TOKEN = st.secrets["HF_TOKEN"] 
    API_URL = "https://router.huggingface.co/v1/chat/completions" 
except Exception: 
    st.error("🔑 HF_TOKEN missing in Streamlit Secrets!") 
    st.stop() 

# --- 3. BRANDED UI STYLING (The #1f2e38 Theme) --- 
st.markdown(f""" 
    <style> 
    /* Main Background and Text */
    .stApp {{ 
        background-color: #0f171c; 
        color: #e2e8f0; 
    }} 
    
    /* Branding Header */
    .brand-header {{
        text-align: center;
        padding: 2rem 0;
    }}
    .brand-title {{
        font-size: 3rem;
        font-weight: 800;
        letter-spacing: -2px;
        color: #ffffff;
    }}
    .brand-accent {{
        color: #ff4d4d;
    }}

    /* Card Containers */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 24px;
        background-color: transparent;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        background-color: #1f2e38;
        border-radius: 8px 8px 0px 0px;
        color: white;
        padding: 0 20px;
    }}
    
    /* Custom Containers */
    .metric-container {{ 
        background-color: #1f2e38; 
        border: 1px solid #2d4250; 
        border-radius: 12px; 
        padding: 20px; 
        text-align: center; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }} 
    .big-price {{ font-size: 2.5rem; font-weight: 700; color: #fff; }} 
    .pos-change {{ color: #4ade80; font-weight: bold; }} 
    .neg-change {{ color: #f87171; font-weight: bold; }} 
    
    /* AI Suggestion Box */
    .ai-box {{ 
        border-left: 5px solid #ff4d4d; 
        background-color: #1f2e38; 
        padding: 25px; 
        border-radius: 8px; 
        margin-top: 15px;
        line-height: 1.6;
    }} 
    
    /* Buttons */
    .stButton>button {{ 
        width: 100%; 
        border-radius: 8px; 
        background-color: #ff4d4d !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        padding: 10px !important;
    }}
    .stButton>button:hover {{
        background-color: #cc3d3d !important;
        border: none !important;
    }}
    </style> 
    <div class="brand-header">
        <div class="brand-title">STOCK<span class="brand-accent">POSTMORTEM</span>.AI</div>
        <div style="color: #64748b; letter-spacing: 2px;">SURGICAL PRECISION IN EVERY TRADE</div>
    </div>
    """, unsafe_allow_html=True) 

# --- 4. UNIVERSAL AI ROUTER --- 
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

# --- 5. HELPER: FETCH & ANALYZE STOCK DATA --- 
def get_stock_data(symbol): 
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"): 
        symbol += ".NS" 
    stock = yf.Ticker(symbol) 
    df = stock.history(period="2y")  
    if df.empty: 
        return None, None, None 
    try: 
        df['RSI'] = ta.rsi(df['Close'], length=14) 
        df['SMA_50'] = ta.sma(df['Close'], length=50) 
        df['SMA_200'] = ta.sma(df['Close'], length=200) 
    except Exception: 
        df['RSI'] = 50 
        df['SMA_50'] = 0 
        df['SMA_200'] = 0 
    df = df.fillna(0) 
    current_price = df['Close'].iloc[-1] 
    if len(df) > 1: 
        prev_close = df['Close'].iloc[-2] 
        change_pct = ((current_price - prev_close) / prev_close) * 100 
    else: 
        change_pct = 0.0 
    technical_summary = ( 
        f"Symbol: {symbol}. Current Price: {current_price:.2f}. " 
        f"RSI (14): {df['RSI'].iloc[-1]:.2f}. " 
        f"50 SMA: {df['SMA_50'].iloc[-1]:.2f}. " 
        f"200 SMA: {df['SMA_200'].iloc[-1]:.2f}. " 
        f"Volume: {df['Volume'].iloc[-1]}. " 
        f"Trend: {'Bullish' if current_price > df['SMA_50'].iloc[-1] else 'Bearish'}." 
    ) 
    chart_df = df.tail(126)  
    return chart_df, technical_summary, change_pct 

# --- 6. HELPER: CHART RENDERING --- 
def render_chart(df, symbol): 
    fig = go.Figure(data=[go.Candlestick(x=df.index, 
                 open=df['Open'], 
                 high=df['High'], 
                 low=df['Low'], 
                 close=df['Close'], 
                 increasing_line_color='#4ade80', decreasing_line_color='#ff4d4d',
                 name=symbol)]) 

    fig.update_layout( 
        xaxis_rangeslider_visible=False, 
        template="plotly_dark", 
        plot_bgcolor="#1f2e38", 
        paper_bgcolor="#0f171c", 
        height=500, 
        margin=dict(l=0, r=0, t=30, b=0), 
        title=f"{symbol} - Forensic Chart View" 
    ) 
    return fig 

# ========================================================= 
#                   MAIN APP UI 
# ========================================================= 

tab1, tab2 = st.tabs(["🔍 LOSS POSTMORTEM", "📊 LIVE TERMINAL"]) 

# TAB 1: POSTMORTEM AUDIT
with tab1: 
    st.markdown("### 🧬 Identify Technical & Psychological Failures") 
    st.caption("Upload your P&L or trade chart to perform a forensic audit.") 
    
    left_col, right_col = st.columns([1, 1.2]) 

    with left_col: 
        file = st.file_uploader("Drop Evidence Image", type=["jpg", "png", "jpeg"]) 
        if file: 
            image = Image.open(file) 
            st.image(image, caption="Analysis Subject", use_container_width=True) 
            buf = io.BytesIO() 
            image.save(buf, format="PNG") 
            img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8') 

    with right_col: 
        if file: 
            if st.button("RUN AUTOPSY"): 
                with st.spinner("Analyzing market pathology..."): 
                    system_logic = ( 
                        "ACT AS: A Senior Financial Auditor. " 
                        "CRITICAL RULE: Perform manual math verification. Do not guess totals. " 
                        "FORMULA: Net Account P/L = (Realised P/L + Unrealised P/L). " 
                        "Individual Stock Check: If P/L is red or has a minus sign, it is a LOSS. " 
                        "TASK: Analyze the portfolio screenshot. Identify setup, entry quality, and psychological errors like FOMO." 
                    ) 
                    
                    payload = { 
                        "model": "Qwen/Qwen2.5-VL-7B-Instruct", 
                        "messages": [ 
                            {"role": "user", "content": [ 
                                {"type": "text", "text": system_logic}, 
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}} 
                            ]} 
                        ], 
                        "max_tokens": 1200 
                    } 
                    
                    res = query_router(payload) 
                    if res and res.status_code == 200: 
                        analysis = res.json()['choices'][0]['message']['content'] 
                        st.markdown(f'<div class="ai-box">{analysis}</div>', unsafe_allow_html=True)
                    else: 
                        st.error("Error connecting to AI Router.") 

# TAB 2: LIVE TERMINAL 
with tab2: 
    st.markdown("##### 🔥 TRENDING ASSETS") 
    cols = st.columns(6) 
    trending = ["RELIANCE", "TATASTEEL", "HDFCBANK", "ADANIENT", "INFY", "ZOMATO"] 
    
    if 'selected_stock' not in st.session_state: 
        st.session_state.selected_stock = "RELIANCE" 

    for i, stock in enumerate(trending): 
        if cols[i].button(stock): 
            st.session_state.selected_stock = stock 

    st.markdown("---") 

    c1, c2 = st.columns([1, 3]) 
    with c1: 
        search_query = st.text_input("🔍 Ticker Search", value=st.session_state.selected_stock) 
        if st.button("PULL DATA"): 
            st.session_state.selected_stock = search_query.upper() 

    try: 
        df, tech_summary, change = get_stock_data(st.session_state.selected_stock) 
        if df is not None: 
            cur_price = df['Close'].iloc[-1] 
            color_class = "pos-change" if change >= 0 else "neg-change" 
            sign = "+" if change >= 0 else "" 
            
            st.markdown(f""" 
                <div class="metric-container"> 
                    <span style="font-size:1.2rem; color:#94a3b8;">{st.session_state.selected_stock}.NS</span><br>
                    <span class="big-price">₹{cur_price:,.2f}</span> 
                    <span class="{color_class}" style="font-size:1.5rem; margin-left:15px;">{sign}{change:.2f}%</span> 
                </div> 
            """, unsafe_allow_html=True) 

            col_chart, col_ai = st.columns([2.5, 1]) 
            with col_chart: 
                fig = render_chart(df, st.session_state.selected_stock) 
                st.plotly_chart(fig, use_container_width=True) 

            with col_ai: 
                st.markdown("### 🤖 CLINICAL ADVICE") 
                if st.button("DIAGNOSE CHART"): 
                    with st.spinner("Scanning candles..."): 
                        ai_prompt = ( 
                            f"ACT AS: Senior Technical Trader. \n" 
                            f"DATA: {tech_summary} \n" 
                            f"TASK: Provide a trading signal. \n" 
                            f"OUTPUT FORMAT: \n" 
                            f"1. SIGNAL: (BUY/SELL/WAIT) \n" 
                            f"2. CONFIDENCE: (High/Medium/Low) \n" 
                            f"3. REASONING: Mention RSI and SMA." 
                        ) 
                        payload = { 
                            "model": "Qwen/Qwen2.5-VL-7B-Instruct", 
                            "messages": [{"role": "user", "content": ai_prompt}], 
                            "max_tokens": 300 
                        } 
                        res = query_router(payload) 
                        if res and res.status_code == 200: 
                            suggestion = res.json()['choices'][0]['message']['content'] 
                            st.markdown(f'<div class="ai-box">{suggestion}</div>', unsafe_allow_html=True) 
                        else: 
                            st.error("AI Network Busy.") 
        else: 
            st.error(f"Stock '{st.session_state.selected_stock}' not found.") 
    except Exception as e: 
        st.error(f"Data Fetch Error: {e}")
