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
import uuid  # Add this to generate unique filenames

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
            # Using better vision model
            API_URL = "https://router.huggingface.co/v1/chat/completions"
            
    except Exception as e:
        st.error(f"⚠️ Configuration Error: {e}")
        st.stop()

# ==========================================
# 2. PREMIUM DARK THEME CSS (UNCHANGED)
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
# 3. IMPROVED HELPER FUNCTIONS
# ==========================================
def clean_text(text):
    """Clean text but preserve structure"""
    # Remove HTML/code artifacts
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'```[\s\S]*?```', '', text)
    return text.strip()

def validate_score(score, min_val=0, max_val=100):
    """Validate and clamp scores"""
    try:
        score = int(score)
        return max(min_val, min(max_val, score))
    except:
        return 50  # Default middle score if parsing fails

def parse_report(text):
    """Enhanced parsing with validation"""
    sections = { 
        "score": 50,  # Default to middle score
        "tags": [], 
        "tech": "Analysis pending...", 
        "psych": "Analysis pending...", 
        "risk": "Analysis pending...", 
        "fix": "Analysis pending...",
        "overall_grade": "C",
        "entry_quality": 50,
        "exit_quality": 50,
        "risk_score": 50,
        "strength": "Analyzing...",
        "critical_error": "Analyzing..."
    }
    
    # Clean text first
    text = clean_text(text)
    
    # Extract and validate score
    score_match = re.search(r'\[SCORE\]\s*(\d+)', text, re.IGNORECASE)
    if score_match: 
        sections['score'] = validate_score(score_match.group(1))
    
    # Extract grade
    grade_match = re.search(r'\[OVERALL_GRADE\]\s*([A-FS][\-\+]?(?:-Tier)?)', text, re.IGNORECASE)
    if grade_match: 
        sections['overall_grade'] = grade_match.group(1).upper()
    
    # Extract and validate quality scores
    entry_match = re.search(r'\[ENTRY_QUALITY\]\s*(\d+)', text, re.IGNORECASE)
    if entry_match: 
        sections['entry_quality'] = validate_score(entry_match.group(1))
    
    exit_match = re.search(r'\[EXIT_QUALITY\]\s*(\d+)', text, re.IGNORECASE)
    if exit_match: 
        sections['exit_quality'] = validate_score(exit_match.group(1))
    
    risk_score_match = re.search(r'\[RISK_SCORE\]\s*(\d+)', text, re.IGNORECASE)
    if risk_score_match: 
        sections['risk_score'] = validate_score(risk_score_match.group(1))
    
    # Extract tags
    tags_match = re.search(r'\[TAGS\](.*?)(?=\[|$)', text, re.DOTALL | re.IGNORECASE)
    if tags_match:
        raw = tags_match.group(1).replace('[', '').replace(']', '').split(',')
        sections['tags'] = [t.strip() for t in raw if t.strip() and len(t.strip()) > 2][:10]  # Limit to 10 tags
    
    # Extract text sections with better patterns
    patterns = {
        "tech": r"\[TECH\](.*?)(?=\[PSYCH\]|\[RISK\]|\[FIX\]|\[STRENGTH\]|\[CRITICAL_ERROR\]|$)",
        "psych": r"\[PSYCH\](.*?)(?=\[RISK\]|\[FIX\]|\[STRENGTH\]|\[CRITICAL_ERROR\]|$)",
        "risk": r"\[RISK\](.*?)(?=\[FIX\]|\[STRENGTH\]|\[CRITICAL_ERROR\]|$)",
        "fix": r"\[FIX\](.*?)(?=\[STRENGTH\]|\[CRITICAL_ERROR\]|$)",
        "strength": r"\[STRENGTH\](.*?)(?=\[CRITICAL_ERROR\]|$)",
        "critical_error": r"\[CRITICAL_ERROR\](.*?)$"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match: 
            content = match.group(1).strip()
            # Filter out any remaining HTML/code
            content = re.sub(r'<[^>]+>', '', content)
            content = re.sub(r'```[\s\S]*?```', '', content)
            if len(content) > 10:  # Only update if substantial content
                sections[key] = content
    
    return sections

def save_analysis(user_id, data, ticker_symbol="UNK", img_url=None):  # Added img_url param
    if not supabase: return
    try:
        payload = {
            "user_id": user_id,
            "ticker": ticker_symbol,
            "score": data.get('score', 50),
            "mistake_tags": data.get('tags', []),
            "technical_analysis": data.get('tech', ''),
            "psych_analysis": data.get('psych', ''),
            "risk_analysis": data.get('risk', ''),
            "fix_action": data.get('fix', ''),
            "image_url": img_url  # Save the link
        }
        supabase.table("trades").insert(payload).execute()
    except Exception as e:
        st.error(f"Database error: {e}")

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
    
    return insights if insights else ["✅ Performance metrics within normal parameters."]

def upload_image_to_supabase(file_obj):
    """Uploads stream/buffer to Supabase Storage and returns public URL"""
    if not supabase: return None
    
    try:
        # Create unique filename
        file_ext = file_obj.name.split('.')[-1]
        file_name = f"{st.session_state['user']}/{uuid.uuid4()}.{file_ext}"
        
        # Reset pointer to start of file
        file_obj.seek(0)
        file_bytes = file_obj.read()
        
        # Upload
        bucket_name = "trade_images"  # Must match what you created in Supabase
        supabase.storage.from_(bucket_name).upload(
            file=file_bytes,
            path=file_name,
            file_options={"content-type": f"image/{file_ext}"}
        )
        
        # Get Public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
        return public_url
    except Exception as e:
        st.error(f"Image Upload Failed: {e}")
        return None

def call_vision_api(prompt, img_b64, max_retries=2):
    """Call vision API with retry logic and better error handling"""
    for attempt in range(max_retries):
        try:
            messages = [
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                    ]
                }
            ]
            
            payload = {
                "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                "messages": messages,
                "max_tokens": 1500,
                "temperature": 0.3,  # Lower temperature for more consistent output
                "top_p": 0.95
            }
            
            headers = {
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json"
            }
            
            res = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            
            if res.status_code == 200:
                content = res.json()["choices"][0]["message"]["content"]
                # Validate response isn't just code/HTML
                if '<div' in content or '<html' in content or '```' in content[:100]:
                    if attempt < max_retries - 1:
                        continue  # Retry
                    else:
                        raise ValueError("Model returning code instead of analysis")
                return content
            else:
                raise Exception(f"API returned {res.status_code}: {res.text[:200]}")
                
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            continue
    
    raise Exception("Max retries exceeded")

# ==========================================
# 4. MAIN APP LOGIC
# ==========================================

