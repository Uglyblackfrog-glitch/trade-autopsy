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
    page_title="Trade Postmortem | AI Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SECURE CREDENTIALS ---
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except Exception:
    st.error("🔑 HF_TOKEN missing in Streamlit Secrets!")
    st.stop()

# --- 3. PROFESSIONAL STYLING (Dark Mode & Cards) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    
    /* ZERODHA/GROWW STYLE METRICS */
    .metric-container {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    .big-price { font-size: 2rem; font-weight: 700; color: #fff; }
    .pos-change { color: #00ff41; font-weight: bold; }
    .neg-change { color: #ff2b2b; font-weight: bold; }
    
    /* AI SUGGESTION BOX */
    .ai-box {
        border-left: 4px solid #58a6ff;
        background-color: #1c2128;
        padding: 20px;
        border-radius: 4px;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. UNIVERSAL AI ROUTER ---
def query_router(payload):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
        "X-Wait-For-Model": "true" 
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    return response

# --- 5. HELPER: FETCH & ANALYZE STOCK DATA ---
def get_stock_data(symbol):
    # Auto-append .NS if user forgets (for NSE India)
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        symbol += ".NS"
        
    stock = yf.Ticker(symbol)
    df = stock.history(period="6mo") # Get 6 months for chart
    
    if df.empty:
        return None, None, None
        
    # Calculate Indicators for AI
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['SMA_50'] = ta.sma(df['Close'], length=50)
    df['SMA_200'] = ta.sma(df['Close'], length=200)
    
    current_price = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    change_pct = ((current_price - prev_close) / prev_close) * 100
    
    # Context summary for AI
    technical_summary = (
        f"Symbol: {symbol}. Current Price: {current_price:.2f}. "
        f"RSI (14): {df['RSI'].iloc[-1]:.2f}. "
        f"50 SMA: {df['SMA_50'].iloc[-1]:.2f}. "
        f"200 SMA: {df['SMA_200'].iloc[-1]:.2f}. "
        f"Volume: {df['Volume'].iloc[-1]}. "
        f"Trend: {'Bullish' if current_price > df['SMA_50'].iloc[-1] else 'Bearish'}."
    )
    
    return df, technical_summary, change_pct

# --- 6. HELPER: ZERODHA STYLE PLOTLY CHART ---
def render_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name=symbol)])

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        height=500,
        margin=dict(l=0, r=0, t=30, b=0),
        title=f"{symbol} - Daily Chart"
    )
    return fig

# =========================================================
#                       MAIN APP UI
# =========================================================

st.title("⚡ TRADING INTELLIGENCE HUB")

# Create two distinct Tabs
tab1, tab2 = st.tabs(["⚖️ POSTMORTEM AUDIT", "📈 LIVE TERMINAL"])

# =========================================================
# TAB 1: YOUR OLD AUDIT CODE (UNCHANGED)
# =========================================================
with tab1:
    st.markdown("### 🔍 Forensic Trade Analysis")
    st.caption("Upload your P&L screenshot to detect psychological errors.")
    
    left_col, right_col = st.columns([1, 1.2])

    with left_col:
        file = st.file_uploader("Upload Evidence", type=["jpg", "png", "jpeg"])
        if file:
            image = Image.open(file)
            st.image(image, caption="Trade Record", use_container_width=True)
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    with right_col:
        if file:
            if st.button("EXECUTE AUDIT"):
                with st.spinner("Analyzing P&L structure..."):
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
                    if res.status_code == 200:
                        analysis = res.json()['choices'][0]['message']['content']
                        st.markdown(f'<div style="background:#161b22; padding:20px; border-radius:10px;">{analysis}</div>', unsafe_allow_html=True)
                    else:
                        st.error(f"Error: {res.text}")

# =========================================================
# TAB 2: THE NEW "ZERODHA-STYLE" LIVE TERMINAL
# =========================================================
with tab2:
    # 1. TRENDING BAR
    st.markdown("##### 🔥 TRENDING NOW")
    cols = st.columns(6)
    trending = ["RELIANCE", "TATASTEEL", "HDFCBANK", "ADANIENT", "INFY", "ZOMATO"]
    
    # Keep track of selected stock in session state
    if 'selected_stock' not in st.session_state:
        st.session_state.selected_stock = "RELIANCE"

    # Create clickable buttons for trending stocks
    for i, stock in enumerate(trending):
        if cols[i].button(stock):
            st.session_state.selected_stock = stock

    st.markdown("---")

    # 2. SEARCH & DATA
    c1, c2 = st.columns([1, 3])
    
    with c1:
        search_query = st.text_input("🔍 Search Stock", value=st.session_state.selected_stock)
        if st.button("LOAD CHART"):
            st.session_state.selected_stock = search_query.upper()

    # Fetch Data
    df, tech_summary, change = get_stock_data(st.session_state.selected_stock)

    if df is not None:
        # 3. HEADER METRICS
        cur_price = df['Close'].iloc[-1]
        color_class = "pos-change" if change >= 0 else "neg-change"
        sign = "+" if change >= 0 else ""
        
        st.markdown(f"""
            <div class="metric-container">
                <span style="font-size:1.2rem; color:#aaa;">{st.session_state.selected_stock}.NS</span><br>
                <span class="big-price">₹{cur_price:,.2f}</span>
                <span class="{color_class}" style="font-size:1.2rem; margin-left:10px;">{sign}{change:.2f}%</span>
            </div>
        """, unsafe_allow_html=True)

        # 4. CHART & AI ANALYST
        col_chart, col_ai = st.columns([2.5, 1])
        
        with col_chart:
            # Render Zerodha-style Plotly Chart
            fig = render_chart(df, st.session_state.selected_stock)
            st.plotly_chart(fig, use_container_width=True)

        with col_ai:
            st.markdown("### 🤖 AI ANALYST")
            st.caption("Real-time Technical Analysis")
            
            if st.button("GENERATE SIGNAL", type="primary"):
                with st.spinner("Reading Indicators..."):
                    ai_prompt = (
                        f"ACT AS: Senior Technical Trader. \n"
                        f"DATA: {tech_summary} \n"
                        f"TASK: Provide a trading signal based strictly on the indicators provided. \n"
                        f"OUTPUT FORMAT: \n"
                        f"1. SIGNAL: (BUY / SELL / WAIT) \n"
                        f"2. CONFIDENCE: (High/Medium/Low) \n"
                        f"3. REASONING: Brief 2 sentence explanation mentioning RSI and SMA."
                    )
                    
                    payload = {
                        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                        "messages": [{"role": "user", "content": ai_prompt}],
                        "max_tokens": 300
                    }
                    
                    res = query_router(payload)
                    if res.status_code == 200:
                        suggestion = res.json()['choices'][0]['message']['content']
                        st.markdown(f'<div class="ai-box">{suggestion}</div>', unsafe_allow_html=True)
                    else:
                        st.error("AI Network Busy.")
            else:
                st.info("Click to ask AI for a live prediction based on RSI & SMA.")

    else:
        st.error(f"Stock '{st.session_state.selected_stock}' not found. Try checking the spelling.")
