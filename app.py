import streamlit as st
import requests
import base64
import io
import re
import pandas as pd
import altair as alt
from PIL import Image
from supabase import create_client, Client
from datetime import datetime

# ==========================================
# 0. AUTHENTICATION & CONFIG
# ==========================================
st.set_page_config(
    page_title="TradeInsight - Smart Trading Analysis", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- USER CREDENTIALS ---
USERS = {
    "trader1": "profit2026",
    "demo_user": "12345",
    "admin": "adminpass"
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = None

def check_login(username, password):
    if username in USERS and USERS[username] == password:
        st.session_state["authenticated"] = True
        st.session_state["user"] = username
        st.rerun()
    else:
        st.error("Invalid credentials. Please try again.")

def logout():
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.rerun()

# ==========================================
# 1. DATABASE & API SETUP
# ==========================================
if st.session_state["authenticated"]:
    try:
        HF_TOKEN = st.secrets.get("HF_TOKEN", "")
        SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
        SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
        
        if not all([HF_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
            st.warning("⚠️ Running in demo mode. Connect your database to save analyses.")
            supabase = None
        else:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            API_URL = "https://router.huggingface.co/v1/chat/completions"
            
    except Exception as e:
        st.error(f"Configuration Error: {e}")
        st.stop()

# ==========================================
# 2. MODERN CLEAN CSS THEME
# ==========================================
st.markdown("""
<style>
    /* --- FONTS & BASE --- */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;600&display=swap');
    
    :root {
        --primary: #2563eb;
        --primary-light: #3b82f6;
        --primary-dark: #1d4ed8;
        --success: #10b981;
        --danger: #ef4444;
        --warning: #f59e0b;
        --neutral-50: #f9fafb;
        --neutral-100: #f3f4f6;
        --neutral-200: #e5e7eb;
        --neutral-300: #d1d5db;
        --neutral-400: #9ca3af;
        --neutral-500: #6b7280;
        --neutral-600: #4b5563;
        --neutral-700: #374151;
        --neutral-800: #1f2937;
        --neutral-900: #111827;
    }
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body, .stApp { 
        background: linear-gradient(135deg, #f0f9ff 0%, #f8fafc 50%, #fef3f2 100%) !important;
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif !important; 
        color: var(--neutral-800);
        line-height: 1.6;
    }

    /* --- HIDE ELEMENTS --- */
    [data-testid="stSidebar"], [data-testid="collapsedControl"], 
    #MainMenu, footer, header { display: none !important; visibility: hidden !important; }
    
    /* --- CONTAINERS --- */
    .main-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 40px 32px;
    }
    
    .card {
        background: white;
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 24px;
        box-shadow: 
            0 1px 3px rgba(0, 0, 0, 0.05),
            0 20px 40px -10px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(0, 0, 0, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .card:hover {
        box-shadow: 
            0 4px 6px rgba(0, 0, 0, 0.05),
            0 25px 50px -12px rgba(0, 0, 0, 0.12);
        transform: translateY(-2px);
    }
    
    .card-compact {
        padding: 24px;
    }
    
    /* --- HEADER --- */
    .app-header {
        background: white;
        border-bottom: 1px solid var(--neutral-200);
        padding: 20px 32px;
        margin: -40px -32px 40px -32px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }
    
    .logo {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .logo-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
    }
    
    .logo-text {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--neutral-900);
        letter-spacing: -0.02em;
    }
    
    .logo-subtext {
        font-size: 0.75rem;
        color: var(--neutral-500);
        margin-top: -2px;
    }
    
    /* --- KPI GRID --- */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 20px;
        margin-bottom: 32px;
    }
    
    .kpi-item {
        background: white;
        border-radius: 14px;
        padding: 24px;
        border: 1px solid var(--neutral-200);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .kpi-item::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary), var(--primary-light));
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .kpi-item:hover {
        border-color: var(--primary-light);
        box-shadow: 0 8px 24px -8px rgba(37, 99, 235, 0.2);
        transform: translateY(-4px);
    }
    
    .kpi-item:hover::before {
        opacity: 1;
    }
    
    .kpi-label {
        font-size: 0.8rem;
        color: var(--neutral-500);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    
    .kpi-value {
        font-family: 'Fira Code', monospace;
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--neutral-900);
        line-height: 1;
    }
    
    .kpi-value.success { color: var(--success); }
    .kpi-value.danger { color: var(--danger); }
    .kpi-value.warning { color: var(--warning); }
    .kpi-value.primary { color: var(--primary); }
    
    /* --- SECTION HEADERS --- */
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 24px;
    }
    
    .section-icon {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
    }
    
    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--neutral-900);
        letter-spacing: -0.01em;
    }
    
    /* --- LOGIN --- */
    .login-wrapper {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #dbeafe 0%, #fef2f2 100%);
    }
    
    .login-card {
        background: white;
        border-radius: 24px;
        padding: 48px;
        width: 100%;
        max-width: 440px;
        box-shadow: 
            0 4px 6px rgba(0, 0, 0, 0.05),
            0 40px 80px -20px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(0, 0, 0, 0.05);
    }
    
    .login-logo {
        width: 72px;
        height: 72px;
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.5rem;
        margin: 0 auto 24px;
    }
    
    .login-title {
        font-size: 1.75rem;
        font-weight: 700;
        text-align: center;
        color: var(--neutral-900);
        margin-bottom: 8px;
    }
    
    .login-subtitle {
        text-align: center;
        color: var(--neutral-500);
        font-size: 0.9rem;
        margin-bottom: 32px;
    }
    
    /* --- TABS --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: var(--neutral-100);
        border-radius: 12px;
        padding: 6px;
        margin-bottom: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: var(--neutral-600);
        font-weight: 600;
        padding: 12px 24px;
        font-size: 0.95rem;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(37, 99, 235, 0.08);
        color: var(--primary);
    }
    
    .stTabs [aria-selected="true"] {
        background: white !important;
        color: var(--primary) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    /* --- BUTTONS --- */
    .stButton button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
        border: none;
        border-radius: 10px;
        color: white;
        font-weight: 600;
        padding: 12px 28px;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.35);
        transform: translateY(-2px);
    }
    
    .stButton button:active {
        transform: translateY(0);
    }
    
    /* --- INPUTS --- */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox select {
        background: var(--neutral-50) !important;
        border: 1px solid var(--neutral-300) !important;
        border-radius: 10px !important;
        color: var(--neutral-900) !important;
        padding: 12px 16px !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, 
    .stTextArea textarea:focus, .stSelectbox select:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
        background: white !important;
    }
    
    /* --- RADIO BUTTONS --- */
    .stRadio > div {
        background: var(--neutral-100);
        padding: 8px;
        border-radius: 10px;
        display: inline-flex;
        gap: 4px;
    }
    
    .stRadio label {
        background: transparent;
        padding: 8px 16px;
        border-radius: 6px;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .stRadio label:hover {
        background: rgba(37, 99, 235, 0.08);
    }
    
    /* --- ANALYSIS REPORT --- */
    .analysis-header {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
        border-radius: 16px 16px 0 0;
        padding: 32px;
        margin: -32px -32px 32px -32px;
        color: white;
    }
    
    .score-display {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .score-main {
        font-family: 'Fira Code', monospace;
        font-size: 5rem;
        font-weight: 800;
        line-height: 1;
        text-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    
    .score-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    
    .ticker-badge {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        padding: 10px 20px;
        border-radius: 10px;
        font-weight: 700;
        font-size: 1.1rem;
        letter-spacing: 1px;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    .analysis-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px;
        margin-top: 24px;
    }
    
    .analysis-item {
        background: var(--neutral-50);
        border-radius: 12px;
        padding: 24px;
        border-left: 4px solid var(--neutral-300);
        transition: all 0.3s ease;
    }
    
    .analysis-item:hover {
        background: white;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    .analysis-label {
        font-weight: 700;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
        display: block;
    }
    
    .analysis-item.tech { border-left-color: #3b82f6; }
    .analysis-item.tech .analysis-label { color: #3b82f6; }
    
    .analysis-item.psych { border-left-color: #8b5cf6; }
    .analysis-item.psych .analysis-label { color: #8b5cf6; }
    
    .analysis-item.risk { border-left-color: #ef4444; }
    .analysis-item.risk .analysis-label { color: #ef4444; }
    
    .analysis-item.fix { border-left-color: #10b981; }
    .analysis-item.fix .analysis-label { color: #10b981; }
    
    .analysis-content {
        color: var(--neutral-700);
        font-size: 0.9rem;
        line-height: 1.7;
    }
    
    /* --- DATAFRAME --- */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--neutral-200);
    }
    
    /* --- INSIGHTS --- */
    .insight-item {
        background: var(--neutral-50);
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 3px solid var(--primary);
        font-size: 0.9rem;
        line-height: 1.6;
        transition: all 0.2s ease;
    }
    
    .insight-item:hover {
        background: white;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
    
    /* --- UTILITY --- */
    .divider {
        height: 1px;
        background: var(--neutral-200);
        margin: 24px 0;
    }
    
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .badge-success {
        background: #dcfce7;
        color: #166534;
    }
    
    .badge-danger {
        background: #fee2e2;
        color: #991b1b;
    }
    
    .badge-warning {
        background: #fef3c7;
        color: #92400e;
    }
    
    /* --- RESPONSIVE --- */
    @media (max-width: 768px) {
        .app-header {
            flex-direction: column;
            gap: 16px;
            text-align: center;
        }
        
        .kpi-grid {
            grid-template-columns: 1fr;
        }
        
        .analysis-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def clean_text(text):
    return re.sub(r'[^\w\s,.:;!?()\[\]\-\'\"%]', '', text).strip()

def parse_report(text):
    sections = { "score": 0, "tags": [], "tech": "N/A", "psych": "N/A", "risk": "N/A", "fix": "N/A" }
    text = clean_text(text)
    
    score_match = re.search(r'\[SCORE\]\s*(\d+)', text)
    if score_match: sections['score'] = int(score_match.group(1))
    
    tags_match = re.search(r'\[TAGS\](.*?)(?=\[|$)', text, re.DOTALL)
    if tags_match:
        raw = tags_match.group(1).replace('[', '').replace(']', '').split(',')
        sections['tags'] = [t.strip() for t in raw if t.strip()]
    
    patterns = {
        "tech": r"\[TECH\](.*?)(?=\[PSYCH\]|\[RISK\]|\[FIX\]|\[SCORE\]|\[TAGS\]|$)",
        "psych": r"\[PSYCH\](.*?)(?=\[RISK\]|\[FIX\]|\[SCORE\]|\[TAGS\]|$)",
        "risk": r"\[RISK\](.*?)(?=\[FIX\]|\[SCORE\]|\[TAGS\]|$)",
        "fix": r"\[FIX\](.*?)(?=\[SCORE\]|\[TAGS\]|$)"
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL)
        if match: sections[key] = match.group(1).strip()
    return sections

def save_analysis(user_id, data, ticker_symbol="UNK"):
    if not supabase: return
    payload = {
        "user_id": user_id,
        "ticker": ticker_symbol,
        "score": data.get('score', 0),
        "mistake_tags": data.get('tags', []),
        "technical_analysis": data.get('tech', ''),
        "psych_analysis": data.get('psych', ''),
        "risk_analysis": data.get('risk', ''),
        "fix_action": data.get('fix', '')
    }
    supabase.table("trades").insert(payload).execute()

def generate_insights(df):
    insights = []
    if df.empty: return ["Start analyzing your trades to receive personalized insights."]
    
    recent_scores = df.head(3)['score'].mean()
    if recent_scores < 50:
        insights.append("⚠️ **Pattern Alert:** Your last 3 trades show lower quality scores. Consider taking a break to reset your decision-making process.")
    elif recent_scores > 80:
        insights.append("✅ **Strong Performance:** Excellent decision quality in recent trades. Your current strategy is working well.")

    all_tags = [tag for sublist in df['mistake_tags'] for tag in sublist]
    if "FOMO" in all_tags:
        fomo_count = all_tags.count("FOMO")
        insights.append(f"📊 **Behavioral Pattern:** FOMO detected in {fomo_count} trades. Consider implementing entry rules to reduce impulsive decisions.")
    
    if "Revenge" in all_tags:
        insights.append("🎯 **Risk Management:** Revenge trading detected. Establish clear loss limits and take mandatory breaks after losses.")
    
    return insights

# ==========================================
# 4. MAIN APP LOGIC
# ==========================================

# --- LOGIN VIEW ---
if not st.session_state["authenticated"]:
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div class="login-card">
            <div class="login-logo">📊</div>
            <h1 class="login-title">TradeInsight</h1>
            <p class="login-subtitle">Smart trading analysis powered by AI</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.text_input("Username", key="username_input", placeholder="Enter your username")
            st.text_input("Password", type="password", key="password_input", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
            if submitted:
                check_login(st.session_state.username_input, st.session_state.password_input)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD VIEW ---
else:
    current_user = st.session_state["user"]
    
    # --- HEADER ---
    st.markdown(f"""
    <div class="app-header">
        <div class="logo">
            <div class="logo-icon">📊</div>
            <div>
                <div class="logo-text">TradeInsight</div>
                <div class="logo-subtext">Smart Trading Analysis</div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 16px;">
            <div style="text-align: right; margin-right: 12px;">
                <div style="font-weight: 600; color: var(--neutral-900);">{current_user}</div>
                <div style="font-size: 0.8rem; color: var(--neutral-500);">Active Session</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # User menu in popover
    col_spacer, col_menu = st.columns([6, 1])
    with col_menu:
        with st.popover("⚙️", use_container_width=True):
            st.markdown(f"**User:** {current_user}")
            st.markdown("**Plan:** Professional")
            st.divider()
            if st.button("Sign Out", type="primary", use_container_width=True):
                logout()
    
    st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
    
    # TABS
    tab1, tab2 = st.tabs(["📝 New Analysis", "📈 Dashboard"])
    
    # --- TAB 1: NEW ANALYSIS ---
    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="section-icon">📝</div>
            <div class="section-title">Trade Analysis</div>
        </div>
        """, unsafe_allow_html=True)
        
        analysis_mode = st.radio(
            "Analysis Method",
            ["Manual Entry", "Chart Upload"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
        
        prompt = ""
        img_b64 = None
        ticker_val = "UNKNOWN"
        ready_to_run = False
        
        if analysis_mode == "Chart Upload":
            st.markdown("#### Upload Trading Chart")
            uploaded_file = st.file_uploader(
                "Drop your chart image here",
                type=["png", "jpg", "jpeg"],
                label_visibility="collapsed"
            )
            
            if uploaded_file:
                st.image(uploaded_file, use_column_width=True)
                st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                
                if st.button("Analyze Chart", type="primary", use_container_width=True):
                    image = Image.open(uploaded_file)
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    prompt = """
                    You are a professional trading analyst. Analyze this chart for:
                    - Technical setup quality
                    - Entry/exit timing
                    - Risk management issues
                    - Psychological factors
                    
                    Provide output in this format:
                    [SCORE] (0-100)
                    [TAGS] (comma-separated mistake types)
                    [TECH] (technical analysis)
                    [PSYCH] (psychological factors)
                    [RISK] (risk assessment)
                    [FIX] (corrective actions)
                    """
                    ticker_val = "CHART"
                    ready_to_run = True
        
        else:
            with st.form("trade_form"):
                st.markdown("#### Trade Details")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    ticker = st.text_input("Ticker Symbol", "AAPL", placeholder="e.g. AAPL")
                with col2:
                    setup = st.selectbox("Setup Type", ["Trend Following", "Mean Reversion", "Breakout", "Breakdown"])
                with col3:
                    emotion = st.selectbox("Emotional State", ["Neutral", "Confident", "Anxious", "FOMO", "Revenge"])
                
                st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
                
                col4, col5, col6 = st.columns(3)
                with col4:
                    entry = st.number_input("Entry Price ($)", 0.0, step=0.01, format="%.2f")
                with col5:
                    exit_price = st.number_input("Exit Price ($)", 0.0, step=0.01, format="%.2f")
                with col6:
                    stop = st.number_input("Stop Loss ($)", 0.0, step=0.01, format="%.2f")
                
                st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
                
                notes = st.text_area(
                    "Trade Notes",
                    height=120,
                    placeholder="Describe your thought process, hesitations, and decision-making during this trade..."
                )
                
                st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                
                submitted = st.form_submit_button("Analyze Trade", type="primary", use_container_width=True)
                
                if submitted:
                    ticker_val = ticker
                    pnl = exit_price - entry if exit_price > 0 and entry > 0 else 0
                    pnl_pct = (pnl / entry * 100) if entry > 0 else 0
                    
                    prompt = f"""
                    You are a professional trading coach. Analyze this trade:
                    
                    TRADE DATA:
                    - Ticker: {ticker}
                    - Setup: {setup}
                    - Emotional State: {emotion}
                    - Entry: ${entry}
                    - Exit: ${exit_price}
                    - Stop: ${stop}
                    - P&L: ${pnl:.2f} ({pnl_pct:.1f}%)
                    - Notes: {notes}
                    
                    Provide constructive analysis in this format:
                    [SCORE] (0-100 quality score)
                    [TAGS] (mistake types: FOMO, Revenge, Poor Risk, No Stop, etc)
                    [TECH] (technical analysis of setup and execution)
                    [PSYCH] (psychological factors and emotional state)
                    [RISK] (risk management assessment)
                    [FIX] (specific actionable improvements)
                    """
                    ready_to_run = True
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # RESULTS
        if ready_to_run and supabase:
            with st.spinner("🤖 Analyzing trade..."):
                try:
                    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
                    if img_b64:
                        messages[0]["content"].append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                        })
                    
                    payload = {
                        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                        "messages": messages,
                        "max_tokens": 600
                    }
                    headers = {
                        "Authorization": f"Bearer {HF_TOKEN}",
                        "Content-Type": "application/json"
                    }
                    res = requests.post(API_URL, headers=headers, json=payload)
                    
                    if res.status_code == 200:
                        report = parse_report(res.json()["choices"][0]["message"]["content"])
                        save_analysis(current_user, report, ticker_val)
                        
                        # Determine score color
                        if report['score'] >= 75:
                            score_color = "var(--success)"
                            score_bg = "linear-gradient(135deg, #10b981 0%, #059669 100%)"
                        elif report['score'] >= 50:
                            score_color = "var(--warning)"
                            score_bg = "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)"
                        else:
                            score_color = "var(--danger)"
                            score_bg = "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)"
                        
                        st.markdown('<div style="height: 32px;"></div>', unsafe_allow_html=True)
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        
                        st.markdown(f"""
                        <div class="analysis-header" style="background: {score_bg};">
                            <div class="score-display">
                                <div>
                                    <div class="score-label">Trade Quality Score</div>
                                    <div class="score-main">{report['score']}</div>
                                </div>
                                <div style="text-align: right;">
                                    <div class="ticker-badge">{ticker_val}</div>
                                    <div style="font-size: 0.85rem; opacity: 0.9; margin-top: 8px;">
                                        {datetime.now().strftime('%B %d, %Y')}
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"""
                        <div class="analysis-grid">
                            <div class="analysis-item tech">
                                <span class="analysis-label">Technical Analysis</span>
                                <div class="analysis-content">{report['tech']}</div>
                            </div>
                            <div class="analysis-item psych">
                                <span class="analysis-label">Psychology</span>
                                <div class="analysis-content">{report['psych']}</div>
                            </div>
                            <div class="analysis-item risk">
                                <span class="analysis-label">Risk Management</span>
                                <div class="analysis-content">{report['risk']}</div>
                            </div>
                            <div class="analysis-item fix">
                                <span class="analysis-label">Action Plan</span>
                                <div class="analysis-content">{report['fix']}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.success("✅ Analysis saved to your dashboard")
                        
                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
    
    # --- TAB 2: DASHBOARD ---
    with tab2:
        if supabase:
            hist = supabase.table("trades").select("*").eq("user_id", current_user).order("created_at", desc=True).execute()
            
            if hist.data:
                df = pd.DataFrame(hist.data)
                df['created_at'] = pd.to_datetime(df['created_at'])
                
                # Calculate metrics
                avg_score = df['score'].mean()
                total_trades = len(df)
                all_tags = [tag for sublist in df['mistake_tags'] for tag in sublist]
                top_mistake = pd.Series(all_tags).mode()[0] if all_tags else "None"
                recent_trend = "Improving" if len(df) >= 2 and df.iloc[0]['score'] > df.iloc[1]['score'] else "Stable"
                
                # KPI Cards
                st.markdown(f"""
                <div class="kpi-grid">
                    <div class="kpi-item">
                        <div class="kpi-label">Average Score</div>
                        <div class="kpi-value primary">{int(avg_score)}</div>
                    </div>
                    <div class="kpi-item">
                        <div class="kpi-label">Total Analyses</div>
                        <div class="kpi-value">{total_trades}</div>
                    </div>
                    <div class="kpi-item">
                        <div class="kpi-label">Top Pattern</div>
                        <div class="kpi-value danger" style="font-size: 1.4rem;">{top_mistake}</div>
                    </div>
                    <div class="kpi-item">
                        <div class="kpi-label">Trend</div>
                        <div class="kpi-value success" style="font-size: 1.6rem;">{recent_trend}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Main content columns
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    # Performance chart
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown("""
                    <div class="section-header">
                        <div class="section-icon">📈</div>
                        <div class="section-title">Performance Trend</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    chart_data = df[['created_at', 'score']].sort_values('created_at')
                    
                    base = alt.Chart(chart_data).encode(
                        x=alt.X('created_at:T', 
                            title=None,
                            axis=alt.Axis(
                                labelColor='#6b7280',
                                labelFontSize=11,
                                grid=False
                            )
                        )
                    )
                    
                    line = base.mark_line(
                        color='#2563eb',
                        strokeWidth=3,
                        point=alt.OverlayMarkDef(
                            color='#2563eb',
                            filled=True,
                            size=80
                        )
                    ).encode(
                        y=alt.Y('score:Q',
                            title='Score',
                            scale=alt.Scale(domain=[0, 100]),
                            axis=alt.Axis(
                                labelColor='#6b7280',
                                titleColor='#374151',
                                grid=True,
                                gridColor='#e5e7eb'
                            )
                        )
                    )
                    
                    area = base.mark_area(
                        color='#2563eb',
                        opacity=0.1
                    ).encode(
                        y='score:Q'
                    )
                    
                    chart = (line + area).properties(
                        height=300
                    ).configure_view(
                        strokeWidth=0
                    )
                    
                    st.altair_chart(chart, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Trade history table
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown("""
                    <div class="section-header">
                        <div class="section-icon">📋</div>
                        <div class="section-title">Trade History</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    table_df = df[['created_at', 'ticker', 'score', 'mistake_tags']].copy()
                    table_df.columns = ['Date', 'Ticker', 'Score', 'Tags']
                    
                    st.dataframe(
                        table_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Score": st.column_config.ProgressColumn(
                                "Score",
                                min_value=0,
                                max_value=100,
                                format="%d"
                            ),
                            "Date": st.column_config.DatetimeColumn(
                                "Date",
                                format="MMM DD, h:mm a"
                            )
                        }
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col_right:
                    # AI Insights
                    st.markdown('<div class="card card-compact">', unsafe_allow_html=True)
                    st.markdown("""
                    <div class="section-header">
                        <div class="section-icon">💡</div>
                        <div class="section-title">Insights</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    insights = generate_insights(df)
                    for insight in insights:
                        st.markdown(f'<div class="insight-item">{insight}</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Mistake distribution
                    st.markdown('<div class="card card-compact">', unsafe_allow_html=True)
                    st.markdown("""
                    <div class="section-header">
                        <div class="section-icon">🎯</div>
                        <div class="section-title">Patterns</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if all_tags:
                        tag_counts = pd.Series(all_tags).value_counts().reset_index()
                        tag_counts.columns = ['Pattern', 'Count']
                        
                        chart = alt.Chart(tag_counts).mark_arc(
                            innerRadius=50,
                            cornerRadius=5,
                            padAngle=0.02
                        ).encode(
                            theta=alt.Theta("Count:Q"),
                            color=alt.Color("Pattern:N",
                                scale=alt.Scale(scheme='blues'),
                                legend=alt.Legend(
                                    title=None,
                                    labelFontSize=11,
                                    labelColor='#6b7280',
                                    orient='bottom'
                                )
                            ),
                            tooltip=['Pattern', 'Count']
                        ).properties(height=280)
                        
                        st.altair_chart(chart, use_container_width=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            
            else:
                st.info("📊 No data yet. Start by analyzing your first trade!")
        
        else:
            st.warning("Connect your database to view dashboard analytics")
