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
st.set_page_config(page_title="StockPostmortem.ai", page_icon="🩸", layout="wide")

# --- USER CREDENTIALS ---
USERS = {
    "trader1": "profit2026",
    "demo_user": "12345",
    "admin": "adminpass"
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
        HF_TOKEN = st.secrets["HF_TOKEN"]
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        API_URL = "https://router.huggingface.co/v1/chat/completions"
    except Exception as e:
        st.error(f"⚠️ Configuration Error: {e}")
        st.stop()

# ==========================================
# 2. CSS STYLING
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;800&display=swap');
    body, .stApp { background-color: #050505 !important; font-family: 'Space Grotesk', sans-serif !important; color: #e2e8f0; }
    .login-box { max-width: 400px; margin: 100px auto; padding: 2rem; border: 1px solid #333; border-radius: 12px; background: #0d1117; }
    .stat-card { background: #0d1117; border: 1px solid #30363d; padding: 15px; border-radius: 8px; text-align: center; }
    .stat-val { font-size: 2rem; font-weight: 800; color: white; }
    .stat-label { color: #888; font-size: 0.8rem; text-transform: uppercase; }
    .report-container { background: #0d1117; border: 1px solid #30363d; border-radius: 12px; padding: 2rem; margin-top: 20px; }
    .analysis-card { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 15px; margin-bottom: 10px; border-left: 4px solid #555; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid #333; }
    .stTabs [data-baseweb="tab"] { border: none; color: #888; }
    .stTabs [aria-selected="true"] { color: #ff4d4d !important; border-bottom: 2px solid #ff4d4d !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def get_user_rules(user_id):
    try:
        response = supabase.table("rules").select("*").eq("user_id", user_id).execute()
        return [r['rule_text'] for r in response.data]
    except:
        return []

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

def save_analysis(user_id, data):
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
    if data.get('score', 0) < 50:
        supabase.table("rules").insert({"user_id": user_id, "rule_text": data.get('fix')}).execute()
        st.toast("📉 New Rule added to Constitution.")

# ==========================================
# 4. MAIN APP LOGIC
# ==========================================
if not st.session_state["authenticated"]:
    # LOGIN SCREEN
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.title("🩸 StockPostmortem")
        st.caption("Secure Access Terminal")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("UNLOCK DASHBOARD", type="primary", use_container_width=True):
                check_login(username, password)
        st.markdown("</div>", unsafe_allow_html=True)

else:
    # DASHBOARD
    current_user = st.session_state["user"]
    with st.sidebar:
        st.header(f"👤 {current_user}")
        if st.button("LOGOUT", use_container_width=True): logout()

    st.markdown("""
    <div style="text-align:center; padding-top: 20px;">
        <div style="font-size: 1.5rem; font-weight: 800; color: white;">STOCK<span style="color:#ff4d4d">POSTMORTEM</span>.AI</div>
    </div>
    """, unsafe_allow_html=True)

    main_tab1, main_tab2, main_tab3 = st.tabs(["🔍 NEW AUTOPSY", "⚖️ CONSTITUTION", "📈 PERFORMANCE"])

    # --- TAB 1: ANALYSIS ---
    with main_tab1:
        my_rules = get_user_rules(current_user)
        if my_rules:
            with st.expander("🚨 ACTIVE RULES (AI IS WATCHING)", expanded=False):
                for rule in my_rules: st.markdown(f"❌ **{rule}**")

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
                    prompt = f"""
                    SYSTEM: You are an Algorithmic Trading Auditor. 
                    TASK: Analyze the image pixel-by-pixel.
                    CONTEXT: User Rules: {my_rules}
                    
                    STRICT CONSTRAINTS:
                    1. Output is BINARY and FACTUAL.
                    2. IGNORE indicators not clearly visible.
                    3. NO conversational filler.
                    
                    OUTPUT FORMAT:
                    [SCORE] 0-100
                    [TAGS] Tag1, Tag2
                    [TECH] Specific candle/structure failure identified.
                    [PSYCH] Implied intent based on entry location.
                    [RISK] Visual stop loss placement analysis.
                    [FIX] One imperative correction rule.
                    """
                    ready_to_run = True

        # --- MODE B: TEXT ANALYSIS (UPDATED) ---
        else:
            with st.form("text_form"):
                # ROW 1: Context (Added Position & Timeframe)
                c1, c2, c3, c4 = st.columns(4)
                with c1: ticker = st.text_input("Ticker", "SPY")
                with c2: position = st.selectbox("Position", ["Long", "Short"]) # NEW FEATURE
                with c3: timeframe = st.selectbox("Timeframe", ["Scalp (1m-5m)", "Day (15m-1h)", "Swing (4h+)"]) # NEW FEATURE
                with c4: setup_type = st.selectbox("Setup", ["Trend Follow", "Reversal", "Breakout"])

                # ROW 2: Math
                c1, c2, c3 = st.columns(3)
                with c1: entry = st.number_input("Entry", value=0.0)
                with c2: exit_price = st.number_input("Exit", value=0.0)
                with c3: stop = st.number_input("Stop Loss", value=0.0)

                # ROW 3: Psychology
                emotion = st.selectbox("Mental State", ["Neutral", "FOMO", "Revenge", "Fear", "Tilt"])
                notes = st.text_area("Context Notes", placeholder="e.g. Broke VWAP, volume was low...")

                if st.form_submit_button("AUDIT TRADE", type="primary", use_container_width=True):
                    try:
                        # 1. PYTHON CALCULATION LAYER
                        risk = abs(entry - stop)
                        loss = abs(entry - exit_price)
                        r_multiple = -1 * (loss / risk) if risk > 0 else 0
                        
                        stop_violation = False
                        # Logic: Did they respect the stop? (Accounts for Long vs Short)
                        if position == "Long":
                            if exit_price < stop: stop_violation = True # Exited below stop
                        else: # Short
                            if exit_price > stop: stop_violation = True # Exited above stop
                            
                        math_block = f"""
                        [CALCULATED_METRICS]
                        Position_Type: {position}
                        Timeframe_Context: {timeframe}
                        Risk_Per_Share: {risk:.2f}
                        Actual_Loss: {loss:.2f}
                        R_Multiple: {r_multiple:.2f}R
                        Stop_Violation: {stop_violation} (TRUE = Critical Discipline Failure)
                        """
                    except:
                        math_block = "[CALCULATED_METRICS] Insufficient numeric data."

                    # 2. SYSTEM PROMPT (Updated with new inputs)
                    prompt = f"""
                    SYSTEM INSTRUCTION:
                    You are a Deterministic Trade Audit Engine. Analyze the inputs below.
                    
                    RULES:
                    1. TONE: Clinical, Harsh, Professional. NO EMOJIS.
                    2. DATA PRIORITY: Use [CALCULATED_METRICS]. Do not recalculate.
                    3. SCORING: If Stop_Violation is True, Max Score is 30.
                    4. USER RULES: Check against: {my_rules}.

                    INPUT DATA:
                    Ticker: {ticker} | Setup: {setup_type} | Emotion: {emotion}
                    Context: {notes}
                    {math_block}

                    REQUIRED OUTPUT FORMAT:
                    [SCORE] (Integer 0-100)
                    [TAGS] (Comma separated errors)
                    [TECH] (Technical critique based on {timeframe} timeframe)
                    [PSYCH] (Diagnosis of {emotion} state)
                    [RISK] (Comment on {r_multiple:.2f}R result)
                    [FIX] (One imperative command. Max 10 words.)
                    """
                    ready_to_run = True

        if ready_to_run:
            with st.spinner("Processing Logic..."):
                try:
                    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
                    if img_b64:
                        messages[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})

                    payload = {
                        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                        "messages": messages,
                        "max_tokens": 600,
                        "temperature": 0.1
                    }
                    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                    res = requests.post(API_URL, headers=headers, json=payload)

                    if res.status_code == 200:
                        raw_content = res.json()["choices"][0]["message"]["content"]
                        report = parse_report(raw_content)
                        save_analysis(current_user, report)
                        
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

    # --- TAB 2 & 3 (UNCHANGED) ---
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
            st.info("No rules yet.")

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
            st.line_chart(df, x="created_at", y="score")
            
            st.markdown("### Recent Autopsies")
            for i, row in df.iterrows():
                with st.expander(f"{row['created_at'][:10]} - Score: {row['score']}"):
                    st.write(f"**Fix:** {row['fix_action']}")
        else:
            st.write("No data available.")
