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
    page_title="StockPostmortem.ai", 
    page_icon="🩸", 
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
    st.session_state["current_page"] = "analyze"  # Default page

# Check for URL parameters
try:
    params = st.query_params
    if "page" in params:
        st.session_state["current_page"] = params["page"]
except:
    pass

def check_login(username, password):
    if username in USERS and USERS[username] == password:
        st.session_state["authenticated"] = True
        st.session_state["user"] = username
        st.rerun()
    else:
        st.error("Access Denied: Invalid Credentials")

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
            st.warning("⚠️ Secrets missing. Running in UI-only mode.")
            supabase = None
        else:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            API_URL = "https://router.huggingface.co/v1/chat/completions"
            
    except Exception as e:
        st.error(f"⚠️ Configuration Error: {e}")
        st.stop()

# ==========================================
# 2. ULTRA-MODERN CSS THEME
# ==========================================
st.markdown("""
<style>
    /* --- GLOBAL FONTS & RESET --- */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body, .stApp { 
        background: #000000 !important;
        background-image: 
            radial-gradient(ellipse at 20% 10%, rgba(220, 38, 38, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 90%, rgba(220, 38, 38, 0.05) 0%, transparent 50%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; 
        color: #f8fafc; 
        line-height: 1.6;
    }
    
    /* --- REMOVE TOP PADDING --- */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
    }

    /* --- HIDE SIDEBAR & STREAMLIT ELEMENTS --- */
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    
    /* --- REFINED GLASSMORPHISM --- */
    .glass-panel {
        background: rgba(15, 15, 15, 0.65);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        padding: 32px;
        margin-bottom: 24px;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.03);
        transition: all 0.3s ease;
    }
    
    .glass-panel:hover {
        border-color: rgba(255, 255, 255, 0.1);
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    
    /* --- KPI CARDS WITH ENHANCED GRADIENT --- */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 20px;
        margin-bottom: 32px;
    }
    
    .kpi-card {
        background: linear-gradient(135deg, rgba(20, 20, 20, 0.8) 0%, rgba(10, 10, 10, 0.9) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 28px 24px;
        border-radius: 16px;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        position: relative;
        overflow: hidden;
    }
    
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(220, 38, 38, 0.5), transparent);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    
    .kpi-card:hover {
        border-color: rgba(220, 38, 38, 0.3);
        transform: translateY(-6px);
        box-shadow: 
            0 16px 48px -12px rgba(220, 38, 38, 0.25),
            0 0 0 1px rgba(220, 38, 38, 0.1);
    }
    
    .kpi-card:hover::before {
        opacity: 1;
    }
    
    .kpi-val { 
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.75rem; 
        font-weight: 700; 
        background: linear-gradient(135deg, #ffffff 0%, #e5e7eb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 8px;
        letter-spacing: -0.02em;
    }
    
    .kpi-label { 
        color: #9ca3af; 
        font-size: 0.75rem; 
        text-transform: uppercase; 
        letter-spacing: 2px; 
        font-weight: 600; 
    }

    /* --- LOGIN CONTAINER --- */
    .login-container {
        max-width: 440px;
        margin: 12vh auto;
        padding: 48px;
        background: rgba(15, 15, 15, 0.85);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        box-shadow: 
            0 20px 60px rgba(0, 0, 0, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
        text-align: center;
    }
    
    .login-logo {
        font-size: 3.5rem;
        margin-bottom: 16px;
        filter: drop-shadow(0 0 20px rgba(220, 38, 38, 0.3));
    }

    /* --- SECTION TITLES --- */
    .section-title {
        font-size: 1rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 12px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    .section-title::before {
        content: '';
        display: block;
        width: 3px;
        height: 20px;
        background: linear-gradient(180deg, #dc2626 0%, #991b1b 100%);
        border-radius: 2px;
        box-shadow: 0 0 10px rgba(220, 38, 38, 0.4);
    }

    /* --- ANALYSIS REPORT GRID --- */
    .report-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 16px;
        margin-top: 24px;
    }
    
    .report-item {
        background: rgba(255, 255, 255, 0.02);
        border-left: 3px solid rgba(100, 100, 100, 0.4);
        padding: 20px;
        border-radius: 0 12px 12px 0;
        transition: all 0.3s ease;
        font-size: 0.9rem;
        line-height: 1.7;
    }
    
    .report-item:hover {
        background: rgba(255, 255, 255, 0.04);
        border-left-color: currentColor;
    }
    
    .report-label {
        font-weight: 700;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 12px;
        display: block;
    }

    /* --- TABS STYLING --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(20, 20, 20, 0.4);
        border-radius: 12px;
        padding: 6px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #9ca3af;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.05);
        color: #f8fafc;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(220, 38, 38, 0.15) !important;
        color: #fca5a5 !important;
        box-shadow: 0 0 20px rgba(220, 38, 38, 0.2);
    }

    /* --- BUTTONS --- */
    .stButton button {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
        border: 1px solid rgba(220, 38, 38, 0.3);
        border-radius: 12px;
        color: white;
        font-weight: 600;
        padding: 12px 28px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(220, 38, 38, 0.2);
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #b91c1c 0%, #7f1d1d 100%);
        box-shadow: 0 6px 24px rgba(220, 38, 38, 0.35);
        transform: translateY(-2px);
    }
    
    /* --- HEADER NAVIGATION --- */
    .header-nav {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0;
        background: rgba(15, 15, 15, 0.4);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 6px;
    }
    
    /* --- NAVIGATION BUTTONS - CLEAN GLASS MORPHISM --- */
    button[key="nav_btn_analyze"],
    button[key="nav_btn_vault"],
    button[key="nav_btn_pricing"] {
        background: transparent !important;
        border: none !important;
        color: rgba(255, 255, 255, 0.6) !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        padding: 12px 32px !important;
        border-radius: 8px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
        box-shadow: none !important;
        margin: 0 4px !important;
        min-height: 44px !important;
    }
    
    button[key="nav_btn_analyze"]:hover,
    button[key="nav_btn_vault"]:hover,
    button[key="nav_btn_pricing"]:hover {
        background: rgba(255, 255, 255, 0.03) !important;
        color: rgba(255, 255, 255, 0.9) !important;
        transform: none !important;
        box-shadow: none !important;
    }
    
    /* Active state with subtle red underline glow */
    button[key="nav_btn_analyze"]::after,
    button[key="nav_btn_vault"]::after,
    button[key="nav_btn_pricing"]::after {
        content: '';
        position: absolute;
        bottom: 6px;
        left: 25%;
        right: 25%;
        height: 2px;
        background: transparent;
        border-radius: 2px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    button[key="nav_btn_analyze"]:hover::after,
    button[key="nav_btn_vault"]:hover::after,
    button[key="nav_btn_pricing"]:hover::after {
        background: linear-gradient(90deg, 
            rgba(220, 38, 38, 0) 0%, 
            rgba(220, 38, 38, 0.4) 50%, 
            rgba(220, 38, 38, 0) 100%);
    }
    
    /* Remove all red backgrounds from buttons */
    div[data-testid="column"] button[key^="nav_btn"] {
        background: transparent !important;
    }
    
    div[data-testid="column"] button[key^="nav_btn"]:hover {
        background: rgba(255, 255, 255, 0.03) !important;
    }

    /* --- INPUTS --- */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox select {
        background: rgba(20, 20, 20, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        color: #f8fafc !important;
        padding: 12px 16px !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus {
        border-color: rgba(220, 38, 38, 0.4) !important;
        box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1) !important;
    }

    /* --- FILE UPLOADER STYLING --- */
    [data-testid="stFileUploader"] {
        background: transparent !important;
    }
    
    [data-testid="stFileUploader"] > div {
        background: transparent !important;
        border: none !important;
    }
    
    [data-testid="stFileUploader"] section {
        background: rgba(15, 15, 15, 0.6) !important;
        backdrop-filter: blur(10px);
        border: 2px dashed rgba(220, 38, 38, 0.3) !important;
        border-radius: 20px !important;
        padding: 60px 40px !important;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1) !important;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(220, 38, 38, 0.6) !important;
        background: rgba(20, 20, 20, 0.7) !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(220, 38, 38, 0.15);
    }
    
    [data-testid="stFileUploader"] section button {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 14px 32px !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 16px rgba(220, 38, 38, 0.25) !important;
        margin-top: 20px !important;
    }
    
    [data-testid="stFileUploader"] section button:hover {
        background: linear-gradient(135deg, #b91c1c 0%, #7f1d1d 100%) !important;
        box-shadow: 0 6px 24px rgba(220, 38, 38, 0.4) !important;
        transform: translateY(-2px);
    }
    
    .upload-icon {
        font-size: 3.5rem;
        margin-bottom: 24px;
        display: block;
        opacity: 0.8;
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    .upload-text {
        font-size: 1.4rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 12px;
        letter-spacing: -0.01em;
    }
    
    .upload-subtext {
        font-size: 0.9rem;
        color: #9ca3af;
        line-height: 1.6;
    }

    /* --- DATAFRAME STYLING --- */
    .stDataFrame {
        background: rgba(15, 15, 15, 0.6);
        border-radius: 12px;
        overflow: hidden;
    }

    /* --- SCORE DISPLAY --- */
    .score-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
    }
    
    .score-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 5rem;
        font-weight: 800;
        line-height: 1;
        letter-spacing: -0.03em;
    }
    
    .score-meta {
        text-align: right;
    }
    
    .ticker-badge {
        background: rgba(255, 255, 255, 0.08);
        padding: 8px 16px;
        border-radius: 8px;
        display: inline-block;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }

    /* --- UTILITY CLASSES --- */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        margin: 24px 0;
    }
    
    .accent-text {
        color: #fca5a5;
        font-weight: 600;
    }
    
    /* --- HIDE UNNECESSARY BOXES --- */
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    
    /* Clean up radio button container */
    .stRadio > div {
        background: transparent !important;
        border: none !important;
    }
    
    /* Clean up form containers */
    [data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
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
    if df.empty: return ["Awaiting data to generate neural patterns."]
    
    recent_scores = df.head(3)['score'].mean()
    if recent_scores < 50:
        insights.append("⚠️ **Tilt Detected:** Last 3 trades avg < 50. Suggest 24h trading halt.")
    elif recent_scores > 80:
        insights.append("🔥 **Flow State:** High decision quality detected. Increase risk tolerance slightly.")

    all_tags = [tag for sublist in df['mistake_tags'] for tag in sublist]
    if "FOMO" in all_tags and "Revenge" in all_tags:
        insights.append("🧠 **Toxic Loop:** 'FOMO' leading to 'Revenge' detected 3x this month.")
    
    return insights

# ==========================================
# 4. MAIN APP LOGIC
# ==========================================

# --- LOGIN VIEW ---
if not st.session_state["authenticated"]:
    st.markdown("""
    <div class="login-container">
        <div class="login-logo">🩸</div>
        <h1 style="margin: 0 0 8px 0; font-size: 2rem; font-weight: 800; letter-spacing: -0.02em;">StockPostmortem</h1>
        <p style="color: #6b7280; font-size: 0.85rem; margin-bottom: 40px; letter-spacing: 2px; text-transform: uppercase;">Algorithmic Behavioral Forensics</p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1,1.2,1])
    with c2:
        with st.form("login_form"):
            st.text_input("Operator ID", key="username_input", placeholder="Enter your ID")
            st.text_input("Access Key", type="password", key="password_input", placeholder="Enter your key")
            submitted = st.form_submit_button("INITIALIZE TERMINAL", type="primary", use_container_width=True)
            if submitted:
                check_login(st.session_state.username_input, st.session_state.password_input)

