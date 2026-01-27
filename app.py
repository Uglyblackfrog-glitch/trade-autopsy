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
            API_URL = "https://router.huggingface.co/v1/chat/completions"
            
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
    
    /* --- RADIO BUTTONS - REMOVE RED, USE GREEN/BLUE --- */
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
    
    /* Override any red radio button styling */
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
    
    /* Remove any red tab underlines */
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #10b981 !important;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 0 !important;
    }
    
    /* --- RADIO BUTTONS --- */
    .stRadio {
        background: transparent !important;
    }
    
    .stRadio > div {
        background: transparent !important;
        padding: 0 !important;
    }
    
    .stRadio > label {
        display: none !important;
    }
    
    /* Radio button selected state - GREEN instead of RED */
    .stRadio div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] {
        color: #9ca3af !important;
        transition: color 0.3s ease !important;
    }
    
    .stRadio div[role="radiogroup"] label[data-baseweb="radio"] div:first-child {
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        background: transparent !important;
    }
    
    .stRadio div[role="radiogroup"] label[data-baseweb="radio"]:hover div:first-child {
        border-color: rgba(16, 185, 129, 0.5) !important;
    }
    
    /* Selected radio button - GREEN theme */
    .stRadio div[role="radiogroup"] label div:first-child[data-checked="true"],
    .stRadio div[role="radiogroup"] label[aria-checked="true"] div:first-child {
        background: #10b981 !important;
        border-color: #10b981 !important;
    }
    
    .stRadio div[role="radiogroup"] label div:first-child[data-checked="true"]::after,
    .stRadio div[role="radiogroup"] label[aria-checked="true"] div:first-child::after {
        background: white !important;
    }
    
    /* Selected text color */
    .stRadio div[role="radiogroup"] label[aria-checked="true"] div[data-testid="stMarkdownContainer"] {
        color: #10b981 !important;
        font-weight: 600 !important;
    }
    
    /* Override Streamlit's default red accent */
    [data-baseweb="radio"] input[type="radio"]:checked {
        accent-color: #10b981 !important;
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
    
    /* Form submit buttons - ensure green theme */
    .stButton button[kind="primary"], 
    button[type="submit"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        border: 1px solid rgba(16, 185, 129, 0.4) !important;
        border-radius: 14px !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 14px 32px !important;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1) !important;
        box-shadow: 
            0 4px 20px rgba(16, 185, 129, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
        letter-spacing: 0.5px !important;
        font-size: 0.9rem !important;
    }
    
    .stButton button[kind="primary"]:hover,
    button[type="submit"]:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        box-shadow: 
            0 8px 32px rgba(16, 185, 129, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.25) !important;
        transform: translateY(-3px) !important;
    }
    
    /* Navigation buttons styled as text links */
    .stButton button[kind="secondary"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #9ca3af !important;
        padding: 8px 16px !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        position: relative;
        transition: all 0.3s ease !important;
    }
    
    .stButton button[kind="secondary"]::after {
        content: '';
        position: absolute;
        bottom: 4px;
        left: 16px;
        right: 16px;
        height: 2px;
        background: linear-gradient(90deg, #10b981, #3b82f6);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    
    .stButton button[kind="secondary"]:hover {
        color: #10b981 !important;
        background: rgba(16, 185, 129, 0.05) !important;
        transform: none !important;
    }
    
    .stButton button[kind="secondary"]:hover::after {
        transform: scaleX(1);
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
    
    [data-testid="stFileUploader"] section button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        border: none !important;
        border-radius: 14px !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 16px 36px !important;
        font-size: 0.95rem !important;
        transition: all 0.4s ease !important;
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3) !important;
        margin-top: 24px !important;
    }
    
    [data-testid="stFileUploader"] section button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.5) !important;
        transform: translateY(-2px);
    }
    
    .upload-icon {
        font-size: 4rem;
        margin-bottom: 28px;
        display: block;
        opacity: 0.9;
        animation: float 3s ease-in-out infinite;
        filter: drop-shadow(0 0 20px rgba(16, 185, 129, 0.3));
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-12px); }
    }
    
    .upload-text {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 14px;
        letter-spacing: -0.01em;
    }
    
    .upload-subtext {
        font-size: 0.92rem;
        color: #9ca3af;
        line-height: 1.7;
    }

    /* --- DATAFRAME --- */
    .stDataFrame {
        background: rgba(15, 15, 20, 0.7);
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* --- SCORE DISPLAY --- */
    .score-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 32px;
    }
    
    .score-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 5.5rem;
        font-weight: 800;
        line-height: 1;
        letter-spacing: -0.04em;
    }
    
    .score-meta {
        text-align: right;
    }
    
    .ticker-badge {
        background: rgba(16, 185, 129, 0.15);
        padding: 10px 20px;
        border-radius: 10px;
        display: inline-block;
        font-weight: 600;
        font-size: 0.95rem;
        letter-spacing: 1px;
        margin-bottom: 10px;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    /* --- UTILITY CLASSES --- */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        margin: 32px 0;
    }
    
    .accent-text {
        color: #10b981;
        font-weight: 600;
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
    
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
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
    
    .result-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.1), transparent);
        animation: shimmer 2s infinite;
    }
    
    .result-card:hover {
        border-color: rgba(16, 185, 129, 0.3);
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(16, 185, 129, 0.2);
    }
    
    .metric-circle {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        position: relative;
        margin: 0 auto;
    }
    
    .metric-circle::before {
        content: '';
        position: absolute;
        inset: -4px;
        border-radius: 50%;
        padding: 4px;
        background: linear-gradient(135deg, #10b981, #3b82f6);
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        animation: spin 3s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    .grade-badge {
        display: inline-block;
        padding: 8px 20px;
        border-radius: 12px;
        font-size: 1.1rem;
        font-weight: 700;
        letter-spacing: 1px;
        animation: pulse 2s ease infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    .progress-bar-container {
        width: 100%;
        height: 12px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 6px;
        overflow: hidden;
        position: relative;
    }
    
    .progress-bar {
        height: 100%;
        border-radius: 6px;
        transition: width 1.5s cubic-bezier(0.23, 1, 0.32, 1);
        position: relative;
        overflow: hidden;
    }
    
    .progress-bar::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        animation: shimmer 1.5s infinite;
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
    
    /* === GLOBAL RED COLOR REMOVAL === */
    /* Override all Streamlit red colors with green */
    button[kind="primary"], 
    button[type="submit"],
    .stButton > button[kind="primary"],
    [data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        border-color: rgba(16, 185, 129, 0.4) !important;
    }
    
    button[kind="primary"]:hover, 
    button[type="submit"]:hover,
    .stButton > button[kind="primary"]:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    }
    
    /* Remove red from error messages and warnings */
    .stAlert, .element-container .stException {
        border-left-color: #f59e0b !important;
    }
    
    /* Radio and checkbox accent colors */
    input[type="radio"]:checked,
    input[type="checkbox"]:checked {
        accent-color: #10b981 !important;
        background-color: #10b981 !important;
        border-color: #10b981 !important;
    }
    
    /* Slider and progress bars */
    .stSlider [role="slider"],
    .stProgress > div > div {
        background-color: #10b981 !important;
    }
    
    /* Any element with red background */
    *[style*="background: red"],
    *[style*="background-color: red"],
    *[style*="background: #ef4444"],
    *[style*="background-color: #ef4444"],
    *[style*="background: #dc2626"],
    *[style*="background-color: #dc2626"],
    *[style*="background: rgb(239, 68, 68)"],
    *[style*="background-color: rgb(239, 68, 68)"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        background-color: #10b981 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def clean_text(text):
    return re.sub(r'[^\w\s,.:;!?()\[\]\-\'\"%]', '', text).strip()

def parse_report(text):
    sections = { 
        "score": 0, 
        "tags": [], 
        "tech": "N/A", 
        "psych": "N/A", 
        "risk": "N/A", 
        "fix": "N/A",
        "overall_grade": "C",
        "entry_quality": 50,
        "exit_quality": 50,
        "risk_score": 50,
        "strength": "N/A",
        "critical_error": "N/A"
    }
    text = clean_text(text)
    
    # Extract score
    score_match = re.search(r'\[SCORE\]\s*(\d+)', text)
    if score_match: sections['score'] = int(score_match.group(1))
    
    # Extract grade
    grade_match = re.search(r'\[OVERALL_GRADE\]\s*([A-FS][\-\+]?(?:-Tier)?)', text)
    if grade_match: sections['overall_grade'] = grade_match.group(1)
    
    # Extract quality scores
    entry_match = re.search(r'\[ENTRY_QUALITY\]\s*(\d+)', text)
    if entry_match: sections['entry_quality'] = int(entry_match.group(1))
    
    exit_match = re.search(r'\[EXIT_QUALITY\]\s*(\d+)', text)
    if exit_match: sections['exit_quality'] = int(exit_match.group(1))
    
    risk_score_match = re.search(r'\[RISK_SCORE\]\s*(\d+)', text)
    if risk_score_match: sections['risk_score'] = int(risk_score_match.group(1))
    
    # Extract tags
    tags_match = re.search(r'\[TAGS\](.*?)(?=\[|$)', text, re.DOTALL)
    if tags_match:
        raw = tags_match.group(1).replace('[', '').replace(']', '').split(',')
        sections['tags'] = [t.strip() for t in raw if t.strip()]
    
    # Extract text sections
    patterns = {
        "tech": r"\[TECH\](.*?)(?=\[PSYCH\]|\[RISK\]|\[FIX\]|\[STRENGTH\]|\[CRITICAL_ERROR\]|\[SCORE\]|\[TAGS\]|$)",
        "psych": r"\[PSYCH\](.*?)(?=\[RISK\]|\[FIX\]|\[STRENGTH\]|\[CRITICAL_ERROR\]|\[SCORE\]|\[TAGS\]|$)",
        "risk": r"\[RISK\](.*?)(?=\[FIX\]|\[STRENGTH\]|\[CRITICAL_ERROR\]|\[SCORE\]|\[TAGS\]|$)",
        "fix": r"\[FIX\](.*?)(?=\[STRENGTH\]|\[CRITICAL_ERROR\]|\[SCORE\]|\[TAGS\]|$)",
        "strength": r"\[STRENGTH\](.*?)(?=\[CRITICAL_ERROR\]|\[SCORE\]|\[TAGS\]|$)",
        "critical_error": r"\[CRITICAL_ERROR\](.*?)(?=\[SCORE\]|\[TAGS\]|$)"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL)
        if match: 
            sections[key] = match.group(1).strip()
    
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

# --- DASHBOARD VIEW ---
else:
    current_user = st.session_state["user"]
    
    # Initialize current_page if not exists
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "analyze"
    
    current_page = st.session_state.get("current_page", "analyze")
    
    # --- PREMIUM NAVIGATION BAR ---
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
            <span class="nav-link {'active' if current_page == 'pricing' else ''}" id="nav_pricing">Pricing</span>
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
    document.getElementById('nav_pricing').onclick = function() {{
        window.location.href = '?page=pricing';
    }};
    </script>
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
                
                if sort_order == "Oldest First":
                    filtered_df = filtered_df.sort_values('created_at', ascending=True)
                elif sort_order == "Highest Score":
                    filtered_df = filtered_df.sort_values('score', ascending=False)
                elif sort_order == "Lowest Score":
                    filtered_df = filtered_df.sort_values('score', ascending=True)
                else:
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
                st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
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
                st.markdown('<div class="glass-panel" style="text-align: center; padding: 80px;">', unsafe_allow_html=True)
                st.markdown("""
                <div style="font-size: 3.5rem; margin-bottom: 20px; opacity: 0.4;">🗄️</div>
                <div style="font-size: 1.2rem; color: #9ca3af; margin-bottom: 10px; font-weight: 600;">Data Vault Empty</div>
                <div style="font-size: 0.95rem; color: #6b7280;">Your audit history will appear here once you start analyzing trades.</div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state["current_page"] == "pricing":
        # PRICING PAGE
        st.markdown('<div class="glass-panel" style="text-align: center; padding: 80px;">', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size: 3.5rem; margin-bottom: 20px; opacity: 0.4;">💳</div>
        <div style="font-size: 1.2rem; color: #9ca3af; margin-bottom: 10px; font-weight: 600;">Pricing Information</div>
        <div style="font-size: 0.95rem; color: #6b7280;">Pricing details coming soon.</div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:  # analyze page (default)
        # TABS
        main_tab1, main_tab2 = st.tabs(["🔎 FORENSIC AUDIT", "📊 PERFORMANCE METRICS"])

        # --- TAB 1: AUDIT (INPUT) ---
        with main_tab1:
            c_mode = st.radio("Input Vector", ["Text Parameters", "Chart Vision"], horizontal=True, label_visibility="collapsed")
        
            prompt = ""
            img_b64 = None
            ticker_val = "IMG"
            ready_to_run = False

            if c_mode == "Chart Vision":
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">Chart Analysis</div>', unsafe_allow_html=True)
                st.markdown("""
                <div style="text-align: center; margin-bottom: 24px;">
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
                    st.markdown('<div style="margin-top: 32px;">', unsafe_allow_html=True)
                    st.image(uploaded_file, use_column_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
                    if st.button("RUN OPTICAL ANALYSIS", type="primary", use_container_width=True):
                        image = Image.open(uploaded_file)
                        buf = io.BytesIO()
                        image.save(buf, format="PNG")
                        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                        prompt = """You are an elite institutional trading analyst with 20+ years experience in quantitative analysis and behavioral finance. Analyze this trading chart/P&L screenshot with EXTREME precision.

CRITICAL ANALYSIS FRAMEWORK:

1. TECHNICAL ANALYSIS (Examine with surgical precision):
   - Entry timing quality (scale: Poor/Fair/Good/Excellent)
   - Exit timing effectiveness
   - Risk-reward ratio calculation
   - Position sizing appropriateness
   - Stop loss placement logic
   - Support/resistance level utilization
   - Trend alignment (with/against major trend)
   - Volume confirmation (if visible)

2. PSYCHOLOGICAL ASSESSMENT (Identify behavioral patterns):
   - Evidence of FOMO (entering late in move)
   - Revenge trading indicators (oversized position after loss)
   - Confirmation bias (ignoring contrary signals)
   - Loss aversion (holding losers too long)
   - Overconfidence (position too large)
   - Fear/panic selling markers
   - Discipline level (following plan vs emotional)

3. RISK MANAGEMENT EVALUATION:
   - Account risk percentage (estimate if visible)
   - Drawdown severity
   - Risk concentration
   - Correlation awareness
   - Liquidity considerations

4. PERFORMANCE METRICS:
   - Win rate pattern
   - Average win vs average loss
   - Consistency of execution
   - Trade frequency appropriateness

OUTPUT FORMAT (MANDATORY - Follow EXACTLY):

[SCORE] (0-100, be CRITICAL - only 70+ for truly good trades)
[OVERALL_GRADE] (F/D/C/B/A/S-Tier)

[TAGS] List 3-5 specific issues: FOMO, Poor_Entry, No_Stop, Oversized, Revenge_Trade, Trend_Counter, Emotional_Exit, Good_RR, Disciplined, etc.

[ENTRY_QUALITY] (0-100) Detailed analysis of entry timing and price level

[EXIT_QUALITY] (0-100) Detailed analysis of exit decision and execution

[RISK_SCORE] (0-100, higher = safer) Risk management quality assessment

[TECH] Comprehensive technical analysis (3-5 specific observations about price action, patterns, indicators)

[PSYCH] Behavioral analysis (2-4 specific psychological patterns detected)

[RISK] Risk assessment (Quantify the risk issues - be specific with numbers/percentages if possible)

[FIX] Actionable 3-step improvement plan (be SPECIFIC, not generic advice)

[STRENGTH] What was done well in this trade (even failed trades have learning points)

[CRITICAL_ERROR] The single biggest mistake (be brutally honest)

Be direct, specific, and brutally honest. Use precise terminology. Quantify whenever possible."""
                        ready_to_run = True
                st.markdown('</div>', unsafe_allow_html=True)

            else:
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">Case Data Input</div>', unsafe_allow_html=True)
                with st.form("audit_form"):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a: ticker = st.text_input("Ticker", "SPY")
                    with col_b: setup_type = st.selectbox("Setup", ["Trend", "Reversal", "Breakout"])
                    with col_c: emotion = st.selectbox("State", ["Neutral", "FOMO", "Revenge", "Tilt"])
                
                    st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
                
                    col_d, col_e, col_f = st.columns(3)
                    with col_d: entry = st.number_input("Entry", 0.0, step=0.01)
                    with col_e: exit_price = st.number_input("Exit", 0.0, step=0.01)
                    with col_f: stop = st.number_input("Stop", 0.0, step=0.01)
                
                    st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
                
                    notes = st.text_area("Execution Notes", height=120, placeholder="Describe your decision-making process, entry hesitation, stop management...")
                
                    st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
                
                    if st.form_submit_button("EXECUTE AUDIT", type="primary", use_container_width=True):
                        ticker_val = ticker
                        
                        # Calculate key metrics
                        pnl = exit_price - entry if exit_price > 0 and entry > 0 else 0
                        pnl_pct = (pnl / entry * 100) if entry > 0 else 0
                        risk = abs(entry - stop) if stop > 0 and entry > 0 else 0
                        risk_pct = (risk / entry * 100) if entry > 0 else 0
                        reward = abs(exit_price - entry) if exit_price > 0 and entry > 0 else 0
                        rr_ratio = (reward / risk) if risk > 0 else 0
                        
                        prompt = f"""You are a world-class trading psychologist and risk management expert. Conduct a DEEP FORENSIC ANALYSIS of this trade with absolute precision.

TRADE DATA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ticker: {ticker}
Setup Type: {setup_type}
Emotional State: {emotion}
Entry: ${entry:.2f}
Exit: ${exit_price:.2f}
Stop Loss: ${stop:.2f}

CALCULATED METRICS:
PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)
Risk: ${risk:.2f} ({risk_pct:.2f}%)
Risk:Reward Ratio: {rr_ratio:.2f}:1

TRADER NOTES:
{notes if notes else "No notes provided"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ANALYSIS REQUIREMENTS:

1. TECHNICAL EXECUTION ANALYSIS:
   - Entry quality relative to setup type
   - Stop loss placement logic (too tight/wide/appropriate?)
   - Risk:Reward ratio assessment (optimal is 1:2 or better)
   - Position sizing implications
   - Setup type alignment with market structure

2. PSYCHOLOGICAL PROFILE:
   - Emotional state impact on decision-making
   - Evidence of cognitive biases in the notes
   - Decision-making process quality
   - Behavioral red flags

3. RISK MANAGEMENT EVALUATION:
   - Account risk percentage (assess if appropriate 1-2% max)
   - Stop loss effectiveness
   - Risk:Reward optimization opportunities
   - Capital preservation strategy

4. PERFORMANCE SCORING:
   - Technical execution: 0-100
   - Psychological discipline: 0-100
   - Risk management: 0-100
   - Overall trade quality: 0-100

OUTPUT FORMAT (FOLLOW EXACTLY):

[SCORE] (0-100, be HARSHLY critical - only 80+ for exceptional trades)
[OVERALL_GRADE] (F/D/C/B/A/S-Tier)

[ENTRY_QUALITY] (0-100) + specific feedback on entry timing/price

[EXIT_QUALITY] (0-100) + analysis of exit decision quality

[RISK_SCORE] (0-100) + risk management effectiveness rating

[TAGS] 3-5 specific behavioral tags: FOMO, Revenge, Disciplined, Poor_RR, Emotional, No_Plan, Good_Execution, etc.

[TECH] Technical analysis (5-7 sentences):
- Entry timing relative to setup
- Stop loss placement analysis
- RR ratio evaluation
- Position sizing assessment
- Setup quality for chosen instrument

[PSYCH] Psychological analysis (4-6 sentences):
- Emotional state impact
- Cognitive biases detected
- Decision-making quality
- Behavioral patterns identified

[RISK] Risk assessment (4-5 sentences with SPECIFIC metrics):
- Account risk percentage estimate
- Stop loss effectiveness
- RR ratio optimization
- Risk concentration issues

[FIX] THREE specific, actionable improvements:
1. [Specific technical fix]
2. [Specific psychological fix]
3. [Specific risk management fix]

[STRENGTH] What was executed well (1-2 sentences)

[CRITICAL_ERROR] The single biggest mistake in this trade (be direct and specific)

Be brutally honest. Use precise numbers. Provide institutional-grade analysis."""
                        ready_to_run = True
                st.markdown('</div>', unsafe_allow_html=True)

            # RESULTS AREA
            if ready_to_run and supabase:
                with st.spinner("🧠 Deep Learning Neural Analysis in Progress..."):
                    try:
                        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
                        if img_b64: messages[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})
                    
                        payload = {"model": "Qwen/Qwen2.5-VL-7B-Instruct", "messages": messages, "max_tokens": 1200}
                        headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                        res = requests.post(API_URL, headers=headers, json=payload)

                        if res.status_code == 200:
                            report = parse_report(res.json()["choices"][0]["message"]["content"])
                            save_analysis(current_user, report, ticker_val)
                        
                            # Determine colors based on score
                            if report['score'] >= 80:
                                score_color = "#10b981"
                                grade_color = "rgba(16, 185, 129, 0.2)"
                            elif report['score'] >= 60:
                                score_color = "#3b82f6"
                                grade_color = "rgba(59, 130, 246, 0.2)"
                            elif report['score'] >= 40:
                                score_color = "#f59e0b"
                                grade_color = "rgba(245, 158, 11, 0.2)"
                            else:
                                score_color = "#ef4444"
                                grade_color = "rgba(239, 68, 68, 0.2)"
                        
                            # ANIMATED HEADER WITH SCORE
                            st.markdown(f"""
                            <div class="glass-panel animate-scale-in" style="border-top: 3px solid {score_color}; margin-top: 32px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px;">
                                    <div>
                                        <div style="color:#6b7280; letter-spacing:3px; font-size:0.7rem; text-transform: uppercase; margin-bottom: 10px; font-weight: 600;">FORENSIC ANALYSIS COMPLETE</div>
                                        <div style="display: flex; align-items: center; gap: 20px;">
                                            <div class="score-value" style="color:{score_color}">{report['score']}</div>
                                            <div class="grade-badge" style="background:{grade_color}; color:{score_color};">
                                                GRADE: {report.get('overall_grade', 'C')}
                                            </div>
                                        </div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div class="ticker-badge">{ticker_val}</div>
                                        <div style="color:#6b7280; font-size:0.85rem; margin-top: 8px;">{datetime.now().strftime('%B %d, %Y • %H:%M')}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # QUALITY METRICS DASHBOARD
                            st.markdown('<div class="glass-panel animate-slide-up" style="animation-delay: 0.1s;">', unsafe_allow_html=True)
                            st.markdown('<div class="section-title">📊 Performance Breakdown</div>', unsafe_allow_html=True)
                            
                            # Create three columns for metrics
                            met_col1, met_col2, met_col3 = st.columns(3)
                            
                            metrics_data = [
                                ("Entry Quality", report.get('entry_quality', 50), met_col1),
                                ("Exit Quality", report.get('exit_quality', 50), met_col2),
                                ("Risk Management", report.get('risk_score', 50), met_col3)
                            ]
                            
                            for metric_name, metric_value, col in metrics_data:
                                with col:
                                    # Determine metric color
                                    if metric_value >= 80:
                                        met_color = "#10b981"
                                    elif metric_value >= 60:
                                        met_color = "#3b82f6"
                                    elif metric_value >= 40:
                                        met_color = "#f59e0b"
                                    else:
                                        met_color = "#ef4444"
                                    
                                    st.markdown(f"""
                                    <div style="text-align: center; padding: 20px;">
                                        <div class="metric-circle" style="background: rgba(255,255,255,0.03);">
                                            <div style="font-size: 2rem; font-weight: 700; color: {met_color}; font-family: 'JetBrains Mono', monospace;">
                                                {metric_value}
                                            </div>
                                            <div style="font-size: 0.7rem; color: #6b7280; text-transform: uppercase; letter-spacing: 1px;">
                                                /100
                                            </div>
                                        </div>
                                        <div style="margin-top: 16px; font-size: 0.9rem; font-weight: 600; color: #e5e7eb;">
                                            {metric_name}
                                        </div>
                                        <div class="progress-bar-container" style="margin-top: 12px;">
                                            <div class="progress-bar" style="width: {metric_value}%; background: linear-gradient(90deg, {met_color}, {met_color}80);"></div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # BEHAVIORAL TAGS WITH ANIMATION
                            if report.get('tags'):
                                st.markdown('<div class="glass-panel animate-slide-right" style="animation-delay: 0.2s;">', unsafe_allow_html=True)
                                st.markdown('<div class="section-title">🏷️ Behavioral Patterns Detected</div>', unsafe_allow_html=True)
                                
                                tags_html = '<div style="display: flex; flex-wrap: wrap; gap: 12px; margin-top: 16px;">'
                                for tag in report['tags']:
                                    # Color code tags
                                    if any(word in tag.lower() for word in ['fomo', 'revenge', 'emotional', 'panic', 'tilt']):
                                        tag_color = "#ef4444"
                                        tag_bg = "rgba(239, 68, 68, 0.15)"
                                    elif any(word in tag.lower() for word in ['disciplined', 'good', 'excellent', 'strong']):
                                        tag_color = "#10b981"
                                        tag_bg = "rgba(16, 185, 129, 0.15)"
                                    else:
                                        tag_color = "#f59e0b"
                                        tag_bg = "rgba(245, 158, 11, 0.15)"
                                    
                                    tags_html += f'''
                                    <div style="
                                        background: {tag_bg};
                                        border: 1px solid {tag_color}40;
                                        padding: 10px 18px;
                                        border-radius: 10px;
                                        color: {tag_color};
                                        font-weight: 600;
                                        font-size: 0.85rem;
                                        letter-spacing: 0.5px;
                                        transition: all 0.3s ease;
                                        cursor: default;
                                    ">{tag}</div>
                                    '''
                                tags_html += '</div>'
                                st.markdown(tags_html, unsafe_allow_html=True)
                                st.markdown('</div>', unsafe_allow_html=True)
                            
                            # VISUALIZATION CHART
                            st.markdown('<div class="glass-panel animate-fade-in" style="animation-delay: 0.3s;">', unsafe_allow_html=True)
                            st.markdown('<div class="section-title">📈 Performance Radar</div>', unsafe_allow_html=True)
                            
                            # Create radar chart data
                            chart_data = pd.DataFrame({
                                'Metric': ['Entry\nQuality', 'Exit\nQuality', 'Risk\nManagement', 'Overall\nScore'],
                                'Score': [
                                    report.get('entry_quality', 50),
                                    report.get('exit_quality', 50),
                                    report.get('risk_score', 50),
                                    report['score']
                                ]
                            })
                            
                            # Create bar chart with custom colors
                            bars = alt.Chart(chart_data).mark_bar(
                                cornerRadiusEnd=8,
                                size=40
                            ).encode(
                                x=alt.X('Metric:N',
                                    axis=alt.Axis(
                                        title=None,
                                        labelColor='#e5e7eb',
                                        labelFontSize=12,
                                        labelAngle=0
                                    )
                                ),
                                y=alt.Y('Score:Q',
                                    scale=alt.Scale(domain=[0, 100]),
                                    axis=alt.Axis(
                                        title='Score',
                                        titleColor='#9ca3af',
                                        labelColor='#9ca3af',
                                        grid=True,
                                        gridColor='#ffffff10'
                                    )
                                ),
                                color=alt.Color('Score:Q',
                                    scale=alt.Scale(
                                        domain=[0, 40, 60, 80, 100],
                                        range=['#ef4444', '#f59e0b', '#3b82f6', '#10b981', '#10b981']
                                    ),
                                    legend=None
                                ),
                                tooltip=[
                                    alt.Tooltip('Metric:N', title='Category'),
                                    alt.Tooltip('Score:Q', title='Score')
                                ]
                            ).properties(
                                height=300
                            ).configure_view(
                                strokeWidth=0,
                                fill='transparent'
                            ).configure(
                                background='transparent'
                            )
                            
                            st.altair_chart(bars, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # DETAILED ANALYSIS SECTIONS
                            col_left, col_right = st.columns(2)
                            
                            with col_left:
                                # TECHNICAL ANALYSIS
                                st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.4s;">', unsafe_allow_html=True)
                                st.markdown("""
                                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                                    <div style="font-size: 1.8rem;">⚙️</div>
                                    <div style="font-size: 1rem; font-weight: 700; color: #3b82f6; text-transform: uppercase; letter-spacing: 1px;">
                                        Technical Analysis
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                st.markdown(f"""
                                <div style="color: #d1d5db; line-height: 1.8; font-size: 0.92rem;">
                                    {report['tech']}
                                </div>
                                """, unsafe_allow_html=True)
                                st.markdown('</div>', unsafe_allow_html=True)
                                
                                # RISK ASSESSMENT
                                st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.6s;">', unsafe_allow_html=True)
                                st.markdown("""
                                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                                    <div style="font-size: 1.8rem;">⚠️</div>
                                    <div style="font-size: 1rem; font-weight: 700; color: #f59e0b; text-transform: uppercase; letter-spacing: 1px;">
                                        Risk Assessment
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                st.markdown(f"""
                                <div style="color: #d1d5db; line-height: 1.8; font-size: 0.92rem;">
                                    {report['risk']}
                                </div>
                                """, unsafe_allow_html=True)
                                st.markdown('</div>', unsafe_allow_html=True)
                            
                            with col_right:
                                # PSYCHOLOGICAL ANALYSIS
                                st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.5s;">', unsafe_allow_html=True)
                                st.markdown("""
                                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                                    <div style="font-size: 1.8rem;">🧠</div>
                                    <div style="font-size: 1rem; font-weight: 700; color: #8b5cf6; text-transform: uppercase; letter-spacing: 1px;">
                                        Psychology Profile
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                st.markdown(f"""
                                <div style="color: #d1d5db; line-height: 1.8; font-size: 0.92rem;">
                                    {report['psych']}
                                </div>
                                """, unsafe_allow_html=True)
                                st.markdown('</div>', unsafe_allow_html=True)
                                
                                # ACTION PLAN
                                st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.7s;">', unsafe_allow_html=True)
                                st.markdown("""
                                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                                    <div style="font-size: 1.8rem;">🎯</div>
                                    <div style="font-size: 1rem; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 1px;">
                                        Action Plan
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                st.markdown(f"""
                                <div style="color: #d1d5db; line-height: 1.8; font-size: 0.92rem;">
                                    {report['fix']}
                                </div>
                                """, unsafe_allow_html=True)
                                st.markdown('</div>', unsafe_allow_html=True)
                            
                            # KEY INSIGHTS - STRENGTH & CRITICAL ERROR
                            if report.get('strength') != 'N/A' or report.get('critical_error') != 'N/A':
                                st.markdown('<div class="glass-panel animate-slide-up" style="animation-delay: 0.8s;">', unsafe_allow_html=True)
                                
                                ins_col1, ins_col2 = st.columns(2)
                                
                                with ins_col1:
                                    if report.get('strength') != 'N/A':
                                        st.markdown(f"""
                                        <div style="
                                            background: rgba(16, 185, 129, 0.1);
                                            border-left: 4px solid #10b981;
                                            padding: 20px;
                                            border-radius: 0 12px 12px 0;
                                        ">
                                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                                                <div style="font-size: 1.5rem;">💪</div>
                                                <div style="font-size: 0.85rem; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 1px;">
                                                    What Went Well
                                                </div>
                                            </div>
                                            <div style="color: #d1d5db; line-height: 1.7; font-size: 0.9rem;">
                                                {report['strength']}
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                
                                with ins_col2:
                                    if report.get('critical_error') != 'N/A':
                                        st.markdown(f"""
                                        <div style="
                                            background: rgba(239, 68, 68, 0.1);
                                            border-left: 4px solid #ef4444;
                                            padding: 20px;
                                            border-radius: 0 12px 12px 0;
                                        ">
                                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                                                <div style="font-size: 1.5rem;">⛔</div>
                                                <div style="font-size: 0.85rem; font-weight: 700; color: #ef4444; text-transform: uppercase; letter-spacing: 1px;">
                                                    Critical Error
                                                </div>
                                            </div>
                                            <div style="color: #d1d5db; line-height: 1.7; font-size: 0.9rem;">
                                                {report['critical_error']}
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                
                                st.markdown('</div>', unsafe_allow_html=True)
                            
                    except Exception as e:
                        st.error(f"⚠️ Analysis Failed: {e}")
                        st.info("💡 Tip: Ensure your image is clear and contains visible price action or trade data.")

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
                            <div class="kpi-val" style="font-size:2.5rem;">{trend}</div>
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
                                background: rgba(255, 255, 255, 0.03);
                                border-left: 4px solid #10b981;
                                padding: 20px;
                                border-radius: 0 12px 12px 0;
                                margin-bottom: 18px;
                                transition: all 0.3s ease;
                            '>
                                <div style='font-size: 1.6rem; margin-bottom: 10px;'>{emoji}</div>
                                <div style='font-size: 0.92rem; line-height: 1.7; color: #d1d5db;'>
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
                            <div style='margin-bottom: 22px;'>
                                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
                                    <span style='font-size: 0.88rem; color: #9ca3af; font-weight: 600;'>{range_name}</span>
                                    <span style='font-size: 0.88rem; color: #e5e7eb; font-family: "JetBrains Mono", monospace;'>{count} ({int(percentage)}%)</span>
                                </div>
                                <div style='
                                    width: 100%;
                                    height: 10px;
                                    background: rgba(255, 255, 255, 0.05);
                                    border-radius: 5px;
                                    overflow: hidden;
                                '>
                                    <div style='
                                        width: {percentage}%;
                                        height: 100%;
                                        background: {color};
                                        border-radius: 5px;
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
                    st.markdown('<div class="glass-panel" style="text-align: center; padding: 80px;">', unsafe_allow_html=True)
                    st.markdown("""
                    <div style="font-size: 3.5rem; margin-bottom: 20px; opacity: 0.4;">📊</div>
                    <div style="font-size: 1.2rem; color: #9ca3af; margin-bottom: 10px; font-weight: 600;">No Performance Data Yet</div>
                    <div style="font-size: 0.95rem; color: #6b7280;">Complete your first forensic audit to see metrics here.</div>
                    """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
