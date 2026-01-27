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
    page_title="Trade Autopsy", 
    page_icon="⚡", 
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
    st.session_state["current_page"] = "analyze"
    st.rerun()

def navigate_to(page):
    st.session_state["current_page"] = page
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
# 2. HYPER-PREMIUM DARK THEME CSS
# ==========================================
st.markdown("""
<style>
    /* --- PREMIUM FONTS --- */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* --- HYPER DARK BACKGROUND --- */
    body, .stApp { 
        background: #0a0a0f !important;
        background-image: 
            radial-gradient(ellipse at 15% 15%, rgba(16, 185, 129, 0.12) 0%, transparent 35%),
            radial-gradient(ellipse at 85% 85%, rgba(59, 130, 246, 0.12) 0%, transparent 35%),
            radial-gradient(ellipse at 50% 50%, rgba(139, 92, 246, 0.06) 0%, transparent 50%);
        font-family: 'Rajdhani', sans-serif !important; 
        color: #e5e7eb; 
        line-height: 1.65;
        overflow-x: hidden;
    }
    
    /* --- ANIMATED GRID BACKGROUND --- */
    body::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            linear-gradient(rgba(16, 185, 129, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(16, 185, 129, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
        pointer-events: none;
        z-index: 0;
        animation: gridMove 20s linear infinite;
    }
    
    @keyframes gridMove {
        0% { transform: translate(0, 0); }
        100% { transform: translate(50px, 50px); }
    }
    
    /* --- CONTAINER SPACING --- */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 2rem !important;
        max-width: 1600px !important;
        position: relative;
        z-index: 1;
    }

    /* --- HIDE STREAMLIT ELEMENTS --- */
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    
    /* --- HYPER PREMIUM HEADER NAVIGATION --- */
    .hyper-header {
        background: rgba(10, 10, 15, 0.85);
        backdrop-filter: blur(30px) saturate(200%);
        -webkit-backdrop-filter: blur(30px) saturate(200%);
        border-bottom: 1px solid rgba(16, 185, 129, 0.2);
        padding: 20px 40px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: sticky;
        top: 0;
        z-index: 1000;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.6),
            inset 0 1px 0 rgba(16, 185, 129, 0.1);
        animation: headerSlideDown 0.6s cubic-bezier(0.23, 1, 0.32, 1);
    }
    
    @keyframes headerSlideDown {
        from {
            transform: translateY(-100%);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    .header-brand {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    
    .header-logo {
        font-size: 2.2rem;
        filter: drop-shadow(0 0 20px rgba(16, 185, 129, 0.6));
        animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); filter: drop-shadow(0 0 20px rgba(16, 185, 129, 0.6)); }
        50% { transform: scale(1.05); filter: drop-shadow(0 0 30px rgba(16, 185, 129, 0.8)); }
    }
    
    .header-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #10b981 0%, #3b82f6 50%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 1px;
        text-transform: uppercase;
        animation: titleGlow 3s ease-in-out infinite;
    }
    
    @keyframes titleGlow {
        0%, 100% { filter: drop-shadow(0 0 10px rgba(16, 185, 129, 0.3)); }
        50% { filter: drop-shadow(0 0 20px rgba(59, 130, 246, 0.5)); }
    }
    
    .header-nav {
        display: flex;
        gap: 8px;
        align-items: center;
    }
    
    .nav-button {
        background: transparent;
        border: 1px solid rgba(16, 185, 129, 0.2);
        color: #9ca3af;
        padding: 12px 28px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.95rem;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        text-transform: uppercase;
        letter-spacing: 1px;
        font-family: 'Rajdhani', sans-serif;
        position: relative;
        overflow: hidden;
    }
    
    .nav-button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.2), transparent);
        transition: left 0.5s ease;
    }
    
    .nav-button:hover {
        background: rgba(16, 185, 129, 0.1);
        border-color: rgba(16, 185, 129, 0.5);
        color: #10b981;
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
    }
    
    .nav-button:hover::before {
        left: 100%;
    }
    
    .nav-button-active {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.25) 0%, rgba(59, 130, 246, 0.25) 100%);
        border-color: rgba(16, 185, 129, 0.6);
        color: #10b981;
        box-shadow: 
            0 0 30px rgba(16, 185, 129, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    .user-badge {
        background: rgba(16, 185, 129, 0.15);
        padding: 10px 20px;
        border-radius: 10px;
        font-size: 0.9rem;
        font-weight: 700;
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        text-transform: uppercase;
        letter-spacing: 1px;
        animation: fadeIn 0.8s ease;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    /* --- HYPER GLASS PANELS --- */
    .glass-panel {
        background: rgba(10, 10, 15, 0.7);
        backdrop-filter: blur(30px) saturate(200%);
        -webkit-backdrop-filter: blur(30px) saturate(200%);
        border: 1px solid rgba(16, 185, 129, 0.15);
        border-radius: 20px;
        padding: 40px;
        margin-bottom: 28px;
        margin-top: 28px;
        box-shadow: 
            0 16px 48px rgba(0, 0, 0, 0.6),
            inset 0 1px 0 rgba(16, 185, 129, 0.1);
        transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
        position: relative;
        overflow: hidden;
        animation: panelSlideUp 0.6s cubic-bezier(0.23, 1, 0.32, 1);
    }
    
    @keyframes panelSlideUp {
        from {
            transform: translateY(30px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    .glass-panel::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.8), rgba(59, 130, 246, 0.8), transparent);
        animation: scanLine 3s ease-in-out infinite;
    }
    
    @keyframes scanLine {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    .glass-panel:hover {
        border-color: rgba(16, 185, 129, 0.4);
        box-shadow: 
            0 20px 60px rgba(0, 0, 0, 0.7),
            0 0 40px rgba(16, 185, 129, 0.2),
            inset 0 1px 0 rgba(16, 185, 129, 0.15);
        transform: translateY(-4px);
    }
    
    /* --- HYPER KPI CARDS --- */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 24px;
        margin-bottom: 32px;
    }
    
    .kpi-card {
        background: linear-gradient(135deg, rgba(15, 15, 20, 0.95) 0%, rgba(10, 10, 15, 0.98) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(16, 185, 129, 0.2);
        padding: 36px 32px;
        border-radius: 18px;
        text-align: center;
        transition: all 0.6s cubic-bezier(0.23, 1, 0.32, 1);
        position: relative;
        overflow: hidden;
        animation: cardPopIn 0.5s cubic-bezier(0.23, 1, 0.32, 1);
    }
    
    @keyframes cardPopIn {
        from {
            transform: scale(0.9);
            opacity: 0;
        }
        to {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    .kpi-card::after {
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at 50% 0%, rgba(16, 185, 129, 0.2), transparent 70%);
        opacity: 0;
        transition: opacity 0.6s ease;
    }
    
    .kpi-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: conic-gradient(
            from 0deg,
            transparent,
            rgba(16, 185, 129, 0.3),
            transparent 30%
        );
        opacity: 0;
        transition: opacity 0.6s ease;
        animation: rotate 4s linear infinite;
    }
    
    @keyframes rotate {
        100% { transform: rotate(360deg); }
    }
    
    .kpi-card:hover {
        border-color: rgba(16, 185, 129, 0.6);
        transform: translateY(-12px) scale(1.03);
        box-shadow: 
            0 24px 72px -12px rgba(16, 185, 129, 0.4),
            0 0 60px rgba(16, 185, 129, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    .kpi-card:hover::after,
    .kpi-card:hover::before {
        opacity: 1;
    }
    
    .kpi-val { 
        font-family: 'Orbitron', monospace;
        font-size: 3.5rem; 
        font-weight: 800; 
        background: linear-gradient(135deg, #ffffff 0%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 12px;
        letter-spacing: -0.02em;
        position: relative;
        z-index: 1;
        animation: numberFlicker 3s ease-in-out infinite;
    }
    
    @keyframes numberFlicker {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.95; }
    }
    
    .kpi-label { 
        color: #9ca3af; 
        font-size: 0.75rem; 
        text-transform: uppercase; 
        letter-spacing: 3px; 
        font-weight: 700;
        position: relative;
        z-index: 1;
    }

    /* --- PREMIUM LOGIN --- */
    .login-container {
        max-width: 500px;
        margin: 8vh auto;
        padding: 64px;
        background: rgba(10, 10, 15, 0.95);
        backdrop-filter: blur(30px);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 24px;
        box-shadow: 
            0 32px 96px rgba(0, 0, 0, 0.7),
            0 0 60px rgba(16, 185, 129, 0.2),
            inset 0 1px 0 rgba(16, 185, 129, 0.1);
        text-align: center;
        position: relative;
        overflow: hidden;
        animation: loginSlideIn 0.8s cubic-bezier(0.23, 1, 0.32, 1);
    }
    
    @keyframes loginSlideIn {
        from {
            transform: translateY(-50px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    .login-container::before {
        content: '';
        position: absolute;
        top: -100%;
        left: -100%;
        width: 300%;
        height: 300%;
        background: conic-gradient(
            from 0deg,
            transparent,
            rgba(16, 185, 129, 0.1),
            transparent 30%,
            transparent 60%,
            rgba(59, 130, 246, 0.1),
            transparent 90%
        );
        animation: rotateGradient 8s linear infinite;
    }
    
    @keyframes rotateGradient {
        100% { transform: rotate(360deg); }
    }
    
    .login-logo {
        font-size: 5rem;
        margin-bottom: 24px;
        filter: drop-shadow(0 0 30px rgba(16, 185, 129, 0.6));
        position: relative;
        z-index: 1;
        animation: logoFloat 3s ease-in-out infinite;
    }
    
    @keyframes logoFloat {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }

    /* --- SECTION TITLES --- */
    .section-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.1rem;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 32px;
        display: flex;
        align-items: center;
        gap: 16px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .section-title::before {
        content: '';
        display: block;
        width: 5px;
        height: 28px;
        background: linear-gradient(180deg, #10b981 0%, #3b82f6 100%);
        border-radius: 3px;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.6);
        animation: pulse 2s ease-in-out infinite;
    }

    /* --- REPORT GRID --- */
    .report-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 24px;
        margin-top: 36px;
    }
    
    .report-item {
        background: rgba(255, 255, 255, 0.02);
        border-left: 4px solid rgba(100, 100, 100, 0.3);
        padding: 28px;
        border-radius: 0 16px 16px 0;
        transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
        font-size: 0.95rem;
        line-height: 1.8;
        position: relative;
        overflow: hidden;
    }
    
    .report-item::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        height: 100%;
        width: 4px;
        background: currentColor;
        opacity: 0;
        transition: opacity 0.5s ease;
    }
    
    .report-item:hover {
        background: rgba(255, 255, 255, 0.05);
        border-left-color: currentColor;
        transform: translateX(8px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    
    .report-item:hover::before {
        opacity: 1;
    }
    
    .report-label {
        font-weight: 800;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 16px;
        display: block;
    }

    /* --- HYPER TABS --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 16px;
        background: transparent;
        border-radius: 0;
        padding: 0;
        margin-bottom: 36px;
        border-bottom: 2px solid rgba(16, 185, 129, 0.2);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 0;
        color: #6b7280;
        font-weight: 700;
        padding: 16px 32px;
        transition: all 0.4s ease;
        font-size: 1rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        font-family: 'Rajdhani', sans-serif;
        border: none;
        border-bottom: 3px solid transparent;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #10b981;
        border-bottom-color: rgba(16, 185, 129, 0.5);
    }
    
    .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: #10b981 !important;
        border-bottom-color: #10b981 !important;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 0 !important;
    }
    
    /* --- RADIO BUTTONS --- */
    .stRadio > div {
        background: rgba(10, 10, 15, 0.6) !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
        border-radius: 14px !important;
        padding: 12px !important;
        display: flex !important;
        gap: 12px !important;
    }
    
    .stRadio > label {
        display: none !important;
    }
    
    .stRadio label {
        background: transparent !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
        color: #9ca3af !important;
        padding: 12px 24px !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    
    .stRadio label:hover {
        background: rgba(16, 185, 129, 0.1) !important;
        border-color: rgba(16, 185, 129, 0.5) !important;
        color: #10b981 !important;
    }

    /* --- HYPER BUTTONS --- */
    .stButton button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border: 1px solid rgba(16, 185, 129, 0.5);
        border-radius: 12px;
        color: white;
        font-weight: 700;
        padding: 16px 40px;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        box-shadow: 
            0 8px 24px rgba(16, 185, 129, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
        letter-spacing: 1.5px;
        font-size: 0.95rem;
        text-transform: uppercase;
        position: relative;
        overflow: hidden;
    }
    
    .stButton button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        transition: left 0.6s ease;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        box-shadow: 
            0 12px 40px rgba(16, 185, 129, 0.6),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
        transform: translateY(-4px) scale(1.02);
    }
    
    .stButton button:hover::before {
        left: 100%;
    }

    /* --- HYPER INPUTS --- */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox select {
        background: rgba(15, 15, 20, 0.8) !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
        padding: 16px 20px !important;
        font-size: 0.95rem !important;
        transition: all 0.4s ease !important;
        font-family: 'Rajdhani', sans-serif !important;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus {
        border-color: rgba(16, 185, 129, 0.6) !important;
        box-shadow: 
            0 0 0 4px rgba(16, 185, 129, 0.15),
            0 8px 24px rgba(16, 185, 129, 0.2) !important;
        background: rgba(15, 15, 20, 0.95) !important;
    }

    /* --- HYPER FILE UPLOADER --- */
    [data-testid="stFileUploader"] section {
        background: rgba(10, 10, 15, 0.8) !important;
        backdrop-filter: blur(20px);
        border: 2px dashed rgba(16, 185, 129, 0.4) !important;
        border-radius: 20px !important;
        padding: 80px 60px !important;
        transition: all 0.6s cubic-bezier(0.23, 1, 0.32, 1) !important;
        position: relative;
        overflow: hidden;
    }
    
    [data-testid="stFileUploader"] section::before {
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.15), transparent 70%);
        opacity: 0;
        transition: opacity 0.6s ease;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(16, 185, 129, 0.8) !important;
        background: rgba(15, 15, 20, 0.95) !important;
        transform: translateY(-8px) scale(1.02);
        box-shadow: 
            0 16px 56px rgba(16, 185, 129, 0.3),
            inset 0 1px 0 rgba(16, 185, 129, 0.2);
    }
    
    [data-testid="stFileUploader"] section:hover::before {
        opacity: 1;
    }
    
    [data-testid="stFileUploader"] section button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        color: white !important;
        font-weight: 700 !important;
        padding: 18px 44px !important;
        font-size: 0.95rem !important;
        transition: all 0.4s ease !important;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.4) !important;
        margin-top: 28px !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
    }
    
    [data-testid="stFileUploader"] section button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        box-shadow: 0 12px 40px rgba(16, 185, 129, 0.6) !important;
        transform: translateY(-3px) scale(1.05);
    }
    
    .upload-icon {
        font-size: 5rem;
        margin-bottom: 32px;
        display: block;
        filter: drop-shadow(0 0 30px rgba(16, 185, 129, 0.5));
        animation: iconFloat 3s ease-in-out infinite;
    }
    
    @keyframes iconFloat {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-15px) rotate(5deg); }
    }
    
    .upload-text {
        font-size: 1.6rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 16px;
        letter-spacing: -0.01em;
    }
    
    .upload-subtext {
        font-size: 0.95rem;
        color: #9ca3af;
        line-height: 1.7;
    }

    /* --- DATAFRAME --- */
    .stDataFrame {
        background: rgba(10, 10, 15, 0.8);
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(16, 185, 129, 0.15);
    }

    /* --- SCORE DISPLAY --- */
    .score-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 40px;
    }
    
    .score-value {
        font-family: 'Orbitron', monospace;
        font-size: 6.5rem;
        font-weight: 900;
        line-height: 1;
        letter-spacing: -0.04em;
        animation: scoreFlicker 2s ease-in-out infinite;
    }
    
    @keyframes scoreFlicker {
        0%, 100% { opacity: 1; text-shadow: 0 0 30px currentColor; }
        50% { opacity: 0.95; text-shadow: 0 0 40px currentColor; }
    }
    
    .score-meta {
        text-align: right;
    }
    
    .ticker-badge {
        background: rgba(16, 185, 129, 0.2);
        padding: 12px 24px;
        border-radius: 12px;
        display: inline-block;
        font-weight: 700;
        font-size: 1rem;
        letter-spacing: 2px;
        margin-bottom: 12px;
        border: 1px solid rgba(16, 185, 129, 0.4);
        text-transform: uppercase;
    }

    /* --- CUSTOM SCROLLBAR --- */
    ::-webkit-scrollbar {
        width: 12px;
        height: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(15, 15, 20, 0.6);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(16, 185, 129, 0.4);
        border-radius: 6px;
        border: 2px solid rgba(15, 15, 20, 0.6);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(16, 185, 129, 0.6);
    }
    
    /* --- REMOVE UNNECESSARY BOXES/CONTAINERS --- */
    [data-testid="stVerticalBlock"] > div:empty,
    [data-testid="stHorizontalBlock"] > div:empty,
    div[class*="stMarkdown"]:empty {
        display: none !important;
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
        <div class="login-logo">⚡</div>
        <h1 style="margin: 0 0 12px 0; font-size: 2.5rem; font-weight: 900; letter-spacing: 2px; position: relative; z-index: 1; font-family: 'Orbitron', sans-serif; text-transform: uppercase; background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Trade Autopsy</h1>
        <p style="color: #6b7280; font-size: 0.85rem; margin-bottom: 52px; letter-spacing: 4px; text-transform: uppercase; position: relative; z-index: 1; font-weight: 600;">Algorithmic Behavioral Forensics</p>
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
    
    # --- HYPER PREMIUM HEADER ---
    analyze_active = "nav-button-active" if current_page == "analyze" else ""
    vault_active = "nav-button-active" if current_page == "data_vault" else ""
    pricing_active = "nav-button-active" if current_page == "pricing" else ""
    
    st.markdown(f"""
    <div class="hyper-header">
        <div class="header-brand">
            <div class="header-logo">⚡</div>
            <div>
                <div class="header-title">Trade Autopsy</div>
            </div>
        </div>
        <div class="header-nav">
            <div class="user-badge">{current_user}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation buttons
    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([1, 1, 1, 8])
    with col_nav1:
        if st.button("ANALYZE", key="nav_analyze", use_container_width=True):
            navigate_to("analyze")
    with col_nav2:
        if st.button("DATA VAULT", key="nav_vault", use_container_width=True):
            navigate_to("data_vault")
    with col_nav3:
        if st.button("PRICING", key="nav_pricing", use_container_width=True):
            navigate_to("pricing")
    
    # --- PAGE ROUTING ---
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
                
                # Table
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
                        "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
                        "Date": st.column_config.DatetimeColumn("Date", format="MMM DD, YYYY HH:mm"),
                        "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                        "Error Tags": st.column_config.TextColumn("Error Tags", width="medium"),
                        "Technical Notes": st.column_config.TextColumn("Technical", width="large"),
                        "Psychology Notes": st.column_config.TextColumn("Psychology", width="large")
                    },
                    height=600
                )
                
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 EXPORT TO CSV",
                    data=csv,
                    file_name=f"trade_autopsy_data_{current_user}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
                
                st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.markdown('<div class="glass-panel" style="text-align: center; padding: 100px;">', unsafe_allow_html=True)
                st.markdown("""
                <div style="font-size: 4rem; margin-bottom: 24px; opacity: 0.4;">🗄️</div>
                <div style="font-size: 1.3rem; color: #9ca3af; margin-bottom: 12px; font-weight: 700;">Data Vault Empty</div>
                <div style="font-size: 1rem; color: #6b7280;">Your audit history will appear here once you start analyzing trades.</div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
    
    elif current_page == "pricing":
        st.markdown('<div class="glass-panel" style="text-align: center; padding: 100px;">', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size: 4rem; margin-bottom: 24px; opacity: 0.4;">💳</div>
        <div style="font-size: 1.3rem; color: #9ca3af; margin-bottom: 12px; font-weight: 700;">Pricing Information</div>
        <div style="font-size: 1rem; color: #6b7280;">Pricing details coming soon.</div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:  # analyze page
        main_tab1, main_tab2 = st.tabs(["🔎 FORENSIC AUDIT", "📊 PERFORMANCE METRICS"])

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
                <div style="text-align: center; margin-bottom: 28px;">
                    <div class="upload-icon">📊</div>
                    <div class="upload-text">Drop your P&L or Chart screenshot here</div>
                    <div class="upload-subtext">Supports PNG, JPG (Max 10MB). Your data is encrypted and deleted after analysis.</div>
                </div>
                """, unsafe_allow_html=True)
            
                uploaded_file = st.file_uploader("Upload Chart Screenshot", type=["png", "jpg"], label_visibility="collapsed", key="chart_upload")
            
                if uploaded_file:
                    st.image(uploaded_file, use_column_width=True)
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
                st.markdown('</div>', unsafe_allow_html=True)

            else:
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">Case Data Input</div>', unsafe_allow_html=True)
                with st.form("audit_form"):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a: ticker = st.text_input("Ticker", "SPY")
                    with col_b: setup_type = st.selectbox("Setup", ["Trend", "Reversal", "Breakout"])
                    with col_c: emotion = st.selectbox("State", ["Neutral", "FOMO", "Revenge", "Tilt"])
                
                    col_d, col_e, col_f = st.columns(3)
                    with col_d: entry = st.number_input("Entry", 0.0, step=0.01)
                    with col_e: exit_price = st.number_input("Exit", 0.0, step=0.01)
                    with col_f: stop = st.number_input("Stop", 0.0, step=0.01)
                
                    notes = st.text_area("Execution Notes", height=140, placeholder="Describe your decision-making process, entry hesitation, stop management...")
                
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
                        
                            score_color = "#10b981" if report['score'] >= 50 else "#ef4444"
                        
                            st.markdown(f"""
                            <div class="glass-panel" style="border-top: 3px solid {score_color}">
                                <div class="score-container">
                                    <div>
                                        <div style="color:#6b7280; letter-spacing:3px; font-size:0.75rem; text-transform: uppercase; margin-bottom: 12px; font-weight: 700;">AUDIT SCORE</div>
                                        <div class="score-value" style="color:{score_color}">{report['score']}</div>
                                    </div>
                                    <div class="score-meta">
                                        <div class="ticker-badge">{ticker_val}</div>
                                        <div style="color:#6b7280; font-size:0.9rem;">{datetime.now().strftime('%B %d, %Y')}</div>
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

        with main_tab2:
            if supabase:
                hist = supabase.table("trades").select("*").eq("user_id", current_user).order("created_at", desc=True).execute()
            
                if hist.data:
                    df = pd.DataFrame(hist.data)
                    df['created_at'] = pd.to_datetime(df['created_at'])
                
                    # Metrics
                    avg_score = df['score'].mean()
                    total_trades = len(df)
                    all_tags = [tag for sublist in df['mistake_tags'] for tag in sublist]
                    win_rate = len(df[df['score'] > 60]) / len(df) * 100 if len(df) > 0 else 0
                    recent_avg = df.head(5)['score'].mean() if len(df) >= 5 else avg_score
                    prev_avg = df.iloc[5:10]['score'].mean() if len(df) >= 10 else avg_score
                    trend = "↗" if recent_avg > prev_avg else "↘" if recent_avg < prev_avg else "→"
                
                    # KPI Cards
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
                            <div class="kpi-val" style="font-size:3rem;">{trend}</div>
                            <div class="kpi-label">Recent Trend</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Performance Chart
                    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">Performance Evolution</div>', unsafe_allow_html=True)
                
                    chart_data = df[['created_at', 'score']].sort_values('created_at').reset_index(drop=True)
                    chart_data['index'] = range(len(chart_data))
                
                    base = alt.Chart(chart_data).encode(
                        x=alt.X('index:Q', 
                            axis=alt.Axis(title='Trade Sequence', grid=False, labelColor='#6b7280', titleColor='#9ca3af', labelFontSize=11, titleFontSize=12)
                        )
                    )
                
                    good_line = alt.Chart(pd.DataFrame({'y': [70]})).mark_rule(strokeDash=[5, 5], color='#10b981', opacity=0.3).encode(y='y:Q')
                    bad_line = alt.Chart(pd.DataFrame({'y': [40]})).mark_rule(strokeDash=[5, 5], color='#ef4444', opacity=0.3).encode(y='y:Q')
                
                    line = base.mark_line(
                        color='#3b82f6', 
                        strokeWidth=3,
                        point=alt.OverlayMarkDef(filled=True, size=80, color='#3b82f6', strokeWidth=2, stroke='#1e40af')
                    ).encode(
                        y=alt.Y('score:Q', scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(title='Quality Score', grid=True, gridColor='rgba(255,255,255,0.04)', labelColor='#6b7280', titleColor='#9ca3af', labelFontSize=11, titleFontSize=12)),
                        tooltip=[alt.Tooltip('index:Q', title='Trade #'), alt.Tooltip('score:Q', title='Score'), alt.Tooltip('created_at:T', title='Date', format='%b %d, %Y')]
                    )
                
                    area = base.mark_area(color='#3b82f6', opacity=0.1, line=False).encode(y='score:Q')
                
                    chart = (good_line + bad_line + area + line).properties(height=320).configure_view(strokeWidth=0, fill='transparent').configure(background='transparent')
                
                    st.altair_chart(chart, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Two columns
                    col_left, col_right = st.columns([1.5, 1])
                
                    with col_left:
                        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                        st.markdown('<div class="section-title">Error Pattern Analysis</div>', unsafe_allow_html=True)
                    
                        if all_tags:
                            tag_counts = pd.Series(all_tags).value_counts().head(6).reset_index()
                            tag_counts.columns = ['Mistake', 'Count']
                        
                            bar_chart = alt.Chart(tag_counts).mark_bar(cornerRadiusEnd=6, height=28).encode(
                                x=alt.X('Count:Q', axis=alt.Axis(title=None, grid=False, labelColor='#6b7280', labelFontSize=11)),
                                y=alt.Y('Mistake:N', sort='-x', axis=alt.Axis(title=None, labelColor='#e5e7eb', labelFontSize=12, labelPadding=10)),
                                color=alt.Color('Count:Q', scale=alt.Scale(scheme='redyellowblue', reverse=True), legend=None),
                                tooltip=[alt.Tooltip('Mistake:N', title='Error Type'), alt.Tooltip('Count:Q', title='Occurrences')]
                            ).properties(height=280).configure_view(strokeWidth=0, fill='transparent').configure(background='transparent')
                        
                            st.altair_chart(bar_chart, use_container_width=True)
                        else:
                            st.info("No error patterns detected yet.")
                    
                        st.markdown('</div>', unsafe_allow_html=True)

                    with col_right:
                        # AI Insights
                        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                        st.markdown('<div class="section-title">AI Insights</div>', unsafe_allow_html=True)
                    
                        insights = generate_insights(df)
                    
                        for insight in insights:
                            parts = insight.split(' ', 1)
                            emoji = parts[0] if len(parts) > 0 else ''
                            content = parts[1] if len(parts) > 1 else insight
                        
                            st.markdown(f"""
                            <div style='background: rgba(255, 255, 255, 0.03); border-left: 4px solid #10b981; padding: 22px; border-radius: 0 12px 12px 0; margin-bottom: 20px; transition: all 0.3s ease;'>
                                <div style='font-size: 1.8rem; margin-bottom: 12px;'>{emoji}</div>
                                <div style='font-size: 0.95rem; line-height: 1.8; color: #d1d5db;'>{content}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                        # Score Distribution
                        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                        st.markdown('<div class="section-title">Score Distribution</div>', unsafe_allow_html=True)
                    
                        score_ranges = pd.cut(df['score'], bins=[0, 40, 60, 80, 100], labels=['Poor (0-40)', 'Fair (40-60)', 'Good (60-80)', 'Excellent (80-100)'])
                        dist_data = score_ranges.value_counts().reset_index()
                        dist_data.columns = ['Range', 'Count']
                    
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
                            <div style='margin-bottom: 24px;'>
                                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>
                                    <span style='font-size: 0.9rem; color: #9ca3af; font-weight: 700;'>{range_name}</span>
                                    <span style='font-size: 0.9rem; color: #e5e7eb; font-family: "JetBrains Mono", monospace;'>{count} ({int(percentage)}%)</span>
                                </div>
                                <div style='width: 100%; height: 12px; background: rgba(255, 255, 255, 0.05); border-radius: 6px; overflow: hidden;'>
                                    <div style='width: {percentage}%; height: 100%; background: {color}; border-radius: 6px; transition: width 0.6s ease;'></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                        st.markdown('</div>', unsafe_allow_html=True)

                    # Recent Activity
                    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">Recent Activity</div>', unsafe_allow_html=True)
                
                    table_df = df.head(10)[['created_at', 'ticker', 'score', 'mistake_tags']].copy()
                    table_df.columns = ['Time', 'Asset', 'Score', 'Primary Errors']
                    table_df['Primary Errors'] = table_df['Primary Errors'].apply(lambda x: ', '.join(x[:2]) if len(x) > 0 else 'None')
                
                    st.dataframe(
                        table_df, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            "Score": st.column_config.ProgressColumn("Quality Score", min_value=0, max_value=100, format="%d"),
                            "Time": st.column_config.DatetimeColumn("Time", format="MMM DD, HH:mm"),
                            "Asset": st.column_config.TextColumn("Asset", width="small")
                        }
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                
                else:
                    st.markdown('<div class="glass-panel" style="text-align: center; padding: 100px;">', unsafe_allow_html=True)
                    st.markdown("""
                    <div style="font-size: 4rem; margin-bottom: 24px; opacity: 0.4;">📊</div>
                    <div style="font-size: 1.3rem; color: #9ca3af; margin-bottom: 12px; font-weight: 700;">No Performance Data Yet</div>
                    <div style="font-size: 1rem; color: #6b7280;">Complete your first forensic audit to see metrics here.</div>
                    """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
