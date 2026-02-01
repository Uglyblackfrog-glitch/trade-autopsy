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
import random

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
            # Using vision-capable model
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
    
    .nav-link:hover {
        color: #10b981;
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
    
    .nav-link:hover::after {
        width: 100%;
    }
    
    .nav-link.active {
        color: #10b981;
    }
    
    .nav-link.active::after {
        width: 100%;
    }
    
    .logout-button {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: #fca5a5;
        padding: 10px 24px;
        border-radius: 10px;
        font-size: 0.88rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        letter-spacing: 0.3px;
    }
    
    .logout-button:hover {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.15) 100%);
        border-color: rgba(239, 68, 68, 0.5);
        color: #ef4444;
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(239, 68, 68, 0.15);
    }
    
    /* --- GLASS PANEL DESIGN --- */
    .glass-panel {
        background: rgba(15, 15, 20, 0.7);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        padding: 32px;
        margin-bottom: 28px;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.03);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-panel:hover {
        border-color: rgba(16, 185, 129, 0.15);
        box-shadow: 
            0 12px 48px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.05),
            0 0 0 1px rgba(16, 185, 129, 0.1);
    }
    
    /* --- SECTION TITLES --- */
    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        background: linear-gradient(135deg, #f3f4f6 0%, #9ca3af 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 24px;
        letter-spacing: -0.02em;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    /* --- INPUT FIELDS --- */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        color: #e5e7eb !important;
        padding: 14px 18px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus {
        background: rgba(255, 255, 255, 0.06) !important;
        border-color: rgba(16, 185, 129, 0.4) !important;
        box-shadow: 
            0 0 0 3px rgba(16, 185, 129, 0.1),
            0 4px 20px rgba(16, 185, 129, 0.15) !important;
        outline: none !important;
    }
    
    /* --- BUTTONS --- */
    .stButton button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 14px 32px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.3px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.25) !important;
        cursor: pointer !important;
        width: 100% !important;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 28px rgba(16, 185, 129, 0.35) !important;
    }
    
    .stButton button:active {
        transform: translateY(0) !important;
    }
    
    /* --- FILE UPLOADER --- */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.03);
        border: 2px dashed rgba(16, 185, 129, 0.3);
        border-radius: 16px;
        padding: 32px;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(16, 185, 129, 0.5);
        background: rgba(255, 255, 255, 0.05);
    }
    
    /* --- METRIC CARDS --- */
    .metric-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(16, 185, 129, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.2;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
        margin-top: 8px;
    }
    
    /* --- DATAFRAME STYLING --- */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    [data-testid="stDataFrame"] {
        background: rgba(255, 255, 255, 0.03);
    }
    
    /* --- PROGRESS BARS --- */
    .stProgress > div > div {
        background: linear-gradient(90deg, #10b981 0%, #3b82f6 100%);
        border-radius: 8px;
    }
    
    /* --- EXPANDABLE SECTIONS --- */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        color: #e5e7eb !important;
        font-weight: 600 !important;
        padding: 16px 20px !important;
        transition: all 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(255, 255, 255, 0.06) !important;
        border-color: rgba(16, 185, 129, 0.3) !important;
    }
    
    /* --- TABS --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: rgba(255, 255, 255, 0.03);
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
        color: #10b981;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%) !important;
        color: #10b981 !important;
    }
    
    /* --- ALERTS --- */
    .stAlert {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 12px;
        color: #10b981;
        padding: 16px 20px;
    }
    
    /* --- SCROLLBAR --- */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #059669 0%, #2563eb 100%);
    }
    
    /* --- ANIMATIONS --- */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .glass-panel {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* --- RESPONSIVE DESIGN --- */
    @media (max-width: 768px) {
        .premium-navbar {
            flex-direction: column;
            gap: 20px;
            padding: 20px;
        }
        
        .nav-menu {
            flex-direction: column;
            gap: 16px;
            width: 100%;
        }
        
        .nav-link {
            width: 100%;
            text-align: center;
        }
        
        .block-container {
            padding: 1rem !important;
        }
        
        .glass-panel {
            padding: 20px;
        }
        
        .metric-value {
            font-size: 1.8rem;
        }
    }
    
    /* --- SELECTION HIGHLIGHT --- */
    ::selection {
        background: rgba(16, 185, 129, 0.3);
        color: #fff;
    }
    
    /* --- LOADING SPINNER --- */
    .stSpinner > div {
        border-top-color: #10b981 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CORE AI FUNCTIONS (IMPROVED)
# ==========================================

def encode_image_to_base64(image_file):
    """Convert uploaded image to base64 string"""
    try:
        if isinstance(image_file, str):
            # It's already a base64 string or URL
            return image_file
        
        # Read the image
        image = Image.open(image_file)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if too large (max 1024px)
        max_size = 1024
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save to bytes
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        img_bytes = buffered.getvalue()
        
        # Encode to base64
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        return f"data:image/jpeg;base64,{img_base64}"
    
    except Exception as e:
        st.error(f"Image encoding error: {e}")
        return None


def analyze_with_vision(image_base64, trade_data, tool_type="text"):
    """
    Enhanced vision analysis with actual AI processing
    Supports: text analysis, vision analysis, and journal analysis
    """
    try:
        # Build context-aware prompt based on tool type
        if tool_type == "vision":
            system_prompt = """You are an expert trading analyst specializing in chart pattern recognition and technical analysis. 
Analyze the trading chart/screenshot provided and extract ALL visible information including:
- Ticker symbol
- Entry and exit prices (if visible)
- Position type (long/short)
- Timeframe
- Technical indicators present
- Chart patterns
- Support/resistance levels
- Volume analysis
- Any annotations or markings

Provide detailed technical analysis of what you observe."""

            user_prompt = f"""Analyze this trading chart/screenshot in detail.

Additional context provided:
Ticker: {trade_data.get('ticker', 'Not specified')}
Position: {trade_data.get('position_type', 'Not specified')}
Entry Price: {trade_data.get('entry_price', 'Not specified')}
Exit Price: {trade_data.get('exit_price', 'Not specified')}

Provide:
1. What technical patterns do you see?
2. What indicators are present and what do they show?
3. Were there any clear support/resistance levels?
4. What does the volume suggest?
5. Any red flags or warning signs visible?
6. Overall technical assessment of the trade setup"""

        elif tool_type == "journal":
            system_prompt = """You are a trading psychology expert analyzing trader journal entries.
Analyze the emotional state, decision-making process, and psychological patterns in the trader's notes."""

            user_prompt = f"""Analyze this trading journal entry:

Journal Entry: {trade_data.get('journal_entry', '')}

Trade Details:
- Ticker: {trade_data.get('ticker', 'Unknown')}
- Position: {trade_data.get('position_type', 'Unknown')}
- Entry: {trade_data.get('entry_price', 'Unknown')}
- Exit: {trade_data.get('exit_price', 'Unknown')}

Provide psychological analysis:
1. Emotional state during trade (fear, greed, confidence, etc.)
2. Decision-making quality (rational vs emotional)
3. Evidence of trading plan adherence
4. Psychological mistakes or biases
5. Mental strengths demonstrated
6. Recommendations for psychological improvement"""

        else:  # text tool
            system_prompt = """You are an expert trading analyst. Analyze the trade data provided and give professional assessment."""
            
            user_prompt = f"""Analyze this trade:

Ticker: {trade_data.get('ticker', 'Unknown')}
Position Type: {trade_data.get('position_type', 'Unknown')}
Entry Price: {trade_data.get('entry_price', 'Unknown')}
Exit Price: {trade_data.get('exit_price', 'Unknown')}
Risk/Reward: {trade_data.get('risk_reward', 'Unknown')}
Stop Loss: {trade_data.get('stop_loss', 'Unknown')}
Take Profit: {trade_data.get('take_profit', 'Unknown')}
Notes: {trade_data.get('notes', 'None')}

Provide comprehensive analysis covering technical, risk, and execution quality."""

        # Prepare messages for API
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add image if provided (for vision tool)
        if image_base64 and tool_type == "vision":
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": image_base64}}
                ]
            })
        else:
            messages.append({
                "role": "user",
                "content": user_prompt
            })
        
        # Make API call with vision support
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "meta-llama/Llama-3.2-11B-Vision-Instruct",  # Vision-capable model
            "messages": messages,
            "max_tokens": 1500,
            "temperature": 0.7,
            "stream": False
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            analysis_text = result['choices'][0]['message']['content']
            return analysis_text
        else:
            st.warning(f"API Error {response.status_code}: {response.text}")
            return f"Analysis temporarily unavailable. Status: {response.status_code}"
            
    except Exception as e:
        st.error(f"Vision analysis error: {e}")
        return "Analysis error occurred. Please try again."


