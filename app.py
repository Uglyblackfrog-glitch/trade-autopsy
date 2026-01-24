import streamlit as st
import requests
import base64
import io
import re
import pandas as pd
import time
from PIL import Image
from supabase import create_client, Client

# ==========================================
# 0. AUTH & CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="StockPostmortem.ai | Forensic Audit", 
    page_icon="🧬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- USER ACCOUNTS (Replace with DB later if needed) ---
USERS = {
    "trader1": "profit2026",
    "demo": "12345",
    "admin": "admin"
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = None

def check_login(username, password):
    if username in USERS and USERS[username] == password:
        st.session_state["authenticated"] = True
        st.session_state["user"] = username
        st.rerun()
    else:
        st.error("⚠️ Access Denied: Invalid Credentials.")

def logout():
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.rerun()

# ==========================================
# 1. DATABASE & API CONNECTION
# ==========================================
if st.session_state["authenticated"]:
    try:
        # Load Secrets
        HF_TOKEN = st.secrets["HF_TOKEN"]
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"⚠️ System Configuration Error: {e}")
        st.stop()

# ==========================================
# 2. THE FORENSIC INTELLIGENCE ENGINE
# ==========================================

def run_scientific_analysis(messages, mode="text"):
    """
    Routes traffic to High-Performance Specialist Models.
    Text Mode: Qwen 2.5 72B (Deep Logic & Reasoning)
    Vision Mode: Qwen 2.5 VL 7B (Visual Data Extraction)
    """
    api_url = "https://router.huggingface.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
    
    if mode == "text":
        model_id = "Qwen/Qwen2.5-72B-Instruct" 
    else:
        model_id = "Qwen/Qwen2.5-VL-7B-Instruct"

    payload = {
        "model": model_id,
        "messages": messages,
        "max_tokens": 2048,  # Increased for VERY DETAILED output
        "temperature": 0.4,  # Low temp for scientific precision
        "top_p": 0.9
    }

    # Robust Retry Loop for Reliability
    for attempt in range(3):
        try:
            res = requests.post(api_url, headers=headers, json=payload, timeout=90)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            elif res.status_code == 503: 
                time.sleep(5) 
                continue
            else:
                raise Exception(f"HF Error {res.status_code}: {res.text}")
        except Exception as e:
            if attempt == 2: raise e
            time.sleep(2)

