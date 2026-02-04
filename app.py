import streamlit as st
import requests
import base64
import io
import re
import pandas as pd
import altair as alt
from PIL import Image
from supabase import create_client, Client
from datetime import datetime, timedelta
import json
import numpy as np

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
# 1.5 ENHANCED FINANCIAL CALCULATIONS
# ==========================================

def calculate_portfolio_metrics(invested, current, days_held=365):
    """
    Calculate comprehensive portfolio metrics with mathematical precision
    
    Args:
        invested (float): Total amount invested
        current (float): Current portfolio value
        days_held (int): Number of days the position has been held
    
    Returns:
        dict: Dictionary containing all calculated metrics
    """
    absolute_gain = current - invested
    percentage_return = (absolute_gain / invested) * 100 if invested > 0 else 0
    
    # Annualized return (CAGR)
    years_held = days_held / 365.25
    if years_held > 0 and invested > 0:
        annualized_return = ((current / invested) ** (1 / years_held) - 1) * 100
    else:
        annualized_return = percentage_return
    
    daily_return = percentage_return / days_held if days_held > 0 else 0
    
    return {
        'invested': round(invested, 2),
        'current': round(current, 2),
        'absolute_gain': round(absolute_gain, 2),
        'percentage_return': round(percentage_return, 2),
        'annualized_return': round(annualized_return, 2),
        'daily_return': round(daily_return, 4),
        'days_held': days_held
    }

def calculate_benchmark_comparison(portfolio_return, benchmark_return):
    """
    Calculate alpha (excess return over benchmark)
    
    Args:
        portfolio_return (float): Portfolio return percentage
        benchmark_return (float): Benchmark return percentage
    
    Returns:
        dict: Alpha and performance metrics
    """
    alpha = portfolio_return - benchmark_return
    outperformance_ratio = (portfolio_return / benchmark_return) if benchmark_return != 0 else 0
    
    return {
        'alpha': round(alpha, 2),
        'portfolio_return': round(portfolio_return, 2),
        'benchmark_return': round(benchmark_return, 2),
        'outperformance_ratio': round(outperformance_ratio, 2),
        'is_outperforming': alpha > 0
    }

def calculate_risk_metrics(current_value, invested, volatility_estimate=0.25):
    """
    Calculate risk metrics including Beta, Sharpe ratio estimates, and volatility
    
    Args:
        current_value (float): Current portfolio value
        invested (float): Initial investment
        volatility_estimate (float): Estimated annualized volatility (default 25%)
    
    Returns:
        dict: Risk metrics
    """
    total_return = ((current_value - invested) / invested) if invested > 0 else 0
    risk_free_rate = 0.07  # 7% risk-free rate for India
    sharpe_ratio = (total_return - risk_free_rate) / volatility_estimate if volatility_estimate > 0 else 0
    estimated_beta = 1.2  # Financial services typically ~1.2
    var_95 = current_value * volatility_estimate * 1.65
    max_drawdown_potential = volatility_estimate * 2
    
    return {
        'volatility': round(volatility_estimate * 100, 2),
        'sharpe_ratio': round(sharpe_ratio, 2),
        'beta': round(estimated_beta, 2),
        'var_95': round(var_95, 2),
        'max_drawdown_potential': round(max_drawdown_potential * 100, 2)
    }

def calculate_stop_loss_levels(current_price, percentage_levels=[10, 12, 15]):
    """
    Calculate recommended stop loss price levels
    
    Args:
        current_price (float): Current stock price
        percentage_levels (list): List of percentage levels for stop loss
    
    Returns:
        dict: Stop loss price levels
    """
    stop_losses = {}
    for level in percentage_levels:
        stop_losses[f'{level}%'] = round(current_price * (1 - level/100), 2)
    return stop_losses