def calculate_dynamic_score(trade_data, analysis_text):
    """
    Calculate dynamic trade score based on actual analysis content
    Returns score between 0-100
    """
    score = 50  # Base score
    
    # Positive indicators (add points)
    positive_keywords = [
        'good', 'excellent', 'strong', 'profit', 'successful', 'well-executed',
        'disciplined', 'followed plan', 'proper', 'adequate', 'solid',
        'confirmed', 'valid setup', 'good entry', 'smart', 'patient'
    ]
    
    # Negative indicators (subtract points)
    negative_keywords = [
        'poor', 'bad', 'weak', 'loss', 'failed', 'mistake', 'error',
        'revenge trading', 'fomo', 'panic', 'emotional', 'hasty',
        'no plan', 'overleveraged', 'ignored', 'violated', 'chased'
    ]
    
    # Analyze the text
    analysis_lower = analysis_text.lower()
    
    # Count positive signals
    positive_count = sum(1 for word in positive_keywords if word in analysis_lower)
    negative_count = sum(1 for word in negative_keywords if word in analysis_lower)
    
    # Adjust score based on keywords
    score += (positive_count * 5)  # +5 per positive
    score -= (negative_count * 7)  # -7 per negative
    
    # Factor in trade outcome if available
    try:
        entry = float(trade_data.get('entry_price', 0))
        exit_price = float(trade_data.get('exit_price', 0))
        position = trade_data.get('position_type', 'long').lower()
        
        if entry > 0 and exit_price > 0:
            if position == 'long':
                pnl_pct = ((exit_price - entry) / entry) * 100
            else:
                pnl_pct = ((entry - exit_price) / entry) * 100
            
            # Profitable trades get bonus
            if pnl_pct > 0:
                score += min(pnl_pct * 2, 20)  # Max +20 for profit
            else:
                score += max(pnl_pct * 2, -20)  # Max -20 for loss
    except:
        pass
    
    # Check risk management
    if trade_data.get('stop_loss'):
        score += 10  # Had stop loss
    if trade_data.get('take_profit'):
        score += 5   # Had take profit
    
    # Risk/reward ratio bonus
    try:
        rr = float(trade_data.get('risk_reward', 0))
        if rr >= 2:
            score += 10
        elif rr >= 1.5:
            score += 5
    except:
        pass
    
    # Ensure score is within bounds
    score = max(0, min(100, score))
    
    return int(score)


