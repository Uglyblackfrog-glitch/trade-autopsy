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
HF_TOKEN = ""
API_URL = "https://router.huggingface.co/v1/chat/completions"
supabase = None

if st.session_state["authenticated"]:
    try:
        HF_TOKEN = st.secrets.get("HF_TOKEN", "")
        SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
        SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
        
        if not all([HF_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
            st.warning("⚠️ Secrets missing. Running in UI-only mode.")
        else:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            
    except Exception as e:
        st.error(f"⚠️ Configuration Error: {e}")

# ==========================================
# 2. PREMIUM DARK THEME CSS (EXACT COPY)
# ==========================================
st.markdown("""
<style>
    /* --- PREMIUM FONTS --- */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
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
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.03);
    }
    .nav-brand { display: flex; align-items: center; gap: 12px; }
    .nav-logo { font-size: 1.8rem; filter: drop-shadow(0 0 16px rgba(16, 185, 129, 0.4)); }
    .nav-title {
        font-size: 1.4rem; font-weight: 700;
        background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; letter-spacing: -0.02em;
    }
    .nav-subtitle { font-size: 0.7rem; color: #6b7280; text-transform: uppercase; letter-spacing: 2px; font-weight: 600; }
    .nav-menu { display: flex; gap: 32px; align-items: center; }
    .nav-link {
        color: #9ca3af; text-decoration: none; font-size: 0.95rem; font-weight: 600;
        letter-spacing: 0.5px; transition: all 0.3s ease; position: relative; padding: 8px 0; cursor: pointer;
    }
    .nav-link::after {
        content: ''; position: absolute; bottom: 0; left: 0; width: 0; height: 2px;
        background: linear-gradient(90deg, #10b981, #3b82f6); transition: width 0.3s ease;
    }
    .nav-link:hover { color: #10b981; }
    .nav-link:hover::after { width: 100%; }
    .nav-link.active { color: #10b981; }
    .nav-link.active::after { width: 100%; }
    
    /* --- GLASS PANELS --- */
    .glass-panel {
        background: rgba(15, 15, 20, 0.75);
        backdrop-filter: blur(24px) saturate(200%);
        -webkit-backdrop-filter: blur(24px) saturate(200%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 36px;
        margin-bottom: 24px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        position: relative; overflow: hidden;
    }
    .glass-panel::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.5), transparent);
        opacity: 0; transition: opacity 0.4s ease;
    }
    .glass-panel:hover {
        border-color: rgba(255, 255, 255, 0.12);
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        transform: translateY(-2px);
    }
    .glass-panel:hover::before { opacity: 1; }

    /* --- KPI CARDS --- */
    .kpi-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 32px; }
    .kpi-card {
        background: linear-gradient(135deg, rgba(20, 20, 28, 0.9) 0%, rgba(10, 10, 15, 0.95) 100%);
        backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 32px 28px; border-radius: 20px; text-align: center;
        transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1); position: relative; overflow: hidden;
    }
    .kpi-card:hover {
        border-color: rgba(16, 185, 129, 0.4); transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 60px -12px rgba(16, 185, 129, 0.3), 0 0 0 1px rgba(16, 185, 129, 0.2);
    }
    .kpi-val { 
        font-family: 'JetBrains Mono', monospace; font-size: 3rem; font-weight: 700; 
        background: linear-gradient(135deg, #ffffff 0%, #10b981 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; margin-bottom: 10px;
    }
    .kpi-label { color: #9ca3af; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 2.5px; font-weight: 600; }

    /* --- INPUTS & BUTTONS --- */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox select {
        background: rgba(20, 20, 28, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
        padding: 14px 18px !important;
    }
    .stButton button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        border: 1px solid rgba(16, 185, 129, 0.4) !important;
        color: white !important; font-weight: 600 !important;
        padding: 14px 32px !important; border-radius: 14px !important;
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3) !important;
    }
    .stButton button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.5) !important;
    }

    /* --- RESULTS DISPLAY --- */
    .score-value { font-family: 'JetBrains Mono', monospace; font-size: 5.5rem; font-weight: 800; line-height: 1; letter-spacing: -0.04em; }
    .ticker-badge { background: rgba(16, 185, 129, 0.15); padding: 10px 20px; border-radius: 10px; display: inline-block; font-weight: 600; color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .report-item { background: rgba(255, 255, 255, 0.03); border-left: 4px solid #10b981; padding: 24px; border-radius: 0 16px 16px 0; margin-bottom: 20px; }
    .report-label { font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 14px; color: #9ca3af; display: block; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. FIXED HELPER FUNCTIONS (CORE AI LOGIC)
# ==========================================

def analyze_image(image_bytes):
    """
    FIXED: Uses a proper Vision Model (Llama-3.2-11B-Vision) to see the chart.
    """
    if not HF_TOKEN:
        return "Vision analysis unavailable (No API Token)."
    
    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}", 
            "Content-Type": "application/json"
        }
        
        # Multimodal payload for Vision model
        payload = {
            "model": "meta-llama/Llama-3.2-11B-Vision-Instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "You are a senior technical analyst. Analyze this stock chart image. Describe: 1. The trend structure (Higher Highs/Lower Lows). 2. Key Support/Resistance levels. 3. Candlestick patterns (e.g., engulfing, pinbars). 4. Any visible indicators."
                        },
                        {
                            "type": "image_url", 
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            "max_tokens": 500
        }
        
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"Vision API Error: {response.status_code}"
            
    except Exception as e:
        return f"Vision Processing Error: {str(e)}"

def parse_report(text):
    """
    FIXED: Uses Regex to dynamically extract the Score, Grade, and Analysis sections.
    """
    report = {
        "score": 0,
        "overall_grade": "N/A",
        "tech": "Analysis failed to generate.",
        "psych": "Analysis failed to generate.",
        "risk": "Analysis failed to generate.",
        "fix": "No fix action available."
    }
    
    try:
        # Extract Score (Matches "Score: 85" or "Score: 85/100")
        score_match = re.search(r"Score:\s*(\d+)", text, re.IGNORECASE)
        if score_match:
            report["score"] = int(score_match.group(1))
            
        # Extract Grade (Matches "Grade: A" or "Grade: B+")
        grade_match = re.search(r"Grade:\s*([A-F][+-]?)", text, re.IGNORECASE)
        if grade_match:
            report["overall_grade"] = grade_match.group(1)

        # Extract Sections using headers as delimiters
        # Note: These patterns align with the prompt instructions in run_forensic_audit
        patterns = {
            "tech": r"Technical Analysis:?\s*(.*?)(?=Psychology:|Risk|Fix|$)",
            "psych": r"Psychology:?\s*(.*?)(?=Risk|Fix|Technical|$)",
            "risk": r"Risk Management:?\s*(.*?)(?=Fix|Technical|Psychology|$)",
            "fix": r"Fix Action:?\s*(.*?)(?=$)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                report[key] = match.group(1).strip()
                
    except Exception as e:
        print(f"Parsing Error: {e}")
        
    return report

def run_forensic_audit(trade_data, image_analysis=""):
    """
    FIXED: Sends both Trade Data AND Image Analysis to the LLM for the final verdict.
    """
    prompt = f"""
    You are a brutal, elite hedge fund Risk Manager. Perform a generic Forensic Audit on this trade.
    
    === TRADER'S INPUT ===
    {trade_data}
    
    === CHART ANALYSIS (From Vision AI) ===
    {image_analysis}
    
    === INSTRUCTIONS ===
    1. Be harsh but constructive. 
    2. Analyze if the entry matched the chart structure.
    3. Grade the trade on execution quality.
    
    === REQUIRED OUTPUT FORMAT (Strictly Follow) ===
    Score: [0-100]
    Grade: [A/B/C/D/F]
    Technical Analysis: [Your critique of the technical setup]
    Psychology: [Your analysis of the trader's emotional state]
    Risk Management: [Your critique of the R:R and sizing]
    Fix Action: [One specific, actionable rule for next time]
    """
    
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
    # Using Llama 3.3 70B for high-quality reasoning
    payload = {
        "model": "meta-llama/Llama-3.3-70B-Instruct",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1200,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Error generating audit: {e}"

def save_analysis(report_data):
    """
    FIXED: Handles RLS errors and ensures user_id is attached.
    """
    if not supabase:
        return None
        
    try:
        # Generate ID and Time
        report_data["id"] = str(uuid.uuid4())
        report_data["created_at"] = datetime.now().isoformat()
        
        # IMPORTANT: Attach User ID for RLS policies
        report_data["user_id"] = st.session_state.get("user", "anonymous")
        
        # Insert
        response = supabase.table("trade_audits").insert(report_data).execute()
        return response
    except Exception as e:
        st.error(f"Database Save Error (Check RLS Policies): {str(e)}")
        return None

# ==========================================
# 4. MAIN APPLICATION LOGIC
# ==========================================

# --- LOGIN SCREEN ---
if not st.session_state["authenticated"]:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-logo">🩸</div>', unsafe_allow_html=True)
    st.markdown('<h1 style="margin-bottom: 10px;">StockPostmortem.ai</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #9ca3af; margin-bottom: 30px;">INSTITUTIONAL GRADE TRADE FORENSICS</p>', unsafe_allow_html=True)
    
    username = st.text_input("Username", placeholder="Enter your ID")
    password = st.text_input("Password", type="password", placeholder="Enter your key")
    
    if st.button("AUTHENTICATE ACCESS", use_container_width=True):
        check_login(username, password)
    
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- NAVIGATION ---
    st.markdown(f"""
    <div class="premium-navbar">
        <div class="nav-brand">
            <div class="nav-logo">🩸</div>
            <div>
                <div class="nav-title">StockPostmortem.ai</div>
                <div class="nav-subtitle">OPERATOR: {st.session_state['user']}</div>
            </div>
        </div>
        <div class="nav-menu">
            <a class="nav-link {'active' if st.session_state['current_page'] == 'analyze' else ''}" onclick="window.location.search='?page=analyze'">ANALYZE</a>
            <a class="nav-link {'active' if st.session_state['current_page'] == 'dashboard' else ''}" onclick="window.location.search='?page=dashboard'">HISTORY</a>
            <a class="nav-link" onclick="window.location.reload()">LOGOUT</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- PAGE: ANALYZE ---
    if st.session_state["current_page"] == "analyze":
        col1, col2 = st.columns([1, 1.5], gap="large")
        
        with col1:
            st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Trade Context</div>', unsafe_allow_html=True)
            
            ticker = st.text_input("Ticker Symbol", placeholder="e.g. SPY, NVDA")
            pnl = st.number_input("P&L ($)", value=0.0, step=10.0)
            
            setup_type = st.selectbox("Setup Type", ["Breakout", "Reversal", "Trend Following", "Scalp", "News Play"])
            mistake_type = st.text_area("What went wrong? (Your notes)", placeholder="I chased the candle...", height=100)
            
            uploaded_file = st.file_uploader("Upload Chart Screenshot", type=['png', 'jpg', 'jpeg'])
            
            if st.button("RUN FORENSIC AUDIT 🩸", type="primary", use_container_width=True):
                if not ticker:
                    st.warning("Please enter a ticker symbol.")
                else:
                    with st.spinner("ANALYZING PRICE ACTION & PSYCHOLOGY..."):
                        # 1. Vision Analysis
                        vision_output = "No chart uploaded."
                        if uploaded_file is not None:
                            image_bytes = uploaded_file.getvalue()
                            vision_output = analyze_image(image_bytes)
                        
                        # 2. Text/Prompt Construction
                        trade_context = f"""
                        Ticker: {ticker}
                        PnL: ${pnl}
                        Setup: {setup_type}
                        Trader Notes: {mistake_type}
                        """
                        
                        # 3. Main Audit
                        raw_analysis = run_forensic_audit(trade_context, vision_output)
                        
                        # 4. Parse Results
                        report = parse_report(raw_analysis)
                        
                        # 5. Save to Session State for display
                        st.session_state['report'] = report
                        st.session_state['report']['ticker'] = ticker
                        st.session_state['report']['pnl'] = pnl
                        
                        # 6. Save to DB
                        db_record = {
                            "ticker": ticker,
                            "pnl": pnl,
                            "setup": setup_type,
                            "score": report['score'],
                            "raw_analysis": raw_analysis,
                            "fix_action": report['fix']
                        }
                        save_analysis(db_record)
                        
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            if 'report' in st.session_state:
                report = st.session_state['report']
                
                # --- SCORE CARD ---
                st.markdown('<div class="glass-panel animate-slide-up">', unsafe_allow_html=True)
                st.markdown(f'<div class="ticker-badge">{report.get("ticker", "UNK")}</div>', unsafe_allow_html=True)
                
                s_col1, s_col2, s_col3 = st.columns([2, 1, 1])
                with s_col1:
                    st.markdown('<div style="font-size: 0.9rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 2px;">Execution Score</div>', unsafe_allow_html=True)
                    # Color coding based on score
                    score_color = "#ef4444" if report['score'] < 50 else "#f59e0b" if report['score'] < 80 else "#10b981"
                    st.markdown(f'<div class="score-value" style="color: {score_color}">{report["score"]}</div>', unsafe_allow_html=True)
                
                with s_col2:
                    st.markdown('<div style="font-size: 0.8rem; color: #9ca3af;">GRADE</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size: 2.5rem; font-weight: 700;">{report["overall_grade"]}</div>', unsafe_allow_html=True)
                    
                with s_col3:
                    st.markdown('<div style="font-size: 0.8rem; color: #9ca3af;">P&L</div>', unsafe_allow_html=True)
                    pnl_val = report.get('pnl', 0)
                    pnl_color = "#10b981" if pnl_val >= 0 else "#ef4444"
                    st.markdown(f'<div style="font-size: 1.5rem; font-weight: 700; color: {pnl_color};">${pnl_val}</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # --- DETAILED ANALYSIS ---
                st.markdown('<div class="section-title">Forensic Breakdown</div>', unsafe_allow_html=True)
                
                # Technical
                st.markdown(f"""
                <div class="report-item animate-slide-right" style="animation-delay: 0.1s;">
                    <span class="report-label">Technical Analysis</span>
                    {report['tech']}
                </div>
                """, unsafe_allow_html=True)
                
                # Psychology
                st.markdown(f"""
                <div class="report-item animate-slide-right" style="animation-delay: 0.2s;">
                    <span class="report-label">Psychology Profile</span>
                    {report['psych']}
                </div>
                """, unsafe_allow_html=True)
                
                # Risk
                st.markdown(f"""
                <div class="report-item animate-slide-right" style="animation-delay: 0.3s;">
                    <span class="report-label">Risk Management</span>
                    {report['risk']}
                </div>
                """, unsafe_allow_html=True)
                
                # Fix Action
                st.markdown(f"""
                <div class="report-item animate-slide-right" style="animation-delay: 0.4s; border-left-color: #f59e0b; background: rgba(245, 158, 11, 0.05);">
                    <span class="report-label" style="color: #f59e0b;">🛑 THE FIX ACTION</span>
                    <strong style="font-size: 1.1em;">{report['fix']}</strong>
                </div>
                """, unsafe_allow_html=True)
                
            else:
                # Placeholder State
                st.markdown('<div class="glass-panel" style="text-align: center; padding: 100px 40px;">', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 4rem; margin-bottom: 20px; opacity: 0.5;">📉</div>', unsafe_allow_html=True)
                st.markdown('<h3 style="margin-bottom: 10px;">Ready for Autopsy</h3>', unsafe_allow_html=True)
                st.markdown('<p style="color: #6b7280;">Input trade details and upload a chart to begin the forensic audit.</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    # --- PAGE: HISTORY/DASHBOARD ---
    elif st.session_state["current_page"] == "dashboard":
        st.markdown('<div class="section-title">Performance Database</div>', unsafe_allow_html=True)
        
        # Fetch Data
        if supabase:
            try:
                # Only show user's own data
                user_id = st.session_state.get("user")
                # Attempt to fetch data. If RLS blocks select, this might return empty.
                response = supabase.table("trade_audits").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
                rows = response.data
            except Exception as e:
                st.error(f"Error fetching history: {e}")
                rows = []
        else:
            rows = []
            st.info("Database not connected. History unavailable.")

        if rows:
            # Metrics
            df = pd.DataFrame(rows)
            avg_score = df['score'].mean()
            win_rate = len(df[df['pnl'] > 0]) / len(df) * 100
            
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-val">{int(avg_score)}</div>
                    <div class="kpi-label">Avg Execution Score</div>
                </div>
                """, unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-val">{len(df)}</div>
                    <div class="kpi-label">Trades Audited</div>
                </div>
                """, unsafe_allow_html=True)
            with m3:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-val">{int(win_rate)}%</div>
                    <div class="kpi-label">Win Rate</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Table/Grid
            for row in rows:
                with st.expander(f"{row.get('created_at')[:10]} | {row.get('ticker')} | Score: {row.get('score')}"):
                    st.write(row.get('raw_analysis'))
                    if row.get('fix_action'):
                        st.markdown(f"**Fix:** {row.get('fix_action')}")
        else:
             st.markdown('<div class="glass-panel" style="text-align: center; color: #6b7280;">No audits recorded yet.</div>', unsafe_allow_html=True)