# ==========================================
# 3. DATA PARSING & STORAGE
# ==========================================
# Custom CSS for "Science Lab" Aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    
    body, .stApp { background-color: #0E1117 !important; color: #E0E0E0; font-family: 'Inter', sans-serif; }
    
    /* Headers */
    h1, h2, h3 { font-family: 'JetBrains Mono', monospace; letter-spacing: -1px; }
    
    /* Report Container */
    .report-box { 
        background: #161B22; 
        border: 1px solid #30363D; 
        border-radius: 12px; 
        padding: 25px; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    
    /* Section Headers in Report */
    .section-title {
        color: #58A6FF;
        font-family: 'JetBrains Mono', monospace;
        font-weight: bold;
        font-size: 1.1rem;
        border-bottom: 1px solid #30363D;
        padding-bottom: 5px;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    
    /* Score Circle */
    .score-circle {
        font-size: 4rem; 
        font-weight: 800; 
        line-height: 1;
    }
    
    /* Buttons */
    button[kind="primary"] { 
        background: linear-gradient(90deg, #238636, #2EA043) !important; 
        border: none; 
        font-family: 'JetBrains Mono', monospace;
    }
</style>
""", unsafe_allow_html=True)

def get_user_rules(user_id):
    try:
        res = supabase.table("rules").select("*").eq("user_id", user_id).execute()
        return [r['rule_text'] for r in res.data]
    except: return []

def parse_scientific_report(text):
    """
    Parses the detailed JSON-like structure from the AI scientist.
    """
    text = text.replace("**", "").replace("##", "").strip()
    
    sections = { 
        "score": 0, 
        "tags": ["Analysis Pending"], 
        "tech": "Detailed analysis generation failed.", 
        "psych": "Psychological profile incomplete.", 
        "risk": "Risk metrics unavailable.", 
        "fix": "Review data manually." 
    }
    
    # Extract Score
    score_match = re.search(r'\[SCORE\]\s*(\d+)', text, re.IGNORECASE)
    if score_match: sections['score'] = int(score_match.group(1))

    # Extract Tags
    tags_match = re.search(r'\[TAGS\](.*?)(?=\[|$)', text, re.DOTALL | re.IGNORECASE)
    if tags_match:
        raw = tags_match.group(1).replace('[', '').replace(']', '').split(',')
        sections['tags'] = [t.strip() for t in raw if t.strip()]
    
    # Extract Deep Dive Sections
    patterns = {
        "tech": r"\[TECHNICAL FORENSICS\](.*?)(?=\[PSYCHOLOGICAL PROFILE\]|\[RISK ASSESSMENT\]|\[STRATEGIC ROADMAP\]|\[SCORE\]|\[TAGS\]|$)",
        "psych": r"\[PSYCHOLOGICAL PROFILE\](.*?)(?=\[RISK ASSESSMENT\]|\[STRATEGIC ROADMAP\]|\[SCORE\]|\[TAGS\]|$)",
        "risk": r"\[RISK ASSESSMENT\](.*?)(?=\[STRATEGIC ROADMAP\]|\[SCORE\]|\[TAGS\]|$)",
        "fix": r"\[STRATEGIC ROADMAP\](.*?)(?=\[SCORE\]|\[TAGS\]|$)"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match: sections[key] = match.group(1).strip()
            
    return sections

def save_to_lab_records(user_id, data):
    payload = {
        "user_id": user_id,
        "score": data.get('score', 0),
        "mistake_tags": data.get('tags', []),
        "technical_analysis": data.get('tech', ''),
        "psych_analysis": data.get('psych', ''),
        "risk_analysis": data.get('risk', ''),
        "fix_action": data.get('fix', '')
    }
    try:
        supabase.table("trades").insert(payload).execute()
        if data.get('score', 0) < 50:
            clean_fix = data.get('fix', 'Follow Strict Protocol').split('.')[0][:100]
            supabase.table("rules").insert({"user_id": user_id, "rule_text": clean_fix}).execute()
            st.toast("🧬 Protocol Violation Recorded. New Rule Added.")
    except Exception as e:
        st.error(f"Database Sync Error: {e}")

# ==========================================
# 4. MAIN LABORATORY INTERFACE
# ==========================================
if not st.session_state["authenticated"]:
    # LOGIN SCREEN
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><br><h1 style='text-align:center'>🧬 STOCK<br>POSTMORTEM</h1>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Investigator ID"); p = st.text_input("Access Key", type="password")
            if st.form_submit_button("AUTHENTICATE", type="primary", use_container_width=True): check_login(u, p)

else:
    # APP INTERFACE
    user = st.session_state["user"]
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/dna-helix.png", width=50)
        st.title(f"Operator: {user}")
        st.divider()
        if st.button("🔒 TERMINATE SESSION"): logout()

    st.markdown("<h1>🧬 FORENSIC <span style='color:#58A6FF'>TRADING LAB</span></h1>", unsafe_allow_html=True)
    
    tab_audit, tab_laws, tab_data = st.tabs(["🔬 DIAGNOSTIC AUDIT", "⚖️ PROTOCOLS", "📊 DATA VAULT"])

    # ----------------------------------------------------
    # TAB 1: DIAGNOSTIC AUDIT (The Core)
    # ----------------------------------------------------
    with tab_audit:
        my_rules = get_user_rules(user)
        if my_rules:
            with st.expander(f"⚠️ ACTIVE PROTOCOLS ({len(my_rules)}) - VIOLATIONS WILL BE PENALIZED"):
                for r in my_rules: st.markdown(f"🔴 {r}")

        # Input Method Selection
        st.write("### Select Data Input Source:")
        mode = st.radio("Input Source", ["Detailed Text Log", "Visual Evidence (Chart/P&L)"], horizontal=True, label_visibility="collapsed")
        
        # --- VISION ANALYSIS (CHARTS & P&L) ---
        if "Visual Evidence" in mode:
            st.info("Supported: Candlestick Charts (Technical Analysis) OR P&L Dashboards (Financial Health Audit)")
            up_file = st.file_uploader("Upload Evidence", type=["png", "jpg", "jpeg"])
            
            if up_file:
                st.image(up_file, width=600, caption="Evidence Locked")
                
                if st.button("INITIATE FORENSIC SCAN", type="primary"):
                    # Process Image
                    image = Image.open(up_file)
                    if image.mode != 'RGB': image = image.convert('RGB')
                    buf = io.BytesIO()
                    image.save(buf, format="JPEG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    
                    # --- THE SCIENTIST PROMPT (VISION) ---
                    prompt = f"""
                    You are Dr. Market, a Chief Investment Officer and Behavioral Economist. 
                    You are auditing a trader's image. It is either a Technical Chart OR a P&L Statement.
                    
                    USER'S ESTABLISHED RULES: {my_rules}

                    Your Goal: Provide a "Scientific Deep Dive" into what went wrong or right.
                    
                    --- ANALYSIS PATH A: IF IMAGE IS A P&L DASHBOARD (Red/Green Numbers) ---
                    1. [TECHNICAL FORENSICS]: Extract the data. Calculate the drawdown %. Identify the "Toxic Asset" (biggest loser). Analyze the Concentration Risk (is the portfolio diversified or gambling?).
                    2. [PSYCHOLOGICAL PROFILE]: Diagnose the behavior based on the numbers. (e.g., "Disposition Effect" if holding losers too long, "Overconfidence" if size is too big).
                    3. [SCORE]: 
                       - If Unrealized Loss > 15%: Score MUST be < 30.
                       - If Holding Losers > Winners: Score MUST be < 40.
                    
                    --- ANALYSIS PATH B: IF IMAGE IS A CHART ---
                    1. [TECHNICAL FORENSICS]: Analyze Market Structure (Higher Highs/Lows), Liquidity Sweeps, Moving Averages, and Volume anomalies.
                    2. [RISK ASSESSMENT]: Identify where the Invalidations (Stop Loss) should have been vs where they were.
                    3. [SCORE]: Grade the entry execution and trade management (0-100).

                    --- OUTPUT FORMAT (STRICT) ---
                    [SCORE] (0-100)
                    [TAGS] (Comma separated list, e.g., Disposition Effect, Liquidity Trap, FOMO)
                    [TECHNICAL FORENSICS] (2-3 detailed paragraphs using economic terms. Be thorough.)
                    [PSYCHOLOGICAL PROFILE] (Deep psychoanalysis of the trader's mental state.)
                    [RISK ASSESSMENT] (Mathematical view of the risk taken vs reward expected.)
                    [STRATEGIC ROADMAP] (Step-by-step scientific method to fix this error.)
                    """
                    
                    messages = [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                        ]
                    }]
                    
                    with st.spinner("🔬 Running Spectral Analysis on Financial Data..."):
                        try:
                            raw = run_scientific_analysis(messages, mode="vision")
                            report = parse_scientific_report(raw)
                            save_to_lab_records(user, report)
                            
                            # DISPLAY REPORT
                            c_score = "#ff4d4d" if report['score'] < 50 else "#00e676"
                            st.markdown(f"""
                            <div class="report-box">
                                <div style="display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid #444; padding-bottom:10px;">
                                    <h2 style="margin:0; color:#fff;">DIAGNOSTIC REPORT</h2>
                                    <div style="text-align:right;">
                                        <div style="font-size:0.8rem; color:#888;">PERFORMANCE SCORE</div>
                                        <div class="score-circle" style="color:{c_score};">{report['score']}</div>
                                    </div>
                                </div>
                                <div style="margin-top:10px; margin-bottom:20px;">
                                    {' '.join([f'<span style="background:#262626; border:1px solid #444; padding:4px 8px; border-radius:4px; font-size:0.8rem; margin-right:5px;">{t}</span>' for t in report['tags']])}
                                </div>
                                
                                <div class="section-title">📊 TECHNICAL FORENSICS</div>
                                <div style="color:#d0d7de; line-height:1.6;">{report['tech']}</div>
                                
                                <div class="section-title">🧠 PSYCHOLOGICAL PROFILE</div>
                                <div style="color:#d0d7de; line-height:1.6;">{report['psych']}</div>
                                
                                <div class="section-title">⚖️ RISK ASSESSMENT</div>
                                <div style="color:#d0d7de; line-height:1.6;">{report['risk']}</div>
                                
                                <div class="section-title">🚀 STRATEGIC ROADMAP</div>
                                <div style="background:rgba(46, 160, 67, 0.1); border-left:4px solid #2ea043; padding:15px; color:#fff;">{report['fix']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        except Exception as e: st.error(f"Analysis Failed: {str(e)}")

        # --- TEXT LOG ANALYSIS ---
        else:
            with st.form("text_audit"):
                c1,c2 = st.columns(2)
                with c1: tick = st.text_input("Asset Ticker", "BTC/USD")
                with c2: timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1H", "4H", "Daily"])
                
                c1,c2,c3 = st.columns(3)
                with c1: ent = st.number_input("Entry Price", 0.0)
                with c2: ex = st.number_input("Exit Price", 0.0)
                with c3: stp = st.number_input("Stop Loss", 0.0)
                
                context = st.text_area("Trader's Context (Why did you take this? How did you feel?)", height=100)
                
                if st.form_submit_button("SUBMIT FOR PEER REVIEW", type="primary", use_container_width=True):
                    # Python Math Logic
                    risk = abs(ent - stp)
                    # Detect Stop Violation
                    violation = False
                    if (ent > stp and ex < stp) or (ent < stp and ex > stp):
                        violation = True
                    
                    r_multiple = 0
                    if risk > 0:
                        if ent > stp: # Long
                            r_multiple = (ex - ent) / risk
                        else: # Short
                            r_multiple = (ent - ex) / risk
                    
                    math_block = f"""
                    [QUANTITATIVE DATA]
                    - Risk Per Share: {risk}
                    - R-Multiple Realized: {r_multiple:.2f}R
                    - Stop Loss Violation Detected: {violation}
                    """
                    
                    prompt = f"""
                    You are the Chief Risk Officer at a proprietary trading firm. 
                    Perform a rigorous post-mortem on this trade.
                    
                    USER RULES: {my_rules}
                    
                    TRADE DATA:
                    Ticker: {tick} ({timeframe})
                    Context: {context}
                    {math_block}
                    
                    SCORING CRITERIA:
                    1. If Stop Loss Violation is TRUE -> Immediate Score Penalty (-50 points). Score cannot exceed 40.
                    2. If R-Multiple is less than 1.0 -> Penalize Score.
                    3. If Context indicates emotional reasoning ("hope", "revenge", "felt like") -> Penalize Score.
                    
                    REQUIRED OUTPUT FORMAT (Detailed & Educational):
                    [SCORE] (0-100)
                    [TAGS] (List of errors found)
                    [TECHNICAL FORENSICS] (Explain the setup validity, market structure, and timing execution.)
                    [PSYCHOLOGICAL PROFILE] (Analyze the user's input. Detect cognitive biases like Confirmation Bias, FOMO, or Tilt.)
                    [RISK ASSESSMENT] (Discuss the R-multiple. Was the risk worth the reward? Was position sizing implied to be safe?)
                    [STRATEGIC ROADMAP] (Detailed instructions on how to prevent this specific failure pattern next time.)
                    """
                    
                    messages = [{"role": "user", "content": prompt}]
                    
                    with st.spinner("🤖 Computing Probability Matrix..."):
                        try:
                            raw = run_scientific_analysis(messages, mode="text")
                            report = parse_scientific_report(raw)
                            save_to_lab_records(user, report)
                            
                             # DISPLAY REPORT (Reusing the beautiful HTML)
                            c_score = "#ff4d4d" if report['score'] < 50 else "#00e676"
                            st.markdown(f"""
                            <div class="report-box">
                                <div style="display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid #444; padding-bottom:10px;">
                                    <h2 style="margin:0; color:#fff;">DIAGNOSTIC REPORT</h2>
                                    <div style="text-align:right;">
                                        <div style="font-size:0.8rem; color:#888;">PERFORMANCE SCORE</div>
                                        <div class="score-circle" style="color:{c_score};">{report['score']}</div>
                                    </div>
                                </div>
                                <div style="margin-top:10px; margin-bottom:20px;">
                                    {' '.join([f'<span style="background:#262626; border:1px solid #444; padding:4px 8px; border-radius:4px; font-size:0.8rem; margin-right:5px;">{t}</span>' for t in report['tags']])}
                                </div>
                                
                                <div class="section-title">📊 TECHNICAL FORENSICS</div>
                                <div style="color:#d0d7de; line-height:1.6;">{report['tech']}</div>
                                
                                <div class="section-title">🧠 PSYCHOLOGICAL PROFILE</div>
                                <div style="color:#d0d7de; line-height:1.6;">{report['psych']}</div>
                                
                                <div class="section-title">⚖️ RISK ASSESSMENT</div>
                                <div style="color:#d0d7de; line-height:1.6;">{report['risk']}</div>
                                
                                <div class="section-title">🚀 STRATEGIC ROADMAP</div>
                                <div style="background:rgba(46, 160, 67, 0.1); border-left:4px solid #2ea043; padding:15px; color:#fff;">{report['fix']}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        except Exception as e: st.error(str(e))

    # ----------------------------------------------------
    # TAB 2: CONSTITUTION
    # ----------------------------------------------------
    with tab_laws:
        st.subheader("📜 Trading Protocols (The Constitution)")
        st.write("These rules are automatically generated when you fail a trade. You must adhere to them.")
        rules = supabase.table("rules").select("*").eq("user_id", user).execute().data
        if not rules:
            st.info("No active restrictions. Stay disciplined.")
        for r in rules:
            c1,c2 = st.columns([5,1])
            with c1: st.error(f"⛔ {r['rule_text']}")
            with c2: 
                if st.button("Expunge", key=r['id']):
                    supabase.table("rules").delete().eq("id", r['id']).execute(); st.rerun()

    # ----------------------------------------------------
    # TAB 3: DATA VAULT
    # ----------------------------------------------------
    with tab_data:
        st.subheader("📂 Historical Trade Ledger")
        hist = supabase.table("trades").select("*").eq("user_id", user).order("created_at", desc=True).execute().data
        if hist:
            df = pd.DataFrame(hist)
            st.dataframe(
                df[['created_at', 'score', 'mistake_tags', 'fix_action']],
                use_container_width=True,
                height=400
            )
        else:
            st.write("No records found in the vault.")