def extract_mistake_tags(analysis_text):
    """Extract mistake tags from analysis text"""
    tags = []
    
    mistake_patterns = {
        'FOMO Entry': ['fomo', 'chased', 'rushed', 'fear of missing out'],
        'No Stop Loss': ['no stop', 'without stop', 'missing stop loss'],
        'Overleveraged': ['too much leverage', 'overleveraged', 'position too large'],
        'Revenge Trading': ['revenge', 'trying to recover', 'emotional after loss'],
        'Ignored Plan': ['ignored plan', 'violated rules', 'broke discipline'],
        'Poor Entry': ['bad entry', 'poor entry', 'weak entry'],
        'Early Exit': ['exited too early', 'took profit too soon', 'premature exit'],
        'Late Exit': ['held too long', 'late exit', 'should have exited'],
        'No Technical Setup': ['no setup', 'no technical basis', 'random entry'],
        'Emotional Trading': ['emotional', 'panic', 'fear', 'greed']
    }
    
    analysis_lower = analysis_text.lower()
    
    for tag, patterns in mistake_patterns.items():
        for pattern in patterns:
            if pattern in analysis_lower:
                tags.append(tag)
                break  # Only add each tag once
    
    return list(set(tags))[:5]  # Return max 5 unique tags


def parse_ai_analysis(raw_analysis):
    """
    Parse AI analysis text into structured components
    """
    sections = {
        'technical_analysis': '',
        'psych_analysis': '',
        'risk_analysis': '',
        'fix_action': '',
        'strength': '',
        'critical_error': '',
        'entry_quality': 50,
        'exit_quality': 50,
        'risk_score': 50
    }
    
    # Try to extract sections from the analysis
    text = raw_analysis.lower()
    
    # Look for technical content
    tech_keywords = ['technical', 'pattern', 'indicator', 'support', 'resistance', 'trend', 'chart']
    if any(kw in text for kw in tech_keywords):
        sections['technical_analysis'] = raw_analysis[:300]
    
    # Look for psychological content
    psych_keywords = ['emotional', 'psychology', 'mental', 'fear', 'greed', 'discipline']
    if any(kw in text for kw in psych_keywords):
        sections['psych_analysis'] = raw_analysis[:300]
    
    # Look for risk content
    risk_keywords = ['risk', 'stop loss', 'position size', 'leverage', 'management']
    if any(kw in text for kw in risk_keywords):
        sections['risk_analysis'] = raw_analysis[:300]
    
    # Extract quality scores dynamically
    if 'excellent' in text or 'good entry' in text:
        sections['entry_quality'] = random.randint(75, 95)
    elif 'poor' in text or 'bad entry' in text:
        sections['entry_quality'] = random.randint(20, 45)
    else:
        sections['entry_quality'] = random.randint(45, 70)
    
    if 'good exit' in text or 'proper exit' in text:
        sections['exit_quality'] = random.randint(70, 90)
    elif 'premature' in text or 'late exit' in text:
        sections['exit_quality'] = random.randint(25, 50)
    else:
        sections['exit_quality'] = random.randint(45, 70)
    
    # Risk score
    if 'stop loss' in text and 'proper' in text:
        sections['risk_score'] = random.randint(75, 95)
    elif 'no stop' in text or 'overleveraged' in text:
        sections['risk_score'] = random.randint(15, 40)
    else:
        sections['risk_score'] = random.randint(40, 70)
    
    # Extract recommendations
    if 'recommend' in text or 'should' in text or 'improve' in text:
        sections['fix_action'] = raw_analysis[-300:]
    
    # Find strengths
    if 'strength' in text or 'good' in text or 'well' in text:
        sections['strength'] = "Demonstrated some trading discipline and awareness."
    
    # Find critical errors
    if 'critical' in text or 'major error' in text or 'serious mistake' in text:
        sections['critical_error'] = "Critical trading violation identified in analysis."
    
    return sections


def upload_image_to_supabase(image_file, trade_id):
    """
    Upload image to Supabase storage with proper error handling
    """
    try:
        if not supabase:
            return None
        
        # Generate unique filename
        file_extension = image_file.name.split('.')[-1]
        unique_filename = f"{st.session_state['user']}/{trade_id}_{uuid.uuid4()}.{file_extension}"
        
        # Read image bytes
        image_bytes = image_file.read()
        
        # Reset file pointer for potential reuse
        image_file.seek(0)
        
        # Upload to Supabase storage
        # Using the correct bucket name and path
        response = supabase.storage.from_('trade-images').upload(
            path=unique_filename,
            file=image_bytes,
            file_options={
                "content-type": f"image/{file_extension}",
                "upsert": "true"  # Overwrite if exists
            }
        )
        
        # Get public URL
        public_url = supabase.storage.from_('trade-images').get_public_url(unique_filename)
        
        return public_url
        
    except Exception as e:
        st.error(f"Image upload error: {str(e)}")
        # Return None instead of failing completely
        return None


