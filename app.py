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
import json
import uuid
import time

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
    st.session_state["current_page"] = "analyze"

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
            # Using multiple model options for better results
            API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-11B-Vision-Instruct"
            API_URL_BACKUP = "https://api-inference.huggingface.co/models/Qwen/Qwen2-VL-7B-Instruct"
            
    except Exception as e:
        st.error(f"⚠️ Configuration Error: {e}")
        st.stop()

# ==========================================
# 2. PREMIUM DARK THEME CSS
# ==========================================
st.markdown("""
<style>
    /* --- PREMIUM FONTS --- */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* --- DARK PREMIUM BACKGROUND --- */
    body, .stApp { 
        background: #0a0a0f !important;
        background-image: 
            radial-gradient(ellipse at 10% 0%, rgba(16, 185, 129, 0.08) 0%, transparent 40%),
            radial-gradient(ellipse at 90% 100%, rgba(59, 130, 246, 0.08) 0%, transparent 40%),
            radial-gradient(ellipse at 50% 50%, rgba(139, 92, 246, 0.04) 0%, transparent 50%);
        font-family: 'Space Grotesk', -apple-system, sans-serif !important; 
        color: #e5e7eb; 
        line-height: 1.7;
    }
    
    /* --- CONTAINER SPACING --- */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1400px !important;
    }

    /* --- HIDE STREAMLIT ELEMENTS --- */
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    
    /* --- PREMIUM NAVIGATION BAR --- */
    .premium-navbar {
        background: rgba(15, 15, 20, 0.8);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 16px 28px;
        margin-bottom: 32px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.03);
    }
    
    .nav-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .nav-logo {
        font-size: 1.8rem;
        filter: drop-shadow(0 0 16px rgba(16, 185, 129, 0.4));
    }
    
    .nav-title {
        font-size: 1.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
    }
    
    .nav-subtitle {
        font-size: 0.7rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 600;
    }
    
    .nav-menu {
        display: flex;
        gap: 32px;
        align-items: center;
    }
    
    .nav-link {
        color: #9ca3af;
        text-decoration: none;
        font-size: 0.95rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        position: relative;
        padding: 8px 0;
        cursor: pointer;
    }
    
    .nav-link::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 0;
        height: 2px;
        background: linear-gradient(90deg, #10b981, #3b82f6);
        transition: width 0.3s ease;
    }
    
    .nav-link:hover {
        color: #10b981;
    }
    
    .nav-link:hover::after {
        width: 100%;
    }
    
    .nav-link.active {
        color: #10b981;
    }
    
    .nav-link.active::after {
        width: 100%;
    }
    
    /* --- RADIO BUTTONS - GREEN THEME --- */
    .stRadio > div[role="radiogroup"] > label > div[data-testid="stMarkdownContainer"] {
        color: #9ca3af !important;
    }
    
    .stRadio > div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child {
        background-color: transparent !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    .stRadio > div[role="radiogroup"] > label[data-baseweb="radio"][data-selected="true"] > div:first-child {
        background-color: #10b981 !important;
        border-color: #10b981 !important;
    }
    
    .stRadio > div[role="radiogroup"] > label[data-baseweb="radio"][data-selected="true"] > div:first-child::after {
        background-color: white !important;
    }
    
    input[type="radio"]:checked {
        accent-color: #10b981 !important;
    }
    
    /* --- PREMIUM GLASS PANELS --- */
    .glass-panel {
        background: rgba(15, 15, 20, 0.75);
        backdrop-filter: blur(24px) saturate(200%);
        -webkit-backdrop-filter: blur(24px) saturate(200%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 36px;
        margin-bottom: 24px;
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
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
        background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.5), transparent);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    
    .glass-panel:hover {
        border-color: rgba(255, 255, 255, 0.12);
        box-shadow: 
            0 16px 48px rgba(0, 0, 0, 0.6),
            inset 0 1px 0 rgba(255, 255, 255, 0.08);
        transform: translateY(-2px);
    }
    
    .glass-panel:hover::before {
        opacity: 1;
    }
    
    /* --- PREMIUM KPI CARDS --- */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 20px;
        margin-bottom: 32px;
    }
    
    .kpi-card {
        background: linear-gradient(135deg, rgba(20, 20, 28, 0.9) 0%, rgba(10, 10, 15, 0.95) 100%);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 32px 28px;
        border-radius: 20px;
        text-align: center;
        transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
        position: relative;
        overflow: hidden;
    }
    
    .kpi-card::after {
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at 50% 0%, rgba(16, 185, 129, 0.15), transparent 70%);
        opacity: 0;
        transition: opacity 0.5s ease;
    }
    
    .kpi-card:hover {
        border-color: rgba(16, 185, 129, 0.4);
        transform: translateY(-8px) scale(1.02);
        box-shadow: 
            0 20px 60px -12px rgba(16, 185, 129, 0.3),
            0 0 0 1px rgba(16, 185, 129, 0.2);
    }
    
    .kpi-card:hover::after {
        opacity: 1;
    }
    
    .kpi-val { 
        font-family: 'JetBrains Mono', monospace;
        font-size: 3rem; 
        font-weight: 700; 
        background: linear-gradient(135deg, #ffffff 0%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 10px;
        letter-spacing: -0.03em;
        position: relative;
        z-index: 1;
    }
    
    .kpi-label { 
        color: #9ca3af; 
        font-size: 0.7rem; 
        text-transform: uppercase; 
        letter-spacing: 2.5px; 
        font-weight: 600;
        position: relative;
        z-index: 1;
    }

    /* --- PREMIUM LOGIN --- */
    .login-container {
        max-width: 480px;
        margin: 10vh auto;
        padding: 56px;
        background: rgba(15, 15, 20, 0.9);
        backdrop-filter: blur(24px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 32px;
        box-shadow: 
            0 24px 80px rgba(0, 0, 0, 0.6),
            inset 0 1px 0 rgba(255, 255, 255, 0.08);
        text-align: center;
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
        background: radial-gradient(circle, rgba(16, 185, 129, 0.1) 0%, transparent 70%);
        animation: rotate 20s linear infinite;
    }
    
    @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .login-logo {
        font-size: 4rem;
        margin-bottom: 20px;
        filter: drop-shadow(0 0 24px rgba(16, 185, 129, 0.4));
        position: relative;
        z-index: 1;
    }

    /* --- SECTION TITLES --- */
    .section-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 28px;
        display: flex;
        align-items: center;
        gap: 14px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .section-title::before {
        content: '';
        display: block;
        width: 4px;
        height: 24px;
        background: linear-gradient(180deg, #10b981 0%, #3b82f6 100%);
        border-radius: 3px;
        box-shadow: 0 0 16px rgba(16, 185, 129, 0.5);
    }

    /* --- REPORT GRID --- */
    .report-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
        margin-top: 32px;
    }
    
    .report-item {
        background: rgba(255, 255, 255, 0.03);
        border-left: 4px solid rgba(100, 100, 100, 0.4);
        padding: 24px;
        border-radius: 0 16px 16px 0;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        font-size: 0.92rem;
        line-height: 1.8;
    }
    
    .report-item:hover {
        background: rgba(255, 255, 255, 0.06);
        border-left-color: currentColor;
        transform: translateX(4px);
    }
    
    .report-label {
        font-weight: 700;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 14px;
        display: block;
    }

    /* --- PREMIUM TABS --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: rgba(20, 20, 28, 0.5);
        border-radius: 16px;
        padding: 8px;
        margin-bottom: 32px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 12px;
        color: #9ca3af;
        font-weight: 600;
        padding: 14px 28px;
        transition: all 0.3s ease;
        font-size: 0.9rem;
        letter-spacing: 0.5px;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.06);
        color: #f8fafc;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(59, 130, 246, 0.2) 100%) !important;
        color: #10b981 !important;
        box-shadow: 0 0 24px rgba(16, 185, 129, 0.3);
    }
    
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #10b981 !important;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 0 !important;
    }

    /* --- PREMIUM BUTTONS --- */
    .stButton button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 14px;
        color: white;
        font-weight: 600;
        padding: 14px 32px;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        box-shadow: 
            0 4px 20px rgba(16, 185, 129, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
        letter-spacing: 0.5px;
        font-size: 0.9rem;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        box-shadow: 
            0 8px 32px rgba(16, 185, 129, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.25);
        transform: translateY(-3px);
    }
    
    .stButton button[kind="primary"], 
    button[type="submit"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        border: 1px solid rgba(16, 185, 129, 0.4) !important;
    }

    /* --- PREMIUM INPUTS --- */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox select {
        background: rgba(20, 20, 28, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
        padding: 14px 18px !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus {
        border-color: rgba(16, 185, 129, 0.5) !important;
        box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.15) !important;
        background: rgba(20, 20, 28, 0.9) !important;
    }

    /* --- PREMIUM FILE UPLOADER --- */
    [data-testid="stFileUploader"] {
        background: transparent !important;
    }
    
    [data-testid="stFileUploader"] > div {
        background: transparent !important;
        border: none !important;
    }
    
    [data-testid="stFileUploader"] section {
        background: rgba(15, 15, 20, 0.7) !important;
        backdrop-filter: blur(16px);
        border: 2px dashed rgba(16, 185, 129, 0.4) !important;
        border-radius: 24px !important;
        padding: 72px 48px !important;
        transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1) !important;
        position: relative;
    }
    
    [data-testid="stFileUploader"] section::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: 24px;
        background: radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.1), transparent 70%);
        opacity: 0;
        transition: opacity 0.5s ease;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(16, 185, 129, 0.7) !important;
        background: rgba(20, 20, 28, 0.8) !important;
        transform: translateY(-4px);
        box-shadow: 0 12px 48px rgba(16, 185, 129, 0.25);
    }
    
    [data-testid="stFileUploader"] section:hover::before {
        opacity: 1;
    }

    /* --- DATAFRAME --- */
    .stDataFrame {
        background: rgba(15, 15, 20, 0.7);
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* === ANIMATED RESULTS DISPLAY === */
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
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes scaleIn {
        from {
            opacity: 0;
            transform: scale(0.9);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .animate-slide-up {
        animation: slideInUp 0.6s cubic-bezier(0.23, 1, 0.32, 1) forwards;
    }
    
    .animate-fade-in {
        animation: fadeIn 0.8s ease forwards;
    }
    
    .animate-scale-in {
        animation: scaleIn 0.5s cubic-bezier(0.23, 1, 0.32, 1) forwards;
    }
    
    .animate-slide-right {
        animation: slideInRight 0.6s cubic-bezier(0.23, 1, 0.32, 1) forwards;
    }
    
    .result-card {
        background: rgba(15, 15, 20, 0.75);
        backdrop-filter: blur(24px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 28px;
        margin-bottom: 20px;
        transition: all 0.4s ease;
        position: relative;
        overflow: hidden;
    }
    
    .result-card:hover {
        border-color: rgba(16, 185, 129, 0.3);
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(16, 185, 129, 0.2);
    }

    /* --- CUSTOM SCROLLBAR --- */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(20, 20, 28, 0.5);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(16, 185, 129, 0.3);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(16, 185, 129, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. IMPROVED HELPER FUNCTIONS
# ==========================================

def validate_score(score, min_val=0, max_val=100):
    """Validate and clamp scores"""
    try:
        score = int(float(score))
        return max(min_val, min(max_val, score))
    except:
        return None

def parse_report(text):
    """Enhanced parsing with strict validation"""
    sections = {}
    
    # Extract score - MUST BE PRESENT
    score_match = re.search(r'\[SCORE\]\s*[:\-]?\s*(\d+)', text, re.IGNORECASE)
    if score_match:
        sections['score'] = validate_score(score_match.group(1))
    else:
        sections['score'] = None
    
    # Extract grade
    grade_match = re.search(r'\[OVERALL_GRADE\]\s*[:\-]?\s*([A-FS][\-\+]?(?:-Tier)?)', text, re.IGNORECASE)
    sections['overall_grade'] = grade_match.group(1).upper() if grade_match else None
    
    # Extract quality scores
    entry_match = re.search(r'\[ENTRY_QUALITY\]\s*[:\-]?\s*(\d+)', text, re.IGNORECASE)
    sections['entry_quality'] = validate_score(entry_match.group(1)) if entry_match else None
    
    exit_match = re.search(r'\[EXIT_QUALITY\]\s*[:\-]?\s*(\d+)', text, re.IGNORECASE)
    sections['exit_quality'] = validate_score(exit_match.group(1)) if exit_match else None
    
    risk_score_match = re.search(r'\[RISK_SCORE\]\s*[:\-]?\s*(\d+)', text, re.IGNORECASE)
    sections['risk_score'] = validate_score(risk_score_match.group(1)) if risk_score_match else None
    
    # Extract tags
    tags_match = re.search(r'\[TAGS\]\s*[:\-]?\s*(.*?)(?=\[|$)', text, re.DOTALL | re.IGNORECASE)
    if tags_match:
        raw = tags_match.group(1).replace('[', '').replace(']', '').split(',')
        sections['tags'] = [t.strip() for t in raw if t.strip() and len(t.strip()) > 2][:10]
    else:
        sections['tags'] = []
    
    # Extract text sections
    patterns = {
        "tech": r"\[TECH\]\s*[:\-]?\s*(.*?)(?=\[PSYCH\]|\[RISK\]|\[FIX\]|$)",
        "psych": r"\[PSYCH\]\s*[:\-]?\s*(.*?)(?=\[RISK\]|\[FIX\]|$)",
        "risk": r"\[RISK\]\s*[:\-]?\s*(.*?)(?=\[FIX\]|$)",
        "fix": r"\[FIX\]\s*[:\-]?\s*(.*?)(?=\[STRENGTH\]|\[CRITICAL_ERROR\]|$)",
        "strength": r"\[STRENGTH\]\s*[:\-]?\s*(.*?)(?=\[CRITICAL_ERROR\]|$)",
        "critical_error": r"\[CRITICAL_ERROR\]\s*[:\-]?\s*(.*?)$"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            # Clean up
            content = re.sub(r'<[^>]+>', '', content)
            content = re.sub(r'```[\s\S]*?```', '', content)
            content = re.sub(r'\n{3,}', '\n\n', content)
            if len(content) > 20:
                sections[key] = content
            else:
                sections[key] = None
        else:
            sections[key] = None
    
    return sections

def validate_analysis(report):
    """Check if analysis is valid (not hallucinated)"""
    # Check if all critical fields are None
    critical_fields = ['score', 'tech', 'psych', 'risk', 'fix']
    none_count = sum(1 for field in critical_fields if report.get(field) is None)
    
    if none_count >= 3:
        return False, "Analysis incomplete - AI failed to extract data"
    
    # Check if score is None
    if report.get('score') is None:
        return False, "No score detected - AI failed to analyze"
    
    # Check for default/placeholder values
    if report.get('score') == 50 and report.get('entry_quality') == 50 and report.get('exit_quality') == 50:
        return False, "Analysis appears to be placeholder values"
    
    # Check if text sections are too short
    text_sections = [report.get('tech', ''), report.get('psych', ''), report.get('risk', '')]
    if all(len(str(s)) < 30 for s in text_sections if s):
        return False, "Analysis text is too brief - likely incomplete"
    
    return True, "Valid"

def save_analysis(user_id, data, ticker_symbol="UNK", img_url=None):
    """Save analysis to database"""
    if not supabase:
        return
    try:
        payload = {
            "user_id": user_id,
            "ticker": ticker_symbol,
            "score": data.get('score', 0),
            "overall_grade": data.get('overall_grade', 'N/A'),
            "entry_quality": data.get('entry_quality', 0),
            "exit_quality": data.get('exit_quality', 0),
            "risk_score": data.get('risk_score', 0),
            "mistake_tags": data.get('tags', []),
            "technical_analysis": data.get('tech', ''),
            "psych_analysis": data.get('psych', ''),
            "risk_analysis": data.get('risk', ''),
            "fix_action": data.get('fix', ''),
            "strength": data.get('strength', ''),
            "critical_error": data.get('critical_error', ''),
            "image_url": img_url
        }
        supabase.table("trades").insert(payload).execute()
    except Exception as e:
        st.error(f"Database save error: {e}")

def upload_image_to_supabase(file_obj):
    """Upload image to Supabase storage"""
    if not supabase:
        return None
    
    try:
        file_ext = file_obj.name.split('.')[-1]
        file_name = f"{st.session_state['user']}/{uuid.uuid4()}.{file_ext}"
        
        file_obj.seek(0)
        file_bytes = file_obj.read()
        
        bucket_name = "trade_images"
        supabase.storage.from_(bucket_name).upload(
            file=file_bytes,
            path=file_name,
            file_options={"content-type": f"image/{file_ext}"}
        )
        
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
        return public_url
    except Exception as e:
        st.warning(f"Image upload failed: {e}")
        return None

def call_vision_api(prompt, img_b64, model="llama", max_retries=2):
    """Call vision API with retry logic"""
    
    # Choose API URL
    api_url = API_URL if model == "llama" else API_URL_BACKUP
    
    for attempt in range(max_retries):
        try:
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                ]
            }]
            
            payload = {
                "inputs": json.dumps(messages),
                "parameters": {
                    "max_new_tokens": 2000,
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "return_full_text": False
                }
            }
            
            headers = {
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json"
            }
            
            res = requests.post(api_url, headers=headers, json=payload, timeout=90)
            
            if res.status_code == 200:
                result = res.json()
                
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    content = result[0].get('generated_text', '')
                elif isinstance(result, dict):
                    content = result.get('generated_text', result.get('output', ''))
                else:
                    content = str(result)
                
                # Validate response isn't just code
                if '<div' in content[:100] or '```python' in content[:100]:
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    raise ValueError("Model returning code instead of analysis")
                
                return content
            else:
                error_msg = f"API Error {res.status_code}: {res.text[:200]}"
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise Exception(error_msg)
                
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2)
    
    raise Exception("Max retries exceeded")

def generate_insights(df):
    """Generate AI insights from trading history"""
    insights = []
    if df.empty:
        return ["📊 No trading history yet. Complete your first analysis to see insights."]
    
    # Calculate metrics
    recent_scores = df.head(3)['score'].mean()
    avg_score = df['score'].mean()
    
    if recent_scores < 40:
        insights.append("🚨 **Critical Alert:** Last 3 trades averaged below 40. Strong recommendation to pause trading for 24-48 hours and review your strategy.")
    elif recent_scores < avg_score - 15:
        insights.append("⚠️ **Performance Decline:** Recent trades significantly below your average. Review your recent decision-making patterns.")
    elif recent_scores > 80:
        insights.append("🔥 **Excellent Performance:** High decision quality in recent trades. Your discipline is paying off.")
    
    # Tag analysis
    all_tags = [tag for sublist in df['mistake_tags'] for tag in sublist]
    if all_tags:
        tag_counts = pd.Series(all_tags).value_counts()
        most_common = tag_counts.index[0]
        
        if tag_counts[most_common] >= 3:
            insights.append(f"🎯 **Pattern Detected:** '{most_common}' appears {tag_counts[most_common]} times in your history. This is a key area for improvement.")
    
    # Win rate
    win_rate = len(df[df['score'] > 60]) / len(df) * 100
    if win_rate < 40:
        insights.append(f"📉 **Low Quality Rate:** Only {win_rate:.0f}% of trades score above 60. Focus on quality over quantity.")
    elif win_rate > 70:
        insights.append(f"✅ **Strong Consistency:** {win_rate:.0f}% quality rate shows good trading discipline.")
    
    return insights if insights else ["✅ Performance metrics within acceptable parameters."]

# ==========================================
# 4. MAIN APP LOGIC
# ==========================================

if not st.session_state["authenticated"]:
    # LOGIN VIEW
    st.markdown("""
    <div class="login-container">
        <div class="login-logo">🩸</div>
        <h1 style="margin: 0 0 10px 0; font-size: 2.2rem; font-weight: 800; letter-spacing: -0.02em; position: relative; z-index: 1;">StockPostmortem</h1>
        <p style="color: #6b7280; font-size: 0.8rem; margin-bottom: 48px; letter-spacing: 3px; text-transform: uppercase; position: relative; z-index: 1;">Algorithmic Behavioral Forensics</p>
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

else:
    # AUTHENTICATED VIEW
    current_user = st.session_state["user"]
    current_page = st.session_state.get("current_page", "analyze")
    
    # NAVIGATION
    st.markdown(f"""
    <div class="premium-navbar">
        <div class="nav-brand">
            <div class="nav-logo">🩸</div>
            <div>
                <div class="nav-title">Trade Autopsy</div>
            </div>
        </div>
        <div class="nav-menu">
            <span class="nav-link {'active' if current_page == 'analyze' else ''}" id="nav_analyze">Analyze</span>
            <span class="nav-link {'active' if current_page == 'data_vault' else ''}" id="nav_vault">Data Vault</span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="
                background: rgba(16, 185, 129, 0.15);
                padding: 8px 16px;
                border-radius: 10px;
                font-size: 0.85rem;
                font-weight: 600;
                color: #10b981;
                border: 1px solid rgba(16, 185, 129, 0.3);
            ">
                {current_user}
            </div>
        </div>
    </div>
    
    <script>
    document.getElementById('nav_analyze').onclick = function() {{
        window.location.href = '?page=analyze';
    }};
    document.getElementById('nav_vault').onclick = function() {{
        window.location.href = '?page=data_vault';
    }};
    </script>
    """, unsafe_allow_html=True)
    
    # PAGE ROUTING
    if current_page == "data_vault":
        # DATA VAULT PAGE
        if supabase:
            hist = supabase.table("trades").select("*").eq("user_id", current_user).order("created_at", desc=True).execute()
            
            if hist.data:
                df = pd.DataFrame(hist.data)
                df['created_at'] = pd.to_datetime(df['created_at'])
                
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                st.markdown(f'<div class="section-title">Complete Audit History ({len(df)} records)</div>', unsafe_allow_html=True)
                
                # Filters
                col_search1, col_search2, col_search3 = st.columns([2, 1, 1])
                
                with col_search1:
                    search_ticker = st.text_input("Search by Ticker", placeholder="e.g., SPY, AAPL", label_visibility="collapsed")
                
                with col_search2:
                    score_filter = st.selectbox("Score Filter", ["All", "Excellent (80+)", "Good (60-80)", "Fair (40-60)", "Poor (<40)"], label_visibility="collapsed")
                
                with col_search3:
                    sort_order = st.selectbox("Sort By", ["Newest First", "Oldest First", "Highest Score", "Lowest Score"], label_visibility="collapsed")
                
                st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                
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
                
                # Apply sorting
                if sort_order == "Oldest First":
                    filtered_df = filtered_df.sort_values('created_at', ascending=True)
                elif sort_order == "Highest Score":
                    filtered_df = filtered_df.sort_values('score', ascending=False)
                elif sort_order == "Lowest Score":
                    filtered_df = filtered_df.sort_values('score', ascending=True)
                
                # Display table
                if len(filtered_df) > 0:
                    display_df = filtered_df[['created_at', 'ticker', 'score', 'overall_grade', 'mistake_tags']].copy()
                    display_df.columns = ['Date', 'Ticker', 'Score', 'Grade', 'Tags']
                    display_df['Tags'] = display_df['Tags'].apply(lambda x: ', '.join(x[:3]) if isinstance(x, list) else '')
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100),
                            "Date": st.column_config.DatetimeColumn("Date", format="MMM DD, YYYY HH:mm")
                        },
                        height=600
                    )
                    
                    # Export button
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Export to CSV",
                        data=csv,
                        file_name=f"stockpostmortem_{current_user}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No records match your filters.")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Detailed history with images
                st.markdown('<div class="glass-panel" style="margin-top: 32px;">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">📜 Detailed Trade History</div>', unsafe_allow_html=True)
                
                for i, row in filtered_df.head(20).iterrows():
                    with st.expander(f"📊 {row['created_at'].strftime('%Y-%m-%d %H:%M')} | {row['ticker']} | Score: {row['score']}/100"):
                        if row.get('image_url'):
                            st.image(row['image_url'], caption="Trade Evidence", width=600)
                            st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Grade:** {row.get('overall_grade', 'N/A')}")
                            st.markdown(f"**Entry Quality:** {row.get('entry_quality', 'N/A')}/100")
                            st.markdown(f"**Exit Quality:** {row.get('exit_quality', 'N/A')}/100")
                        with col2:
                            st.markdown(f"**Risk Score:** {row.get('risk_score', 'N/A')}/100")
                            tags = row.get('mistake_tags', [])
                            st.markdown(f"**Tags:** {', '.join(tags) if tags else 'None'}")
                        
                        if row.get('technical_analysis'):
                            st.markdown("**📈 Technical:**")
                            st.write(row['technical_analysis'])
                        
                        if row.get('psych_analysis'):
                            st.markdown("**🧠 Psychology:**")
                            st.write(row['psych_analysis'])
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="glass-panel" style="text-align: center; padding: 80px;">', unsafe_allow_html=True)
                st.markdown("""
                <div style="font-size: 3.5rem; margin-bottom: 20px; opacity: 0.4;">🗄️</div>
                <div style="font-size: 1.2rem; color: #9ca3af; margin-bottom: 10px; font-weight: 600;">Data Vault Empty</div>
                <div style="font-size: 0.95rem; color: #6b7280;">Your audit history will appear here once you start analyzing trades.</div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # ANALYZE PAGE
        main_tab1, main_tab2 = st.tabs(["🔎 FORENSIC AUDIT", "📊 PERFORMANCE METRICS"])
        
        with main_tab1:
            c_mode = st.radio("Input Method", ["Chart Vision", "Text Parameters"], horizontal=True, label_visibility="collapsed")
            
            if c_mode == "Chart Vision":
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">Chart Analysis</div>', unsafe_allow_html=True)
                st.markdown("""
                <div style="text-align: center; margin-bottom: 24px;">
                    <div style="font-size: 3rem; margin-bottom: 16px;">📊</div>
                    <div style="font-size: 1.3rem; font-weight: 600; margin-bottom: 12px;">Upload Trading Chart</div>
                    <div style="font-size: 0.9rem; color: #9ca3af;">Supports PNG, JPG. AI will analyze price action, risk, and behavioral patterns.</div>
                </div>
                """, unsafe_allow_html=True)
                
                uploaded_file = st.file_uploader("Upload Chart", type=["png", "jpg", "jpeg"], label_visibility="collapsed", key="chart_upload")
                
                if uploaded_file:
                    st.image(uploaded_file, use_column_width=True)
                    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
                    
                    with st.expander("📝 Optional: Provide Context (Improves Accuracy)"):
                        manual_ticker = st.text_input("Ticker Symbol", "", placeholder="e.g., AAPL, TSLA")
                        manual_context = st.text_area("Trade Context", height=100, placeholder="Entry reasoning, exit reasoning, emotional state, etc.")
                    
                    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
                    
                    if st.button("🧬 RUN ANALYSIS", type="primary", use_container_width=True):
                        with st.spinner("📤 Uploading evidence..."):
                            stored_image_url = upload_image_to_supabase(uploaded_file)
                        
                        with st.spinner("🔬 Running AI analysis (30-60 sec)..."):
                            try:
                                # Process image
                                image = Image.open(uploaded_file)
                                max_size = (1920, 1080)
                                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                                buf = io.BytesIO()
                                image.save(buf, format="PNG", optimize=True)
                                img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                                
                                # Build context
                                context_str = ""
                                if manual_ticker or manual_context:
                                    context_str = "\n\nUSER PROVIDED CONTEXT:\n"
                                    if manual_ticker:
                                        context_str += f"Ticker: {manual_ticker}\n"
                                    if manual_context:
                                        context_str += f"Context: {manual_context}\n"
                                
                                # IMPROVED PROMPT - Simple and Direct
                                prompt = f"""Analyze this trading chart image and provide a detailed assessment.

{context_str}

ANALYSIS REQUIREMENTS:

1. IDENTIFY what you see:
   - What ticker/asset is shown?
   - What are the visible price levels?
   - What is the P&L shown (profit/loss amount and percentage)?
   - Is this a single trade or portfolio view?

2. TECHNICAL ANALYSIS:
   - Entry timing and price level
   - Exit timing and price level
   - Stop loss placement (if visible)
   - Risk/reward ratio
   - Chart pattern quality

3. BEHAVIORAL ANALYSIS:
   - Signs of FOMO, revenge trading, or emotional decisions
   - Exit discipline (cutting losses vs. holding winners)
   - Risk management quality

4. SCORE the trade from 0-100:
   - 90-100: Excellent execution, strong discipline
   - 70-89: Good trade, minor improvements needed
   - 50-69: Average, several mistakes
   - 30-49: Poor execution, major issues
   - 0-29: Catastrophic, fundamental problems

OUTPUT FORMAT (MANDATORY):

[SCORE] <number 0-100>

[OVERALL_GRADE] <A/B/C/D/F>

[ENTRY_QUALITY] <number 0-100>

[EXIT_QUALITY] <number 0-100>

[RISK_SCORE] <number 0-100>

[TAGS] <comma-separated behavioral tags: FOMO, Revenge_Trading, Good_Exit, Poor_Entry, No_Stop_Loss, Overleveraged, etc.>

[TECH] <2-3 sentences: Technical analysis with specific price levels and chart observations>

[PSYCH] <2-3 sentences: Psychological/behavioral analysis of decision-making>

[RISK] <2-3 sentences: Risk management assessment with specific observations>

[FIX] <3 specific actionable improvements:
1. [specific improvement]
2. [specific improvement]  
3. [specific improvement]>

[STRENGTH] <1-2 sentences: What was done well>

[CRITICAL_ERROR] <1 sentence: Biggest single mistake>

BE SPECIFIC. USE ACTUAL NUMBERS FROM THE CHART. BE HONEST AND DIRECT."""

                                # Call API with retry
                                try:
                                    raw_response = call_vision_api(prompt, img_b64, model="llama")
                                except:
                                    st.warning("Primary model failed, trying backup...")
                                    raw_response = call_vision_api(prompt, img_b64, model="qwen")
                                
                                # Parse response
                                report = parse_report(raw_response)
                                
                                # Validate
                                is_valid, error_msg = validate_analysis(report)
                                
                                if not is_valid:
                                    st.error(f"❌ Analysis Failed: {error_msg}")
                                    st.warning("The AI could not properly analyze your chart. Please try:")
                                    st.info("• Upload a clearer image with visible price levels\n• Use the Text Parameters mode instead\n• Provide more context in the optional fields")
                                    st.expander("Show raw AI response").write(raw_response)
                                else:
                                    # Fill in missing values
                                    if report['score'] is None:
                                        report['score'] = 50
                                    if report['overall_grade'] is None:
                                        if report['score'] >= 80: report['overall_grade'] = 'A'
                                        elif report['score'] >= 60: report['overall_grade'] = 'B'
                                        elif report['score'] >= 40: report['overall_grade'] = 'C'
                                        elif report['score'] >= 20: report['overall_grade'] = 'D'
                                        else: report['overall_grade'] = 'F'
                                    if report['entry_quality'] is None:
                                        report['entry_quality'] = report['score']
                                    if report['exit_quality'] is None:
                                        report['exit_quality'] = report['score']
                                    if report['risk_score'] is None:
                                        report['risk_score'] = report['score']
                                    
                                    # Save
                                    ticker_val = manual_ticker if manual_ticker else "CHART"
                                    save_analysis(current_user, report, ticker_val, stored_image_url)
                                    
                                    # DISPLAY RESULTS
                                    score_color = "#10b981" if report['score'] >= 80 else "#3b82f6" if report['score'] >= 60 else "#f59e0b" if report['score'] >= 40 else "#ef4444"
                                    grade_color = f"rgba({int(score_color[1:3], 16)}, {int(score_color[3:5], 16)}, {int(score_color[5:7], 16)}, 0.2)"
                                    
                                    st.markdown(f"""
                                    <div class="glass-panel animate-scale-in" style="border-top: 3px solid {score_color}; margin-top: 32px;">
                                        <div style="display: flex; justify-content: space-between; align-items: center;">
                                            <div>
                                                <div style="color:#6b7280; letter-spacing:3px; font-size:0.7rem; text-transform: uppercase; margin-bottom: 10px;">ANALYSIS COMPLETE</div>
                                                <div style="display: flex; align-items: center; gap: 20px;">
                                                    <div style="font-family: 'JetBrains Mono'; font-size: 4rem; font-weight: 700; color:{score_color}">{report['score']}</div>
                                                    <div style="background:{grade_color}; color:{score_color}; padding: 8px 20px; border-radius: 12px; font-weight: 700;">
                                                        GRADE: {report['overall_grade']}
                                                    </div>
                                                </div>
                                            </div>
                                            <div style="text-align: right;">
                                                <div style="background: rgba(16, 185, 129, 0.15); padding: 8px 16px; border-radius: 10px; color: #10b981; font-weight: 600;">{ticker_val}</div>
                                                <div style="color:#6b7280; font-size:0.85rem; margin-top: 8px;">{datetime.now().strftime('%B %d, %Y')}</div>
                                            </div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Metrics
                                    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                                    st.markdown('<div class="section-title">📊 Quality Metrics</div>', unsafe_allow_html=True)
                                    
                                    col1, col2, col3 = st.columns(3)
                                    for metric_name, metric_value, col in [
                                        ("Entry Quality", report['entry_quality'], col1),
                                        ("Exit Quality", report['exit_quality'], col2),
                                        ("Risk Management", report['risk_score'], col3)
                                    ]:
                                        with col:
                                            met_color = "#10b981" if metric_value >= 80 else "#3b82f6" if metric_value >= 60 else "#f59e0b" if metric_value >= 40 else "#ef4444"
                                            st.markdown(f"""
                                            <div style="text-align: center; padding: 20px;">
                                                <div style="font-size: 2.5rem; font-weight: 700; color: {met_color}; font-family: 'JetBrains Mono';">{metric_value}</div>
                                                <div style="font-size: 0.9rem; font-weight: 600; color: #e5e7eb; margin-top: 8px;">{metric_name}</div>
                                                <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; margin-top: 12px;">
                                                    <div style="width: {metric_value}%; height: 100%; background: {met_color}; border-radius: 4px;"></div>
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                    
                                    st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    # Tags
                                    if report['tags']:
                                        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                                        st.markdown('<div class="section-title">🏷️ Behavioral Patterns</div>', unsafe_allow_html=True)
                                        tags_html = '<div style="display: flex; flex-wrap: wrap; gap: 12px;">'
                                        for tag in report['tags']:
                                            tag_color = "#ef4444" if any(w in tag.lower() for w in ['fomo', 'revenge', 'panic']) else "#10b981" if any(w in tag.lower() for w in ['good', 'disciplined']) else "#f59e0b"
                                            tags_html += f'<div style="background: rgba({int(tag_color[1:3], 16)}, {int(tag_color[3:5], 16)}, {int(tag_color[5:7], 16)}, 0.15); border: 1px solid {tag_color}; padding: 10px 18px; border-radius: 10px; color: {tag_color}; font-weight: 600;">{tag}</div>'
                                        tags_html += '</div>'
                                        st.markdown(tags_html, unsafe_allow_html=True)
                                        st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    # Analysis sections
                                    col_left, col_right = st.columns(2)
                                    
                                    with col_left:
                                        if report['tech']:
                                            st.markdown('<div class="result-card">', unsafe_allow_html=True)
                                            st.markdown('<div style="font-size: 1rem; font-weight: 700; color: #3b82f6; margin-bottom: 12px;">⚙️ TECHNICAL ANALYSIS</div>', unsafe_allow_html=True)
                                            st.markdown(f'<div style="color: #d1d5db; line-height: 1.7;">{report["tech"]}</div>', unsafe_allow_html=True)
                                            st.markdown('</div>', unsafe_allow_html=True)
                                        
                                        if report['risk']:
                                            st.markdown('<div class="result-card">', unsafe_allow_html=True)
                                            st.markdown('<div style="font-size: 1rem; font-weight: 700; color: #f59e0b; margin-bottom: 12px;">⚠️ RISK ASSESSMENT</div>', unsafe_allow_html=True)
                                            st.markdown(f'<div style="color: #d1d5db; line-height: 1.7;">{report["risk"]}</div>', unsafe_allow_html=True)
                                            st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    with col_right:
                                        if report['psych']:
                                            st.markdown('<div class="result-card">', unsafe_allow_html=True)
                                            st.markdown('<div style="font-size: 1rem; font-weight: 700; color: #8b5cf6; margin-bottom: 12px;">🧠 PSYCHOLOGY</div>', unsafe_allow_html=True)
                                            st.markdown(f'<div style="color: #d1d5db; line-height: 1.7;">{report["psych"]}</div>', unsafe_allow_html=True)
                                            st.markdown('</div>', unsafe_allow_html=True)
                                        
                                        if report['fix']:
                                            st.markdown('<div class="result-card">', unsafe_allow_html=True)
                                            st.markdown('<div style="font-size: 1rem; font-weight: 700; color: #10b981; margin-bottom: 12px;">🎯 ACTION PLAN</div>', unsafe_allow_html=True)
                                            st.markdown(f'<div style="color: #d1d5db; line-height: 1.7;">{report["fix"]}</div>', unsafe_allow_html=True)
                                            st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    # Key insights
                                    if report['strength'] or report['critical_error']:
                                        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                                        ins_col1, ins_col2 = st.columns(2)
                                        
                                        if report['strength']:
                                            with ins_col1:
                                                st.markdown(f"""
                                                <div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 20px; border-radius: 0 12px 12px 0;">
                                                    <div style="font-size: 1rem; font-weight: 700; color: #10b981; margin-bottom: 12px;">💪 STRENGTH</div>
                                                    <div style="color: #d1d5db; line-height: 1.7;">{report['strength']}</div>
                                                </div>
                                                """, unsafe_allow_html=True)
                                        
                                        if report['critical_error']:
                                            with ins_col2:
                                                st.markdown(f"""
                                                <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 20px; border-radius: 0 12px 12px 0;">
                                                    <div style="font-size: 1rem; font-weight: 700; color: #ef4444; margin-bottom: 12px;">⛔ CRITICAL ERROR</div>
                                                    <div style="color: #d1d5db; line-height: 1.7;">{report['critical_error']}</div>
                                                </div>
                                                """, unsafe_allow_html=True)
                                        
                                        st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    st.success("✅ Analysis complete!")
                                
                            except Exception as e:
                                st.error(f"❌ Analysis Error: {str(e)}")
                                st.info("Try using Text Parameters mode or upload a clearer image.")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            else:
                # TEXT PARAMETERS MODE
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">Manual Trade Input</div>', unsafe_allow_html=True)
                
                with st.form("manual_trade_form"):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        ticker = st.text_input("Ticker", "SPY")
                    with col_b:
                        setup_type = st.selectbox("Setup", ["Trend", "Reversal", "Breakout", "Range"])
                    with col_c:
                        emotion = st.selectbox("Emotional State", ["Neutral", "FOMO", "Revenge", "Fearful", "Greedy"])
                    
                    col_d, col_e, col_f = st.columns(3)
                    with col_d:
                        entry = st.number_input("Entry Price", 0.0, step=0.01)
                    with col_e:
                        exit_price = st.number_input("Exit Price", 0.0, step=0.01)
                    with col_f:
                        stop = st.number_input("Stop Loss", 0.0, step=0.01)
                    
                    notes = st.text_area("Trade Notes", height=120, placeholder="Describe your reasoning, decision-making process, what you were thinking...")
                    
                    submitted = st.form_submit_button("🔬 ANALYZE TRADE", type="primary", use_container_width=True)
                    
                    if submitted and entry > 0 and exit_price > 0:
                        pnl = exit_price - entry
                        pnl_pct = (pnl / entry * 100) if entry > 0 else 0
                        risk = abs(entry - stop) if stop > 0 else 0
                        risk_pct = (risk / entry * 100) if entry > 0 else 0
                        rr_ratio = (abs(pnl) / risk) if risk > 0 else 0
                        
                        # Simple, direct prompt
                        prompt = f"""Analyze this trade and provide honest assessment.

TRADE DETAILS:
Ticker: {ticker}
Setup Type: {setup_type}
Emotional State: {emotion}
Entry: ${entry:.2f}
Exit: ${exit_price:.2f}
Stop Loss: ${stop:.2f}

CALCULATED METRICS:
P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)
Risk: ${risk:.2f} ({risk_pct:.2f}%)
R:R Ratio: {rr_ratio:.2f}:1

TRADER NOTES: {notes if notes else "No notes provided"}

Provide analysis in this EXACT format:

[SCORE] <0-100 based on execution quality>

[OVERALL_GRADE] <A/B/C/D/F>

[ENTRY_QUALITY] <0-100>

[EXIT_QUALITY] <0-100>

[RISK_SCORE] <0-100>

[TAGS] <3-5 tags: FOMO, Good_RR, Poor_Stop, etc.>

[TECH] <2-3 sentences on technical execution>

[PSYCH] <2-3 sentences on psychological factors>

[RISK] <2-3 sentences on risk management>

[FIX] <3 specific improvements>

[STRENGTH] <What was good>

[CRITICAL_ERROR] <Biggest mistake>"""

                        with st.spinner("Analyzing trade..."):
                            try:
                                # Text-only API call
                                headers = {
                                    "Authorization": f"Bearer {HF_TOKEN}",
                                    "Content-Type": "application/json"
                                }
                                
                                payload = {
                                    "inputs": prompt,
                                    "parameters": {
                                        "max_new_tokens": 1500,
                                        "temperature": 0.3,
                                        "return_full_text": False
                                    }
                                }
                                
                                res = requests.post(API_URL, headers=headers, json=payload, timeout=60)
                                
                                if res.status_code == 200:
                                    result = res.json()
                                    if isinstance(result, list):
                                        raw_response = result[0].get('generated_text', '')
                                    else:
                                        raw_response = result.get('generated_text', '')
                                    
                                    report = parse_report(raw_response)
                                    is_valid, _ = validate_analysis(report)
                                    
                                    if is_valid:
                                        # Fill missing
                                        if report['score'] is None: report['score'] = 50
                                        if report['overall_grade'] is None: report['overall_grade'] = 'C'
                                        if report['entry_quality'] is None: report['entry_quality'] = report['score']
                                        if report['exit_quality'] is None: report['exit_quality'] = report['score']
                                        if report['risk_score'] is None: report['risk_score'] = report['score']
                                        
                                        save_analysis(current_user, report, ticker, None)
                                        
                                        # Display (same as above)
                                        score_color = "#10b981" if report['score'] >= 80 else "#3b82f6" if report['score'] >= 60 else "#f59e0b" if report['score'] >= 40 else "#ef4444"
                                        
                                        st.markdown(f"""
                                        <div class="glass-panel" style="border-top: 3px solid {score_color}; margin-top: 32px;">
                                            <div style="text-align: center;">
                                                <div style="font-size: 4rem; font-weight: 700; color:{score_color}; font-family: 'JetBrains Mono';">{report['score']}</div>
                                                <div style="font-size: 1.5rem; font-weight: 700; color: #e5e7eb; margin-top: 12px;">Grade: {report['overall_grade']}</div>
                                                <div style="color: #6b7280; margin-top: 8px;">{ticker} | {datetime.now().strftime('%B %d, %Y')}</div>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        # Show analysis sections
                                        if report['tech']:
                                            st.markdown("### ⚙️ Technical")
                                            st.write(report['tech'])
                                        if report['psych']:
                                            st.markdown("### 🧠 Psychology")
                                            st.write(report['psych'])
                                        if report['risk']:
                                            st.markdown("### ⚠️ Risk")
                                            st.write(report['risk'])
                                        if report['fix']:
                                            st.markdown("### 🎯 Fixes")
                                            st.write(report['fix'])
                                        
                                        st.success("✅ Analysis complete!")
                                    else:
                                        st.error("Analysis failed validation. Try again with more details.")
                                else:
                                    st.error(f"API Error: {res.status_code}")
                            
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        with main_tab2:
            # PERFORMANCE METRICS
            if supabase:
                hist = supabase.table("trades").select("*").eq("user_id", current_user).order("created_at", desc=True).execute()
                
                if hist.data:
                    df = pd.DataFrame(hist.data)
                    df['created_at'] = pd.to_datetime(df['created_at'])
                    
                    avg_score = df['score'].mean()
                    total_trades = len(df)
                    win_rate = len(df[df['score'] > 60]) / len(df) * 100
                    
                    # KPIs
                    st.markdown(f"""
                    <div class="kpi-container">
                        <div class="kpi-card">
                            <div class="kpi-val">{int(avg_score)}</div>
                            <div class="kpi-label">Avg Score</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-val">{int(win_rate)}%</div>
                            <div class="kpi-label">Quality Rate</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-val">{total_trades}</div>
                            <div class="kpi-label">Total Trades</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Chart
                    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">Performance Evolution</div>', unsafe_allow_html=True)
                    
                    chart_data = df[['created_at', 'score']].sort_values('created_at')
                    chart_data['index'] = range(len(chart_data))
                    
                    line_chart = alt.Chart(chart_data).mark_line(point=True, color='#3b82f6').encode(
                        x=alt.X('index:Q', title='Trade #'),
                        y=alt.Y('score:Q', scale=alt.Scale(domain=[0, 100]), title='Score'),
                        tooltip=['index', 'score', 'created_at']
                    ).properties(height=300)
                    
                    st.altair_chart(line_chart, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Insights
                    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">AI Insights</div>', unsafe_allow_html=True)
                    
                    insights = generate_insights(df)
                    for insight in insights:
                        st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.03); border-left: 4px solid #10b981; padding: 20px; border-radius: 0 12px 12px 0; margin-bottom: 16px;">
                            {insight}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                else:
                    st.info("No performance data yet. Complete your first analysis to see metrics.")