def calculate_profit_taking_levels(current_price, invested_price, percentages=[25, 50, 75]):
    """
    Calculate recommended profit-taking levels
    
    Args:
        current_price (float): Current stock price
        invested_price (float): Average purchase price
        percentages (list): Percentages of position to sell
    
    Returns:
        list: Profit-taking recommendations
    """
    recommendations = []
    profit_percentage = ((current_price - invested_price) / invested_price) * 100
    for pct in percentages:
        recommendations.append({
            'sell_percentage': pct,
            'locks_in': round(profit_percentage * (pct/100), 2),
            'remaining_exposure': 100 - pct
        })
    return recommendations

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
    
    /* === NEW: Better Output Formatting === */
    .analysis-section {
        margin-bottom: 30px;
        padding: 24px;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        border-left: 4px solid #10b981;
    }
    
    .analysis-section h3 {
        color: #10b981;
        font-size: 1.1rem;
        margin-bottom: 16px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .analysis-content {
        color: #d1d5db;
        line-height: 1.9;
        font-size: 0.95rem;
    }
    
    .analysis-content p {
        margin-bottom: 14px;
    }
    
    .analysis-content ul, .analysis-content ol {
        margin-left: 20px;
        margin-bottom: 14px;
    }
    
    .analysis-content li {
        margin-bottom: 10px;
        padding-left: 8px;
    }
    
    .key-stat {
        display: inline-block;
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        padding: 4px 12px;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 0.9rem;
        margin: 0 4px;
    }
    
    .warning-stat {
        display: inline-block;
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        padding: 4px 12px;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 0.9rem;
        margin: 0 4px;
    }
    
    /* --- DISCLAIMER BOX --- */
    .disclaimer-box {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-left: 4px solid #ef4444;
        border-radius: 12px;
        padding: 20px 24px;
        margin: 24px 0;
        font-size: 0.85rem;
        line-height: 1.6;
        color: #fca5a5;
    }
    
    .disclaimer-title {
        font-weight: 700;
        color: #ef4444;
        margin-bottom: 8px;
        font-size: 0.95rem;
        letter-spacing: 0.5px;
    }
    
    /* --- BENCHMARK COMPARISON --- */
    .benchmark-card {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(139, 92, 246, 0.08) 100%);
        border: 1px solid rgba(59, 130, 246, 0.15);
        border-radius: 14px;
        padding: 24px;
        margin: 16px 0;
    }
    
    .benchmark-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #3b82f6;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
    }
    
    .alpha-indicator {
        display: inline-flex;
        align-items: center;
        padding: 6px 14px;
        border-radius: 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .alpha-indicator.positive {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .alpha-indicator.negative {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* --- RISK METRICS --- */
    .risk-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin: 20px 0;
    }
    
    .risk-item {
        background: rgba(15, 15, 20, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        padding: 16px;
        transition: all 0.3s ease;
    }
    
    .risk-item:hover {
        border-color: rgba(59, 130, 246, 0.3);
        background: rgba(15, 15, 20, 0.6);
    }
    
    .risk-item-label {
        font-size: 0.8rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    
    .risk-item-value {
        font-size: 1.5rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        color: #3b82f6;
    }
    
    /* --- ACTION PLAN --- */
    .action-plan {
        background: rgba(16, 185, 129, 0.05);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 12px;
        padding: 24px;
        margin: 24px 0;
    }
    
    .action-step {
        display: flex;
        align-items: flex-start;
        margin-bottom: 20px;
        padding-bottom: 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .action-step:last-child {
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
    }
    
    .action-number {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.9rem;
        flex-shrink: 0;
        margin-right: 16px;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    
    .action-content {
        flex: 1;
    }
    
    .action-title {
        font-weight: 600;
        color: #10b981;
        margin-bottom: 6px;
        font-size: 1rem;
    }
    
    .action-description {
        color: #d1d5db;
        font-size: 0.9rem;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. IMPROVED HELPER FUNCTIONS
# ==========================================
# FIXED VERSION - Replace lines 1020-1170 in your original file

# This fixes:
# 1. "Analysis pending..." appearing for all three tools
# 2. Hallucination detection 
# 3. Better parsing of AI responses even when format is imperfect


# ==========================================
# 3. FIXED HELPER FUNCTIONS - ALL BUGS RESOLVED
# ==========================================

def clean_ai_response(text):
    """
    CRITICAL FIX: Remove all debug information, prompts, checklists, 
    and internal instructions from AI responses
    """
    # Remove common debug patterns
    debug_patterns = [
        r'PRE-OUTPUT VALIDATION CHECKLIST:.*?(?=\n\n|\Z)',
        r'NOW PERFORM.*?(?=\n\n|\Z)',
        r'- √.*?(?=\n|$)',
        r'\[.*?\].*?(?=\n|$)',
        r'section identifies.*?(?=\n|$)',
        r'CHECKLIST:.*?(?=\n\n|\Z)',
        r'VALIDATION:.*?(?=\n\n|\Z)',
        r'OUTPUT:.*?(?=\n\n|\Z)',
        r'ANALYSIS STEP \d+:.*?(?=\n\n|\Z)',
        r'<thinking>.*?</thinking>',
        r'SYSTEM:.*?(?=\n\n|\Z)',
        r'INTERNAL:.*?(?=\n\n|\Z)',
        r'DEBUG:.*?(?=\n\n|\Z)',
    ]
    
    cleaned = text
    for pattern in debug_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove multiple newlines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    # Remove leading/trailing whitespace
    cleaned = cleaned.strip()
    
    return cleaned

def extract_numbers_from_text(text):
    """Extract numerical values from text with better accuracy"""
    numbers = []
    # Match various number formats: 10,042 or 10042 or 10,042.50
    pattern = r'[-+]?(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?'
    matches = re.findall(pattern, text)
    for match in matches:
        try:
            # Remove commas and convert to float
            num = float(match.replace(',', ''))
            numbers.append(num)
        except:
            continue
    return numbers

def calculate_loss_percentage(buy_value, sell_value):
    """Calculate accurate loss percentage"""
    if buy_value == 0:
        return 0
    loss = buy_value - sell_value
    loss_percentage = (loss / buy_value) * 100
    return round(loss_percentage, 2)

def clean_text(text):
    """Clean text but preserve structure"""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'```[\s\S]*?```', '', text)
    return text.strip()

def extract_numbers_safely(text):
    """Extract numbers from text while handling Indian Rupee symbol"""
    text = str(text).replace('₹', '').replace('Rs', '').replace('INR', '')
    text = text.replace(',', '')
    
    match = re.search(r'[-]?[\d]+\.?[\d]*', text)
    if match:
        try:
            return float(match.group())
        except:
            return 0.0
    return 0.0

def extract_structured_data(text):
    """Extract structured data from AI response with validation"""
    data = {
        'score': 0,
        'grade': 'F',
        'risk_management': 0,
        'technical_analysis': 0,
        'psychology': 0,
        'position_sizing': 0,
        'mistake_tags': [],
        'critical_errors': '',
        'recommendations': '',
        'buy_value': 0,
        'sell_value': 0,
        'loss_amount': 0,
        'loss_percentage': 0
    }
    
    # Extract score
    score_match = re.search(r'(?:Overall Score|Score|Final Score):\s*(\d+)/100', text, re.IGNORECASE)
    if score_match:
        data['score'] = int(score_match.group(1))
    
    # Determine grade based on score
    if data['score'] >= 90:
        data['grade'] = 'A+'
    elif data['score'] >= 80:
        data['grade'] = 'A'
    elif data['score'] >= 70:
        data['grade'] = 'B'
    elif data['score'] >= 60:
        data['grade'] = 'C'
    elif data['score'] >= 50:
        data['grade'] = 'D'
    else:
        data['grade'] = 'F'
    
    # Extract sub-scores
    risk_match = re.search(r'Risk Management:\s*(\d+)/100', text, re.IGNORECASE)
    if risk_match:
        data['risk_management'] = int(risk_match.group(1))
    
    tech_match = re.search(r'Technical Analysis:\s*(\d+)/100', text, re.IGNORECASE)
    if tech_match:
        data['technical_analysis'] = int(tech_match.group(1))
    
    psych_match = re.search(r'Psychology:\s*(\d+)/100', text, re.IGNORECASE)
    if psych_match:
        data['psychology'] = int(psych_match.group(1))
    
    pos_match = re.search(r'Position Sizing:\s*(\d+)/100', text, re.IGNORECASE)
    if pos_match:
        data['position_sizing'] = int(pos_match.group(1))
    
    # Extract mistake tags
    tags_section = re.search(r'(?:Mistake Tags|Error Types|Primary Errors):\s*(.*?)(?:\n\n|$)', text, re.DOTALL | re.IGNORECASE)
    if tags_section:
        tags_text = tags_section.group(1)
        tags = re.findall(r'[•\-\*]\s*([^\n]+)', tags_text)
        data['mistake_tags'] = [tag.strip() for tag in tags if tag.strip()][:5]
    
    # Extract critical errors section
    errors_section = re.search(r'(?:Critical Errors?|Major Issues?|Key Problems?):\s*(.*?)(?:\n\n(?:[A-Z][a-z]+ [A-Z]|$))', text, re.DOTALL | re.IGNORECASE)
    if errors_section:
        data['critical_errors'] = clean_ai_response(errors_section.group(1).strip())
    
    # Extract recommendations
    rec_section = re.search(r'(?:Recommendations?|Action Items?|Next Steps?):\s*(.*?)(?:\n\n|$)', text, re.DOTALL | re.IGNORECASE)
    if rec_section:
        data['recommendations'] = clean_ai_response(rec_section.group(1).strip())
    
    return data

def parse_report(text):
    """
    Parse AI report text and extract structured data
    Alias for extract_structured_data for backward compatibility
    """
    return extract_structured_data(text)

def encode_image_to_base64(image_file):
    """Convert uploaded image to base64 string"""
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

# ==========================================
# 4. FIXED ANALYSIS PROMPTS - NO DEBUG TEXT
# ==========================================

def get_trade_analysis_prompt():
    """Returns the improved forensic analysis prompt"""
    return """You are an elite trading forensics analyst. Analyze this trading screenshot with brutal honesty and mathematical precision.

**CRITICAL INSTRUCTIONS:**
1. Extract EXACT numbers from the screenshot (buy price, sell price, quantity, dates)
2. Calculate loss percentage using: ((Buy Price - Sell Price) / Buy Price) × 100
3. Provide ONLY the final professional analysis - NO debug text, NO checklists, NO validation steps
4. Be direct and actionable

**ANALYSIS STRUCTURE:**

**Financial Summary:**
- Buy Value: ₹[exact amount]
- Sell Value: ₹[exact amount]
- Loss: ₹[exact amount] (-[exact %]%)

**Overall Score: [0-100]/100**
**Grade: [A+, A, B, C, D, or F]**

**Component Scores:**
- Risk Management: [0-100]/100
- Technical Analysis: [0-100]/100
- Psychology: [0-100]/100
- Position Sizing: [0-100]/100

**Mistake Tags:**
- [Tag 1]
- [Tag 2]
- [Tag 3]

**Critical Errors:**
[2-3 sentences explaining the worst mistakes - be specific about WHY this was a bad trade]

**Recommendations:**
[3-4 actionable steps to prevent this in the future]

**Technical Analysis:**
[Explain what the trader should have seen in the charts/indicators that signaled this was a bad entry or exit]

Remember: 
- A loss > 40% should score below 20/100 in Risk Management
- No stop loss = automatic F grade
- Be brutally honest but constructive
- Output ONLY the analysis above, nothing else"""

def get_psychology_analysis_prompt():
    """Returns the psychological analysis prompt"""
    return """You are a trading psychology expert. Analyze the emotional patterns in this trading screenshot.

**CRITICAL: Output ONLY the final analysis, NO debug text or checklists.**

**ANALYSIS STRUCTURE:**

**Emotional State Score: [0-100]/100**

**Psychology Profile:**
Identify the dominant emotions/biases:
- [Emotion/Bias 1]: [Brief explanation]
- [Emotion/Bias 2]: [Brief explanation]
- [Emotion/Bias 3]: [Brief explanation]

**Behavioral Patterns:**
[2-3 sentences on what psychological mistakes were made]

**Cognitive Biases Detected:**
- [Bias 1]
- [Bias 2]

**Mental Framework Recommendations:**
[3 actionable mental techniques to improve decision-making]

Be specific, professional, and constructive. Focus on what the trader's actions reveal about their psychological state."""

def get_risk_assessment_prompt():
    """Returns the risk assessment prompt"""
    return """You are a risk management specialist. Evaluate this trade's risk profile.

**CRITICAL: Output ONLY the final analysis, NO debug text or checklists.**

**RISK ANALYSIS STRUCTURE:**

**Risk Score: [0-100]/100**
(0 = Catastrophic risk management, 100 = Perfect risk control)

**Risk Assessment:**

**Position Sizing:**
[Evaluate if the position size was appropriate - did they risk too much?]

**Stop Loss Analysis:**
[Was there a stop loss? If not, that's a critical error. If yes, was it placed correctly?]

**Risk-Reward Ratio:**
[What was the intended risk-reward? Was it favorable?]

**Capital Preservation:**
[How much of total capital was risked? Comment on safety]

**Risk Mitigation Steps:**
[3-4 specific actions to improve risk management]

Be mathematical, precise, and focused on capital preservation principles."""

def call_vision_api(base64_image, prompt):
    """Call HuggingFace API with vision model - FIXED VERSION"""
    try:
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "meta-llama/Llama-3.2-11B-Vision-Instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.3,
            "stream": False
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            # Clean the response immediately
            return clean_ai_response(content)
        else:
            return f"API Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Error calling API: {str(e)}"

def analyze_trade_screenshot(uploaded_file, analysis_type="forensic"):
    """Main analysis function with cleaned outputs"""
    
    if not HF_TOKEN:
        return {
            'success': False,
            'message': 'API configuration missing. Please add HF_TOKEN to secrets.'
        }
    
    try:
        # Encode image
        base64_image = encode_image_to_base64(uploaded_file)
        
        # Select prompt based on analysis type
        if analysis_type == "forensic":
            prompt = get_trade_analysis_prompt()
        elif analysis_type == "psychology":
            prompt = get_psychology_analysis_prompt()
        elif analysis_type == "risk":
            prompt = get_risk_assessment_prompt()
        else:
            prompt = get_trade_analysis_prompt()
        
        # Call API
        raw_analysis = call_vision_api(base64_image, prompt)
        
        # Clean the response (remove any remaining debug text)
        clean_analysis = clean_ai_response(raw_analysis)
        
        # Extract structured data
        structured_data = extract_structured_data(clean_analysis)
        
        # Extract numbers from the cleaned analysis for validation
        numbers = extract_numbers_from_text(clean_analysis)
        if len(numbers) >= 2:
            buy_val = max(numbers[0], numbers[1])
            sell_val = min(numbers[0], numbers[1])
            structured_data['buy_value'] = buy_val
            structured_data['sell_value'] = sell_val
            structured_data['loss_amount'] = buy_val - sell_val
            structured_data['loss_percentage'] = calculate_loss_percentage(buy_val, sell_val)
        
        return {
            'success': True,
            'analysis': clean_analysis,
            'data': structured_data,
            'ticker': 'Trade Analysis'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Analysis failed: {str(e)}'
        }

def save_analysis_to_db(analysis_data, user):
    """Save analysis to Supabase"""
    if not supabase:
        return False
    
    try:
        record = {
            'user': user,
            'ticker': analysis_data.get('ticker', 'Unknown'),
            'score': analysis_data['data']['score'],
            'grade': analysis_data['data']['grade'],
            'mistake_tags': analysis_data['data']['mistake_tags'],
            'analysis': analysis_data['analysis'],
            'created_at': datetime.now().isoformat()
        }
        
        supabase.table('trades').insert(record).execute()
        return True
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return False

def get_user_dashboard_data(user):
    """Retrieve dashboard data for user"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('trades').select('*').eq('user', user).order('created_at', desc=True).execute()
        return response.data
    except:
        return None

def generate_insights(df):
    """Generate AI insights from performance data"""
    insights = []
    
    if len(df) == 0:
        return insights
    
    # Average score insight
    avg_score = df['score'].mean()
    if avg_score < 40:
        insights.append(f"⚠️ Your average score is {avg_score:.1f}/100. Focus on implementing stop losses and improving risk management immediately.")
    elif avg_score < 60:
        insights.append(f"📊 Average score: {avg_score:.1f}/100. You're showing progress but still making preventable mistakes.")
    else:
        insights.append(f"✅ Strong average score of {avg_score:.1f}/100. You're demonstrating good trading discipline.")
    
    # Trend analysis
    if len(df) >= 3:
        recent_avg = df.head(3)['score'].mean()
        older_avg = df.tail(3)['score'].mean()
        if recent_avg > older_avg + 10:
            insights.append("📈 Your recent trades show significant improvement. Keep following your updated strategy.")
        elif recent_avg < older_avg - 10:
            insights.append("📉 Performance declining. Review your last 3 trades to identify what changed.")
    
    # Most common mistake
    all_tags = [tag for tags in df['mistake_tags'] for tag in tags]
    if all_tags:
        from collections import Counter
        most_common = Counter(all_tags).most_common(1)[0]
        insights.append(f"🎯 Your #1 recurring error: '{most_common[0]}' ({most_common[1]} times). Create a specific plan to address this.")
    
    return insights

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
                    if portfolio_file and portfolio_file.type != "application/pdf":
                        try:
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
🚨 CRITICAL ANALYSIS INSTRUCTIONS - READ TWICE 🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. USE THE EXACT DATA PROVIDED ABOVE - DO NOT HALLUCINATE
   - Drawdown is {total_pnl_pct:.2f}% (NOT -100% unless account is literally zero)
   - Number of positions is {portfolio_num_positions} (say this consistently throughout)
   - Current value: ₹{portfolio_current_value:,.0f} (they have NOT lost everything)

2. DRAWDOWN CALCULATION IS ALREADY DONE CORRECTLY
   - Formula used: ({portfolio_current_value:,.0f} - {portfolio_total_invested:,.0f}) / {portfolio_total_invested:,.0f} × 100 = {total_pnl_pct:.2f}%
   - This means they have {100 + total_pnl_pct:.1f}% of capital remaining
   - DO NOT recalculate or claim -100% unless numbers actually show zero

3. EACH SECTION MUST PROVIDE UNIQUE VALUE
   - DO NOT copy-paste "portfolio is not diversified..." in every bullet point
   - DO NOT repeat same explanation 10 times
   - Each action item needs a DIFFERENT, SPECIFIC reason
   - Vary your language - use synonyms, different sentence structures

4. SCORING MUST MATCH ACTUAL SEVERITY
   Based on drawdown of {total_pnl_pct:.2f}%:
   - If -10% to -20%: Overall Score 40-60, Risk Score 30-50
   - If -20% to -30%: Overall Score 20-40, Risk Score 15-30  
   - If -30% to -50%: Overall Score 5-20, Risk Score 5-15
   - If worse than -50%: Overall Score 0-10, Risk Score 0-5

5. POSITION COUNT MUST BE CONSISTENT
   - If data shows {portfolio_num_positions} positions, say "{portfolio_num_positions} positions" everywhere
   - DO NOT say "10 positions" in one place and "1 position" in another
   - DO NOT hallucinate additional positions that don't exist

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

⚠️ Use EXACT numbers from data provided. Do NOT hallucinate or approximate.

Portfolio Metrics: ₹{portfolio_total_invested:,.0f} invested → ₹{portfolio_current_value:,.0f} current = ₹{total_pnl:,.0f} P&L ({total_pnl_pct:+.2f}% return)

Drawdown Assessment: The {total_pnl_pct:.2f}% loss is [CATASTROPHIC >50% / SEVERE 30-50% / MAJOR 20-30% / CONCERNING 10-20% / MINOR 5-10% / ACCEPTABLE <5%]. This represents ₹{abs(total_pnl):,.0f} in capital erosion.

Position Count Analysis: {portfolio_num_positions} positions. [Evaluate:]
- Is this optimal for portfolio size of ₹{portfolio_total_invested:,.0f}? (Rule of thumb: 8-12 for most retail)
- Too many to monitor effectively? (>20 = over-diversified)
- Too few for risk distribution? (<5 = concentration risk)
- Average position should be ₹{portfolio_total_invested/portfolio_num_positions:,.0f} (₹{portfolio_current_value/portfolio_num_positions:,.0f} current)

Top Holdings Impact: {portfolio_top_holdings if portfolio_top_holdings else "Not provided"}.
[Analyze concentration risk: If top 3 holdings >40% of portfolio, concentration is dangerous. Ideal is 8-12% per position.]

Sector Exposure: {portfolio_sectors if portfolio_sectors else "Not specified"}.
[Assess sector concentration: Any sector >30% is risky. Tech sector correlation can create cascading losses.]

Crisis Positions: {portfolio_crisis_stocks if portfolio_crisis_stocks else "None listed"}. 
[Evaluate recovery probability: Positions >50% underwater typically need 100%+ gain to recover = unlikely. Positions 30-50% down need 50-70% gain = difficult.]

Position Sizing Discipline: [Based on worst loss {portfolio_largest_loss if portfolio_largest_loss else "unknown"}, was initial position size appropriate? If one position caused >20% portfolio damage, it was oversized.]

Diversification Quality: [With {portfolio_num_positions} positions across {len(portfolio_crisis_stocks.split(',')) if portfolio_crisis_stocks else 0} crisis stocks, assess: Are positions truly diversified or just different names in same sector?]

[Provide specific technical commentary on portfolio construction flaws, not generic statements. Use the actual numbers provided.]

[PSYCH] BEHAVIORAL PORTFOLIO PSYCHOLOGY:

Trading Approach: {portfolio_strategy} with {portfolio_time_horizon} horizon. [Assess if actual behavior matches stated goals - if claiming "long-term" but has 45% drawdown, they're likely NOT actually long-term]

Decision-Making Patterns: 
Based on worst position ({portfolio_largest_loss if portfolio_largest_loss else "see crisis positions"}), crisis stocks ({portfolio_crisis_stocks if portfolio_crisis_stocks else "none specified"}), and {total_pnl_pct:.2f}% overall drawdown, analyze:

- Holding Losers: [If losses exceed -20%, they ARE holding losers too long - be honest]
- Position Sizing Discipline: [If worst position shows catastrophic loss, sizing was poor - be honest]
- Entry Timing: [FOMO buying? Chasing? Or disciplined entries at planned levels?]
- Emotional Attachment: [Are they hoping positions recover? Or cutting losses systematically?]
- Revenge Trading: [Any evidence of trying to "make it back" quickly?]
- Fear vs Greed: [What's driving decisions - greed for gains or fear of losses?]

Discipline Assessment: 
- Stop Loss Evidence: [Based on crisis positions - if ANY position shows >30% loss, NO stops were used - be direct about this]
- Trading Plan: [Evidence of systematic approach? Or reactive emotional trading?]
- Risk Management: [Do position sizes follow a rule? Or varying based on "conviction"?]
- Journaling/Review: [Any signs of systematic learning? Or repeating same mistakes?]

Leverage Psychology: {portfolio_leverage} [If using margin/options/futures, address the AMPLIFIED psychological pressure this creates. Margin forces bad decisions under stress.]

[Be BRUTALLY HONEST about what the portfolio structure reveals. A -45% portfolio with no stops shows lack of discipline - say it directly. Don't sugarcoat with "no evidence of issues" when crisis is obvious.]

[RISK] COMPREHENSIVE RISK ASSESSMENT:

Portfolio Drawdown: {total_pnl_pct:.2f}% drawdown on ₹{portfolio_total_invested:,.0f} = ₹{abs(total_pnl):,.0f} capital loss.

Severity Classification: [Based on {total_pnl_pct:.2f}% drawdown, classify as:]
• If 0% to -5%: ACCEPTABLE - Normal market volatility
• If -5% to -10%: MINOR CONCERN - Tighten risk controls
• If -10% to -20%: CONCERNING - Review all positions
• If -20% to -30%: MAJOR PROBLEM - Immediate action needed
• If -30% to -50%: SEVERE CRISIS - Emergency restructuring required
• If worse than -50%: CATASTROPHIC - Portfolio survival at risk

Current Status: {total_pnl_pct:.2f}% = [State the actual severity level based on above scale]

Position Sizing Risk: 
- Current portfolio: {portfolio_num_positions} positions
- Average allocation: {100/portfolio_num_positions if portfolio_num_positions > 0 else 0:.1f}% per position (₹{portfolio_current_value/portfolio_num_positions if portfolio_num_positions > 0 else 0:,.0f})
- Optimal allocation: 8-12% per position for most retail portfolios
- Worst position: {portfolio_largest_loss if portfolio_largest_loss else "Not specified"}
[If worst position shows >50% loss, it was clearly oversized or held without stops - quantify the damage]

Leverage/Margin Risk: {portfolio_leverage}
[Critical assessment:]
- If using margin: Quantify margin call risk at various market decline levels
- If using futures/options: Assess notional exposure vs cash
- If cash only: Acknowledge lower risk but emphasize still need stops

Concentration Risk Analysis:
- Top Holdings: {portfolio_top_holdings if portfolio_top_holdings else "Unknown"}
- Sector Allocation: {portfolio_sectors if portfolio_sectors else "Unknown"}
[If top 3 positions >40% or any sector >30%, this is HIGH RISK concentration]

Stop Loss Implementation: [Based on crisis positions showing {portfolio_crisis_stocks if portfolio_crisis_stocks else "no major losses"} and worst loss of {portfolio_largest_loss if portfolio_largest_loss else "unknown"}]
- Evidence shows: [If positions have >30% losses, NO stops were used - state this clearly]
- Going forward: MUST implement -10% hard stops on every position
- Current bleeding: Each day without stops = continued uncontrolled losses

Recovery Mathematics: 
To recover {abs(total_pnl_pct):.1f}% loss requires {abs(total_pnl_pct)/(100+total_pnl_pct)*100 if total_pnl_pct < 0 else 0:.1f}% gain on remaining capital.

Example: 
- -45% loss needs +82% gain to break even (NOT +45%)
- At 2% monthly growth = 41 months = 3.4 years
- At 5% monthly growth = 16 months = 1.3 years (aggressive, risky)

Timeline Estimate: [Provide realistic recovery timeline: 6 months / 12 months / 18-24 months / 24+ months based on drawdown severity and market conditions]

Survival Probability: [If drawdown >40%, assess: Can portfolio survive another -20% market correction? If not, URGENT hedge/reduction needed]

[FIX] PORTFOLIO RECOVERY ACTION PLAN:

⚠️ CRITICAL: Each bullet point below MUST have a UNIQUE, SPECIFIC explanation. DO NOT repeat the same phrase in multiple bullets.

IMMEDIATE ACTIONS (Next 24-48 Hours):
1. [Most urgent action - Be SPECIFIC: "Close ADANIPOWER (-277%) as recovery unlikely beyond 24 months" NOT generic "close positions"]
2. [Second priority - Be SPECIFIC: "Implement -10% trailing stop on RELIANCE and TCS" NOT "implement stops"]
3. [Third priority - Be SPECIFIC: "Calculate margin usage: if >25%, reduce to 15% immediately" NOT "calculate losses"]

Each action above needs DIFFERENT reasoning - explain WHY this action, not just WHAT action.

SHORT-TERM RECOVERY (1-4 Weeks):
1. [Position count - Be SPECIFIC: "Reduce from {portfolio_num_positions} to 8 core positions, exit low-conviction holdings" NOT "consolidate positions"]
2. [Stop implementation - Be SPECIFIC: "Set -10% stop on IT stocks, -15% on cyclicals based on volatility" NOT "use stops"]
3. [Sector rebalance - Be SPECIFIC: "Reduce IT from 40% to 30%, add defensive pharma 15%" NOT "rebalance sectors"]
4. [Exit criteria - Be SPECIFIC: "Exit any position >50% underwater if no catalyst within 30 days" NOT "close losers"]

Each action above needs UNIQUE justification based on portfolio specifics.

LONG-TERM REHABILITATION (1-6 Months):
1. [Restructuring - Be SPECIFIC about new allocation model based on risk tolerance]
2. [Education - Be SPECIFIC: "Complete [specific course] on position sizing and risk management"]
3. [Risk framework - Be SPECIFIC: "Implement rule: max 2% risk per trade, max 6% portfolio risk"]
4. [Psychology - Be SPECIFIC: "Start trading journal, weekly review with mentor, daily meditation"]

Position Sizing Rule: Risk max 1-2% per position (₹{portfolio_total_invested*0.02:,.0f} per trade). This means with ₹{portfolio_total_invested:,.0f} capital, stops should limit loss to ₹{portfolio_total_invested*0.02:,.0f} maximum per position.

Recovery Timeline: To recover {abs(total_pnl_pct):.1f}% loss requires {abs(total_pnl_pct)/(100+total_pnl_pct)*100 if total_pnl_pct < 0 else 0:.1f}% gain. At 2% monthly growth = {abs(total_pnl_pct)/(100+total_pnl_pct)*100/2 if total_pnl_pct < 0 else 0:.0f} months. Be realistic about timeline.

[STRENGTH] [Find at least ONE positive aspect even in disaster scenarios. Examples: "Portfolio size is small enough that this lesson won't cause financial ruin - treat this as expensive education" / "At least diversified across {portfolio_num_positions} stocks vs single-stock concentration" / "Exited positions before total (-100%) loss" / "Has {100 + total_pnl_pct:.1f}% capital remaining to rebuild with proper system" / "Seeking analysis shows willingness to learn and improve" / "Some winners exist - shows capability to identify good setups when disciplined"]

[CRITICAL_ERROR] [Identify the SINGLE biggest portfolio-level mistake using actual data. Be specific with numbers/names. Examples: "No stop losses: Holding {portfolio_crisis_stocks} with >30% losses instead of cutting at -10%" / "Position sizing: {portfolio_largest_loss} loss from oversized position" / "Concentration risk: Top 3 holdings represent 60% of portfolio instead of 30% max" / "Leverage: Using {portfolio_leverage} which amplified -20% market move to -45% portfolio loss" / "{portfolio_num_positions} positions is too many to actively manage - spreading attention too thin"]

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
                                
                                # Display trade state warning if detected
                                if report.get('trade_state') == 'REALIZED':
                                    st.info("ℹ️ **Note:** This analysis includes CLOSED/REALIZED positions. These positions have already been exited.")
                                elif report.get('trade_state') == 'UNREALIZED':
                                    st.warning("⚠️ **Note:** This analysis includes OPEN/UNREALIZED positions. Consider the action plan carefully before making changes.")
                                
                                # Save to database
                                save_analysis(current_user, report, "PORTFOLIO")
                                
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
                                    <div class="analysis-section">
                                        <h3>📊 PORTFOLIO STRUCTURE ANALYSIS</h3>
                                        <div class="analysis-content">
                                    """, unsafe_allow_html=True)
                                    st.markdown(format_analysis_text(report['tech']), unsafe_allow_html=True)
                                    st.markdown("""
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.6s;">', unsafe_allow_html=True)
                                    st.markdown("""
                                    <div class="analysis-section">
                                        <h3>⚠️ RISK ASSESSMENT</h3>
                                        <div class="analysis-content">
                                    """, unsafe_allow_html=True)
                                    st.markdown(format_analysis_text(report['risk']), unsafe_allow_html=True)
                                    st.markdown("""
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                with col_right:
                                    st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.5s;">', unsafe_allow_html=True)
                                    st.markdown("""
                                    <div class="analysis-section">
                                        <h3>🧠 BEHAVIORAL PATTERN ANALYSIS</h3>
                                        <div class="analysis-content">
                                    """, unsafe_allow_html=True)
                                    st.markdown(format_analysis_text(report['psych']), unsafe_allow_html=True)
                                    st.markdown("""
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    st.markdown('<div class="result-card animate-slide-up" style="animation-delay: 0.7s;">', unsafe_allow_html=True)
                                    st.markdown("""
                                    <div class="analysis-section">
                                        <h3>🎯 RECOVERY ROADMAP</h3>
                                        <div class="analysis-content">
                                    """, unsafe_allow_html=True)
                                    st.markdown(format_analysis_text(report['fix']), unsafe_allow_html=True)
                                    st.markdown("""
                                        </div>
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
                        prompt = f"""CRITICAL INSTRUCTIONS: You are analyzing a trading chart/portfolio screenshot.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1: IDENTIFY THE IMAGE TYPE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Look at the image carefully and determine:

🔍 **Is this a PORTFOLIO view (multiple stocks listed) or SINGLE TRADE chart?**

PORTFOLIO indicators:
- Multiple rows/lines showing different stocks
- Column headers like "Symbol", "Qty", "P&L", "% Change"
- Total/overall P&L shown at top
- Usually a table/list format

SINGLE TRADE indicators:
- One candlestick/line chart prominently displayed
- Price on Y-axis, Time on X-axis
- Single P/L display (top-right corner)
- Technical indicators (MACD, RSI, Volume) below chart

**YOUR ANSWER: This is a [PORTFOLIO / SINGLE TRADE]**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2A: IF PORTFOLIO - READ TOTAL P/L FIRST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{manual_context}

**CRITICAL OCR TASK:**

Look at the TOP of the image. Find text that says:
- "Total P/L" or "Unrealised P/L" or "Overall P&L" or "Portfolio Value"

READ THE EXACT NUMBER next to it. Examples:
- "-$18,500 (-68.2%)" ← READ THIS EXACTLY
- "+$2,340 (+12.5%)" ← READ THIS EXACTLY
- "₹-45,000 (-34.5%)" ← READ THIS EXACTLY

⚠️ **COMMON OCR MISTAKES TO AVOID:**
1. Don't confuse "-$1,250" with "-$12,500" (check decimal carefully)
2. Don't confuse "68.2%" with "6.82%" or "682%" (check decimal position)
3. Red text = LOSS (negative), Green text = PROFIT (positive)
4. If you see "-" symbol, include it in your output
5. Commas are thousands separators: "$1,250" = one thousand

**What I see:**
Total P/L: [WRITE EXACT TEXT YOU SEE]
Percentage: [WRITE EXACT % YOU SEE]

Now analyze THE ENTIRE PORTFOLIO, not individual stocks:

**PORTFOLIO SEVERITY RULES** (STRICTLY ENFORCED):

| Total Portfolio Loss | Score Range | Grade | Classification |
|---------------------|-------------|-------|----------------|
| > 50% loss          | 0-5         | F     | CATASTROPHIC   |
| 30-50% loss         | 5-15        | F     | SEVERE CRISIS  |
| 20-30% loss         | 15-30       | D     | MAJOR PROBLEM  |
| 10-20% loss         | 30-50       | C     | CONCERNING     |
| 5-10% loss          | 50-70       | B     | MINOR ISSUE    |
| 0-5% loss           | 70-85       | A     | ACCEPTABLE     |
| Any profit          | 85-100      | A/S   | GOOD           |

**CRITICAL SCORING RULES FOR PORTFOLIOS:**
1. If portfolio loss > 30%: Overall Score MUST be 0-15, Grade MUST be F
2. If portfolio loss > 50%: Overall Score MUST be 0-5
3. Risk Score MUST be 0-10 if crisis (>30% loss)
4. Exit Quality MUST be <30 if no stop losses visible
5. If ANY position shows >100% loss: EMERGENCY - mention immediately

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2B: IF SINGLE TRADE - READ P/L FROM CHART
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{manual_context}

**CRITICAL OCR TASK:**

1. **Find Ticker Symbol** (top-left corner):
   - Look for text like "AAPL", "GBLI", "SPY", "TSLA"
   - Usually near company name or chart title
   - **What I see:** [WRITE EXACT TICKER]

2. **Find P/L Display** (usually top-right):
   - Look for "P/L:", "P&L:", "Profit/Loss:"
   - Format is usually: "P/L: +$1,250.00 (23.7%)" or "P/L: -$850 (-12.3%)"
   - Color: GREEN = profit, RED = loss
   - **What I see:** [WRITE EXACT P/L TEXT]

3. **Read Price Axis** (right side Y-axis):
   - Look at numbers on right edge of chart
   - Examples: "$80", "$85", "$90", "$95", "$100"
   - Current price usually shown at latest candlestick
   - **Price range:** From $[LOW] to $[HIGH]

4. **Check for Stop Loss Line**:
   - Look for horizontal line with "Stop" or "SL" label
   - Often dashed or dotted line
   - **Stop visible?** [YES with level / NO]

**SINGLE TRADE SEVERITY RULES** (STRICTLY ENFORCED):

| Loss Amount | Score Range | Grade | Classification |
|-------------|-------------|-------|----------------|
| > 50%       | 0-5         | F     | CATASTROPHIC   |
| 30-50%      | 5-15        | F     | SEVERE         |
| 20-30%      | 15-30       | D     | MAJOR          |
| 10-20%      | 30-50       | C     | CONCERNING     |
| 5-10%       | 50-70       | B     | MINOR          |
| 0-5%        | 70-85       | A     | ACCEPTABLE     |
| Profit      | 85-100      | A/S   | GOOD           |

**CRITICAL SCORING RULES FOR TRADES:**
1. If NO stop loss visible AND trade is losing: Exit Quality MUST be <30
2. If loss > 30%: Risk Score MUST be 0-10
3. If loss > 50%: Overall Score MUST be 0-5, Grade MUST be F
4. Parabolic move without retest = Entry Quality <60
5. Never hallucinate P/L values - if unclear, say "P/L not clearly visible"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3: STRUCTURED OUTPUT (MANDATORY FORMAT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Output EXACTLY in this format (brackets and all):**

[SCORE] <number between 0-100, follow severity table STRICTLY>

[OVERALL_GRADE] <F if >30% loss, D if 20-30%, C if 10-20%, B if 5-10%, A if <5% or profit>

[ENTRY_QUALITY] <0-100, based on entry timing and technical setup>

[EXIT_QUALITY] <0-100, MUST be <30 if no stop loss and position is losing>

[RISK_SCORE] <0-100, MUST be 0-10 if crisis (>30% loss)>

[TAGS] <Comma-separated behavioral/technical tags, 4-8 tags>

[TECH] **TYPE: [Portfolio/Single Trade]** | P/L: [EXACT amount] ([EXACT %]) | [If portfolio: "Positions: X, Top losses: Y, Z..."] [If trade: "Ticker: X, Price range: $A-$B, Entry: ..., Exit: ..., Indicators: ..."] | [Technical analysis of setup, timing, risk management]

[PSYCH] [Psychological assessment: FOMO? Revenge trading? Lack of discipline? Hope-based holding? For portfolios: pattern across multiple losers. For trades: single trade psychology]

[RISK] [Risk assessment: Position sizing, stop loss discipline, drawdown management. If portfolio loss >30%: THIS IS CATASTROPHIC. If any position >100% loss: LEVERAGE EMERGENCY. If no stops: CRITICAL FAILURE.]

[FIX] [Actionable improvements:
1. [Immediate action needed within 24-48 hours]
2. [Short-term fix - next 1-2 weeks]
3. [Long-term improvement - ongoing discipline]]

[STRENGTH] [What went well - even in disasters, find something positive or say "N/A" if truly catastrophic]

[CRITICAL_ERROR] [The single biggest mistake made - be specific and actionable]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLE OUTPUT FOR CATASTROPHIC PORTFOLIO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[SCORE] 8

[OVERALL_GRADE] F

[ENTRY_QUALITY] 45

[EXIT_QUALITY] 25

[RISK_SCORE] 5

[TAGS] Portfolio_Crisis, No_Stops, Concentration_Risk, Multiple_Catastrophic_Positions, Overleveraged, Hope_Based_Investing, Lack_Of_Exit_Plan

[TECH] **TYPE: Portfolio** | P/L: -$18,500 (-68.2%) | Positions: 1 visible (AAPL), heavily concentrated. Current value appears significantly below invested amount. Chart shows sustained downtrend without exit. No visible stop loss implementation. Position sizing appears to be 100% of portfolio in single stock - extreme concentration risk. Technical indicators (MACD) show bearish divergence throughout decline.

[PSYCH] This portfolio demonstrates severe behavioral failures: holding a massive loser without exit plan (loss aversion bias), likely averaging down or refusing to accept reality (hope-based investing), complete absence of sell discipline. The -68% loss suggests emotional attachment to position rather than rules-based management. No evidence of cutting losses early or protecting capital.

[RISK] CATASTROPHIC FAILURE: Portfolio is down -68.2%, which classifies as emergency-level crisis. No stop losses implemented anywhere. Entire portfolio appears concentrated in single position (AAPL) - zero diversification. This level of drawdown typically takes 18-24 months to recover from even with perfect execution. The absence of any risk management tools (stops, position sizing, diversification) is the primary cause of catastrophic loss.

[FIX]
1. IMMEDIATE (24-48h): Close AAPL position completely or reduce to <5% of portfolio. Stop all new position entries until risk framework established.
2. SHORT-TERM (1-2 weeks): Implement mandatory stop losses on all positions at -8% maximum. Establish position sizing rules: no single position >10% of portfolio. Paper trade for 2 weeks before risking capital.
3. LONG-TERM (ongoing): Diversify across minimum 8-10 positions. Establish written trading plan with entry/exit rules. Track every trade with post-trade analysis. Consider working with trading coach/mentor given severity of loss.

[STRENGTH] N/A - Portfolio is completely wiped out with no redeeming tactical decisions visible.

[CRITICAL_ERROR] Complete absence of stop loss discipline. The single biggest mistake was allowing a position to decline -68% without any exit trigger. This indicates no risk management plan existed at entry, and emotional attachment prevented rational exit decisions. Stop losses at -10% would have prevented 85% of this loss.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL REMINDERS BEFORE YOU START:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ READ P/L VALUES EXACTLY - Don't hallucinate numbers
✅ FOLLOW SEVERITY TABLES - Score must match loss percentage
✅ Risk Score MUST be 0-10 if loss >30%
✅ Exit Quality MUST be <30 if no stops and losing
✅ Grade MUST be F if loss >30%
✅ Be BRUTALLY HONEST - This is forensic analysis, not cheerleading
✅ Use EXACT format with [BRACKETS]
✅ If you can't read something, say "unclear" rather than guessing

NOW ANALYZE THE IMAGE:
"""
                        
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
                        portfolio_prompt = f"""CRITICAL INSTRUCTIONS: You are analyzing a complete investment portfolio.

This is NOT a single trade - this is PORTFOLIO-LEVEL FORENSIC ANALYSIS.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER-PROVIDED PORTFOLIO DATA (TREAT AS AUTHORITATIVE):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Invested: {portfolio_total_invested:,.2f}
Current Value: {portfolio_current_value:,.2f}
Number of Positions: {portfolio_num_positions}

CALCULATED METRICS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total P/L: ${total_pnl:,.2f}
Portfolio Drawdown: {total_pnl_pct:+.2f}%
Average Position Size: ${portfolio_total_invested / max(portfolio_num_positions, 1):,.2f}

SEVERITY CLASSIFICATION:
{
    "🚨 CATASTROPHIC EMERGENCY" if total_pnl_pct < -50 else
    "⚠️ SEVERE CRISIS" if total_pnl_pct < -30 else
    "⚠️ MAJOR PROBLEM" if total_pnl_pct < -20 else
    "⚠️ CONCERNING" if total_pnl_pct < -10 else
    "⚠️ MINOR ISSUE" if total_pnl_pct < -5 else
    "✓ ACCEPTABLE" if total_pnl_pct < 5 else
    "✓ PERFORMING WELL"
}

Position Details (if image provided):
- Review uploaded image/PDF for individual stock holdings
- Look for concentrated positions (any single stock >20% of portfolio)
- Identify crisis positions (individual losses >50%)
- Check for sector concentration risks
- Verify if stop losses are visible

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PORTFOLIO ANALYSIS FRAMEWORK:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**1. PORTFOLIO HEALTH SCORE (PRIMARY METRIC):**

Use this STRICT severity table:

| Portfolio Drawdown | Score Range | Grade | Classification |
|--------------------|-------------|-------|----------------|
| < -50%             | 0-5         | F     | CATASTROPHIC   |
| -30% to -50%       | 5-15        | F     | SEVERE CRISIS  |
| -20% to -30%       | 15-30       | D     | MAJOR PROBLEM  |
| -10% to -20%       | 30-50       | C     | CONCERNING     |
| -5% to -10%        | 50-70       | B     | MINOR ISSUE    |
| 0% to -5%          | 70-85       | A     | ACCEPTABLE     |
| 0% to +10%         | 85-92       | A     | GOOD           |
| > +10%             | 93-100      | S     | EXCELLENT      |

**Current drawdown: {total_pnl_pct:+.2f}%**
**Therefore, base score must be in range shown in table above.**

**2. DIVERSIFICATION ASSESSMENT:**

Analyze number of positions:
- < 3 positions: Extreme concentration risk (-20 points)
- 3-5 positions: High concentration (-10 points)
- 6-12 positions: Good diversification (baseline)
- 13-20 positions: Well diversified (+5 points)
- > 20 positions: Over-diversified, can't manage properly (-10 points)

**Current: {portfolio_num_positions} positions**

**3. POSITION SIZING DISCIPLINE:**

Evaluate based on image (if provided):
- Any single position >30% of portfolio = Catastrophic concentration
- Any single position >20% of portfolio = High risk
- Largest position should be <15% ideally
- Look for "barbell" portfolio (few large bets + many small)

**4. CRISIS POSITION IDENTIFICATION:**

From image analysis, identify:
- Positions with >50% individual losses (likely beyond recovery)
- Positions with >100% losses (LEVERAGE/MARGIN EMERGENCY)
- How many positions are in crisis vs recovering
- Whether losers are being held while winners are sold (common mistake)

**5. SECTOR & CORRELATION RISK:**

If image shows sector/industry data:
- Too concentrated in one sector? (e.g., all tech stocks)
- Positions correlated? (will all fall together in crash)
- Balanced across defensive/growth/value?

**6. RISK MANAGEMENT SCORING (0-100):**

**CRITICAL ENFORCEMENT:**
- If portfolio drawdown > 30%: Risk Score MUST NOT EXCEED 10
- If portfolio drawdown > 50%: Risk Score MUST NOT EXCEED 5
- If any position shows >100% loss: Risk Score MUST be 0-5 (leverage emergency)
- If {portfolio_num_positions} > 20: Risk Score maximum 60 (too many to manage)
- If {portfolio_num_positions} < 3: Risk Score maximum 40 (concentration)

Base calculations:
- No stop losses visible anywhere: Base score 0-20
- Some stops visible: Base score 40-60
- All positions have stops: Base score 70-90
- Diversified sizing: +10
- Concentrated sizing: -20
- Multiple crisis positions: -30

**7. ENTRY QUALITY (Portfolio-Level):**

Assess average entry quality across positions:
- Did trader buy at reasonable valuations?
- Evidence of FOMO buying at market tops?
- Disciplined entry points or emotional?
- Scale-in approach or lump sum at worst time?

Score 0-100 based on aggregate entry discipline.

**8. EXIT QUALITY (Portfolio-Level):**

**CRITICAL ENFORCEMENT:**
- If portfolio shows multiple large losers held: Exit Quality MUST BE <30
- If no stops visible anywhere: Exit Quality MUST BE <40
- If portfolio drawdown >30% with no exits: Exit Quality MUST BE <20

Assess based on:
- Are stop losses being used? (If no = automatic cap at 40)
- Is there exit discipline or hope-based holding?
- Are losers being held while winners sold? (disposition effect)
- Evidence of averaging down into losers?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRED OUTPUT FORMAT (EXACT):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[SCORE] <Use severity table strictly based on {total_pnl_pct:+.2f}% drawdown>

[OVERALL_GRADE] <F if <-30%, D if -20 to -30%, C if -10 to -20%, etc.>

[ENTRY_QUALITY] <0-100, assess average entry discipline across portfolio>

[EXIT_QUALITY] <0-100, MUST BE <30 if multiple big losers held, <40 if no stops>

[RISK_SCORE] <0-100, MUST BE ≤10 if drawdown>30%, ≤5 if drawdown>50%>

[TAGS] <6-10 portfolio-specific tags: Portfolio_Crisis, Overleveraged, No_Stops, Concentration_Risk, Multiple_Catastrophic_Positions, Sector_Concentration, Over_Diversified, Hope_Based_Investing, Lack_Of_Exit_Plan, Averaging_Down, Position_Sizing_Failure, etc.>

[TECH] PORTFOLIO STRUCTURE ANALYSIS: Total P/L: ${total_pnl:,.2f} ({total_pnl_pct:+.2f}%). Portfolio holds {portfolio_num_positions} positions. Invested: ${portfolio_total_invested:,.2f}, Current Value: ${portfolio_current_value:,.2f}. [From image: List top 3-5 worst-performing individual positions with their specific losses. Identify any positions >20% of portfolio (concentration). Note sector concentration if visible. Analyze diversification quality. Comment on position sizing discipline. Flag any positions showing >100% loss as leverage/margin emergency.]

[PSYCH] PORTFOLIO PSYCHOLOGY PROFILE: [Analyze behavioral patterns across entire portfolio. Evidence of FOMO buying? Holding losers and cutting winners (disposition effect)? Refusing to accept losses (hope-based investing)? Averaging down into failing positions? Revenge trading after losses? Lack of selling discipline? Emotional attachment? This should analyze the OVERALL decision-making psychology, not individual trades. If drawdown >30%, this is evidence of catastrophic psychological failures in risk management.]

[RISK] PORTFOLIO RISK ASSESSMENT: [CRITICAL SECTION - This is where you MUST be brutally honest. If drawdown is {total_pnl_pct:+.2f}%, classify severity per table above. Analyze: (1) Position sizing - any individual position >20% is high risk. (2) Stop loss discipline - if no stops visible and portfolio is down >30%, this is catastrophic failure. (3) Diversification - {portfolio_num_positions} positions: is this adequate? (4) Drawdown management - at what point will trader cut losses? (5) If ANY position shows >100% loss, this is likely MARGIN/LEVERAGE emergency requiring immediate action. (6) Recovery timeline: portfolios down >30% typically need 18-24+ months to recover. (7) Correlation risk: are all positions in same sector?]

[FIX] PORTFOLIO RECOVERY PLAN:

**IMMEDIATE ACTIONS (Next 24-48 Hours):**
[What must happen NOW to stop bleeding. Examples: "Close AAPL position completely", "Investigate positions showing >100% loss for margin/leverage issues", "Halt all new position entries immediately", "Deposit emergency funds if margin call risk"]

**SHORT-TERM RECOVERY (1-4 Weeks):**
[Steps to stabilize. Examples: "Implement -10% stop loss on every remaining position", "Close positions with >50% individual losses (likely beyond recovery)", "Reduce portfolio to maximum 8-10 positions", "Paper trade new system for 2 weeks before live capital deployment", "Position size maximum 10% per stock going forward"]

**LONG-TERM REHABILITATION (1-6 Months):**
[Systemic changes needed. Examples: "Rebuild portfolio with diversified approach across 8-10 sectors", "Establish written trading plan with entry/exit rules for every position", "Mandatory post-trade review for every position weekly", "Education: complete risk management course before adding new positions", "Work with trading mentor/coach given severity of loss", "Implement position sizing calculator tool", "Recovery timeline: expect 18-24 months to break even at this drawdown level"]

[STRENGTH] [Find anything positive, even in disasters. Examples: "Portfolio diversification across sectors prevented total loss", "At least some positions were closed before reaching -100%", "Willingness to seek analysis shows potential for improvement", or if truly nothing: "The portfolio size is small enough that this lesson won't cause financial ruin - treat this as expensive education"]

[CRITICAL_ERROR] [The single biggest portfolio-level mistake. Usually one of: "Complete absence of stop loss discipline across all positions", "Extreme concentration in single position (AAPL = 100% of portfolio)", "Averaging down into losing positions instead of cutting losses", "Holding losers and selling winners (disposition effect)", "Using leverage/margin without understanding risk", "No exit plan or rules - hope-based investing", "Position sizing failure - bet too much on single idea". Be specific and explain impact: e.g., "The critical error was lacking ANY stop loss discipline. If -10% stops had been used on every position, this portfolio would be down -10% maximum instead of {total_pnl_pct:+.1f}%. This single failure is responsible for approximately ${abs(total_pnl) * 0.85:,.2f} of the ${abs(total_pnl):,.2f} loss."]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRE-OUTPUT VALIDATION CHECKLIST:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before submitting output, verify:

✓ Score matches severity table for {total_pnl_pct:+.2f}% drawdown
✓ If drawdown <-30%: Score is 0-15, Grade is F, Risk Score ≤10
✓ If drawdown <-50%: Score is 0-5, Risk Score ≤5
✓ Exit Quality ≤30 if multiple big losers visible
✓ All numbers match user-provided data exactly
✓ [TECH] section identifies specific worst positions from image
✓ [CRITICAL_ERROR] is specific and quantifies impact
✓ [FIX] section has three time-based categories with multiple actions each

NOW PERFORM PORTFOLIO FORENSIC ANALYSIS:
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
                        
                        prompt = f"""You are Dr. Michael Steinhardt, legendary hedge fund manager with 45 years experience and $500M AUM. Analyze this trade with brutal institutional honesty using evidence-based quantitative methods.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRADE DATA (USER-PROVIDED PARAMETERS):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ticker: {ticker}
Setup Type: {setup_type}
Emotional State at Entry: {emotion}

PRICE LEVELS:
Entry: ${entry:.2f}
Exit: ${exit_price:.2f}
Stop Loss: ${stop:.2f if stop > 0 else "NOT SET ⚠️"}

CALCULATED METRICS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Profit/Loss: ${pnl:.2f} ({pnl_pct:+.2f}%)
Risk Amount: ${risk:.2f} ({risk_pct:.2f}% of entry)
Realized R:R Ratio: {rr_ratio:.2f}:1
{'⚠️ NO STOP LOSS DEFINED' if stop <= 0 else '✓ Stop Loss Set'}

TRADER NOTES:
{notes if notes else "No execution notes provided"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYSIS FRAMEWORK:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**1. SEVERITY ASSESSMENT (PRIMARY DRIVER OF SCORE):**

| P/L Loss Level | Base Score | Grade | Classification |
|----------------|------------|-------|----------------|
| > 50% loss     | 0-5        | F     | CATASTROPHIC   |
| 30-50% loss    | 5-15       | F     | SEVERE         |
| 20-30% loss    | 15-30      | D     | MAJOR FAILURE  |
| 10-20% loss    | 30-50      | C     | POOR           |
| 5-10% loss     | 50-70      | B     | MEDIOCRE       |
| 0-5% loss      | 70-85      | A     | ACCEPTABLE     |
| 0-10% profit   | 85-92      | A     | GOOD           |
| > 10% profit   | 93-100     | S     | EXCELLENT      |

**2. RISK MANAGEMENT SCORING (0-100 scale):**

Calculate Risk Score based on:
- Stop Loss Present: +40 points base
- Stop Loss Absent: 0 points base (automatic cap at 30 maximum)
- R:R Ratio < 1:1 = -20 points
- R:R Ratio 1:2 = base
- R:R Ratio > 1:3 = +20 points
- Position risk > 5% of account = -30 points
- Emotional state "FOMO" or "Revenge" or "Tilt" = -15 points

**If loss >30%: Risk Score MUST NOT EXCEED 10 (crisis override)**
**If no stop loss AND losing trade: Risk Score MUST NOT EXCEED 20**

**3. ENTRY QUALITY SCORING (0-100 scale):**

Assess based on:
- Setup appropriateness for market condition
- Entry timing relative to technical levels
- Confirmation indicators present
- Emotional state impact (FOMO/Revenge = lower score)
- {setup_type} setup validation

Scoring guide:
- 90-100: Perfect setup, ideal entry timing, all confirmations
- 70-89: Good setup, decent timing, most confirmations
- 50-69: Average setup, questionable timing, some confirmations
- 30-49: Poor setup, bad timing, few confirmations
- 0-29: Terrible setup, emotional entry, no confirmations

**4. EXIT QUALITY SCORING (0-100 scale):**

Assess based on:
- Whether stop loss was actually SET (if not = automatic cap at 30)
- Whether exit was rules-based vs emotional
- Risk management during trade
- Trailing stop usage
- Profit-taking discipline

**CRITICAL: If stop={stop}, this means:**
- If stop ≤ 0 AND trade lost money: Exit Quality MAXIMUM 30
- If stop > 0 AND hit stop: Exit Quality 60-80 (good discipline)
- If stop > 0 AND didn't hit stop: Exit Quality varies by other factors

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRED OUTPUT FORMAT (EXACT):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[SCORE] <0-100, use severity table strictly>

[OVERALL_GRADE] <F/D/C/B/A/S-Tier, align with severity table>

[ENTRY_QUALITY] <0-100, assess setup and timing>

[EXIT_QUALITY] <0-100, MUST BE ≤30 if no stop AND losing, ≤50 if no stop AND winning>

[RISK_SCORE] <0-100, MUST BE ≤10 if loss>30%, MUST BE ≤20 if no stop AND losing>

[TAGS] <4-7 comma-separated tags describing behavioral and technical issues>

[TECH] TECHNICAL ASSESSMENT: {ticker} | Entry: ${entry:.2f}, Exit: ${exit_price:.2f}, Stop: ${stop:.2f if stop > 0 else "NOT SET"}. P/L: ${pnl:.2f} ({pnl_pct:+.2f}%). Risk: ${risk:.2f} ({risk_pct:.2f}%). R:R: {rr_ratio:.2f}:1. [Analyze the {setup_type} setup quality, entry timing relative to technical levels, whether stop placement was appropriate for volatility, and if risk amount was proportional to account size. Use specific numbers and percentages.]

[PSYCH] PSYCHOLOGICAL PROFILE: Entered in {emotion} emotional state. [Analyze how this emotional state affected decision-making. Did it cause premature entry, late entry, no stop loss, or poor exit? Connect the emotion to the technical execution failures. For "Neutral" state, analyze whether discipline was maintained. For "FOMO/Revenge/Tilt", explain specific impacts on trade quality.]

[RISK] RISK MANAGEMENT ASSESSMENT: [Analyze: (1) Stop loss discipline - was it set? appropriate? honored? (2) Position sizing - was {risk_pct:.2f}% risk appropriate? (3) R:R ratio of {rr_ratio:.2f}:1 - is this acceptable? (4) Overall risk framework - does trader have a system? If loss >30% or no stop, this section MUST emphasize catastrophic risk failure.]

[FIX] ACTIONABLE IMPROVEMENTS (exactly 3):
1. [Specific technical fix with numbers - e.g., "Set stop loss at -2% below entry ($X) on every trade"]
2. [Specific psychological fix - e.g., "Wait 30 minutes after seeing setup before entering to avoid FOMO"]
3. [Specific risk fix - e.g., "Limit risk to 1% of account max ($X per trade) and verify R:R >1:2"]

[STRENGTH] [Identify 1-2 things done correctly, even if trade lost. If truly nothing, write "Trader recognized mistake by seeking analysis - willingness to improve is the only strength here."]

[CRITICAL_ERROR] [The single biggest mistake in this trade. Be specific: "Not setting a stop loss" or "Entering on FOMO emotion" or "Risk of {risk_pct:.1f}% was too large" or "R:R of {rr_ratio:.1f}:1 was unacceptable". Explain why this was most critical.]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL VALIDATION CHECKS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before finalizing your output, verify:

✓ If pnl_pct < -30%: Score is 0-15, Grade is F, Risk Score is 0-10
✓ If stop ≤ 0 AND pnl < 0: Exit Quality ≤ 30, Risk Score ≤ 20
✓ If emotion is "FOMO" or "Revenge" or "Tilt": Psych section explains impact, Score penalized
✓ R:R ratio < 1:1 is BAD - must be reflected in Risk Score and critique
✓ All numbers in [TECH] section match the provided data exactly
✓ [FIX] section has EXACTLY 3 numbered actionable items

NOW PERFORM THE ANALYSIS:
"""
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
                        
                        # Display trade state warning if detected
                        if report.get('trade_state') == 'REALIZED':
                            st.info("ℹ️ **Note:** This analysis is for a CLOSED/REALIZED trade. The position has already been exited.")
                        elif report.get('trade_state') == 'UNREALIZED':
                            st.warning("⚠️ **Note:** This analysis is for an OPEN/UNREALIZED position. Consider the action plan carefully.")
                        
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
                        
                        save_analysis(current_user, report, ticker_val)
                        
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
                
                else:
                    st.markdown('<div class="glass-panel" style="text-align: center; padding: 80px;">', unsafe_allow_html=True)
                    st.markdown("""
                    <div style="font-size: 3.5rem; margin-bottom: 20px; opacity: 0.4;">📊</div>
                    <div style="font-size: 1.2rem; color: #9ca3af; margin-bottom: 10px; font-weight: 600;">No Performance Data Yet</div>
                    <div style="font-size: 0.95rem; color: #6b7280;">Complete your first forensic audit to see metrics here.</div>
                    """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