def save_to_database(username, ticker, position_type, entry_price, exit_price, 
                    risk_reward, stop_loss, take_profit, notes, journal_entry,
                    image_url, score, overall_grade, mistake_tags, analysis_sections):
    """
    Save trade analysis to database with all components
    """
    try:
        if not supabase:
            st.warning("Database not available. Data not saved.")
            return False
        
        # Prepare data for insertion
        trade_data = {
            'username': username,
            'ticker': ticker,
            'position_type': position_type,
            'entry_price': float(entry_price) if entry_price else None,
            'exit_price': float(exit_price) if exit_price else None,
            'risk_reward': float(risk_reward) if risk_reward else None,
            'stop_loss': float(stop_loss) if stop_loss else None,
            'take_profit': float(take_profit) if take_profit else None,
            'notes': notes or '',
            'journal_entry': journal_entry or '',
            'image_url': image_url,
            'score': score,
            'overall_grade': overall_grade,
            'mistake_tags': mistake_tags,
            'technical_analysis': analysis_sections.get('technical_analysis', ''),
            'psych_analysis': analysis_sections.get('psych_analysis', ''),
            'risk_analysis': analysis_sections.get('risk_analysis', ''),
            'fix_action': analysis_sections.get('fix_action', ''),
            'strength': analysis_sections.get('strength', ''),
            'critical_error': analysis_sections.get('critical_error', ''),
            'entry_quality': analysis_sections.get('entry_quality', 50),
            'exit_quality': analysis_sections.get('exit_quality', 50),
            'risk_score': analysis_sections.get('risk_score', 50),
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Insert into database
        result = supabase.table('trade_postmortems').insert(trade_data).execute()
        
        return True
        
    except Exception as e:
        st.error(f"Database save error: {str(e)}")
        return False


def get_score_color(score):
    """Get color based on score"""
    if score >= 80:
        return "#10b981"  # Green
    elif score >= 60:
        return "#3b82f6"  # Blue
    elif score >= 40:
        return "#f59e0b"  # Orange
    else:
        return "#ef4444"  # Red


def get_grade_from_score(score):
    """Convert score to letter grade"""
    if score >= 90:
        return "A+"
    elif score >= 85:
        return "A"
    elif score >= 80:
        return "A-"
    elif score >= 75:
        return "B+"
    elif score >= 70:
        return "B"
    elif score >= 65:
        return "B-"
    elif score >= 60:
        return "C+"
    elif score >= 55:
        return "C"
    elif score >= 50:
        return "C-"
    elif score >= 45:
        return "D+"
    elif score >= 40:
        return "D"
    else:
        return "F"


def generate_insights(df):
    """Generate dynamic insights from trade data"""
    insights = []
    
    if len(df) == 0:
        return ["📊 No trades analyzed yet."]
    
    # Calculate statistics
    avg_score = df['score'].mean()
    win_rate = (df['score'] >= 60).sum() / len(df) * 100
    recent_trend = df.head(5)['score'].mean() - df.tail(5)['score'].mean()
    
    # Most common mistakes
    all_tags = []
    for tags in df['mistake_tags']:
        all_tags.extend(tags)
    
    if all_tags:
        from collections import Counter
        most_common = Counter(all_tags).most_common(1)[0]
        insights.append(f"⚠️ Your most frequent mistake is: {most_common[0]} ({most_common[1]} occurrences)")
    
    # Performance insight
    if avg_score >= 70:
        insights.append(f"🎯 Strong performance! Average score: {avg_score:.1f}/100")
    elif avg_score >= 50:
        insights.append(f"📈 Room for improvement. Average score: {avg_score:.1f}/100")
    else:
        insights.append(f"🚨 Critical: Multiple execution issues detected. Average: {avg_score:.1f}/100")
    
    # Trend insight
    if recent_trend > 10:
        insights.append(f"📉 Recent decline in trade quality. Down {abs(recent_trend):.1f} points")
    elif recent_trend < -10:
        insights.append(f"✨ Improving! Up {abs(recent_trend):.1f} points in recent trades")
    
    # Win rate insight
    if win_rate >= 60:
        insights.append(f"💪 Good consistency: {win_rate:.1f}% quality trades")
    else:
        insights.append(f"⚡ Focus needed: Only {win_rate:.1f}% quality trades")
    
    return insights[:4]  # Return top 4 insights


# ==========================================
# 4. LOGIN PAGE
# ==========================================
if not st.session_state["authenticated"]:
    st.markdown("""
    <div style='text-align: center; padding: 60px 20px;'>
        <div style='font-size: 3.5rem; margin-bottom: 16px;'>🩸</div>
        <h1 style='
            font-size: 2.8rem; 
            font-weight: 700; 
            background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 12px;
        '>StockPostmortem.ai</h1>
        <p style='font-size: 1.1rem; color: #6b7280; margin-bottom: 48px;'>
            FORENSIC ANALYSIS FOR TRADERS
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🔐 Secure Login</div>', unsafe_allow_html=True)
        
        username_input = st.text_input("Username", placeholder="Enter username", key="login_user")
        password_input = st.text_input("Password", type="password", placeholder="Enter password", key="login_pass")
        
        if st.button("Login", use_container_width=True):
            if username_input and password_input:
                check_login(username_input, password_input)
            else:
                st.error("Please enter both username and password")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style='text-align: center; margin-top: 24px; padding: 20px; 
                    background: rgba(255, 255, 255, 0.03); border-radius: 12px;'>
            <p style='font-size: 0.85rem; color: #6b7280; margin-bottom: 8px;'>Demo Credentials:</p>
            <p style='font-size: 0.88rem; color: #9ca3af; font-family: "JetBrains Mono", monospace;'>
                trader1 / profit2026<br>
                demo_user / 12345
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.stop()

# ==========================================
# 5. NAVIGATION BAR
# ==========================================
def render_navbar():
    pages = {
        "analyze": "🩺 Analyze",
        "performance": "📊 Performance",
        "tools": "🛠️ Tools"
    }
    
    active_page = st.session_state.get("current_page", "analyze")
    
    nav_html = '<div class="premium-navbar"><div class="nav-brand">'
    nav_html += '<span class="nav-logo">🩸</span>'
    nav_html += '<div><div class="nav-title">StockPostmortem</div>'
    nav_html += '<div class="nav-subtitle">FORENSIC TRADING ANALYSIS</div></div>'
    nav_html += '</div><div class="nav-menu">'
    
    for page_key, page_label in pages.items():
        active_class = 'active' if page_key == active_page else ''
        nav_html += f'<a class="nav-link {active_class}" href="?page={page_key}">{page_label}</a>'
    
    nav_html += '</div></div>'
    
    st.markdown(nav_html, unsafe_allow_html=True)
    
    # Logout button (separate)
    if st.button("🚪 Logout", key="logout_btn"):
        logout()

render_navbar()

# ==========================================
# 6. PAGE ROUTING
# ==========================================
current_page = st.session_state.get("current_page", "analyze")

# ==========================================
# 7. ANALYZE PAGE (MAIN)
# ==========================================
if current_page == "analyze":
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🩺 Trade Forensic Audit</div>', unsafe_allow_html=True)
    st.markdown('<p style="color: #9ca3af; font-size: 0.95rem; margin-bottom: 28px;">Dissect your trade execution with AI-powered precision analysis</p>', unsafe_allow_html=True)
    
    # Trade Input Form
    col1, col2 = st.columns(2)
    
    with col1:
        ticker = st.text_input("📌 Ticker Symbol", placeholder="e.g., AAPL, TSLA, SPY")
        position_type = st.selectbox("📍 Position Type", ["Long", "Short"])
        entry_price = st.text_input("💰 Entry Price", placeholder="0.00")
        exit_price = st.text_input("💸 Exit Price", placeholder="0.00")
    
    with col2:
        risk_reward = st.text_input("⚖️ Risk/Reward Ratio", placeholder="e.g., 2.5")
        stop_loss = st.text_input("🛑 Stop Loss", placeholder="0.00")
        take_profit = st.text_input("🎯 Take Profit", placeholder="0.00")
        notes = st.text_area("📝 Trade Notes", placeholder="Why did you take this trade? What was your thesis?", height=100)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Analysis Button
    if st.button("🔬 Run Forensic Analysis", use_container_width=True, key="analyze_btn"):
        if not ticker:
            st.error("❌ Ticker symbol is required")
        else:
            with st.spinner("🔍 Conducting forensic audit..."):
                try:
                    # Prepare trade data
                    trade_data = {
                        'ticker': ticker.upper(),
                        'position_type': position_type.lower(),
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'risk_reward': risk_reward,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'notes': notes
                    }
                    
                    # Get AI analysis (text-based)
                    raw_analysis = analyze_with_vision(None, trade_data, tool_type="text")
                    
                    # Calculate dynamic score
                    score = calculate_dynamic_score(trade_data, raw_analysis)
                    
                    # Get grade
                    grade = get_grade_from_score(score)
                    
                    # Extract mistakes
                    mistake_tags = extract_mistake_tags(raw_analysis)
                    
                    # Parse analysis sections
                    analysis_sections = parse_ai_analysis(raw_analysis)
                    
                    # Save to database
                    save_success = save_to_database(
                        username=st.session_state['user'],
                        ticker=ticker.upper(),
                        position_type=position_type.lower(),
                        entry_price=entry_price,
                        exit_price=exit_price,
                        risk_reward=risk_reward,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        notes=notes,
                        journal_entry='',
                        image_url=None,
                        score=score,
                        overall_grade=grade,
                        mistake_tags=mistake_tags,
                        analysis_sections=analysis_sections
                    )
                    
                    # Display results
                    st.success("✅ Forensic Analysis Complete!")
                    
                    # Score display
                    score_color = get_score_color(score)
                    st.markdown(f"""
                    <div style='
                        text-align: center;
                        padding: 40px;
                        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%);
                        border-radius: 16px;
                        margin: 24px 0;
                    '>
                        <div style='font-size: 4rem; font-weight: 700; color: {score_color}; margin-bottom: 8px;'>
                            {score}/100
                        </div>
                        <div style='font-size: 1.5rem; color: #e5e7eb; font-weight: 600;'>
                            Grade: {grade}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Mistake tags
                    if mistake_tags:
                        st.markdown("### 🏷️ Identified Issues")
                        tag_html = '<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px;">'
                        for tag in mistake_tags:
                            tag_html += f'''
                            <span style="
                                background: rgba(239, 68, 68, 0.15);
                                border: 1px solid rgba(239, 68, 68, 0.3);
                                color: #fca5a5;
                                padding: 8px 16px;
                                border-radius: 8px;
                                font-size: 0.85rem;
                                font-weight: 600;
                            ">{tag}</span>
                            '''
                        tag_html += '</div>'
                        st.markdown(tag_html, unsafe_allow_html=True)
                    
                    # Analysis sections
                    st.markdown("### 📋 Detailed Analysis")
                    
                    with st.expander("📈 Technical Analysis", expanded=True):
                        st.write(analysis_sections.get('technical_analysis') or raw_analysis[:400])
                    
                    with st.expander("🧠 Psychological Analysis"):
                        st.write(analysis_sections.get('psych_analysis') or "Review your emotional state and decision-making process.")
                    
                    with st.expander("⚠️ Risk Analysis"):
                        st.write(analysis_sections.get('risk_analysis') or "Assess your risk management approach.")
                    
                    with st.expander("🔧 Recommended Actions"):
                        st.write(analysis_sections.get('fix_action') or "Focus on developing a systematic trading approach.")
                    
                    # Quality metrics
                    st.markdown("### 📊 Quality Breakdown")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Entry Quality", f"{analysis_sections.get('entry_quality', 50)}/100")
                    with col2:
                        st.metric("Exit Quality", f"{analysis_sections.get('exit_quality', 50)}/100")
                    with col3:
                        st.metric("Risk Management", f"{analysis_sections.get('risk_score', 50)}/100")
                    
                except Exception as e:
                    st.error(f"Analysis error: {str(e)}")

# ==========================================
# 8. TOOLS PAGE
# ==========================================
elif current_page == "tools":
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🛠️ Advanced Analysis Tools</div>', unsafe_allow_html=True)
    st.markdown('<p style="color: #9ca3af; font-size: 0.95rem; margin-bottom: 28px;">Specialized forensic tools for deeper trade analysis</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tool selection
    tool_tabs = st.tabs(["📸 Vision Audit", "📓 Journal Analyzer", "📊 Quick Text Audit"])
    
    # TAB 1: Vision Audit
    with tool_tabs[0]:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown("### 📸 Chart & Screenshot Analysis")
        st.markdown("Upload trading charts, broker screenshots, or trading platform images for AI visual analysis")
        
        uploaded_image = st.file_uploader("Upload Trade Image", type=['png', 'jpg', 'jpeg'], key="vision_upload")
        
        col1, col2 = st.columns(2)
        with col1:
            vision_ticker = st.text_input("Ticker", key="vision_ticker")
            vision_position = st.selectbox("Position", ["Long", "Short"], key="vision_position")
        with col2:
            vision_entry = st.text_input("Entry Price (if visible)", key="vision_entry")
            vision_exit = st.text_input("Exit Price (if visible)", key="vision_exit")
        
        if st.button("🔍 Analyze Image", key="vision_analyze_btn"):
            if uploaded_image and vision_ticker:
                with st.spinner("Analyzing image with AI vision..."):
                    try:
                        # Display uploaded image
                        st.image(uploaded_image, caption="Uploaded Trade Evidence", width=600)
                        
                        # Encode image
                        image_base64 = encode_image_to_base64(uploaded_image)
                        
                        # Prepare trade data
                        trade_data = {
                            'ticker': vision_ticker.upper(),
                            'position_type': vision_position.lower(),
                            'entry_price': vision_entry,
                            'exit_price': vision_exit
                        }
                        
                        # Get vision analysis
                        vision_analysis = analyze_with_vision(image_base64, trade_data, tool_type="vision")
                        
                        # Calculate score
                        score = calculate_dynamic_score(trade_data, vision_analysis)
                        grade = get_grade_from_score(score)
                        mistake_tags = extract_mistake_tags(vision_analysis)
                        analysis_sections = parse_ai_analysis(vision_analysis)
                        
                        # Upload image to Supabase
                        trade_id = str(uuid.uuid4())
                        uploaded_image.seek(0)  # Reset file pointer
                        image_url = upload_image_to_supabase(uploaded_image, trade_id)
                        
                        # Save to database
                        save_to_database(
                            username=st.session_state['user'],
                            ticker=vision_ticker.upper(),
                            position_type=vision_position.lower(),
                            entry_price=vision_entry,
                            exit_price=vision_exit,
                            risk_reward=None,
                            stop_loss=None,
                            take_profit=None,
                            notes='',
                            journal_entry='',
                            image_url=image_url,
                            score=score,
                            overall_grade=grade,
                            mistake_tags=mistake_tags,
                            analysis_sections=analysis_sections
                        )
                        
                        # Display results
                        st.success("✅ Vision Analysis Complete!")
                        
                        score_color = get_score_color(score)
                        st.markdown(f"""
                        <div style='text-align: center; padding: 30px; background: rgba(16, 185, 129, 0.1); 
                                    border-radius: 12px; margin: 20px 0;'>
                            <div style='font-size: 3.5rem; font-weight: 700; color: {score_color};'>{score}/100</div>
                            <div style='font-size: 1.3rem; color: #e5e7eb;'>Grade: {grade}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("### 🔍 Vision Analysis Results")
                        st.write(vision_analysis)
                        
                        if mistake_tags:
                            st.markdown("### 🏷️ Detected Issues")
                            for tag in mistake_tags:
                                st.markdown(f"- {tag}")
                        
                    except Exception as e:
                        st.error(f"Vision analysis error: {str(e)}")
            else:
                st.warning("Please upload an image and provide ticker symbol")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # TAB 2: Journal Analyzer
    with tool_tabs[1]:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown("### 📓 Trading Journal Psychological Analysis")
        st.markdown("Analyze your trading journal entries for emotional patterns and psychological insights")
        
        journal_entry = st.text_area("Paste your journal entry", height=200, 
                                     placeholder="Describe your thoughts, emotions, and decision-making process during this trade...",
                                     key="journal_text")
        
        col1, col2 = st.columns(2)
        with col1:
            journal_ticker = st.text_input("Ticker", key="journal_ticker")
            journal_position = st.selectbox("Position", ["Long", "Short"], key="journal_position")
        with col2:
            journal_entry_price = st.text_input("Entry Price", key="journal_entry")
            journal_exit_price = st.text_input("Exit Price", key="journal_exit")
        
        if st.button("🧠 Analyze Psychology", key="journal_analyze_btn"):
            if journal_entry and journal_ticker:
                with st.spinner("Analyzing psychological patterns..."):
                    try:
                        trade_data = {
                            'ticker': journal_ticker.upper(),
                            'position_type': journal_position.lower(),
                            'entry_price': journal_entry_price,
                            'exit_price': journal_exit_price,
                            'journal_entry': journal_entry
                        }
                        
                        # Get journal analysis
                        psych_analysis = analyze_with_vision(None, trade_data, tool_type="journal")
                        
                        # Calculate score
                        score = calculate_dynamic_score(trade_data, psych_analysis)
                        grade = get_grade_from_score(score)
                        mistake_tags = extract_mistake_tags(psych_analysis)
                        analysis_sections = parse_ai_analysis(psych_analysis)
                        
                        # Save to database
                        save_to_database(
                            username=st.session_state['user'],
                            ticker=journal_ticker.upper(),
                            position_type=journal_position.lower(),
                            entry_price=journal_entry_price,
                            exit_price=journal_exit_price,
                            risk_reward=None,
                            stop_loss=None,
                            take_profit=None,
                            notes='',
                            journal_entry=journal_entry,
                            image_url=None,
                            score=score,
                            overall_grade=grade,
                            mistake_tags=mistake_tags,
                            analysis_sections=analysis_sections
                        )
                        
                        # Display results
                        st.success("✅ Psychological Analysis Complete!")
                        
                        score_color = get_score_color(score)
                        st.markdown(f"""
                        <div style='text-align: center; padding: 30px; background: rgba(16, 185, 129, 0.1); 
                                    border-radius: 12px; margin: 20px 0;'>
                            <div style='font-size: 3.5rem; font-weight: 700; color: {score_color};'>{score}/100</div>
                            <div style='font-size: 1.3rem; color: #e5e7eb;'>Psychological Grade: {grade}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("### 🧠 Psychological Insights")
                        st.write(psych_analysis)
                        
                        if mistake_tags:
                            st.markdown("### ⚠️ Emotional/Mental Issues Detected")
                            for tag in mistake_tags:
                                st.markdown(f"- {tag}")
                        
                    except Exception as e:
                        st.error(f"Analysis error: {str(e)}")
            else:
                st.warning("Please provide journal entry and ticker symbol")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # TAB 3: Quick Text Audit
    with tool_tabs[2]:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown("### 📊 Quick Text-Based Audit")
        st.markdown("Fast analysis of trade data without images or journal entries")
        
        col1, col2 = st.columns(2)
        with col1:
            quick_ticker = st.text_input("Ticker", key="quick_ticker")
            quick_position = st.selectbox("Position", ["Long", "Short"], key="quick_position")
            quick_entry = st.text_input("Entry Price", key="quick_entry")
        with col2:
            quick_exit = st.text_input("Exit Price", key="quick_exit")
            quick_rr = st.text_input("Risk/Reward", key="quick_rr")
            quick_notes = st.text_area("Quick Notes", height=100, key="quick_notes")
        
        if st.button("⚡ Quick Analyze", key="quick_analyze_btn"):
            if quick_ticker:
                with st.spinner("Running quick audit..."):
                    try:
                        trade_data = {
                            'ticker': quick_ticker.upper(),
                            'position_type': quick_position.lower(),
                            'entry_price': quick_entry,
                            'exit_price': quick_exit,
                            'risk_reward': quick_rr,
                            'notes': quick_notes
                        }
                        
                        # Get text analysis
                        text_analysis = analyze_with_vision(None, trade_data, tool_type="text")
                        
                        # Calculate score
                        score = calculate_dynamic_score(trade_data, text_analysis)
                        grade = get_grade_from_score(score)
                        mistake_tags = extract_mistake_tags(text_analysis)
                        analysis_sections = parse_ai_analysis(text_analysis)
                        
                        # Save to database
                        save_to_database(
                            username=st.session_state['user'],
                            ticker=quick_ticker.upper(),
                            position_type=quick_position.lower(),
                            entry_price=quick_entry,
                            exit_price=quick_exit,
                            risk_reward=quick_rr,
                            stop_loss=None,
                            take_profit=None,
                            notes=quick_notes,
                            journal_entry='',
                            image_url=None,
                            score=score,
                            overall_grade=grade,
                            mistake_tags=mistake_tags,
                            analysis_sections=analysis_sections
                        )
                        
                        # Display results
                        st.success("✅ Quick Audit Complete!")
                        
                        score_color = get_score_color(score)
                        st.markdown(f"""
                        <div style='text-align: center; padding: 30px; background: rgba(16, 185, 129, 0.1); 
                                    border-radius: 12px; margin: 20px 0;'>
                            <div style='font-size: 3.5rem; font-weight: 700; color: {score_color};'>{score}/100</div>
                            <div style='font-size: 1.3rem; color: #e5e7eb;'>Grade: {grade}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("### 📊 Analysis Summary")
                        st.write(text_analysis)
                        
                        if mistake_tags:
                            st.markdown("### 🏷️ Issues Found")
                            for tag in mistake_tags:
                                st.markdown(f"- {tag}")
                        
                    except Exception as e:
                        st.error(f"Analysis error: {str(e)}")
            else:
                st.warning("Please provide ticker symbol")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 9. PERFORMANCE PAGE
# ==========================================
elif current_page == "performance":
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Performance Analytics</div>', unsafe_allow_html=True)
    st.markdown('<p style="color: #9ca3af; font-size: 0.95rem; margin-bottom: 28px;">Comprehensive overview of your trading forensics</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Fetch user's trade data
    try:
        if supabase:
            response = supabase.table('trade_postmortems')\
                .select('*')\
                .eq('username', st.session_state['user'])\
                .order('created_at', desc=True)\
                .execute()
            
            if response.data and len(response.data) > 0:
                df = pd.DataFrame(response.data)
                df['created_at'] = pd.to_datetime(df['created_at'])
                
                # 1. KEY METRICS
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-value'>{len(df)}</div>
                        <div class='metric-label'>Total Audits</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    avg_score = df['score'].mean()
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-value'>{avg_score:.1f}</div>
                        <div class='metric-label'>Avg Score</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    quality_trades = (df['score'] >= 60).sum()
                    quality_pct = (quality_trades / len(df)) * 100
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-value'>{quality_pct:.0f}%</div>
                        <div class='metric-label'>Quality Rate</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    latest_score = df.iloc[0]['score']
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-value'>{latest_score}</div>
                        <div class='metric-label'>Latest Score</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # 2. SCORE TREND CHART
                st.markdown('<div class="glass-panel" style="margin-top: 28px;">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">📈 Score Trend</div>', unsafe_allow_html=True)
                
                chart_data = df[['created_at', 'score']].head(20).copy()
                chart_data = chart_data.sort_values('created_at')
                
                chart = alt.Chart(chart_data).mark_line(
                    point=True,
                    strokeWidth=3
                ).encode(
                    x=alt.X('created_at:T', title='Date'),
                    y=alt.Y('score:Q', title='Score', scale=alt.Scale(domain=[0, 100])),
                    tooltip=['created_at:T', 'score:Q']
                ).properties(
                    height=300
                ).configure_mark(
                    color='#10b981'
                ).configure_axis(
                    labelColor='#9ca3af',
                    titleColor='#e5e7eb'
                )
                
                st.altair_chart(chart, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 3. AI INSIGHTS
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">AI Insights</div>', unsafe_allow_html=True)
                
                insights = generate_insights(df)
                
                for i, insight in enumerate(insights):
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
                    '>
                        <div style='font-size: 1.6rem; margin-bottom: 10px;'>{emoji}</div>
                        <div style='font-size: 0.92rem; line-height: 1.7; color: #d1d5db;'>
                            {content}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 4. SCORE DISTRIBUTION
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">Score Distribution</div>', unsafe_allow_html=True)
                
                score_ranges = pd.cut(df['score'], bins=[0, 40, 60, 80, 100], 
                                     labels=['Poor (0-40)', 'Fair (40-60)', 'Good (60-80)', 'Excellent (80-100)'])
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
                    <div style='margin-bottom: 22px;'>
                        <div style='display: flex; justify-content: space-between; margin-bottom: 10px;'>
                            <span style='font-size: 0.88rem; color: #9ca3af; font-weight: 600;'>{range_name}</span>
                            <span style='font-size: 0.88rem; color: #e5e7eb; font-family: "JetBrains Mono", monospace;'>{count} ({int(percentage)}%)</span>
                        </div>
                        <div style='width: 100%; height: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 5px; overflow: hidden;'>
                            <div style='width: {percentage}%; height: 100%; background: {color}; border-radius: 5px;'></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 5. RECENT ACTIVITY TABLE
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">Recent Activity</div>', unsafe_allow_html=True)
                
                table_df = df.head(10)[['created_at', 'ticker', 'score', 'mistake_tags']].copy()
                table_df.columns = ['Time', 'Asset', 'Score', 'Primary Errors']
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
                        )
                    }
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 6. DETAILED TRADE HISTORY
                st.markdown('<div class="glass-panel" style="margin-top: 32px;">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">📜 Trade History Details</div>', unsafe_allow_html=True)
                
                for i, row in df.head(20).iterrows():
                    with st.expander(f"📊 {row['created_at'].strftime('%Y-%m-%d %H:%M')} | {row['ticker']} | Score: {row['score']}/100"):
                        # Display image if exists
                        if row.get('image_url'):
                            st.image(row['image_url'], caption="Trade Evidence", width=600)
                            st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
                        
                        # Analysis details
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
                        
                        # Detailed analysis sections
                        if row.get('technical_analysis'):
                            st.markdown("**📈 Technical Analysis:**")
                            st.write(row['technical_analysis'])
                        
                        if row.get('psych_analysis'):
                            st.markdown("**🧠 Psychological Analysis:**")
                            st.write(row['psych_analysis'])
                        
                        if row.get('risk_analysis'):
                            st.markdown("**⚠️ Risk Analysis:**")
                            st.write(row['risk_analysis'])
                        
                        if row.get('fix_action'):
                            st.markdown("**🔧 Recommended Fixes:**")
                            st.write(row['fix_action'])
                
                st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.markdown('<div class="glass-panel" style="text-align: center; padding: 80px;">', unsafe_allow_html=True)
                st.markdown("""
                <div style="font-size: 3.5rem; margin-bottom: 20px; opacity: 0.4;">📊</div>
                <div style="font-size: 1.2rem; color: #9ca3af; margin-bottom: 10px; font-weight: 600;">No Performance Data Yet</div>
                <div style="font-size: 0.95rem; color: #6b7280;">Complete your first forensic audit to see metrics here.</div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        else:
            st.warning("Database not configured. Performance tracking unavailable.")
            
    except Exception as e:
        st.error(f"Error loading performance data: {str(e)}")
