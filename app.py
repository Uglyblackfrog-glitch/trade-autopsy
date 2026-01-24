import streamlit as st
import requests
import base64
import io
import re
import pandas as pd
from PIL import Image
from supabase import create_client, Client

# ==========================================
# 0. AUTHENTICATION & CONFIG
# ==========================================
# THIS MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="StockPostmortem.ai", page_icon="🩸", layout="wide")

# --- USER CREDENTIALS (HARDCODED FOR DEMO) ---
USERS = {
    "trader1": "profit2026",
    "demo_user": "12345",
    "admin": "adminpass"
}

# Session State Init
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = None

def check_login(username, password):
    if username in USERS and USERS[username] == password:
        st.session_state["authenticated"] = True
        st.session_state["user"] = username
        st.rerun()
    else:
        st.error("Incorrect username or password")

def logout():
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.rerun()

# ==========================================
# 1. DATABASE & API SETUP
# ==========================================
if st.session_state["authenticated"]:
    try:
        # Load secrets from .streamlit/secrets.toml
        HF_TOKEN = st.secrets["HF_TOKEN"]
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
        
        # Initialize Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        API_URL = "https://router.huggingface.co/v1/chat/completions"
        
    except Exception as e:
        st.error(f"⚠️ Configuration Error: {e}")
        st.info("Ensure HF_TOKEN, SUPABASE_URL, and SUPABASE_KEY are in secrets.toml")
        st.stop()