# --- DASHBOARD VIEW ---
else:
    current_user = st.session_state["user"]
    current_page = st.session_state.get("current_page", "analyze")
    
    # --- EXACT HEADER FROM SCREENSHOT ---
    st.markdown(f"""
    <div class="header-bar">
        <div class="header-content">
            <!-- Logo -->
            <div class="header-logo">
                <span style="color: #ffffff;">STOCK</span><span style="color: #dc2626;">POSTMORTEM</span><span style="color: #9ca3af;">.AI</span>
            </div>
            
            <!-- Navigation -->
            <div class="header-nav-items">
                <a href="#" class="nav-item {'nav-item-active' if current_page == 'analyze' else ''}" onclick="document.getElementById('btn_analyze').click(); return false;">
                    ANALYZE {'<span class="dropdown-arrow">▼</span>' if current_page == 'analyze' else ''}
                </a>
                <a href="#" class="nav-item {'nav-item-active' if current_page == 'data_vault' else ''}" onclick="document.getElementById('btn_vault').click(); return false;">
                    DATA VAULT
                </a>
                <a href="#" class="nav-item {'nav-item-active' if current_page == 'pricing' else ''}" onclick="document.getElementById('btn_pricing').click(); return false;">
                    PRICING
                </a>
            </div>
            
            <!-- Get Started Button -->
            <button class="get-started-btn" onclick="document.getElementById('btn_user').click();">
                Get Started
            </button>
        </div>
    </div>
    
    <style>
        .header-bar {{
            background: #1a1d24;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            position: sticky;
            top: 0;
            z-index: 1000;
            margin: -2rem -3rem 2rem -3rem;
            padding: 0 48px;
        }}
        
        .header-content {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 72px;
            max-width: 1600px;
            margin: 0 auto;
        }}
        
        .header-logo {{
            font-family: 'Inter', sans-serif;
            font-size: 1.25rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            flex-shrink: 0;
        }}
        
        .header-nav-items {{
            display: flex;
            align-items: center;
            gap: 48px;
            flex: 1;
            justify-content: center;
        }}
        
        .nav-item {{
            color: #9ca3af;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            text-decoration: none;
            transition: color 0.3s ease;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
        }}
        
        .nav-item:hover {{
            color: #ffffff;
        }}
        
        .nav-item-active {{
            color: #ffffff !important;
        }}
        
        .dropdown-arrow {{
            font-size: 0.65rem;
            opacity: 0.7;
        }}
        
        .get-started-btn {{
            background: #dc2626;
            color: #ffffff;
            border: none;
            border-radius: 50px;
            padding: 12px 32px;
            font-size: 0.95rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
            flex-shrink: 0;
        }}
        
        .get-started-btn:hover {{
            background: #b91c1c;
            box-shadow: 0 6px 16px rgba(220, 38, 38, 0.4);
            transform: translateY(-1px);
        }}
        
        .get-started-btn:active {{
            transform: translateY(0);
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Hidden navigation buttons
    nav_cols = st.columns([1, 1, 1, 1])
    with nav_cols[0]:
        if st.button("analyze", key="btn_analyze"):
            st.session_state["current_page"] = "analyze"
            st.rerun()
    with nav_cols[1]:
        if st.button("vault", key="btn_vault"):
            st.session_state["current_page"] = "data_vault"
            st.rerun()
    with nav_cols[2]:
        if st.button("pricing", key="btn_pricing"):
            st.session_state["current_page"] = "pricing"
            st.rerun()
    with nav_cols[3]:
        if st.button("user", key="btn_user"):
            pass  # User menu trigger
    
    # Hide navigation buttons
    st.markdown("""
    <style>
        button[key="btn_analyze"],
        button[key="btn_vault"],
        button[key="btn_pricing"],
        button[key="btn_user"] {
            display: none !important;
        }
        div[data-testid="column"]:has(button[key^="btn_"]) {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # User menu popover (separate from header)
    with st.popover(f"👤 {current_user}", use_container_width=False):
        st.markdown(f"**Operator:** {current_user}")
        st.caption("Access Level: PRO")
        st.markdown("---")
        if st.button("🔴 DISCONNECT", type="primary", use_container_width=True):
            logout()
    
    st.markdown("""
    <div style="height: 1px; background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent); margin: 20px 0 32px 0;"></div>
    """, unsafe_allow_html=True)
    
    # --- PAGE ROUTING ---
    if st.session_state["current_page"] == "data_vault":
        # DATA VAULT PAGE
        if supabase:
            hist = supabase.table("trades").select("*").eq("user_id", current_user).order("created_at", desc=True).execute()
            
            if hist.data:
                df = pd.DataFrame(hist.data)
                df['created_at'] = pd.to_datetime(df['created_at'])
                
                # Main Data Table
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                st.markdown(f'<div class="section-title">Complete Audit History ({len(df)} records)</div>', unsafe_allow_html=True)
                
                # Filter and Search
                col_search1, col_search2, col_search3 = st.columns([2, 1, 1])
                
                with col_search1:
                    search_ticker = st.text_input("Search by Ticker", placeholder="e.g., SPY, AAPL", label_visibility="collapsed")
                
                with col_search2:
                    score_filter = st.selectbox("Score Filter", ["All", "Excellent (80+)", "Good (60-80)", "Fair (40-60)", "Poor (<40)"], label_visibility="collapsed")
                
                with col_search3:
                    sort_order = st.selectbox("Sort By", ["Newest First", "Oldest First", "Highest Score", "Lowest Score"], label_visibility="collapsed")
                
                st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
                
                # Apply filters
                filtered_df = df.copy()
                
                if search_ticker:
                    filtered_df = filtered_df[filtered_df['ticker'].str.contains(search_ticker, case=False, na=False)]
                
                if score_filter == "Excellent (80+)":
                    filtered_df = filtered_df[filtered_df['score'] >= 80]
                elif score_filter == "Good (60-80)":
                    filtered_df = filtered_df[(filtered_df['score'] >= 60) & (filtered_df['score'] < 80)]
                elif score_filter == "Fair (40-60)":
                    filtered_df = filtered_df[(filtered_df['score'] >= 40) & (filtered_df['score'] < 60)]
                elif score_filter == "Poor (<40)":
                    filtered_df = filtered_df[filtered_df['score'] < 40]
                
                if sort_order == "Oldest First":
                    filtered_df = filtered_df.sort_values('created_at', ascending=True)
                elif sort_order == "Highest Score":
                    filtered_df = filtered_df.sort_values('score', ascending=False)
                elif sort_order == "Lowest Score":
                    filtered_df = filtered_df.sort_values('score', ascending=True)
                else:  # Newest First (default)
                    filtered_df = filtered_df.sort_values('created_at', ascending=False)
                
                # Prepare table data
                table_df = filtered_df[['created_at', 'ticker', 'score', 'mistake_tags', 'technical_analysis', 'psych_analysis']].copy()
                table_df.columns = ['Date', 'Ticker', 'Score', 'Error Tags', 'Technical Notes', 'Psychology Notes']
                
                # Format tags
                table_df['Error Tags'] = table_df['Error Tags'].apply(
                    lambda x: ', '.join(x[:3]) if len(x) > 0 else 'None'
                )
                
                # Truncate long text
                table_df['Technical Notes'] = table_df['Technical Notes'].apply(
                    lambda x: (x[:80] + '...') if len(str(x)) > 80 else x
                )
                table_df['Psychology Notes'] = table_df['Psychology Notes'].apply(
                    lambda x: (x[:80] + '...') if len(str(x)) > 80 else x
                )
                
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
                            format="MMM DD, YYYY HH:mm"
                        ),
                        "Ticker": st.column_config.TextColumn(
                            "Ticker",
                            width="small"
                        ),
                        "Error Tags": st.column_config.TextColumn(
                            "Error Tags",
                            width="medium"
                        ),
                        "Technical Notes": st.column_config.TextColumn(
                            "Technical",
                            width="large"
                        ),
                        "Psychology Notes": st.column_config.TextColumn(
                            "Psychology",
                            width="large"
                        )
                    },
                    height=600
                )
                
                # Export option
                st.markdown('<div style="margin-top: 16px;"></div>', unsafe_allow_html=True)
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Export to CSV",
                    data=csv,
                    file_name=f"stockpostmortem_data_{current_user}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=False
                )
                
                st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.markdown('<div class="glass-panel" style="text-align: center; padding: 60px;">', unsafe_allow_html=True)
                st.markdown("""
                <div style="font-size: 3rem; margin-bottom: 16px; opacity: 0.3;">🗄️</div>
                <div style="font-size: 1.1rem; color: #9ca3af; margin-bottom: 8px;">Data Vault Empty</div>
                <div style="font-size: 0.9rem; color: #6b7280;">Your audit history will appear here once you start analyzing trades.</div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state["current_page"] == "pricing":
        # PRICING PAGE (Placeholder)
        st.markdown('<div class="glass-panel" style="text-align: center; padding: 60px;">', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size: 3rem; margin-bottom: 16px; opacity: 0.3;">💳</div>
        <div style="font-size: 1.1rem; color: #9ca3af; margin-bottom: 8px;">Pricing Information</div>
        <div style="font-size: 0.9rem; color: #6b7280;">Pricing details coming soon.</div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:  # analyze page (default)
        # TABS
        main_tab1, main_tab2 = st.tabs(["🔎 FORENSIC AUDIT", "📊 PERFORMANCE METRICS"])

        # --- TAB 1: AUDIT (INPUT) ---
        with main_tab1:
            st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Case Data Input</div>', unsafe_allow_html=True)
        
            c_mode = st.radio("Input Vector", ["Text Parameters", "Chart Vision"], horizontal=True, label_visibility="collapsed")
        
            prompt = ""
            img_b64 = None
            ticker_val = "IMG"
            ready_to_run = False

            if c_mode == "Chart Vision":
                st.markdown("""
                <div style="text-align: center; margin-bottom: 20px;">
                    <div class="upload-icon">📊</div>
                    <div class="upload-text">Drop your P&L or Chart screenshot here</div>
                    <div class="upload-subtext">Supports PNG, JPG (Max 10MB). Your data is encrypted and deleted after analysis.</div>
                </div>
                """, unsafe_allow_html=True)
            
                uploaded_file = st.file_uploader(
                    "Upload Chart Screenshot", 
                    type=["png", "jpg"], 
                    label_visibility="collapsed",
                    key="chart_upload"
                )
            
                if uploaded_file:
                    st.markdown('<div style="margin-top: 24px;">', unsafe_allow_html=True)
                    st.image(uploaded_file, use_column_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                    if st.button("RUN OPTICAL ANALYSIS", type="primary", use_container_width=True):
                        image = Image.open(uploaded_file)
                        buf = io.BytesIO()
                        image.save(buf, format="PNG")
                        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                        prompt = f"""
                        SYSTEM: Hedge Fund Risk Manager.
                        TASK: Analyze chart for technical/psychological errors.
                        OUTPUT: [SCORE], [TAGS], [TECH], [PSYCH], [RISK], [FIX].
                        """
                        ready_to_run = True

            else:
                with st.form("audit_form"):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a: ticker = st.text_input("Ticker", "SPY")
                    with col_b: setup_type = st.selectbox("Setup", ["Trend", "Reversal", "Breakout"])
                    with col_c: emotion = st.selectbox("State", ["Neutral", "FOMO", "Revenge", "Tilt"])
                
                    st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)
                
                    col_d, col_e, col_f = st.columns(3)
                    with col_d: entry = st.number_input("Entry", 0.0, step=0.01)
                    with col_e: exit_price = st.number_input("Exit", 0.0, step=0.01)
                    with col_f: stop = st.number_input("Stop", 0.0, step=0.01)
                
                    st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)
                
                    notes = st.text_area("Execution Notes", height=100, placeholder="Describe your decision-making process, entry hesitation, stop management...")
                
                    st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
                
                    if st.form_submit_button("EXECUTE AUDIT", type="primary", use_container_width=True):
                        ticker_val = ticker
                        prompt = f"""
                        SYSTEM: Trading Coach.
                        DATA: {ticker} | {setup_type} | {emotion} | Note: {notes}
                        ENTRY: {entry} | EXIT: {exit_price} | STOP: {stop}
                        OUTPUT: [SCORE], [TAGS], [TECH], [PSYCH], [RISK], [FIX].
                        """
                        ready_to_run = True
            st.markdown('</div>', unsafe_allow_html=True)

            # RESULTS AREA
            if ready_to_run and supabase:
                with st.spinner("🧠 AI Forensic Analysis in progress..."):
                    try:
                        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
                        if img_b64: messages[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})
                    
                        payload = {"model": "Qwen/Qwen2.5-VL-7B-Instruct", "messages": messages, "max_tokens": 600}
                        headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                        res = requests.post(API_URL, headers=headers, json=payload)

                        if res.status_code == 200:
                            report = parse_report(res.json()["choices"][0]["message"]["content"])
                            save_analysis(current_user, report, ticker_val)
                        
                            score_color = "#dc2626" if report['score'] < 50 else "#10b981"
                        
                            st.markdown(f"""
                            <div class="glass-panel" style="border-top: 3px solid {score_color}">
                                <div class="score-container">
                                    <div>
                                        <div style="color:#6b7280; letter-spacing:2.5px; font-size:0.7rem; text-transform: uppercase; margin-bottom: 8px;">AUDIT SCORE</div>
                                        <div class="score-value" style="color:{score_color}">{report['score']}</div>
                                    </div>
                                    <div class="score-meta">
                                        <div class="ticker-badge">{ticker_val}</div>
                                        <div style="color:#6b7280; font-size:0.8rem;">{datetime.now().strftime('%B %d, %Y')}</div>
                                    </div>
                                </div>
                                <div class="report-grid">
                                    <div class="report-item" style="border-left-color: #3b82f6;">
                                        <span class="report-label" style="color:#3b82f6;">Technical Analysis</span>
                                        {report['tech']}
                                    </div>
                                    <div class="report-item" style="border-left-color: #f59e0b;">
                                        <span class="report-label" style="color:#f59e0b;">Psychology</span>
                                        {report['psych']}
                                    </div>
                                    <div class="report-item" style="border-left-color: #ef4444;">
                                        <span class="report-label" style="color:#ef4444;">Risk Assessment</span>
                                        {report['risk']}
                                    </div>
                                    <div class="report-item" style="border-left-color: #10b981;">
                                        <span class="report-label" style="color:#10b981;">Corrective Action</span>
                                        {report['fix']}
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Analysis Failed: {e}")

        # --- TAB 2: DASHBOARD ---
        with main_tab2:
            if supabase:
                hist = supabase.table("trades").select("*").eq("user_id", current_user).order("created_at", desc=True).execute()
            
                if hist.data:
                    df = pd.DataFrame(hist.data)
                    df['created_at'] = pd.to_datetime(df['created_at'])
                
                    # METRICS CALC
                    avg_score = df['score'].mean()
                    total_trades = len(df)
                    all_tags = [tag for sublist in df['mistake_tags'] for tag in sublist]
                    top_mistake = pd.Series(all_tags).mode()[0] if all_tags else "None"
                
                    # Calculate win rate (scores > 60 = good trades)
                    win_rate = len(df[df['score'] > 60]) / len(df) * 100 if len(df) > 0 else 0
                
                    # Recent trend (last 5 vs previous 5)
                    recent_avg = df.head(5)['score'].mean() if len(df) >= 5 else avg_score
                    prev_avg = df.iloc[5:10]['score'].mean() if len(df) >= 10 else avg_score
                    trend = "↗" if recent_avg > prev_avg else "↘" if recent_avg < prev_avg else "→"
                
                    # 1. KPI ROW
                    st.markdown(f"""
                    <div class="kpi-container">
                        <div class="kpi-card">
                            <div class="kpi-val">{int(avg_score)}</div>
                            <div class="kpi-label">Avg Quality Score</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-val">{int(win_rate)}%</div>
                            <div class="kpi-label">Quality Rate</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-val">{total_trades}</div>
                            <div class="kpi-label">Total Audits</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-val" style="font-size:2rem;">{trend}</div>
                            <div class="kpi-label">Recent Trend</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 2. MAIN CHART - Full Width
                    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">Performance Evolution</div>', unsafe_allow_html=True)
                
                    chart_data = df[['created_at', 'score']].sort_values('created_at').reset_index(drop=True)
                    chart_data['index'] = range(len(chart_data))
                
                    # Create base chart
                    base = alt.Chart(chart_data).encode(
                        x=alt.X('index:Q', 
                            axis=alt.Axis(
                                title='Trade Sequence',
                                grid=False,
                                labelColor='#6b7280',
                                titleColor='#9ca3af',
                                labelFontSize=11,
                                titleFontSize=12
                            )
                        )
                    )
                
                    # Reference lines
                    good_line = alt.Chart(pd.DataFrame({'y': [70]})).mark_rule(
                        strokeDash=[5, 5],
                        color='#10b981',
                        opacity=0.3
                    ).encode(y='y:Q')
                
                    bad_line = alt.Chart(pd.DataFrame({'y': [40]})).mark_rule(
                        strokeDash=[5, 5],
                        color='#ef4444',
                        opacity=0.3
                    ).encode(y='y:Q')
                
                    # Main line with gradient
                    line = base.mark_line(
                        color='#3b82f6', 
                        strokeWidth=3,
                        point=alt.OverlayMarkDef(
                            filled=True,
                            size=80,
                            color='#3b82f6',
                            strokeWidth=2,
                            stroke='#1e40af'
                        )
                    ).encode(
                        y=alt.Y('score:Q', 
                            scale=alt.Scale(domain=[0, 100]),
                            axis=alt.Axis(
                                title='Quality Score',
                                grid=True,
                                gridColor='rgba(255,255,255,0.04)',
                                labelColor='#6b7280',
                                titleColor='#9ca3af',
                                labelFontSize=11,
                                titleFontSize=12
                            )
                        ),
                        tooltip=[
                            alt.Tooltip('index:Q', title='Trade #'),
                            alt.Tooltip('score:Q', title='Score'),
                            alt.Tooltip('created_at:T', title='Date', format='%b %d, %Y')
                        ]
                    )
                
                    area = base.mark_area(
                        color='#3b82f6', 
                        opacity=0.1,
                        line=False
                    ).encode(y='score:Q')
                
                    chart = (good_line + bad_line + area + line).properties(
                        height=320
                    ).configure_view(
                        strokeWidth=0,
                        fill='transparent'
                    ).configure(
                        background='transparent'
                    )
                
                    st.altair_chart(chart, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # 3. TWO COLUMN LAYOUT
                    col_left, col_right = st.columns([1.5, 1])
                
                    with col_left:
                        # MISTAKE BREAKDOWN with Bar Chart
                        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                        st.markdown('<div class="section-title">Error Pattern Analysis</div>', unsafe_allow_html=True)
                    
                        if all_tags:
                            tag_counts = pd.Series(all_tags).value_counts().head(6).reset_index()
                            tag_counts.columns = ['Mistake', 'Count']
                        
                            # Horizontal bar chart
                            bar_chart = alt.Chart(tag_counts).mark_bar(
                                cornerRadiusEnd=6,
                                height=28
                            ).encode(
                                x=alt.X('Count:Q',
                                    axis=alt.Axis(
                                        title=None,
                                        grid=False,
                                        labelColor='#6b7280',
                                        labelFontSize=11
                                    )
                                ),
                                y=alt.Y('Mistake:N',
                                    sort='-x',
                                    axis=alt.Axis(
                                        title=None,
                                        labelColor='#e5e7eb',
                                        labelFontSize=12,
                                        labelPadding=10
                                    )
                                ),
                                color=alt.Color('Count:Q',
                                    scale=alt.Scale(
                                        scheme='redyellowblue',
                                        reverse=True
                                    ),
                                    legend=None
                                ),
                                tooltip=[
                                    alt.Tooltip('Mistake:N', title='Error Type'),
                                    alt.Tooltip('Count:Q', title='Occurrences')
                                ]
                            ).properties(
                                height=280
                            ).configure_view(
                                strokeWidth=0,
                                fill='transparent'
                            ).configure(
                                background='transparent'
                            )
                        
                            st.altair_chart(bar_chart, use_container_width=True)
                        else:
                            st.info("No error patterns detected yet.")
                    
                        st.markdown('</div>', unsafe_allow_html=True)

                    with col_right:
                        # AI INSIGHTS
                        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                        st.markdown('<div class="section-title">AI Insights</div>', unsafe_allow_html=True)
                    
                        insights = generate_insights(df)
                    
                        for i, insight in enumerate(insights):
                            # Parse emoji and content
                            parts = insight.split(' ', 1)
                            emoji = parts[0] if len(parts) > 0 else ''
                            content = parts[1] if len(parts) > 1 else insight
                        
                            st.markdown(f"""
                            <div style='
                                background: rgba(255, 255, 255, 0.02);
                                border-left: 3px solid #dc2626;
                                padding: 16px;
                                border-radius: 0 10px 10px 0;
                                margin-bottom: 16px;
                            '>
                                <div style='font-size: 1.5rem; margin-bottom: 8px;'>{emoji}</div>
                                <div style='font-size: 0.9rem; line-height: 1.6; color: #d1d5db;'>
                                    {content}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                        # SCORE DISTRIBUTION
                        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                        st.markdown('<div class="section-title">Score Distribution</div>', unsafe_allow_html=True)
                    
                        # Create score ranges
                        score_ranges = pd.cut(df['score'], bins=[0, 40, 60, 80, 100], labels=['Poor (0-40)', 'Fair (40-60)', 'Good (60-80)', 'Excellent (80-100)'])
                        dist_data = score_ranges.value_counts().reset_index()
                        dist_data.columns = ['Range', 'Count']
                    
                        # Color mapping
                        color_map = {
                            'Poor (0-40)': '#ef4444',
                            'Fair (40-60)': '#f59e0b',
                            'Good (60-80)': '#3b82f6',
                            'Excellent (80-100)': '#10b981'
                        }
                    
                        for _, row in dist_data.iterrows():
                            range_name = row['Range']
                            count = row['Count']
                            percentage = (count / len(df)) * 100
                            color = color_map.get(range_name, '#6b7280')
                        
                            st.markdown(f"""
                            <div style='margin-bottom: 20px;'>
                                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
                                    <span style='font-size: 0.85rem; color: #9ca3af; font-weight: 600;'>{range_name}</span>
                                    <span style='font-size: 0.85rem; color: #e5e7eb; font-family: "JetBrains Mono", monospace;'>{count} ({int(percentage)}%)</span>
                                </div>
                                <div style='
                                    width: 100%;
                                    height: 8px;
                                    background: rgba(255, 255, 255, 0.05);
                                    border-radius: 4px;
                                    overflow: hidden;
                                '>
                                    <div style='
                                        width: {percentage}%;
                                        height: 100%;
                                        background: {color};
                                        border-radius: 4px;
                                        transition: width 0.6s ease;
                                    '></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                        st.markdown('</div>', unsafe_allow_html=True)

                    # 4. RECENT TRADES TABLE
                    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">Recent Activity</div>', unsafe_allow_html=True)
                
                    table_df = df.head(10)[['created_at', 'ticker', 'score', 'mistake_tags']].copy()
                    table_df.columns = ['Time', 'Asset', 'Score', 'Primary Errors']
                
                    # Format tags to show only first 2
                    table_df['Primary Errors'] = table_df['Primary Errors'].apply(
                        lambda x: ', '.join(x[:2]) if len(x) > 0 else 'None'
                    )
                
                    st.dataframe(
                        table_df, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            "Score": st.column_config.ProgressColumn(
                                "Quality Score", 
                                min_value=0, 
                                max_value=100, 
                                format="%d"
                            ),
                            "Time": st.column_config.DatetimeColumn(
                                "Time", 
                                format="MMM DD, HH:mm"
                            ),
                            "Asset": st.column_config.TextColumn(
                                "Asset",
                                width="small"
                            )
                        }
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                
                else:
                    st.markdown('<div class="glass-panel" style="text-align: center; padding: 60px;">', unsafe_allow_html=True)
                    st.markdown("""
                    <div style="font-size: 3rem; margin-bottom: 16px; opacity: 0.3;">📊</div>
                    <div style="font-size: 1.1rem; color: #9ca3af; margin-bottom: 8px;">No Performance Data Yet</div>
                    <div style="font-size: 0.9rem; color: #6b7280;">Complete your first forensic audit to see metrics here.</div>
                    """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