# --- LOGIN VIEW (UNCHANGED) ---
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
            <span class="nav-link {'active' if current_page == 'portfolio' else ''}" id="nav_portfolio">Portfolio</span>
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
    document.getElementById('nav_portfolio').onclick = function() {{
        window.location.href = '?page=portfolio';
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
    if st.session_state["current_page"] == "portfolio":
        # PORTFOLIO ANALYSIS PAGE - COMPLETELY SEPARATE
        st.markdown('<div class="glass-panel" style="text-align: center; padding: 60px 40px; margin-bottom: 40px;">', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size: 3.5rem; margin-bottom: 20px;">📊</div>
        <div style="font-size: 2rem; font-weight: 700; margin-bottom: 16px; background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Portfolio Health Analyzer
        </div>
        <div style="font-size: 1rem; color: #9ca3af; max-width: 700px; margin: 0 auto; line-height: 1.7;">
            Comprehensive analysis of your entire investment portfolio. Upload screenshots or PDFs, get detailed risk assessment, concentration analysis, and restructuring recommendations.
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # UPLOAD SECTION
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📂 Upload Portfolio Data</div>', unsafe_allow_html=True)
        
        col_upload_left, col_upload_right = st.columns([1.2, 1])
        
        with col_upload_left:
            st.markdown("""
            <div style="margin-bottom: 24px;">
                <div style="font-size: 1.1rem; font-weight: 600; color: #e5e7eb; margin-bottom: 12px;">📸 Upload Portfolio Screenshot or PDF</div>
                <div style="font-size: 0.9rem; color: #9ca3af; line-height: 1.6;">
                    Upload screenshots from your broker app, portfolio tracker, or export PDFs. We support all major brokers including Zerodha, Groww, Upstox, Angel One, etc.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            portfolio_file = st.file_uploader(
                "Upload Portfolio Screenshot or PDF", 
                type=["png", "jpg", "jpeg", "pdf"], 
                label_visibility="collapsed",
                key="portfolio_upload_main",
                help="Upload your full portfolio view showing all positions and P&L"
            )
            
            if portfolio_file:
                if portfolio_file.type == "application/pdf":
                    st.success("✅ PDF uploaded successfully!")
                    st.info("📄 PDF analysis extracts: Total P&L, Position count, Individual holdings")
                else:
                    st.success("✅ Image uploaded successfully!")
                    st.markdown('<div style="margin-top: 20px; border-radius: 12px; overflow: hidden; border: 2px solid rgba(16, 185, 129, 0.3);">', unsafe_allow_html=True)
                    st.image(portfolio_file, use_column_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
        
        with col_upload_right:
            st.markdown("""
            <div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 20px; border-radius: 0 12px 12px 0; margin-bottom: 20px;">
                <div style="font-size: 1rem; font-weight: 600; color: #10b981; margin-bottom: 12px;">💡 What We Analyze</div>
                <div style="font-size: 0.85rem; color: #d1d5db; line-height: 1.7;">
                    • Overall portfolio P&L and drawdown<br>
                    • Position sizing discipline<br>
                    • Diversification vs concentration<br>
                    • Stop loss implementation<br>
                    • Leverage/margin risks<br>
                    • Sector exposure analysis<br>
                    • Crisis position identification<br>
                    • Recovery timeline estimation
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; padding: 20px; border-radius: 0 12px 12px 0;">
                <div style="font-size: 1rem; font-weight: 600; color: #f59e0b; margin-bottom: 12px;">⚠️ Manual Input Recommended</div>
                <div style="font-size: 0.85rem; color: #d1d5db; line-height: 1.7;">
                    For best accuracy, provide your portfolio data manually below. AI image analysis can miss details in complex portfolio views.
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # MANUAL INPUT SECTION
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📝 Manual Portfolio Data (Highly Recommended)</div>', unsafe_allow_html=True)
        
        with st.form("portfolio_input_form"):
            st.markdown("**Core Portfolio Metrics**")
            col_m1, col_m2, col_m3 = st.columns(3)
            
            with col_m1:
                portfolio_total_invested = st.number_input(
                    "Total Invested (₹)", 
                    min_value=0.0, 
                    step=10000.0, 
                    format="%.2f",
                    help="Total capital you've invested across all positions"
                )
            
            with col_m2:
                portfolio_current_value = st.number_input(
                    "Current Value (₹)", 
                    min_value=0.0, 
                    step=10000.0, 
                    format="%.2f",
                    help="Current market value of your entire portfolio"
                )
            
            with col_m3:
                portfolio_num_positions = st.number_input(
                    "Number of Positions", 
                    min_value=1, 
                    max_value=500, 
                    value=10,
                    help="How many different stocks/assets you hold"
                )
            
            st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
            st.markdown("**Position Details (Optional but Helpful)**")
            
            col_m4, col_m5 = st.columns(2)
            
            with col_m4:
                portfolio_largest_loss = st.text_input(
                    "Worst Position", 
                    placeholder="e.g., ADANIPOWER -₹45,000 (-277%)",
                    help="Your biggest losing position with amount and %"
                )
                
                portfolio_largest_gain = st.text_input(
                    "Best Position", 
                    placeholder="e.g., TCS +₹85,000 (+35%)",
                    help="Your biggest winning position with amount and %"
                )
            
            with col_m5:
                portfolio_crisis_stocks = st.text_input(
                    "Crisis Positions (>30% loss)", 
                    placeholder="e.g., ADANIPOWER, AARTIIND, YESBANK",
                    help="List stocks with major losses, comma-separated"
                )
                
                portfolio_top_holdings = st.text_input(
                    "Top 3 Holdings by %", 
                    placeholder="e.g., RELIANCE 15%, INFY 12%, TCS 10%",
                    help="Your largest positions by portfolio weight"
                )
            
            st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
            st.markdown("**Additional Context**")
            
            col_m6, col_m7 = st.columns(2)
            
            with col_m6:
                portfolio_sectors = st.text_input(
                    "Main Sectors", 
                    placeholder="e.g., IT 40%, Banking 25%, Pharma 15%",
                    help="Your sector allocation if known"
                )
                
                portfolio_strategy = st.selectbox(
                    "Investment Approach",
                    ["Long-term investing", "Swing trading", "Day trading", "Mixed approach", "No clear strategy"],
                    help="How do you approach the market?"
                )
            
            with col_m7:
                portfolio_time_horizon = st.selectbox(
                    "Time Horizon",
                    ["< 6 months", "6-12 months", "1-2 years", "2-5 years", "5+ years", "No specific timeline"],
                    help="How long do you plan to hold?"
                )
                
                portfolio_leverage = st.selectbox(
                    "Leverage/Margin Usage",
                    ["No leverage (cash only)", "Margin < 25%", "Margin 25-50%", "Margin > 50%", "Futures/Options", "Not sure"],
                    help="Are you trading with borrowed money?"
                )
            
            st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
            
            portfolio_description = st.text_area(
                "Additional Context (Very Important!)", 
                height=120, 
                placeholder="""Describe your situation:
• How did you build this portfolio?
• Any specific problems you're facing?
• Previous trading experience?
• Risk management practices?
• Stop loss usage?
• Why are you seeking analysis?""",
                help="More context = better, more personalized analysis"
            )
            
            st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
            
            submitted = st.form_submit_button("🔬 RUN COMPREHENSIVE PORTFOLIO ANALYSIS", type="primary", use_container_width=True)
            
            if submitted:
                # Validation
                if portfolio_total_invested == 0 or portfolio_current_value == 0:
                    st.error("⚠️ Please enter both Total Invested and Current Value for analysis.")
                else:
                    # Calculate metrics
                    total_pnl = portfolio_current_value - portfolio_total_invested
                    total_pnl_pct = (total_pnl / portfolio_total_invested * 100) if portfolio_total_invested > 0 else 0
                    
                    # Prepare image if uploaded
                    img_b64 = None
                    stored_portfolio_image_url = None  # Initialize URL variable
                    if portfolio_file and portfolio_file.type != "application/pdf":
                        try:
                            # Upload to Supabase first
                            with st.spinner("Uploading portfolio evidence to secure vault..."):
                                stored_portfolio_image_url = upload_image_to_supabase(portfolio_file)
                            
                            # Process for AI analysis
                            image = Image.open(portfolio_file)
                            max_size = (1920, 1080)
                            image.thumbnail(max_size, Image.Resampling.LANCZOS)
                            buf = io.BytesIO()
                            image.save(buf, format="PNG", optimize=True)
                            img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                        except:
                            st.warning("Could not process image, using manual data only")
                    
                    # Build comprehensive portfolio context
                    portfolio_context = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPREHENSIVE PORTFOLIO DATA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PORTFOLIO OVERVIEW:
Total Invested: ₹{portfolio_total_invested:,.2f}
Current Value: ₹{portfolio_current_value:,.2f}
Total P&L: ₹{total_pnl:,.2f} ({total_pnl_pct:+.2f}%)
Number of Positions: {portfolio_num_positions}

POSITION DETAILS:
Worst Position: {portfolio_largest_loss if portfolio_largest_loss else "Not provided"}
Best Position: {portfolio_largest_gain if portfolio_largest_gain else "Not provided"}
Crisis Stocks: {portfolio_crisis_stocks if portfolio_crisis_stocks else "None listed"}
Top Holdings: {portfolio_top_holdings if portfolio_top_holdings else "Not provided"}

PORTFOLIO STRUCTURE:
Sector Allocation: {portfolio_sectors if portfolio_sectors else "Not provided"}
Strategy: {portfolio_strategy}
Time Horizon: {portfolio_time_horizon}
Leverage Usage: {portfolio_leverage}

TRADER CONTEXT:
{portfolio_description if portfolio_description else "No additional context provided"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THIS IS GROUND TRUTH DATA. Analyze based on these exact values.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
                    
                    # COMPREHENSIVE PORTFOLIO ANALYSIS PROMPT
                    portfolio_prompt = f"""You are a Senior Portfolio Manager with 30+ years experience managing institutional portfolios. You specialize in retail portfolio risk assessment and restructuring.

{portfolio_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPREHENSIVE PORTFOLIO ANALYSIS FRAMEWORK:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. PORTFOLIO HEALTH ASSESSMENT:
   Analyze the overall portfolio drawdown of {total_pnl_pct:.2f}%
   - Is this acceptable, concerning, or catastrophic?
   - Current value vs invested (recovery difficulty)
   - Number of positions ({portfolio_num_positions}) - over/under diversified?
   - Win/loss distribution based on provided positions

2. RISK MANAGEMENT DEEP DIVE:
   - Position sizing: With {portfolio_num_positions} positions, average should be ~{100/portfolio_num_positions if portfolio_num_positions > 0 else 0:.1f}% each
   - Concentration risk: Top holdings analysis
   - Stop loss discipline: Evidence from crisis positions
   - Leverage assessment: {portfolio_leverage} - flag if dangerous
   - Sector concentration: {portfolio_sectors if portfolio_sectors else "Unknown"} - any overexposure?

3. CRISIS IDENTIFICATION:
   Crisis Positions: {portfolio_crisis_stocks if portfolio_crisis_stocks else "None specified"}
   Worst Position: {portfolio_largest_loss if portfolio_largest_loss else "Not provided"}
   - Any positions >100% loss? (leverage emergency)
   - Multiple positions >50% loss? (exit discipline failure)
   - Recovery likelihood for crisis positions

4. BEHAVIORAL PATTERN ANALYSIS:
   Strategy: {portfolio_strategy}
   Time Horizon: {portfolio_time_horizon}
   Context: {portfolio_description[:200] if portfolio_description else "Minimal"}
   - Holding losers too long?
   - FOMO buying at peaks?
   - Averaging down mistakes?
   - Emotional vs. systematic approach?

5. PORTFOLIO STRUCTURE EVALUATION:
   - {portfolio_num_positions} positions: Is this manageable?
   - Sector allocation quality
   - Market cap diversification
   - Correlation risks
   - Appropriate for stated time horizon?

SEVERITY CLASSIFICATION (CRITICAL):

Drawdown >50%: CATASTROPHIC EMERGENCY (Score: 0-5, Grade: F)
Drawdown 30-50%: SEVERE CRISIS (Score: 5-15, Grade: F)
Drawdown 20-30%: MAJOR PROBLEM (Score: 15-30, Grade: D)
Drawdown 10-20%: CONCERNING (Score: 30-50, Grade: C)
Drawdown 5-10%: MINOR ISSUE (Score: 50-70, Grade: B)
Drawdown 0-5%: ACCEPTABLE (Score: 70-85, Grade: A)
Profit >0%: GOOD (Score: 85-100, Grade: A/S-Tier)

SPECIAL CONSIDERATIONS:
- Leverage usage increases severity by one level
- >20 positions increases severity (over-diversification)
- Multiple crisis stocks increases severity
- No clear strategy increases severity

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY OUTPUT FORMAT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[SCORE] <0-100 based on drawdown and risk factors>

[OVERALL_GRADE] <F/D/C/B/A/S-Tier based on severity table>

[ENTRY_QUALITY] <0-100: Average entry timing quality across portfolio>

[EXIT_QUALITY] <0-100: Exit discipline - stop loss usage, holding losers?>

[RISK_SCORE] <0-100: Portfolio risk management quality - MUST be 0-10 if crisis>

[TAGS] <Choose 5-8 relevant tags: Portfolio_Crisis, Overleveraged, No_Stops, Concentration_Risk, Over_Diversified, Sector_Concentration, Multiple_Losers, Exit_Failure, Hope_Trading, Good_Diversification, Disciplined_Stops, etc.>

[TECH] PORTFOLIO STRUCTURE ANALYSIS:

Portfolio Metrics: ₹{portfolio_total_invested:,.0f} invested → ₹{portfolio_current_value:,.0f} current = ₹{total_pnl:,.0f} ({total_pnl_pct:+.2f}%)

Position Count Analysis: {portfolio_num_positions} positions. [Is this optimal? Too many to manage? Too few for diversification?]

Top Holdings Impact: {portfolio_top_holdings if portfolio_top_holdings else "Not provided"}. [Concentration risk assessment]

Sector Exposure: {portfolio_sectors if portfolio_sectors else "Unknown"}. [Any dangerous concentration?]

Crisis Positions: {portfolio_crisis_stocks if portfolio_crisis_stocks else "None listed"}. [Recovery likelihood? Should close?]

[Provide specific technical commentary on portfolio construction, position sizing, diversification quality, and structural issues]

[PSYCH] BEHAVIORAL PORTFOLIO PSYCHOLOGY:

Trading Approach: {portfolio_strategy} with {portfolio_time_horizon} horizon. [Is behavior aligned with stated goals?]

Decision-Making Patterns: [Based on crisis positions, worst loss, and description, analyze: Are they holding losers too long? Cutting winners early? FOMO buying? Revenge trading? Averaging down? Emotional attachment?]

Discipline Assessment: [Evidence of trading plan? Stop loss usage? Position sizing rules? Or hope-based investing?]

{portfolio_leverage} - [If using leverage, address the psychological impact and risk]

[Analyze the trader's MINDSET and behavioral patterns visible in portfolio structure]

[RISK] COMPREHENSIVE RISK ASSESSMENT:

Portfolio Drawdown: {total_pnl_pct:.2f}% = [CATASTROPHIC/SEVERE/MAJOR/CONCERNING/MINOR/ACCEPTABLE]

Position Sizing: Avg {100/portfolio_num_positions if portfolio_num_positions > 0 else 0:.1f}% per position with {portfolio_num_positions} holdings. [Assessment of sizing discipline]

Leverage Risk: {portfolio_leverage}. [If using margin/futures/options, this is RED FLAG - quantify danger]

Concentration Risk: [Based on top holdings and sector allocation, assess if too concentrated]

Stop Loss Implementation: [Based on crisis positions and description, are stops used? If not, bleeding continues]

Recovery Mathematics: To recover {abs(total_pnl_pct):.1f}% loss requires {abs(total_pnl_pct)/(100+total_pnl_pct)*100 if total_pnl_pct < 0 else 0:.1f}% gain. Timeline: [Estimate 6mo/12mo/18mo/24mo+]

[Provide specific risk metrics and quantified danger assessment]

[FIX] PORTFOLIO RESTRUCTURING ROADMAP:

IMMEDIATE (Next 24-48 hours):
1. [Most urgent action - usually investigate leverage, close worst positions, or stop new trades]
2. [Second priority - typically implement stops or hedge risks]
3. [Third priority - usually calculate actual losses and set recovery plan]

SHORT TERM (1-4 weeks):
1. [Position reduction/consolidation - specific numbers]
2. [Stop loss implementation - specific % levels]
3. [Sector rebalancing if needed]
4. [Close beyond-recovery positions]

LONG TERM (1-6 months):
1. [Complete portfolio restructuring strategy]
2. [Education/skill development needs]
3. [New risk management framework]
4. [Psychology reset and habit building]

Position Sizing Rule Going Forward: Risk no more than 1-2% per position (₹{portfolio_total_invested*0.02:,.0f} max per trade)

[STRENGTH] [Find something positive even in disaster: diversification across sectors? at least some winners? closed positions before -100%? still has capital to recover?]

[CRITICAL_ERROR] [The single biggest portfolio-level mistake: usually no stops, concentration, leverage, or holding losers. Be specific with numbers/names]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES:
- If drawdown >30%, score MUST be 0-15, grade F
- If leverage + crisis, increase severity dramatically
- Be specific with numbers from provided data
- Recovery timeline must be realistic based on drawdown
- If crisis positions listed, address them specifically by name
- Focus on PORTFOLIO MANAGEMENT not stock picking
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
                    
                    # Run analysis
                    with st.spinner("🔬 Running Deep Portfolio Analysis... This may take 30-60 seconds..."):
                        try:
                            messages = [{"role": "user", "content": [{"type": "text", "text": portfolio_prompt}]}]
                            if img_b64:
                                messages[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})
                            
                            payload = {
                                "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                                "messages": messages,
                                "max_tokens": 2000,
                                "temperature": 0.3
                            }
                            
                            headers = {
                                "Authorization": f"Bearer {HF_TOKEN}",
                                "Content-Type": "application/json"
                            }
                            
                            res = requests.post(API_URL, headers=headers, json=payload, timeout=90)
                            
                            if res.status_code == 200:
                                raw_response = res.json()["choices"][0]["message"]["content"]
                                report = parse_report(raw_response)
                                
                                # Save to database with image URL
                                save_analysis(current_user, report, "PORTFOLIO", stored_portfolio_image_url)
                                
                                # Display results with same beautiful UI as trade analysis
                                # [All the visualization code from trade analysis - reuse the same display logic]
                                
                                # Determine colors
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
                                
                                # HEADER
                                st.markdown(f"""
                                <div class="glass-panel animate-scale-in" style="border-top: 3px solid {score_color}; margin-top: 32px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px;">
                                        <div>
                                            <div style="color:#6b7280; letter-spacing:3px; font-size:0.7rem; text-transform: uppercase; margin-bottom: 10px; font-weight: 600;">PORTFOLIO ANALYSIS COMPLETE</div>
                                            <div style="display: flex; align-items: center; gap: 20px;">
                                                <div class="score-value" style="color:{score_color}">{report['score']}</div>
                                                <div class="grade-badge" style="background:{grade_color}; color:{score_color};">
                                                    GRADE: {report.get('overall_grade', 'C')}
                                                </div>
                                            </div>
                                        </div>
                                        <div style="text-align: right;">
                                            <div class="ticker-badge">PORTFOLIO</div>
                                            <div style="color:#6b7280; font-size:0.85rem; margin-top: 8px;">{datetime.now().strftime('%B %d, %Y • %H:%M')}</div>
                                            <div style="color: {score_color}; font-size:1.1rem; font-weight: 700; margin-top: 8px; font-family: 'JetBrains Mono', monospace;">
                                                {total_pnl_pct:+.2f}%
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # METRICS
                                st.markdown('<div class="glass-panel animate-slide-up" style="animation-delay: 0.1s;">', unsafe_allow_html=True)
                                st.markdown('<div class="section-title">📊 Portfolio Health Metrics</div>', unsafe_allow_html=True)
                                
                                met_col1, met_col2, met_col3 = st.columns(3)
                                
                                metrics_data = [
                                    ("Position Entry Quality", report.get('entry_quality', 50), met_col1),
                                    ("Exit Discipline", report.get('exit_quality', 50), met_col2),
                                    ("Risk Management", report.get('risk_score', 50), met_col3)
                                ]
                                
                                for metric_name, metric_value, col in metrics_data:
                                    with col:
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
                                
                                # TAGS
                                if report.get('tags'):
                                    st.markdown('<div class="glass-panel animate-slide-right" style="animation-delay: 0.2s;">', unsafe_allow_html=True)
                                    st.markdown('<div class="section-title">🏷️ Portfolio Risk Factors</div>', unsafe_allow_html=True)
                                    
                                    tags_html = '<div style="display: flex; flex-wrap: wrap; gap: 12px; margin-top: 16px;">'
                                    for tag in report['tags']:
                                        if any(word in tag.lower() for word in ['crisis', 'catastrophic', 'emergency', 'overleveraged', 'failure']):
                                            tag_color = "#ef4444"
                                            tag_bg = "rgba(239, 68, 68, 0.15)"
                                        elif any(word in tag.lower() for word in ['good', 'disciplined', 'strong', 'excellent']):
                                            tag_color = "#10b981"
                                            tag_bg = "rgba(16, 185, 129, 0.15)"
                                        else:
                                            tag_color = "#f59e0b"
                                            tag_bg = "rgba(245, 158, 11, 0.15)"
                                        
                                        tags_html += f'<div style="background: {tag_bg}; border: 1px solid {tag_color}40; padding: 10px 18px; border-radius: 10px; color: {tag_color}; font-weight: 600; font-size: 0.85rem; letter-spacing: 0.5px;">{tag}</div>'
                                    tags_html += '</div>'
                                    st.markdown(tags_html, unsafe_allow_html=True)
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                # DETAILED ANALYSIS
                                col_left, col_right = st.columns(2)
                                
                                with col_left:
                                    st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.4s;">', unsafe_allow_html=True)
                                    st.markdown("""
                                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                                        <div style="font-size: 1.8rem;">📊</div>
                                        <div style="font-size: 1rem; font-weight: 700; color: #3b82f6; text-transform: uppercase; letter-spacing: 1px;">
                                            Portfolio Structure
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown(f"""
                                    <div style="color: #d1d5db; line-height: 1.8; font-size: 0.92rem;">
                                        {report['tech']}
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.6s;">', unsafe_allow_html=True)
                                    st.markdown("""
                                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                                        <div style="font-size: 1.8rem;">⚠️</div>
                                        <div style="font-size: 1rem; font-weight: 700; color: #f59e0b; text-transform: uppercase; letter-spacing: 1px;">
                                            Risk Analysis
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
                                    st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.5s;">', unsafe_allow_html=True)
                                    st.markdown("""
                                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                                        <div style="font-size: 1.8rem;">🧠</div>
                                        <div style="font-size: 1rem; font-weight: 700; color: #8b5cf6; text-transform: uppercase; letter-spacing: 1px;">
                                            Behavioral Analysis
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown(f"""
                                    <div style="color: #d1d5db; line-height: 1.8; font-size: 0.92rem;">
                                        {report['psych']}
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.7s;">', unsafe_allow_html=True)
                                    st.markdown("""
                                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                                        <div style="font-size: 1.8rem;">🎯</div>
                                        <div style="font-size: 1rem; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 1px;">
                                            Recovery Roadmap
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown(f"""
                                    <div style="color: #d1d5db; line-height: 1.8; font-size: 0.92rem;">
                                        {report['fix']}
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                # KEY INSIGHTS
                                if report.get('strength') or report.get('critical_error'):
                                    st.markdown('<div class="glass-panel animate-slide-up" style="animation-delay: 0.8s;">', unsafe_allow_html=True)
                                    
                                    ins_col1, ins_col2 = st.columns(2)
                                    
                                    with ins_col1:
                                        if report.get('strength'):
                                            st.markdown(f"""
                                            <div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 20px; border-radius: 0 12px 12px 0;">
                                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                                                    <div style="font-size: 1.5rem;">💪</div>
                                                    <div style="font-size: 0.85rem; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 1px;">
                                                        What's Working
                                                    </div>
                                                </div>
                                                <div style="color: #d1d5db; line-height: 1.7; font-size: 0.9rem;">
                                                    {report['strength']}
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                    
                                    with ins_col2:
                                        if report.get('critical_error'):
                                            st.markdown(f"""
                                            <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 20px; border-radius: 0 12px 12px 0;">
                                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                                                    <div style="font-size: 1.5rem;">⛔</div>
                                                    <div style="font-size: 0.85rem; font-weight: 700; color: #ef4444; text-transform: uppercase; letter-spacing: 1px;">
                                                        Biggest Problem
                                                    </div>
                                                </div>
                                                <div style="color: #d1d5db; line-height: 1.7; font-size: 0.9rem;">
                                                    {report['critical_error']}
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                    
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                st.success("✅ Portfolio analysis complete! Review recommendations above.")
                            
                            else:
                                st.error(f"API Error: {res.status_code} - {res.text[:200]}")
                        
                        except Exception as e:
                            st.error(f"Analysis failed: {str(e)}")
                            st.info("Try providing more manual data or uploading a clearer screenshot.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state["current_page"] == "data_vault":
        # DATA VAULT PAGE (UNCHANGED - keeping all the existing code)
        if supabase:
            hist = supabase.table("trades").select("*").eq("user_id", current_user).order("created_at", desc=True).execute()
            
            if hist.data:
                df = pd.DataFrame(hist.data)
                df['created_at'] = pd.to_datetime(df['created_at'])
                
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                st.markdown(f'<div class="section-title">Complete Audit History ({len(df)} records)</div>', unsafe_allow_html=True)
                
                col_search1, col_search2, col_search3 = st.columns([2, 1, 1])
                
                with col_search1:
                    search_ticker = st.text_input("Search by Ticker", placeholder="e.g., SPY, AAPL", label_visibility="collapsed")
                
                with col_search2:
                    score_filter = st.selectbox("Score Filter", ["All", "Excellent (80+)", "Good (60-80)", "Fair (40-60)", "Poor (<40)"], label_visibility="collapsed")
                
                with col_search3:
                    sort_order = st.selectbox("Sort By", ["Newest First", "Oldest First", "Highest Score", "Lowest Score"], label_visibility="collapsed")
                
                st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
                
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
                
                table_df = filtered_df[['created_at', 'ticker', 'score', 'mistake_tags', 'technical_analysis', 'psych_analysis']].copy()
                table_df.columns = ['Date', 'Ticker', 'Score', 'Error Tags', 'Technical Notes', 'Psychology Notes']
                
                table_df['Error Tags'] = table_df['Error Tags'].apply(
                    lambda x: ', '.join(x[:3]) if len(x) > 0 else 'None'
                )
                
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
        st.markdown('<div class="glass-panel" style="text-align: center; padding: 80px;">', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size: 3.5rem; margin-bottom: 20px; opacity: 0.4;">💳</div>
        <div style="font-size: 1.2rem; color: #9ca3af; margin-bottom: 10px; font-weight: 600;">Pricing Information</div>
        <div style="font-size: 0.95rem; color: #6b7280;">Pricing details coming soon.</div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:  # analyze page
        main_tab1, main_tab2 = st.tabs(["🔎 FORENSIC AUDIT", "📊 PERFORMANCE METRICS"])

        # --- TAB 1: IMPROVED CHART VISION ANALYSIS ---
        with main_tab1:
            c_mode = st.radio("Input Vector", ["Text Parameters", "Chart Vision", "Portfolio Analysis"], horizontal=True, label_visibility="collapsed")
        
            prompt = ""
            img_b64 = None
            ticker_val = "IMG"
            ready_to_run = False

            if c_mode == "Chart Vision":
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">Quantitative Chart Analysis</div>', unsafe_allow_html=True)
                st.markdown("""
                <div style="text-align: center; margin-bottom: 24px;">
                    <div class="upload-icon">📊</div>
                    <div class="upload-text">Upload Trading Chart for Deep Analysis</div>
                    <div class="upload-subtext">Supports PNG, JPG (Max 10MB). Our AI analyzes price action, risk metrics, and behavioral patterns.</div>
                </div>
                """, unsafe_allow_html=True)
            
                uploaded_file = st.file_uploader(
                    "Upload Chart Screenshot", 
                    type=["png", "jpg", "jpeg"], 
                    label_visibility="collapsed",
                    key="chart_upload"
                )
            
                if uploaded_file:
                    st.markdown('<div style="margin-top: 32px;">', unsafe_allow_html=True)
                    st.image(uploaded_file, use_column_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Manual override option
                    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
                    with st.expander("📝 Optional: Help AI Read Your Chart (if it struggles)"):
                        st.markdown("If the AI generates wrong prices, you can provide key info to help:")
                        manual_ticker = st.text_input("Ticker Symbol (e.g., GLIT, AAPL)", "", placeholder="Leave blank for auto-detect")
                        manual_pnl = st.text_input("Your P&L shown (e.g., -$18,500 or +$2,340)", "", placeholder="Leave blank for auto-detect")
                        manual_pnl_pct = st.text_input("Your P&L % shown (e.g., -66.2% or +15.3%)", "", placeholder="Leave blank for auto-detect")
                        manual_price_range = st.text_input("Price range on chart (e.g., $200 to $290)", "", placeholder="Leave blank for auto-detect")
                    
                    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
                    
                    if st.button("🧬 RUN QUANTITATIVE ANALYSIS", type="primary", use_container_width=True):
                        # 1. Upload Image First
                        with st.spinner("Uploading evidence to secure vault..."):
                            stored_image_url = upload_image_to_supabase(uploaded_file)
                        
                        # 2. Process Image for AI (Existing logic)
                        image = Image.open(uploaded_file)
                        # Optimize image size
                        max_size = (1920, 1080)
                        image.thumbnail(max_size, Image.Resampling.LANCZOS)
                        
                        buf = io.BytesIO()
                        image.save(buf, format="PNG", optimize=True)
                        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                        
                        # Build prompt with manual overrides if provided
                        manual_context = ""
                        if manual_ticker or manual_pnl or manual_pnl_pct or manual_price_range:
                            manual_context = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            manual_context += "USER PROVIDED THIS INFORMATION FROM THE CHART:\n"
                            if manual_ticker:
                                manual_context += f"- Ticker: {manual_ticker}\n"
                            if manual_pnl:
                                manual_context += f"- P&L: {manual_pnl}\n"
                            if manual_pnl_pct:
                                manual_context += f"- P&L Percentage: {manual_pnl_pct}\n"
                            if manual_price_range:
                                manual_context += f"- Price Range: {manual_price_range}\n"
                            manual_context += "USE THIS INFORMATION - IT IS CORRECT. Analyze based on these real values.\n"
                            manual_context += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        
                        # MASSIVELY IMPROVED PROMPT
                        prompt = f"""CRITICAL INSTRUCTIONS: Analyze this trading/portfolio screenshot.

FIRST: IDENTIFY WHAT YOU'RE LOOKING AT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Look carefully at the image and determine:

1. Is this a PORTFOLIO view (multiple stocks listed) or SINGLE CHART?
2. If portfolio: How many stocks/positions are visible?
3. If portfolio: What is the TOTAL P&L shown at top?
4. If portfolio: What is the TOTAL percentage gain/loss?
5. If single chart: Proceed with normal chart analysis

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IF THIS IS A PORTFOLIO SCREENSHOT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Read the TOTAL/OVERALL P&L at the top (usually labeled "Total P/L", "Unrealised P/L", "Portfolio Value", etc.)

Analyze the PORTFOLIO as a whole, not individual stocks.

Identify:
- Total number of positions
- Largest losses (list top 3-5 by % or amount)
- Any position showing >100% loss (red flag for leverage/options/error)
- Overall portfolio drawdown percentage
- Risk concentration issues

PORTFOLIO OUTPUT FORMAT:

[SCORE] <0-100 based on OVERALL portfolio health>

[OVERALL_GRADE] <F if total loss>20%, D if >10%, C if >5%, etc.>

[ENTRY_QUALITY] <Average entry quality across visible positions>

[EXIT_QUALITY] <Exit discipline assessment based on how losses were managed>

[RISK_SCORE] <0-100 based on PORTFOLIO-LEVEL risk management>

[TAGS] <Portfolio_Crisis, Overleveraged, No_Stops, Concentration_Risk, Multiple_Catastrophic_Positions, etc.>

[TECH] PORTFOLIO ANALYSIS: Total P/L: [EXACT total P/L] ([EXACT %]). Number of positions: [count]. Current value: [amount]. Invested: [amount]. Top losses: [list 3-5 worst positions with their %]. Critical observations about portfolio structure and risk concentration.

[PSYCH] PORTFOLIO PSYCHOLOGY: [Analyze the decision-making that led to multiple simultaneous losses. Look for patterns: averaging down? holding losers? FOMO buying? lack of selling discipline?]

[RISK] PORTFOLIO RISK ASSESSMENT: [Analyze diversification, position sizing across portfolio, stop loss discipline, drawdown management, any positions >100% loss (leverage red flags)]

[FIX] PORTFOLIO RECOVERY PLAN:
1. [Immediate crisis management - which positions to close NOW]
2. [Risk reduction strategy - position sizing going forward]
3. [Rehabilitation timeline and rules]

[STRENGTH] [What's working in the portfolio, if anything]

[CRITICAL_ERROR] [The biggest portfolio-level mistake - usually lack of risk management, no stops, or concentration]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IF THIS IS A SINGLE CHART (not portfolio):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{manual_context}

Look at the TOP RIGHT corner of the trading interface. You will see:
- "P/L: [some amount]" - This is the profit/loss. READ IT EXACTLY.
- "([some percentage])" - This is the percentage. READ IT EXACTLY.

The P/L text is usually in RED (loss) or GREEN (profit). What do you see?

Look at the TOP LEFT. You will see the ticker symbol (e.g., "AAPL", "GLIT", "SPY", etc.). What is it?

Look at the RIGHT SIDE Y-AXIS. You will see price levels. What are the numbers? (e.g., $100, $200, $300?)

SEVERITY ASSESSMENT:

Based on the P/L you read:

IF loss > 50% of account → CATASTROPHIC EMERGENCY (Score: 0-5)
IF loss > 30% of account → SEVERE CRISIS (Score: 5-15)
IF loss > 10% of account → MAJOR PROBLEM (Score: 15-30)
IF loss < 5% of account → Poor trade (Score: 30-50)
IF profit > 0% → Grade normally (Score: 50-100)

SINGLE TRADE OUTPUT FORMAT:

[SCORE] <Use severity guide above>

[OVERALL_GRADE] <F if loss>50%, D if loss>30%, C if loss>10%, etc.>

[ENTRY_QUALITY] <0-100>

[EXIT_QUALITY] <0-100>

[RISK_SCORE] <0-100>

[TAGS] <Based on single trade behavior>

[TECH] Ticker: [EXACT ticker]. P&L: [EXACT P&L] ([EXACT %]). Chart price range: [ACTUAL prices on Y-axis]. [Analysis of price action]

[PSYCH] [Single trade psychology analysis]

[RISK] [Single trade risk analysis]

[FIX] [Specific improvements for this trade]

[STRENGTH] [What went well]

[CRITICAL_ERROR] [Biggest mistake in this trade]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL REMINDERS:
1. FIRST determine if this is PORTFOLIO or SINGLE TRADE
2. If portfolio with multiple losses, this is likely a SEVERE crisis
3. Any position showing >100% loss needs immediate investigation
4. Portfolio losses of >20% = catastrophic failure
5. Use EXACT numbers you see on screen, no hallucinations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
                        
                        ready_to_run = True
                st.markdown('</div>', unsafe_allow_html=True)

            elif c_mode == "Portfolio Analysis":
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">📊 Portfolio Health Analysis</div>', unsafe_allow_html=True)
                st.markdown("""
                <div style="text-align: center; margin-bottom: 24px;">
                    <div class="upload-icon">📂</div>
                    <div class="upload-text">Upload Your Portfolio Screenshot or PDF</div>
                    <div class="upload-subtext">Supports PNG, JPG, PDF. We'll analyze your entire portfolio health, risk metrics, and provide restructuring recommendations.</div>
                </div>
                """, unsafe_allow_html=True)
            
                portfolio_file = st.file_uploader(
                    "Upload Portfolio Screenshot or PDF", 
                    type=["png", "jpg", "jpeg", "pdf"], 
                    label_visibility="collapsed",
                    key="portfolio_upload"
                )
            
                if portfolio_file:
                    # Display preview based on file type
                    if portfolio_file.type == "application/pdf":
                        st.info("📄 PDF uploaded. Analysis will extract portfolio data from PDF.")
                    else:
                        st.markdown('<div style="margin-top: 32px;">', unsafe_allow_html=True)
                        st.image(portfolio_file, use_column_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Manual portfolio data input (recommended for accuracy)
                    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
                    with st.expander("📝 Manual Portfolio Data (Recommended for Best Results)", expanded=True):
                        st.markdown("**Provide your portfolio details for most accurate analysis:**")
                        
                        col_p1, col_p2 = st.columns(2)
                        with col_p1:
                            portfolio_total_invested = st.number_input("Total Invested Amount", min_value=0.0, step=1000.0, format="%.2f", help="Total capital invested")
                            portfolio_current_value = st.number_input("Current Portfolio Value", min_value=0.0, step=1000.0, format="%.2f", help="Current market value")
                            portfolio_num_positions = st.number_input("Number of Positions", min_value=1, max_value=200, value=10, help="How many stocks/assets in portfolio")
                        
                        with col_p2:
                            portfolio_largest_loss = st.text_input("Largest Single Loss", placeholder="e.g., AAPL -₹50,000 (-45%)", help="Your worst performing position")
                            portfolio_largest_gain = st.text_input("Largest Single Gain", placeholder="e.g., TSLA +₹30,000 (+60%)", help="Your best performing position")
                            portfolio_crisis_stocks = st.text_input("Stocks in Crisis (>30% loss)", placeholder="e.g., ADANIPOWER, AARTIIND", help="Comma-separated list")
                        
                        portfolio_description = st.text_area(
                            "Additional Portfolio Context", 
                            height=100, 
                            placeholder="Describe your portfolio: sectors, strategy, time horizon, any leveraged positions, margin usage, etc.",
                            help="More context = better analysis"
                        )
                    
                    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
                    
                    if st.button("🔬 ANALYZE PORTFOLIO HEALTH", type="primary", use_container_width=True):
                        # Calculate portfolio metrics
                        total_pnl = portfolio_current_value - portfolio_total_invested if portfolio_total_invested > 0 else 0
                        total_pnl_pct = (total_pnl / portfolio_total_invested * 100) if portfolio_total_invested > 0 else 0
                        
                        # Prepare image if not PDF
                        img_b64 = None
                        if portfolio_file.type != "application/pdf":
                            image = Image.open(portfolio_file)
                            max_size = (1920, 1080)
                            image.thumbnail(max_size, Image.Resampling.LANCZOS)
                            buf = io.BytesIO()
                            image.save(buf, format="PNG", optimize=True)
                            img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                        
                        # Build portfolio context
                        portfolio_context = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PORTFOLIO DATA PROVIDED BY USER:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Invested: {portfolio_total_invested:,.2f}
Current Value: {portfolio_current_value:,.2f}
Total P&L: {total_pnl:,.2f} ({total_pnl_pct:+.2f}%)
Number of Positions: {portfolio_num_positions}
Largest Loss: {portfolio_largest_loss if portfolio_largest_loss else "Not specified"}
Largest Gain: {portfolio_largest_gain if portfolio_largest_gain else "Not specified"}
Crisis Stocks (>30% loss): {portfolio_crisis_stocks if portfolio_crisis_stocks else "None specified"}

Additional Context:
{portfolio_description if portfolio_description else "No additional context provided"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

USE THIS INFORMATION AS GROUND TRUTH. Analyze based on these provided values.
"""
                        
                        # PORTFOLIO-SPECIFIC PROMPT
                        portfolio_prompt = f"""You are analyzing a COMPLETE INVESTMENT PORTFOLIO. This is NOT a single trade - this is portfolio-level risk assessment.

{portfolio_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PORTFOLIO ANALYSIS FRAMEWORK:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. PORTFOLIO HEALTH ASSESSMENT:
   - Overall portfolio P&L and percentage
   - Drawdown severity (current loss from peak)
   - Number of positions (diversification vs. over-diversification)
   - Win/loss ratio across portfolio
   - Concentration risk (any position >10% of portfolio?)

2. RISK MANAGEMENT EVALUATION:
   - Are stop losses in place across positions?
   - Position sizing discipline (should be 1-5% per position)
   - Correlation risk (positions moving together?)
   - Sector concentration
   - Any leveraged/margin positions (red flag)
   - Positions with >50% losses (likely beyond recovery)

3. PORTFOLIO STRUCTURE ANALYSIS:
   - Too many positions? (>20 = likely over-diversified)
   - Too few? (<5 = concentration risk)
   - Balance between growth/value/defensive
   - Sector diversification
   - Market cap diversification

4. CRISIS IDENTIFICATION:
   - Any positions showing >100% loss (leverage/margin emergency)
   - Multiple positions >50% down (poor exit discipline)
   - Portfolio drawdown >30% (severe crisis)
   - Evidence of averaging down into losers
   - Revenge trading patterns

5. PSYCHOLOGICAL ASSESSMENT:
   - Holding losers, cutting winners? (common retail mistake)
   - Evidence of FOMO buying at tops
   - Lack of selling discipline
   - Emotional attachment to positions
   - Hope-based investing vs. risk management

SEVERITY LEVELS FOR PORTFOLIOS:

Portfolio Drawdown >50%: CATASTROPHIC (Score 0-5)
Portfolio Drawdown 30-50%: SEVERE CRISIS (Score 5-15)
Portfolio Drawdown 20-30%: MAJOR PROBLEM (Score 15-30)
Portfolio Drawdown 10-20%: CONCERNING (Score 30-50)
Portfolio Drawdown 5-10%: MINOR ISSUE (Score 50-70)
Portfolio Drawdown <5%: ACCEPTABLE (Score 70-100)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[SCORE] <0-100 based on portfolio drawdown severity>

[OVERALL_GRADE] <F if >30% loss, D if 20-30%, C if 10-20%, B if 5-10%, A if <5%>

[ENTRY_QUALITY] <Average entry quality across portfolio - rate the timing of buys>

[EXIT_QUALITY] <Exit discipline - are stop losses used? Or holding losers?>

[RISK_SCORE] <0-100 portfolio-level risk management quality>

[TAGS] <Portfolio_Crisis, Overleveraged, No_Stops, Concentration_Risk, Too_Many_Positions, Sector_Concentration, Multiple_Losers, No_Exit_Plan, Hope_Based_Investing, etc.>

[TECH] PORTFOLIO TECHNICAL ANALYSIS: Total P&L: {total_pnl:,.2f} ({total_pnl_pct:+.2f}%). Portfolio has {portfolio_num_positions} positions. [Analyze diversification, concentration, position sizing. List top 3-5 problem positions. Identify sector exposure risks. Comment on portfolio structure.]

[PSYCH] PORTFOLIO PSYCHOLOGY PROFILE: [Analyze the decision-making patterns across the portfolio. Are they holding losers and cutting winners? Evidence of FOMO? Revenge trading? Lack of selling discipline? Emotional attachment to positions? This should be behavioral analysis of their OVERALL trading psychology based on portfolio patterns.]

[RISK] PORTFOLIO RISK ASSESSMENT: [Analyze portfolio-level risk: position sizing discipline, stop loss usage across positions, concentration risk, correlation risk, drawdown management, any leverage/margin red flags. If portfolio loss >30%, this is CATASTROPHIC. If any position shows >100% loss, this is margin/leverage emergency.]

[FIX] PORTFOLIO RESTRUCTURING PLAN:
1. IMMEDIATE ACTIONS: [What needs to happen in next 24-48 hours - close crisis positions, investigate leverage, stop opening new positions]
2. SHORT TERM (1-4 weeks): [Which positions to close/reduce, how to implement stops, position sizing rules]
3. LONG TERM (1-6 months): [Portfolio rebuild strategy, education needs, risk management framework, psychological reset]

[STRENGTH] [What's working in the portfolio, if anything. Even in disasters, find something - e.g., "Diversification across sectors prevents total loss" or "At least closed some positions before -100%"]

[CRITICAL_ERROR] [The biggest portfolio-level mistake. Usually: no stop losses, concentration risk, averaging down losers, lack of exit plan, emotional position holding, or taking on leverage without understanding it]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL PORTFOLIO-SPECIFIC RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. If portfolio drawdown >30%: This is CATASTROPHIC portfolio failure, score MUST be 0-10
2. If any position shows >100% loss: LEVERAGE/MARGIN EMERGENCY - flag immediately
3. If >20 positions: Likely over-diversification - too many positions to manage properly
4. If multiple positions >50% loss: Exit discipline failure - holding losers too long
5. Portfolio analysis is about RISK MANAGEMENT, not individual stock picking
6. Focus on position sizing, diversification, stop losses, and exit discipline
7. A portfolio can have some winners but still fail due to poor risk management
8. Recovery from >30% drawdown typically takes 12-24+ months minimum

REMEMBER: This is PORTFOLIO analysis, not trade analysis. Focus on overall risk management, diversification, position sizing discipline, and exit strategy across ALL positions.
"""
                        
                        ready_to_run = True
                        ticker_val = "PORTFOLIO"
                        prompt = portfolio_prompt
                
                st.markdown('</div>', unsafe_allow_html=True)

            else:  # Text Parameters mode
                # TEXT PARAMETERS (UNCHANGED)
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
                        
                        pnl = exit_price - entry if exit_price > 0 and entry > 0 else 0
                        pnl_pct = (pnl / entry * 100) if entry > 0 else 0
                        risk = abs(entry - stop) if stop > 0 and entry > 0 else 0
                        risk_pct = (risk / entry * 100) if entry > 0 else 0
                        reward = abs(exit_price - entry) if exit_price > 0 and entry > 0 else 0
                        rr_ratio = (reward / risk) if risk > 0 else 0
                        
                        prompt = f"""You are Dr. Michael Steinhardt, legendary hedge fund manager with 45 years experience. Analyze this trade with brutal institutional honesty.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRADE DATA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ticker: {ticker}
Setup: {setup_type}
Emotional State: {emotion}
Entry: ${entry:.2f}
Exit: ${exit_price:.2f}
Stop: ${stop:.2f}

METRICS:
PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)
Risk: ${risk:.2f} ({risk_pct:.2f}%)
R:R Ratio: {rr_ratio:.2f}:1

NOTES: {notes if notes else "No notes"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OUTPUT FORMAT (EXACT):

[SCORE] <0-100>

[OVERALL_GRADE] <F/D/C/B/A/S-Tier>

[ENTRY_QUALITY] <0-100>

[EXIT_QUALITY] <0-100>

[RISK_SCORE] <0-100>

[TAGS] <comma-separated, 3-5 tags>

[TECH] <3-5 sentences with NUMBERS: entry timing, stop placement, R:R analysis, setup quality>

[PSYCH] <2-4 sentences: emotional state impact, biases detected, discipline assessment>

[RISK] <3-4 sentences with PERCENTAGES: account risk, position size, stop effectiveness>

[FIX] <Exactly 3 improvements:
1. [Specific technical fix]
2. [Specific psychological fix]
3. [Specific risk fix]>

[STRENGTH] <1-2 sentences on what was good>

[CRITICAL_ERROR] <Single biggest mistake>

BE HARSH. USE NUMBERS. BE SPECIFIC."""
                        ready_to_run = True
                st.markdown('</div>', unsafe_allow_html=True)

            # IMPROVED RESULTS PROCESSING
            if ready_to_run and supabase:
                with st.spinner("🧠 Running Deep Quantitative Analysis..."):
                    try:
                        if img_b64:
                            # Use improved API call function
                            raw_response = call_vision_api(prompt, img_b64)
                        else:
                            # Text analysis
                            messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
                            payload = {
                                "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                                "messages": messages,
                                "max_tokens": 1500,
                                "temperature": 0.3
                            }
                            headers = {
                                "Authorization": f"Bearer {HF_TOKEN}",
                                "Content-Type": "application/json"
                            }
                            res = requests.post(API_URL, headers=headers, json=payload, timeout=60)
                            if res.status_code == 200:
                                raw_response = res.json()["choices"][0]["message"]["content"]
                            else:
                                raise Exception(f"API Error: {res.status_code}")
                        
                        # Parse with improved validation
                        report = parse_report(raw_response)
                        
                        # HALLUCINATION DETECTION
                        hallucination_detected = False
                        warning_messages = []
                        
                        # Check if analysis contains common hallucinated prices that appear in examples
                        hallucinated_prices = ['$445', '$435', '$451', '$458', '$440', '$437']
                        tech_text = report.get('tech', '').lower()
                        
                        if any(price in report.get('tech', '') for price in hallucinated_prices):
                            hallucination_detected = True
                            warning_messages.append("⚠️ AI may have hallucinated prices from examples rather than analyzing your actual chart")
                        
                        # Check for catastrophic loss detection
                        if 'catastrophic' in raw_response.lower() or 'emergency' in raw_response.lower():
                            if report['score'] > 20:
                                # AI detected catastrophe but didn't score it correctly
                                report['score'] = max(10, report['score'] // 5)
                                report['overall_grade'] = 'F'
                                report['risk_score'] = min(20, report['risk_score'])
                                warning_messages.append("🚨 Score adjusted for catastrophic loss detected in analysis")
                        
                        # Validate we got real analysis
                        if (report['score'] == 50 and 
                            report['entry_quality'] == 50 and 
                            report['exit_quality'] == 50):
                            warning_messages.append("⚠️ Analysis may be incomplete. Try a clearer image with visible price levels.")
                        
                        # Display warnings if any
                        if warning_messages:
                            for msg in warning_messages:
                                st.warning(msg)
                        
                        # Save with image URL if available
                        image_url_to_save = stored_image_url if 'stored_image_url' in locals() else None
                        save_analysis(current_user, report, ticker_val, image_url_to_save)
                        
                        # REST OF THE DISPLAY CODE REMAINS EXACTLY THE SAME...
                        # (All the visualization code from line 2000+ stays unchanged)
                        
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
                        
                        met_col1, met_col2, met_col3 = st.columns(3)
                        
                        metrics_data = [
                            ("Entry Quality", report.get('entry_quality', 50), met_col1),
                            ("Exit Quality", report.get('exit_quality', 50), met_col2),
                            ("Risk Management", report.get('risk_score', 50), met_col3)
                        ]
                        
                        for metric_name, metric_value, col in metrics_data:
                            with col:
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
                                
                                tags_html += f'<div style="background: {tag_bg}; border: 1px solid {tag_color}40; padding: 10px 18px; border-radius: 10px; color: {tag_color}; font-weight: 600; font-size: 0.85rem; letter-spacing: 0.5px; transition: all 0.3s ease; cursor: default;">{tag}</div>'
                            tags_html += '</div>'
                            st.markdown(tags_html, unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # VISUALIZATION CHART
                        st.markdown('<div class="glass-panel animate-fade-in" style="animation-delay: 0.3s;">', unsafe_allow_html=True)
                        st.markdown('<div class="section-title">📈 Performance Radar</div>', unsafe_allow_html=True)
                        
                        chart_data = pd.DataFrame({
                            'Metric': ['Entry\nQuality', 'Exit\nQuality', 'Risk\nManagement', 'Overall\nScore'],
                            'Score': [
                                report.get('entry_quality', 50),
                                report.get('exit_quality', 50),
                                report.get('risk_score', 50),
                                report['score']
                            ]
                        })
                        
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
                        
                        # KEY INSIGHTS
                        if report.get('strength') != 'N/A' and report.get('strength') != 'Analyzing...':
                            st.markdown('<div class="glass-panel animate-slide-up" style="animation-delay: 0.8s;">', unsafe_allow_html=True)
                            
                            ins_col1, ins_col2 = st.columns(2)
                            
                            with ins_col1:
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
                                if report.get('critical_error') != 'N/A' and report.get('critical_error') != 'Analyzing...':
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
                        st.error(f"⚠️ Analysis Failed: {str(e)}")
                        st.info("""
                        💡 **Troubleshooting Tips:**
                        - Ensure chart image is clear with visible price levels
                        - Check that the image shows actual trading activity (not just a blank chart)
                        - Try a different screenshot with better contrast
                        - Make sure prices and indicators are legible
                        - If problem persists, try the Text Parameters mode instead
                        """)
        
        # TAB 2: PERFORMANCE METRICS - COMPLETE DASHBOARD
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
                    
                    # 5. DETAILED TRADE HISTORY WITH IMAGES
                    st.markdown('<div class="glass-panel" style="margin-top: 32px;">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">📜 Trade History Details</div>', unsafe_allow_html=True)
                    
                    for i, row in df.head(20).iterrows():
                        with st.expander(f"📊 {row['created_at'].strftime('%Y-%m-%d %H:%M')} | {row['ticker']} | Score: {row['score']}/100"):
                            # CHECK IF IMAGE EXISTS AND DISPLAY IT
                            if row.get('image_url'):
                                st.image(row['image_url'], caption="Original Trade Evidence", width=600)
                                st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
                            
                            # Display analysis details
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(f"**Quality Grade:** {row.get('overall_grade', 'N/A')}")
                                st.markdown(f"**Entry Quality:** {row.get('entry_quality', 'N/A')}/100")
                                st.markdown(f"**Exit Quality:** {row.get('exit_quality', 'N/A')}/100")
                                st.markdown(f"**Risk Score:** {row.get('risk_score', 'N/A')}/100")
                            
                            with col2:
                                tags = row.get('mistake_tags', [])
                                if tags:
                                    st.markdown(f"**Error Tags:** {', '.join(tags)}")
                                else:
                                    st.markdown("**Error Tags:** None")
                            
                            st.markdown("---")
                            
                            # Technical Analysis
                            if row.get('technical_analysis'):
                                st.markdown("**📈 Technical Analysis:**")
                                st.write(row['technical_analysis'])
                            
                            # Psychological Analysis
                            if row.get('psych_analysis'):
                                st.markdown("**🧠 Psychological Analysis:**")
                                st.write(row['psych_analysis'])
                            
                            # Risk Analysis
                            if row.get('risk_analysis'):
                                st.markdown("**⚠️ Risk Analysis:**")
                                st.write(row['risk_analysis'])
                            
                            # Fix Action
                            if row.get('fix_action'):
                                st.markdown("**🔧 Recommended Fixes:**")
                                st.write(row['fix_action'])
                            
                            # Strength
                            if row.get('strength'):
                                st.markdown("**💪 Strengths:**")
                                st.write(row['strength'])
                            
                            # Critical Error
                            if row.get('critical_error'):
                                st.markdown("**🚨 Critical Error:**")
                                st.write(row['critical_error'])
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                else:
                    st.markdown('<div class="glass-panel" style="text-align: center; padding: 80px;">', unsafe_allow_html=True)
                    st.markdown("""
                    <div style="font-size: 3.5rem; margin-bottom: 20px; opacity: 0.4;">📊</div>
                    <div style="font-size: 1.2rem; color: #9ca3af; margin-bottom: 10px; font-weight: 600;">No Performance Data Yet</div>
                    <div style="font-size: 0.95rem; color: #6b7280;">Complete your first forensic audit to see metrics here.</div>
                    """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
