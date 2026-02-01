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
supabase = None
API_URL = "https://router.huggingface.co/v1/chat/completions"
HF_TOKEN = ""

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
# 2. PREMIUM DARK THEME CSS
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
    .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; max-width: 1400px !important; }
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    #MainMenu, footer, header { visibility: hidden; }
    
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
    .nav-link:hover, .nav-link.active { color: #10b981; }
    
    /* --- PREMIUM GLASS PANELS --- */
    .glass-panel {
        background: rgba(15, 15, 20, 0.75);
        backdrop-filter: blur(24px) saturate(200%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 36px;
        margin-bottom: 24px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        position: relative; overflow: hidden;
    }
    .glass-panel:hover {
        border-color: rgba(255, 255, 255, 0.12);
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        transform: translateY(-2px);
    }
    
    /* --- PREMIUM INPUTS & BUTTONS --- */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox select {
        background: rgba(20, 20, 28, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
        padding: 14px 18px !important;
    }
    .stButton button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 14px;
        color: white;
        font-weight: 600;
        padding: 14px 32px;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);
    }
    .stButton button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.5);
    }
    
    /* --- KPI CARDS --- */
    .kpi-card {
        background: linear-gradient(135deg, rgba(20, 20, 28, 0.9) 0%, rgba(10, 10, 15, 0.95) 100%);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 32px 28px;
        border-radius: 20px;
        text-align: center;
        transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
    }
    .kpi-val { 
        font-family: 'JetBrains Mono', monospace; font-size: 3rem; font-weight: 700; 
        background: linear-gradient(135deg, #ffffff 0%, #10b981 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .kpi-label { color: #9ca3af; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 2.5px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. FIXED HELPER FUNCTIONS (CORE AI ENGINE)
# ==========================================

def analyze_image(image_bytes):
    """
    FIXED VISION: Uses Llama 3.2 Vision with correct payload structure.
    Returns text description of the chart.
    """
    if not HF_TOKEN:
        return "Vision Analysis Skipped: No API Token."
    
    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}", 
            "Content-Type": "application/json"
        }
        
        # Multimodal payload for Llama 3.2 Vision
        payload = {
            "model": "meta-llama/Llama-3.2-11B-Vision-Instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "Analyze this stock chart image. Describe: 1) The main trend (bullish/bearish), 2) Key Support & Resistance levels, 3) Any visible candlestick patterns (e.g., Doji, Hammer, Engulfing)."
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
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"Vision API Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Vision Processing Error: {str(e)}"

def run_forensic_audit(trade_data, image_analysis=""):
    """
    FIXED ANALYSIS: Combines User Data + Vision Analysis for a 70B Model Audit.
    """
    if not HF_TOKEN:
        return "Error: No API Token configured."

    # Prompt engineering to force specific formatting
    prompt = f"""
    You are a brutal, high-performance trading psychology coach. Perform a FORENSIC AUDIT on this trade.
    
    --- TRADER DATA ---
    {trade_data}
    
    --- CHART EVIDENCE (Vision AI Analysis) ---
    {image_analysis}
    
    --- TASK ---
    Analyze the entry, exit, and mindset. Be critical.
    
    --- OUTPUT FORMAT (STRICT) ---
    Score: [0-100]
    Grade: [A/B/C/D/F]
    Technical Analysis: [Your breakdown of the price action and setup]
    Psychology: [Analysis of the trader's mental state/errors]
    Risk Management: [Critique of position sizing and R:R]
    Fix Action: [ONE actionable step to fix this forever]
    """
    
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}", 
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "meta-llama/Llama-3.3-70B-Instruct",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"AI Error: {response.text}"
    except Exception as e:
        return f"Request Error: {str(e)}"