# ==========================================
# 2. CSS STYLING
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;800&display=swap');
    
    body, .stApp { background-color: #050505 !important; font-family: 'Space Grotesk', sans-serif !important; color: #e2e8f0; }
    
    /* Login Box */
    .login-box { max-width: 400px; margin: 100px auto; padding: 2rem; border: 1px solid #333; border-radius: 12px; background: #0d1117; }
    
    /* Stats & Score */
    .stat-card { background: #0d1117; border: 1px solid #30363d; padding: 15px; border-radius: 8px; text-align: center; }
    .stat-val { font-size: 2rem; font-weight: 800; color: white; }
    .stat-label { color: #888; font-size: 0.8rem; text-transform: uppercase; }
    
    /* Report Cards */
    .report-container { background: #0d1117; border: 1px solid #30363d; border-radius: 12px; padding: 2rem; margin-top: 20px; }
    .analysis-card { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 15px; margin-bottom: 10px; border-left: 4px solid #555; }
    
    /* Custom Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid #333; }
    .stTabs [data-baseweb="tab"] { border: none; color: #888; }
    .stTabs [aria-selected="true"] { color: #ff4d4d !important; border-bottom: 2px solid #ff4d4d !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================

def get_user_rules(user_id):
    """Fetch active rules for logged-in user"""
    try:
        response = supabase.table("rules").select("*").eq("user_id", user_id).execute()
        return [r['rule_text'] for r in response.data]
    except:
        return []

def clean_text(text):
    """STRICT FILTER: Removes emojis and filler."""
    # Remove emojis and non-standard characters
    text = re.sub(r'[^\w\s,.:;!?()\[\]\-\'\"%]', '', text) 
    return text.strip()

def parse_report(text):
    """Robust Regex Parsing"""
    sections = {
        "score": 0, "tags": [], 
        "tech": "N/A", "psych": "N/A", "risk": "N/A", "fix": "N/A"
    }
    
    # Clean input first
    text = clean_text(text)

    # 1. Extract Score
    score_match = re.search(r'\[SCORE\]\s*(\d+)', text)
    if score_match: sections['score'] = int(score_match.group(1))
    
    # 2. Extract Tags
    tags_match = re.search(r'\[TAGS\](.*?)(?=\[|$)', text, re.DOTALL)
    if tags_match:
        raw = tags_match.group(1).replace('[', '').replace(']', '').split(',')
        sections['tags'] = [t.strip() for t in raw if t.strip()]

    # 3. Extract Text Blocks
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

def save_analysis(user_id, data):
    """Save trade to DB"""
    payload = {
        "user_id": user_id,
        "score": data.get('score', 0),
        "mistake_tags": data.get('tags', []),
        "technical_analysis": data.get('tech', ''),
        "psych_analysis": data.get('psych', ''),
        "risk_analysis": data.get('risk', ''),
        "fix_action": data.get('fix', '')
    }
    supabase.table("trades").insert(payload).execute()
    
    # Auto-Rule Generation
    if data.get('score', 0) < 50:
        supabase.table("rules").insert({"user_id": user_id, "rule_text": data.get('fix')}).execute()
        st.toast("📉 New Rule added to Constitution.")

# ==========================================
# 4. MAIN APP LOGIC
# ==========================================

if not st.session_state["authenticated"]:
    # --- LOGIN SCREEN ---
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.title("🩸 StockPostmortem")
        st.caption("Secure Access Terminal")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("UNLOCK DASHBOARD", type="primary", use_container_width=True)
            
            if submit_login:
                check_login(username, password)
        st.markdown("</div>", unsafe_allow_html=True)

else:
    # --- DASHBOARD (LOGGED IN) ---
    current_user = st.session_state["user"]
    
    # Sidebar
    with st.sidebar:
        st.header(f"👤 {current_user}")
        if st.button("LOGOUT", use_container_width=True): logout()

    st.markdown("""
    <div style="text-align:center; padding-top: 20px;">
        <div style="font-size: 1.5rem; font-weight: 800; color: white;">STOCK<span style="color:#ff4d4d">POSTMORTEM</span>.AI</div>
    </div>
    """, unsafe_allow_html=True)

    # Tabs
    main_tab1, main_tab2, main_tab3 = st.tabs(["🔍 NEW AUTOPSY", "⚖️ CONSTITUTION", "📈 PERFORMANCE"])

    # --- TAB 1: ANALYSIS ---
    with main_tab1:
        my_rules = get_user_rules(current_user)
        
        # Display Rules Alert
        if my_rules:
            with st.expander("🚨 ACTIVE RULES (AI IS WATCHING)", expanded=False):
                for rule in my_rules:
                    st.markdown(f"❌ **{rule}**")

        # UI Layout
        c_mode = st.radio("Input Mode", ["Text Report", "Chart Vision"], horizontal=True, label_visibility="collapsed")
        
        prompt = ""
        img_b64 = None
        ready_to_run = False

        # --- MODE A: VISION ANALYSIS ---
        if c_mode == "Chart Vision":
            uploaded_file = st.file_uploader("Upload Chart", type=["png", "jpg"])
            if uploaded_file:
                st.image(uploaded_file, width=400)
                if st.button("RUN VISION AUDIT", type="primary"):
                    image = Image.open(uploaded_file)
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    
                    # SYSTEM PROMPT FOR VISION
                    prompt = f"""
                    SYSTEM: You are an Algorithmic Trading Auditor. 
                    TASK: Analyze the image pixel-by-pixel.
                    
                    STRICT CONSTRAINTS:
                    1. Output is BINARY and FACTUAL. Do not infer "emotions".
                    2. IGNORE indicators not clearly visible.
                    3. NO conversational filler. NO emojis.
                    
                    OUTPUT FORMAT:
                    [SCORE] 0-100
                    [TAGS] Tag1, Tag2
                    [TECH] Specific candle/structure failure identified.
                    [PSYCH] Implied intent based on entry location.
                    [RISK] Visual stop loss placement analysis.
                    [FIX] One imperative correction rule.
                    """
                    ready_to_run = True

        # --- MODE B: TEXT ANALYSIS ---
        else:
            with st.form("text_form"):
                c1, c2, c3 = st.columns(3)
                with c1: ticker = st.text_input("Ticker", "SPY")
                with c2: emotion = st.selectbox("State", ["Neutral", "FOMO", "Revenge", "Fear", "Tilt"])
                with c3: setup_type = st.selectbox("Setup", ["Trend Follow", "Reversal", "Breakout", "Impulse"])

                c4, c5, c6 = st.columns(3)
                with c4: entry = st.number_input("Entry", value=0.0)
                with c5: exit_price = st.number_input("Exit", value=0.0)
                with c6: stop = st.number_input("Stop Loss", value=0.0)

                notes = st.text_area("Context Notes", placeholder="e.g. Broke VWAP, volume was low...")

                if st.form_submit_button("AUDIT TRADE", type="primary", use_container_width=True):
                    
                    # 1. PYTHON CALCULATION LAYER (Deterministic)
                    try:
                        risk = abs(entry - stop)
                        loss = abs(entry - exit_price)
                        r_multiple = -1 * (loss / risk) if risk > 0 else 0
                        
                        # Logic: Did they respect the stop?
                        stop_violation = False
                        if (entry > stop and exit_price < stop) or (entry < stop and exit_price > stop):
                            stop_violation = True
                            
                        # Logic: Slippage check
                        slippage = 0
                        if risk > 0:
                            slippage = ((loss - risk) / risk) * 100
                        
                        math_block = f"""
                        [CALCULATED_METRICS]
                        Risk_Per_Share: {risk:.2f}
                        Actual_Loss: {loss:.2f}
                        R_Multiple: {r_multiple:.2f}R
                        Stop_Violation: {stop_violation} (TRUE = Critical Failure)
                        Risk_Deviation_Percent: {slippage:.2f}%
                        """
                    except:
                        math_block = "[CALCULATED_METRICS] Insufficient numeric data."

                    # 2. THE SYSTEM PROMPT
                    prompt = f"""
                    SYSTEM INSTRUCTION:
                    You are a Deterministic Trade Audit Engine. You are NOT a chatbot. 
                    You analyze input parameters and output a JSON-like structured report.
                    
                    RULES:
                    1. TONE: Clinical, Harsh, Professional. NO EMOJIS. NO "I think".
                    2. DATA PRIORITY: Use the [CALCULATED_METRICS] above. Do not recalculate.
                    3. SCORING: 
                       - If Stop_Violation == True, Max Score is 30.
                       - If Emotion == 'Revenge' or 'Tilt', Max Score is 40.
                    4. USER RULES: Check against: {my_rules}. If violated, mention it.

                    INPUT DATA:
                    Ticker: {ticker} | Setup: {setup_type} | Emotion: {emotion}
                    Notes: {notes}
                    {math_block}

                    REQUIRED OUTPUT FORMAT:
                    [SCORE] (Integer 0-100)
                    [TAGS] (Comma separated lists of errors, e.g., Stop Violation, Tilt, Poor R:R)
                    [TECH] (Technical reason for failure based on setup type)
                    [PSYCH] (Diagnosis of the reported emotion vs action)
                    [RISK] (Comment solely on R-Multiple and Stop Adherence)
                    [FIX] (One short imperative command. Max 10 words.)
                    """
                    ready_to_run = True

        # --- EXECUTION ENGINE ---
        if ready_to_run:
            with st.spinner("Processing Logic..."):
                try:
                    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
                    
                    if img_b64:
                        messages[0]["content"].append({
                            "type": "image_url", 
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                        })

                    # 3. API CONFIGURATION
                    payload = {
                        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                        "messages": messages,
                        "max_tokens": 600,
                        "temperature": 0.1,  # <--- CRITICAL: Removes creativity/randomness
                        "top_p": 0.85,
                        "frequency_penalty": 0.5 
                    }
                    
                    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                    res = requests.post(API_URL, headers=headers, json=payload)

                    if res.status_code == 200:
                        raw_content = res.json()["choices"][0]["message"]["content"]
                        
                        # 4. POST-PROCESSING (Emoji Killer)
                        report = parse_report(raw_content) 
                        save_analysis(current_user, report)
                        
                        # DISPLAY
                        score_color = "#ef4444" if report['score'] < 50 else "#10b981"
                        st.markdown(f"""
                        <div class="report-container">
                            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; padding-bottom:15px; margin-bottom:20px;">
                                <div style="font-size:1.2rem; font-weight:bold; color:#888;">AUDIT RESULT</div>
                                <div style="font-size:3.5rem; font-weight:900; color:{score_color};">{report['score']}</div>
                            </div>
                            <div class="analysis-card" style="border-left-color: #3b82f6;"><b>TECH:</b> {report['tech']}</div>
                            <div class="analysis-card" style="border-left-color: #f59e0b;"><b>PSYCH:</b> {report['psych']}</div>
                            <div class="analysis-card" style="border-left-color: #ef4444;"><b>RISK:</b> {report['risk']}</div>
                            <div class="analysis-card" style="border-left-color: #10b981; background:rgba(16, 185, 129, 0.1);"><b>FIX:</b> {report['fix']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"API Error: {res.status_code}")
                
                except Exception as e:
                    st.error(f"System Failure: {e}")

    # --- TAB 2: RULES ---
    with main_tab2:
        st.subheader("📜 The Law")
        rules_data = supabase.table("rules").select("*").eq("user_id", current_user).execute()
        if rules_data.data:
            for r in rules_data.data:
                c1, c2 = st.columns([5, 1])
                c1.markdown(f"⛔ **{r['rule_text']}**")
                if c2.button("🗑️", key=r['id']):
                    supabase.table("rules").delete().eq("id", r['id']).execute()
                    st.rerun()
        else:
            st.info("No rules yet. Analyze bad trades to generate them.")

    # --- TAB 3: PERFORMANCE ---
    with main_tab3:
        st.subheader("📈 Trader Evolution")
        hist = supabase.table("trades").select("*").eq("user_id", current_user).order("created_at", desc=True).execute()
        
        if hist.data:
            df = pd.DataFrame(hist.data)
            
            avg_score = df['score'].mean()
            all_tags = [tag for sublist in df['mistake_tags'] for tag in sublist]
            demon = pd.Series(all_tags).mode()[0] if all_tags else "None"
            
            k1, k2, k3 = st.columns(3)
            k1.markdown(f"<div class='stat-card'><div class='stat-val'>{int(avg_score)}</div><div class='stat-label'>Avg Score</div></div>", unsafe_allow_html=True)
            k2.markdown(f"<div class='stat-card'><div class='stat-val'>{len(df)}</div><div class='stat-label'>Trades Logged</div></div>", unsafe_allow_html=True)
            k3.markdown(f"<div class='stat-card' style='border-color:#ff4d4d'><div class='stat-val' style='color:#ff4d4d; font-size:1.5rem'>{demon}</div><div class='stat-label'>Main Weakness</div></div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.caption("Decision Quality Over Time")
            st.line_chart(df, x="created_at", y="score")
            
            st.markdown("### Recent Autopsies")
            for i, row in df.iterrows():
                with st.expander(f"{row['created_at'][:10]} - Score: {row['score']}"):
                    st.write(f"**Fix:** {row['fix_action']}")
        else:
            st.write("No data available. Upload your first loss to begin tracking.")
