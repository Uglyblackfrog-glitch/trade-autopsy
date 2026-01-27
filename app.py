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

# Initialize session state ONCE
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.current_page = "analyze"

# Check URL parameters
try:
    params = st.query_params
    if "page" in params and st.session_state.authenticated:
        st.session_state.current_page = params["page"]
except:
    pass

def check_login(username, password):
    """Handle login authentication"""
    if username in USERS and USERS[username] == password:
        st.session_state.authenticated = True
        st.session_state.user = username
        st.rerun()
    else:
        st.error("❌ Invalid credentials. Please try again.")

def logout():
    """Handle logout"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.current_page = "analyze"
    st.rerun()

# ==========================================
# 1. DATABASE & API SETUP
# ==========================================
supabase = None
HF_TOKEN = ""
API_URL = ""

if st.session_state.authenticated:
    try:
        HF_TOKEN = st.secrets.get("HF_TOKEN", "")
        SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
        SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
        
        if not all([HF_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
            st.warning("⚠️ Configuration incomplete. Some features may be limited.")
            supabase = None
        else:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            API_URL = "https://router.huggingface.co/v1/chat/completions"
    except Exception as e:
        st.error(f"⚠️ Configuration Error: {e}")

# ==========================================
# 2. PREMIUM DARK THEME CSS
# ==========================================
st.markdown("""
<style>
    /* ===== FONTS & RESET ===== */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* ===== GLOBAL STYLES ===== */
    html, body, .stApp {
        background: #000000 !important;
        font-family: 'Space Grotesk', -apple-system, sans-serif !important;
        color: #ffffff;
        overflow-x: hidden;
    }
    
    /* Subtle red gradient overlay */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(circle at 15% 15%, rgba(220, 38, 38, 0.03) 0%, transparent 40%),
            radial-gradient(circle at 85% 85%, rgba(220, 38, 38, 0.02) 0%, transparent 40%);
        pointer-events: none;
        z-index: 0;
    }
    
    /* Remove default padding */
    .block-container {
        padding: 2rem 3rem 3rem 3rem !important;
        max-width: 1600px !important;
        position: relative;
        z-index: 1;
    }
    
    /* ===== HIDE STREAMLIT ELEMENTS ===== */
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    
    /* ===== LOGIN PAGE STYLES ===== */
    .login-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        padding: 2rem;
        position: relative;
    }
    
    .login-container {
        width: 100%;
        max-width: 480px;
        background: rgba(10, 10, 10, 0.6);
        backdrop-filter: blur(40px) saturate(180%);
        -webkit-backdrop-filter: blur(40px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 32px;
        padding: 60px 50px;
        box-shadow: 
            0 24px 80px rgba(0, 0, 0, 0.6),
            inset 0 1px 0 rgba(255, 255, 255, 0.03),
            0 0 0 1px rgba(220, 38, 38, 0.05);
        position: relative;
        overflow: hidden;
    }
    
    .login-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(220, 38, 38, 0.06) 0%, transparent 70%);
        animation: pulse 8s ease-in-out infinite;
        pointer-events: none;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    
    .login-logo {
        font-size: 4rem;
        margin-bottom: 24px;
        filter: drop-shadow(0 0 30px rgba(220, 38, 38, 0.4));
        animation: float 4s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-12px); }
    }
    
    .login-title {
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        margin-bottom: 12px;
        background: linear-gradient(135deg, #ffffff 0%, #e5e7eb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .login-subtitle {
        color: #6b7280;
        font-size: 0.95rem;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-bottom: 48px;
        font-weight: 500;
    }
    
    /* ===== GLASSMORPHISM PANELS ===== */
    .glass-panel {
        background: rgba(15, 15, 15, 0.5);
        backdrop-filter: blur(30px) saturate(150%);
        -webkit-backdrop-filter: blur(30px) saturate(150%);
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-radius: 24px;
        padding: 32px;
        margin-bottom: 24px;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.02);
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        position: relative;
        overflow: hidden;
    }
    
    .glass-panel::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(220, 38, 38, 0.3), transparent);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    
    .glass-panel:hover {
        border-color: rgba(255, 255, 255, 0.06);
        box-shadow: 
            0 12px 48px rgba(0, 0, 0, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.04);
        transform: translateY(-2px);
    }
    
    .glass-panel:hover::before {
        opacity: 1;
    }
    
    /* ===== SECTION HEADERS ===== */
    .section-header {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 32px;
        padding-bottom: 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
    
    .section-icon {
        font-size: 2rem;
        filter: drop-shadow(0 0 20px rgba(220, 38, 38, 0.3));
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #ffffff 0%, #9ca3af 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .section-subtitle {
        font-size: 0.9rem;
        color: #6b7280;
        margin-top: 4px;
    }
    
    /* ===== KPI CARDS ===== */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 20px;
        margin-bottom: 32px;
    }
    
    .kpi-card {
        background: linear-gradient(135deg, rgba(20, 20, 20, 0.6) 0%, rgba(10, 10, 10, 0.8) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 20px;
        padding: 32px 28px;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        position: relative;
        overflow: hidden;
    }
    
    .kpi-card::after {
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
        border-color: rgba(220, 38, 38, 0.2);
        transform: translateY(-8px) scale(1.02);
        box-shadow: 
            0 20px 60px -16px rgba(220, 38, 38, 0.3),
            0 0 0 1px rgba(220, 38, 38, 0.1);
    }
    
    .kpi-card:hover::after {
        opacity: 1;
    }
    
    .kpi-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ffffff 0%, #d1d5db 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 12px;
        letter-spacing: -0.03em;
        line-height: 1;
    }
    
    .kpi-label {
        color: #9ca3af;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 600;
    }
    
    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: rgba(20, 20, 20, 0.3);
        border-radius: 16px;
        padding: 8px;
        margin-bottom: 32px;
        border: 1px solid rgba(255, 255, 255, 0.02);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 12px;
        color: #6b7280;
        font-weight: 600;
        font-size: 0.95rem;
        padding: 14px 28px;
        transition: all 0.3s ease;
        border: none;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.03);
        color: #d1d5db;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(220, 38, 38, 0.15) 0%, rgba(153, 27, 27, 0.1) 100%) !important;
        color: #fca5a5 !important;
        box-shadow: 
            0 4px 20px rgba(220, 38, 38, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 0 !important;
    }
    
    /* ===== BUTTONS ===== */
    .stButton button {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
        border: 1px solid rgba(220, 38, 38, 0.3);
        border-radius: 14px;
        color: white;
        font-weight: 600;
        font-size: 0.95rem;
        padding: 14px 32px;
        transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
        box-shadow: 
            0 4px 16px rgba(220, 38, 38, 0.25),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #b91c1c 0%, #7f1d1d 100%);
        box-shadow: 
            0 8px 32px rgba(220, 38, 38, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.15);
        transform: translateY(-2px);
        border-color: rgba(220, 38, 38, 0.5);
    }
    
    .stButton button:active {
        transform: translateY(0px);
    }
    
    /* ===== INPUTS ===== */
    .stTextInput input, 
    .stNumberInput input, 
    .stTextArea textarea, 
    .stSelectbox select {
        background: rgba(20, 20, 20, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
        padding: 14px 18px !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(10px);
    }
    
    .stTextInput input:focus, 
    .stNumberInput input:focus, 
    .stTextArea textarea:focus, 
    .stSelectbox select:focus {
        border-color: rgba(220, 38, 38, 0.4) !important;
        box-shadow: 
            0 0 0 3px rgba(220, 38, 38, 0.1),
            0 4px 16px rgba(0, 0, 0, 0.3) !important;
        background: rgba(20, 20, 20, 0.6) !important;
    }
    
    .stTextInput label, 
    .stNumberInput label, 
    .stTextArea label, 
    .stSelectbox label {
        color: #9ca3af !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        margin-bottom: 8px !important;
    }
    
    /* ===== FILE UPLOADER ===== */
    [data-testid="stFileUploader"] {
        background: transparent !important;
    }
    
    [data-testid="stFileUploader"] section {
        background: rgba(15, 15, 15, 0.4) !important;
        backdrop-filter: blur(20px);
        border: 2px dashed rgba(220, 38, 38, 0.25) !important;
        border-radius: 24px !important;
        padding: 60px 40px !important;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1) !important;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(220, 38, 38, 0.5) !important;
        background: rgba(20, 20, 20, 0.5) !important;
        box-shadow: 0 8px 32px rgba(220, 38, 38, 0.15);
    }
    
    /* ===== RADIO BUTTONS ===== */
    .stRadio > label {
        display: none !important;
    }
    
    .stRadio > div {
        background: rgba(20, 20, 20, 0.3) !important;
        border-radius: 12px !important;
        padding: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.04);
    }
    
    .stRadio [role="radiogroup"] {
        gap: 8px !important;
    }
    
    .stRadio label {
        background: transparent !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease !important;
        color: #6b7280 !important;
        font-weight: 600 !important;
    }
    
    .stRadio label:hover {
        background: rgba(255, 255, 255, 0.03) !important;
        color: #d1d5db !important;
    }
    
    .stRadio input:checked + label {
        background: rgba(220, 38, 38, 0.15) !important;
        color: #fca5a5 !important;
    }
    
    /* ===== DATAFRAME ===== */
    .stDataFrame {
        background: transparent !important;
        border-radius: 16px !important;
        overflow: hidden !important;
    }
    
    .stDataFrame [data-testid="stDataFrameResizable"] {
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-radius: 16px !important;
    }
    
    /* ===== REPORT GRID ===== */
    .report-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
        margin-top: 24px;
    }
    
    .report-card {
        background: rgba(255, 255, 255, 0.02);
        border-left: 3px solid;
        padding: 24px;
        border-radius: 0 16px 16px 0;
        transition: all 0.3s ease;
    }
    
    .report-card:hover {
        background: rgba(255, 255, 255, 0.04);
        transform: translateX(4px);
    }
    
    .report-label {
        font-weight: 700;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 12px;
        display: block;
        opacity: 0.9;
    }
    
    .report-content {
        color: #d1d5db;
        font-size: 0.95rem;
        line-height: 1.7;
    }
    
    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(20, 20, 20, 0.3);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(220, 38, 38, 0.3);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(220, 38, 38, 0.5);
    }
    
    /* ===== ANIMATIONS ===== */
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .glass-panel {
        animation: slideInUp 0.6s ease-out;
    }
    
    /* ===== SPINNER ===== */
    .stSpinner > div {
        border-color: rgba(220, 38, 38, 0.3) rgba(220, 38, 38, 0.3) rgba(220, 38, 38, 0.3) #dc2626 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def clean_text(text):
    """Clean and sanitize text"""
    return re.sub(r'[^\w\s,.:;!?()\[\]\-\'\"%]', '', text).strip()

def parse_report(text):
    """Parse AI report into structured sections"""
    sections = {
        "score": 0,
        "tags": [],
        "tech": "N/A",
        "psych": "N/A",
        "risk": "N/A",
        "fix": "N/A"
    }
    text = clean_text(text)
    
    score_match = re.search(r'\[SCORE\]\s*(\d+)', text)
    if score_match:
        sections['score'] = int(score_match.group(1))
    
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
        if match:
            sections[key] = match.group(1).strip()
    
    return sections

def save_analysis(user_id, data, ticker_symbol="UNK"):
    """Save analysis to database"""
    if not supabase:
        return
    try:
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
    except Exception as e:
        st.error(f"Failed to save analysis: {e}")

def generate_insights(df):
    """Generate AI insights from trade data"""
    insights = []
    if df.empty:
        return ["📊 Awaiting data to generate insights."]
    
    recent_scores = df.head(3)['score'].mean()
    if recent_scores < 50:
        insights.append("⚠️ **Tilt Detected:** Last 3 trades averaged below 50. Consider a 24-hour trading pause.")
    elif recent_scores > 80:
        insights.append("🔥 **Peak Performance:** High decision quality detected. Operating in optimal state.")
    
    all_tags = [tag for sublist in df['mistake_tags'] for tag in sublist]
    if all_tags:
        from collections import Counter
        tag_counts = Counter(all_tags)
        if tag_counts.most_common(1)[0][1] >= 3:
            insights.append(f"🎯 **Pattern Alert:** '{tag_counts.most_common(1)[0][0]}' recurring {tag_counts.most_common(1)[0][1]}x. Review workflow.")
    
    if len(df) >= 10:
        win_rate = len(df[df['score'] > 60]) / len(df) * 100
        if win_rate > 70:
            insights.append(f"💎 **Consistency:** {win_rate:.0f}% quality rate. Maintain current strategy.")
    
    return insights if insights else ["✨ Continue building your track record for deeper insights."]

# ==========================================
# 4. MAIN APP
# ==========================================

# --- LOGIN PAGE ---
if not st.session_state.authenticated:
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-container">
            <div style="text-align: center; position: relative; z-index: 1;">
                <div class="login-logo">🩸</div>
                <h1 class="login-title">StockPostmortem</h1>
                <p class="login-subtitle">Elite Trading Forensics</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input(
                "Username",
                placeholder="Enter your trader ID",
                key="username_input"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your access key",
                key="password_input"
            )
            
            st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)
            
            submitted = st.form_submit_button(
                "ACCESS TERMINAL",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                if username and password:
                    check_login(username, password)
                else:
                    st.error("⚠️ Please enter both username and password")
        
        st.markdown('</div></div>', unsafe_allow_html=True)

# --- AUTHENTICATED DASHBOARD ---
else:
    current_user = st.session_state.user
    current_page = st.session_state.get("current_page", "analyze")
    
    # === HEADER ===
    header_col1, header_col2, header_col3 = st.columns([2, 6, 2])
    
    with header_col1:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 14px;">
            <span style="font-size: 2rem; filter: drop-shadow(0 0 15px rgba(220, 38, 38, 0.5));">🩸</span>
            <div>
                <div style="font-size: 1.4rem; font-weight: 700; letter-spacing: -0.02em;">
                    <span style="color: #ffffff;">Stock</span><span style="background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">Postmortem</span>
                </div>
                <div style="font-size: 0.7rem; color: #6b7280; text-transform: uppercase; letter-spacing: 2px; margin-top: 2px;">Forensic AI</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with header_col2:
        nav_col1, nav_col2, nav_col3 = st.columns(3)
        
        with nav_col1:
            if st.button("🔬 ANALYZE", key="nav_analyze", use_container_width=True):
                st.session_state.current_page = "analyze"
                st.rerun()
        
        with nav_col2:
            if st.button("🗄️ DATA VAULT", key="nav_vault", use_container_width=True):
                st.session_state.current_page = "data_vault"
                st.rerun()
        
        with nav_col3:
            if st.button("💳 PRICING", key="nav_pricing", use_container_width=True):
                st.session_state.current_page = "pricing"
                st.rerun()
    
    with header_col3:
        if st.button(f"👤 {current_user} ▼", key="user_menu", use_container_width=True):
            logout()
    
    st.markdown('<div style="height: 32px;"></div>', unsafe_allow_html=True)
    
    # === PAGE ROUTING ===
    
    # --- ANALYZE PAGE ---
    if current_page == "analyze":
        tab1, tab2 = st.tabs(["🔎 FORENSIC AUDIT", "📊 PERFORMANCE METRICS"])
        
        with tab1:
            st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
            
            c_mode = st.radio(
                "mode",
                ["📝 Text Analysis", "📊 Chart Vision"],
                horizontal=True,
                label_visibility="collapsed"
            )
            
            st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
            
            prompt = ""
            img_b64 = None
            ticker_val = "IMG"
            ready_to_run = False
            
            if c_mode == "📊 Chart Vision":
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                st.markdown("""
                <div class="section-header">
                    <span class="section-icon">📷</span>
                    <div>
                        <div class="section-title">Visual Analysis</div>
                        <div class="section-subtitle">Upload your trading chart or P&L screenshot</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                uploaded_file = st.file_uploader(
                    "Upload Chart",
                    type=["png", "jpg", "jpeg"],
                    label_visibility="collapsed",
                    key="chart_upload"
                )
                
                if uploaded_file:
                    st.markdown('<div style="margin-top: 24px;">', unsafe_allow_html=True)
                    st.image(uploaded_file, use_column_width=True)
                    st.markdown('</div><div style="height: 20px;"></div>', unsafe_allow_html=True)
                    
                    if st.button("🚀 RUN ANALYSIS", type="primary", use_container_width=True):
                        image = Image.open(uploaded_file)
                        buf = io.BytesIO()
                        image.save(buf, format="PNG")
                        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                        prompt = "SYSTEM: Trading Analyst. TASK: Analyze chart. OUTPUT: [SCORE], [TAGS], [TECH], [PSYCH], [RISK], [FIX]."
                        ready_to_run = True
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            else:  # Text Analysis
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                st.markdown("""
                <div class="section-header">
                    <span class="section-icon">📋</span>
                    <div>
                        <div class="section-title">Trade Details</div>
                        <div class="section-subtitle">Enter your trade parameters for analysis</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.form("trade_form"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        ticker = st.text_input("Ticker Symbol", "SPY")
                    with col2:
                        setup = st.selectbox("Setup Type", ["Trend", "Reversal", "Breakout", "Range"])
                    with col3:
                        emotion = st.selectbox("Mental State", ["Neutral", "FOMO", "Revenge", "Tilt", "Confident"])
                    
                    st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
                    
                    col4, col5, col6 = st.columns(3)
                    with col4:
                        entry = st.number_input("Entry Price", 0.0, step=0.01, format="%.2f")
                    with col5:
                        exit_p = st.number_input("Exit Price", 0.0, step=0.01, format="%.2f")
                    with col6:
                        stop = st.number_input("Stop Loss", 0.0, step=0.01, format="%.2f")
                    
                    st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
                    
                    notes = st.text_area(
                        "Trade Notes",
                        height=120,
                        placeholder="Describe your thought process, entry hesitation, exit reasoning..."
                    )
                    
                    st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
                    
                    if st.form_submit_button("🚀 ANALYZE TRADE", type="primary", use_container_width=True):
                        ticker_val = ticker
                        prompt = f"SYSTEM: Trading Coach. DATA: {ticker} | {setup} | {emotion} | Notes: {notes} | Entry: {entry} | Exit: {exit_p} | Stop: {stop}. OUTPUT: [SCORE], [TAGS], [TECH], [PSYCH], [RISK], [FIX]."
                        ready_to_run = True
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # === RESULTS ===
            if ready_to_run and supabase and HF_TOKEN:
                with st.spinner("🧠 AI analyzing your trade..."):
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
                        
                        res = requests.post(API_URL, headers=headers, json=payload, timeout=30)
                        
                        if res.status_code == 200:
                            report = parse_report(res.json()["choices"][0]["message"]["content"])
                            save_analysis(current_user, report, ticker_val)
                            
                            st.markdown('<div style="height: 32px;"></div>', unsafe_allow_html=True)
                            
                            score_color = "#dc2626" if report['score'] < 50 else "#10b981" if report['score'] >= 70 else "#f59e0b"
                            
                            st.markdown(f"""
                            <div class="glass-panel" style="border-top: 3px solid {score_color};">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px;">
                                    <div>
                                        <div style="color: #6b7280; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 12px;">QUALITY SCORE</div>
                                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 5rem; font-weight: 800; color: {score_color}; line-height: 1; letter-spacing: -0.03em;">{report['score']}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="background: rgba(255, 255, 255, 0.05); padding: 10px 20px; border-radius: 12px; font-weight: 700; font-size: 1.1rem; letter-spacing: 1px; margin-bottom: 8px;">{ticker_val}</div>
                                        <div style="color: #6b7280; font-size: 0.85rem;">{datetime.now().strftime('%B %d, %Y')}</div>
                                    </div>
                                </div>
                                
                                <div class="report-grid">
                                    <div class="report-card" style="border-left-color: #3b82f6;">
                                        <span class="report-label" style="color: #3b82f6;">⚙️ TECHNICAL</span>
                                        <div class="report-content">{report['tech']}</div>
                                    </div>
                                    <div class="report-card" style="border-left-color: #f59e0b;">
                                        <span class="report-label" style="color: #f59e0b;">🧠 PSYCHOLOGY</span>
                                        <div class="report-content">{report['psych']}</div>
                                    </div>
                                    <div class="report-card" style="border-left-color: #ef4444;">
                                        <span class="report-label" style="color: #ef4444;">⚠️ RISK FACTORS</span>
                                        <div class="report-content">{report['risk']}</div>
                                    </div>
                                    <div class="report-card" style="border-left-color: #10b981;">
                                        <span class="report-label" style="color: #10b981;">✅ ACTION PLAN</span>
                                        <div class="report-content">{report['fix']}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error(f"❌ Analysis failed: {res.status_code}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        
        # === PERFORMANCE TAB ===
        with tab2:
            st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
            
            if supabase:
                try:
                    hist = supabase.table("trades").select("*").eq("user_id", current_user).order("created_at", desc=True).execute()
                    
                    if hist.data:
                        df = pd.DataFrame(hist.data)
                        df['created_at'] = pd.to_datetime(df['created_at'])
                        
                        # Calculate metrics
                        avg_score = df['score'].mean()
                        total_trades = len(df)
                        win_rate = len(df[df['score'] > 60]) / len(df) * 100 if len(df) > 0 else 0
                        
                        recent_avg = df.head(5)['score'].mean() if len(df) >= 5 else avg_score
                        prev_avg = df.iloc[5:10]['score'].mean() if len(df) >= 10 else avg_score
                        trend = "📈" if recent_avg > prev_avg else "📉" if recent_avg < prev_avg else "➡️"
                        
                        # KPI Cards
                        st.markdown(f"""
                        <div class="kpi-grid">
                            <div class="kpi-card">
                                <div class="kpi-value">{int(avg_score)}</div>
                                <div class="kpi-label">Avg Score</div>
                            </div>
                            <div class="kpi-card">
                                <div class="kpi-value">{int(win_rate)}%</div>
                                <div class="kpi-label">Quality Rate</div>
                            </div>
                            <div class="kpi-card">
                                <div class="kpi-value">{total_trades}</div>
                                <div class="kpi-label">Total Trades</div>
                            </div>
                            <div class="kpi-card">
                                <div class="kpi-value" style="font-size: 2.5rem;">{trend}</div>
                                <div class="kpi-label">Trend</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Chart
                        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                        st.markdown("""
                        <div class="section-header">
                            <span class="section-icon">📈</span>
                            <div>
                                <div class="section-title">Performance Evolution</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        chart_data = df[['created_at', 'score']].sort_values('created_at').reset_index(drop=True)
                        chart_data['index'] = range(len(chart_data))
                        
                        base = alt.Chart(chart_data).encode(
                            x=alt.X('index:Q', axis=alt.Axis(title='Trade Sequence', grid=False))
                        )
                        
                        line = base.mark_line(
                            color='#3b82f6',
                            strokeWidth=3,
                            point=alt.OverlayMarkDef(filled=True, size=100, color='#3b82f6')
                        ).encode(
                            y=alt.Y('score:Q', scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(title='Score')),
                            tooltip=['index:Q', 'score:Q', 'created_at:T']
                        )
                        
                        area = base.mark_area(color='#3b82f6', opacity=0.1).encode(y='score:Q')
                        
                        chart = (area + line).properties(height=350).configure_view(strokeWidth=0, fill='transparent').configure(background='transparent')
                        
                        st.altair_chart(chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Insights
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                            st.markdown("""
                            <div class="section-header">
                                <span class="section-icon">🎯</span>
                                <div>
                                    <div class="section-title">Recent Activity</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            table_df = df.head(5)[['created_at', 'ticker', 'score']].copy()
                            table_df.columns = ['Date', 'Ticker', 'Score']
                            
                            st.dataframe(
                                table_df,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
                                    "Date": st.column_config.DatetimeColumn("Date", format="MMM DD, HH:mm")
                                }
                            )
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                            st.markdown("""
                            <div class="section-header">
                                <span class="section-icon">💡</span>
                                <div>
                                    <div class="section-title">AI Insights</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            insights = generate_insights(df)
                            for insight in insights:
                                st.markdown(f"""
                                <div style="background: rgba(255, 255, 255, 0.02); border-left: 3px solid #dc2626; padding: 16px; border-radius: 0 12px 12px 0; margin-bottom: 12px;">
                                    <div style="font-size: 0.9rem; line-height: 1.6; color: #d1d5db;">{insight}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    else:
                        st.markdown("""
                        <div class="glass-panel" style="text-align: center; padding: 80px 40px;">
                            <div style="font-size: 4rem; margin-bottom: 24px; opacity: 0.3;">📊</div>
                            <div style="font-size: 1.3rem; font-weight: 600; margin-bottom: 12px;">No Data Yet</div>
                            <div style="color: #6b7280; font-size: 0.95rem;">Complete your first audit to see performance metrics.</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                except Exception as e:
                    st.error(f"Error loading data: {e}")
    
    # --- DATA VAULT PAGE ---
    elif current_page == "data_vault":
        st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-panel" style="text-align: center; padding: 80px 40px;">
            <div style="font-size: 4rem; margin-bottom: 24px; opacity: 0.3;">🗄️</div>
            <div style="font-size: 1.3rem; font-weight: 600; margin-bottom: 12px;">Data Vault</div>
            <div style="color: #6b7280; font-size: 0.95rem;">Access your complete trade history and analytics.</div>
        </div>
        """, unsafe_allow_html=True)
    
    # --- PRICING PAGE ---
    elif current_page == "pricing":
        st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-panel" style="text-align: center; padding: 80px 40px;">
            <div style="font-size: 4rem; margin-bottom: 24px; opacity: 0.3;">💳</div>
            <div style="font-size: 1.3rem; font-weight: 600; margin-bottom: 12px;">Pricing Plans</div>
            <div style="color: #6b7280; font-size: 0.95rem;">Choose the plan that fits your trading needs.</div>
        </div>
        """, unsafe_allow_html=True)