def parse_report(text):
    """
    FIXED PARSING: Uses Regex to extract dynamic scores and sections.
    """
    # Default fallback values
    report = {
        "score": 50,
        "overall_grade": "C",
        "tech": "Analysis failed to parse.",
        "psych": "Analysis failed to parse.",
        "risk": "Analysis failed to parse.",
        "fix": "Analysis failed to parse."
    }
    
    try:
        # 1. Extract Score
        score_match = re.search(r"Score:\s*(\d+)", text, re.IGNORECASE)
        if score_match:
            report["score"] = int(score_match.group(1))
            
        # 2. Extract Grade
        grade_match = re.search(r"Grade:\s*([A-F][+-]?)", text, re.IGNORECASE)
        if grade_match:
            report["overall_grade"] = grade_match.group(1)

        # 3. Extract Sections
        patterns = {
            "tech": r"Technical Analysis:?\s*(.*?)(?=Psychology:|Risk|Fix|$)",
            "psych": r"Psychology:?\s*(.*?)(?=Risk|Technical|Fix|$)",
            "risk": r"Risk Management:?\s*(.*?)(?=Fix|Technical|Psychology|$)",
            "fix": r"Fix Action:?\s*(.*?)(?=$)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                report[key] = match.group(1).strip()
                
    except Exception as e:
        print(f"Parsing error: {e}")
        
    return report

def save_analysis(report_data):
    """
    FIXED DATABASE: Includes user_id and handles RLS errors.
    """
    if not supabase:
        return None
    try:
        # Add metadata
        report_data["id"] = str(uuid.uuid4())
        report_data["created_at"] = datetime.now().isoformat()
        report_data["user_id"] = st.session_state.get("user", "anonymous")
        
        # Insert
        response = supabase.table("trade_audits").insert(report_data).execute()
        return response
    except Exception as e:
        st.error(f"Database Error (RLS?): {str(e)}")
        return None

# ==========================================
# 4. MAIN APP LOGIC
# ==========================================

if not st.session_state["authenticated"]:
    # --- LOGIN PAGE ---
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-logo">🩸</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 2rem; font-weight: 700; margin-bottom: 10px;">StockPostmortem</div>', unsafe_allow_html=True)
    st.markdown('<div style="color: #9ca3af; margin-bottom: 30px;">Forensic Audit System for Traders</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username", placeholder="trader1")
    with col2:
        password = st.text_input("Password", type="password", placeholder="••••••••")
        
    if st.button("AUTHENTICATE SYSTEM", use_container_width=True):
        check_login(username, password)
        
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- NAVBAR ---
    st.markdown(f"""
    <div class="premium-navbar">
        <div class="nav-brand">
            <div class="nav-logo">🩸</div>
            <div>
                <div class="nav-title">StockPostmortem.ai</div>
                <div class="nav-subtitle">OPERATOR: {st.session_state['user'].upper()}</div>
            </div>
        </div>
        <div class="nav-menu">
            <div class="nav-link {'active' if st.session_state['current_page'] == 'analyze' else ''}" onclick="window.location.href='?page=analyze'">ANALYZE</div>
            <div class="nav-link {'active' if st.session_state['current_page'] == 'dashboard' else ''}" onclick="window.location.href='?page=dashboard'">DASHBOARD</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- LOGOUT BUTTON ---
    if st.sidebar.button("Logout"):
        logout()

    # ==========================================
    # PAGE: ANALYZE
    # ==========================================
    if st.session_state["current_page"] == "analyze":
        st.markdown('<div class="section-title">Initiate New Audit</div>', unsafe_allow_html=True)
        
        col_input, col_chart = st.columns([1, 1], gap="large")
        
        with col_input:
            st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
            st.markdown('<div class="report-label">Trade Data</div>', unsafe_allow_html=True)
            
            ticker = st.text_input("Ticker Symbol", placeholder="e.g. NIFTY, TSLA")
            pnl = st.number_input("P&L ($)", value=0.0, step=10.0)
            
            setup = st.selectbox("Setup Used", ["Breakout", "Reversal", "Trend Following", "Scalp", "News", "Impulse"])
            
            notes = st.text_area("Trader's Notes (Why did you enter/exit?)", height=150, 
                               placeholder="I saw a double bottom but entered too early...")
                               
            uploaded_file = st.file_uploader("Upload Chart Screenshot", type=['png', 'jpg', 'jpeg'])
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button("RUN FORENSIC AUDIT", type="primary", use_container_width=True):
                if not notes:
                    st.warning("Please provide trade notes.")
                else:
                    with st.spinner("🔍 Running Deep Forensic Analysis..."):
                        # 1. Vision Analysis
                        vision_text = ""
                        if uploaded_file:
                            image_bytes = uploaded_file.getvalue()
                            vision_text = analyze_image(image_bytes)
                        
                        # 2. Construct Data Packet
                        trade_context = f"""
                        Ticker: {ticker}
                        P&L: {pnl}
                        Setup: {setup}
                        Trader Notes: {notes}
                        """
                        
                        # 3. Get AI Analysis
                        raw_audit = run_forensic_audit(trade_context, vision_text)
                        
                        # 4. Parse Results
                        structured_report = parse_report(raw_audit)
                        
                        # 5. Save to DB
                        db_entry = {
                            "ticker": ticker,
                            "pnl": pnl,
                            "setup": setup,
                            "notes": notes,
                            "ai_score": structured_report["score"],
                            "ai_grade": structured_report["overall_grade"],
                            "technical_analysis": structured_report["tech"],
                            "psychology": structured_report["psych"],
                            "risk_management": structured_report["risk"],
                            "fix_action": structured_report["fix"],
                            "vision_data": vision_text
                        }
                        save_analysis(db_entry)
                        
                        # 6. Store in Session for Display
                        st.session_state["last_audit"] = structured_report
                        st.rerun()

        with col_chart:
            # RESULTS DISPLAY
            if "last_audit" in st.session_state:
                res = st.session_state["last_audit"]
                
                # Dynamic Color based on Grade
                grade_color = "#10b981" if res["overall_grade"] in ['A', 'A+', 'A-', 'B'] else "#ef4444"
                
                st.markdown(f"""
                <div class="glass-panel animate-fade-in">
                    <div class="score-container">
                        <div>
                            <div class="report-label">FORENSIC SCORE</div>
                            <div class="score-value" style="color: {grade_color}">{res['score']}</div>
                        </div>
                        <div class="score-meta">
                            <div class="grade-badge" style="background: {grade_color}20; color: {grade_color}; border: 1px solid {grade_color}40;">
                                GRADE: {res['overall_grade']}
                            </div>
                        </div>
                    </div>
                    
                    <div class="report-grid">
                        <div class="report-item">
                            <span class="report-label" style="color:#3b82f6">Technical Reality</span>
                            {res['tech']}
                        </div>
                        <div class="report-item">
                            <span class="report-label" style="color:#8b5cf6">Psychology Check</span>
                            {res['psych']}
                        </div>
                        <div class="report-item">
                            <span class="report-label" style="color:#f59e0b">Risk Profile</span>
                            {res['risk']}
                        </div>
                        <div class="report-item" style="background: rgba(16, 185, 129, 0.1); border-left-color: #10b981;">
                            <span class="report-label" style="color:#10b981">REQUIRED FIX</span>
                            {res['fix']}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="glass-panel" style="text-align: center; padding: 60px;">
                    <div style="font-size: 4rem; opacity: 0.2; margin-bottom: 20px;">📊</div>
                    <div style="color: #6b7280;">Waiting for trade data...</div>
                </div>
                """, unsafe_allow_html=True)

    # ==========================================
    # PAGE: DASHBOARD
    # ==========================================
    elif st.session_state["current_page"] == "dashboard":
        st.markdown('<div class="section-title">Performance Database</div>', unsafe_allow_html=True)
        
        if not supabase:
            st.error("Database not connected.")
        else:
            # Fetch data for current user
            user = st.session_state.get("user")
            response = supabase.table("trade_audits").select("*").eq("user_id", user).order("created_at", desc=True).execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                
                # KPI CARDS
                st.markdown('<div class="kpi-container">', unsafe_allow_html=True)
                
                kpi1, kpi2, kpi3 = st.columns(3)
                
                avg_score = df['ai_score'].mean()
                total_pnl = df['pnl'].sum()
                win_rate = (len(df[df['pnl'] > 0]) / len(df)) * 100 if len(df) > 0 else 0
                
                with kpi1:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-val">{int(avg_score)}</div>
                        <div class="kpi-label">AVG AI SCORE</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with kpi2:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-val">${total_pnl:.0f}</div>
                        <div class="kpi-label">NET P&L</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with kpi3:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-val">{int(win_rate)}%</div>
                        <div class="kpi-label">WIN RATE</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown('</div>', unsafe_allow_html=True)
                
                # RECENT AUDITS LIST
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                st.markdown('<div class="report-label">Recent Audits</div>', unsafe_allow_html=True)
                
                for index, row in df.iterrows():
                    with st.expander(f"{row['created_at'][:10]} | {row['ticker']} | Score: {row['ai_score']}"):
                        st.markdown(f"""
                        **Setup:** {row['setup']}  
                        **P&L:** ${row['pnl']}  
                        **AI Grade:** {row['ai_grade']}
                        
                        ---
                        **Technical Analysis:** {row['technical_analysis']}
                        
                        **Fix Action:** {row['fix_action']}
                        """)
                st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.info("No audits found. Go to 'Analyze' to log your first trade.")
