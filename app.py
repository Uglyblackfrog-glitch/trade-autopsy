import streamlit as st
import google.generativeai as genai
import requests
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
# 1. DATABASE & API SETUP (HYBRID ENGINE)
# ==========================================
if st.session_state["authenticated"]:
    try:
        # Load Secrets
        GOOGLE_KEY = st.secrets["GOOGLE_API_KEY"] # For Vision
        GROQ_KEY = st.secrets["GROQ_API_KEY"]     # For Logic
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
        
        # Connect Clients
        genai.configure(api_key=GOOGLE_KEY) # The Eye
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) # The Memory
        
    except Exception as e:
        st.error(f"⚠️ Configuration Error: {e}")
        st.warning("Make sure you added GOOGLE_API_KEY and GROQ_API_KEY to secrets.toml")
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
    .stat-label { color: #888; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }
    .report-container { background: #0d1117; border: 1px solid #30363d; border-radius: 12px; padding: 2rem; margin-top: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
    .analysis-card { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 15px; margin-bottom: 10px; border-left: 4px solid #555; }
    button[kind="primary"] { background-color: #ff4d4d !important; border: none; color: white !important; font-weight: bold; letter-spacing: 1px; }
    button[kind="primary"]:hover { background-color: #ff3333 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def get_user_rules(user_id):
    try:
        response = supabase.table("rules").select("*").eq("user_id", user_id).execute()
        return [r['rule_text'] for r in response.data]
    except: return []

def clean_text(text):
    return re.sub(r'[^\w\s,.:;!?()\[\]\-\'\"%]', '', text).strip()

def parse_report(text):
    """Robust V6 Parser for Hybrid Output"""
    sections = { "score": 0, "tags": [], "tech": "N/A", "psych": "N/A", "risk": "N/A", "fix": "N/A" }
    text = clean_text(text)
    
    # Smarter Score Finder
    score_match = re.search(r'\[SCORE\]\s*(\d+)', text)
    if not score_match: score_match = re.search(r'(?:^|\n)\[(\d+)\]', text)
    if score_match: sections['score'] = int(score_match.group(1))

    # Tags Finder
    tags_match = re.search(r'\[TAGS\](.*?)(?=\[|$)', text, re.DOTALL)
    if tags_match:
        raw = tags_match.group(1).replace('[', '').replace(']', '').split(',')
        sections['tags'] = [t.strip().replace('"', '') for t in raw if t.strip()]
    
    # Section Finder
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
        clean_fix = data.get('fix', 'Follow process').replace('"', '')
        supabase.table("rules").insert({"user_id": user_id, "rule_text": clean_fix}).execute()
        st.toast("📉 New Rule added to Constitution.")

# ==========================================
# 4. MAIN APP LOGIC
# ==========================================
if not st.session_state["authenticated"]:
    # LOGIN SCREEN
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><br><br><div class='login-box'>", unsafe_allow_html=True)
        st.title("🩸 StockPostmortem")
        st.caption("Hybrid Engine: Gemini + Groq")
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
        st.divider()
        st.caption("System Status:")
        st.caption("🟢 Vision: Google Gemini 2.0")
        st.caption("🟢 Logic: Groq Llama 3.3")

    st.markdown("""
    <div style="text-align:center; padding-top: 20px;">
        <div style="font-size: 1.8rem; font-weight: 800; color: white;">STOCK<span style="color:#ff4d4d">POSTMORTEM</span>.AI</div>
        <div style="color: #666; font-size: 0.9rem; margin-bottom: 20px;">HYBRID RISK AUDITOR</div>
    </div>
    """, unsafe_allow_html=True)

    main_tab1, main_tab2, main_tab3 = st.tabs(["🔍 NEW AUTOPSY", "⚖️ CONSTITUTION", "📈 PERFORMANCE"])

    # --- TAB 1: HYBRID ANALYSIS ---
    with main_tab1:
        my_rules = get_user_rules(current_user)
        if my_rules:
            with st.expander(f"🚨 ACTIVE RULES ({len(my_rules)})"):
                for rule in my_rules: st.markdown(f"❌ **{rule}**")

        c_mode = st.radio("Mode", ["Text Report (Groq Logic)", "Chart Vision (Gemini Eye)"], horizontal=True, label_visibility="collapsed")
        
        prompt = ""
        img_data = None
        ready_to_run = False
        engine_used = ""

        # --- MODE A: VISION (GEMINI 2.0 FLASH) ---
        if "Chart Vision" in c_mode:
            uploaded_file = st.file_uploader("Upload Chart", type=["png", "jpg"])
            if uploaded_file:
                st.image(uploaded_file, caption="Target", width=400)
                if st.button("RUN VISION AUDIT", type="primary"):
                    img_data = Image.open(uploaded_file)
                    engine_used = "Gemini 2.0 Flash"
                    
                    prompt = f"""
                    SYSTEM: You are a Trading Risk Manager. Analyze this chart image.
                    CONTEXT: User Rules: {my_rules}
                    
                    OUTPUT FORMAT:
                    [SCORE] 0-100
                    [TAGS] Tag1, Tag2
                    [TECH] Technical critique.
                    [PSYCH] Implied emotion based on entry/exit.
                    [RISK] Visual stop loss placement analysis.
                    [FIX] One imperative correction rule.
                    """
                    ready_to_run = True

        # --- MODE B: TEXT LOGIC (GROQ / LLAMA 3.3) ---
        else:
            with st.form("text_form"):
                c1, c2, c3, c4 = st.columns(4)
                with c1: ticker = st.text_input("Ticker", "SPY")
                with c2: position = st.selectbox("Position", ["Long", "Short"])
                with c3: timeframe = st.selectbox("Timeframe", ["Scalp", "Day", "Swing"])
                with c4: setup_type = st.selectbox("Setup", ["Trend", "Reversal", "Breakout"])

                c1, c2, c3 = st.columns(3)
                with c1: entry = st.number_input("Entry", 0.0)
                with c2: exit_price = st.number_input("Exit", 0.0)
                with c3: stop = st.number_input("Stop Loss", 0.0)

                emotion = st.selectbox("Mental State", ["Neutral", "FOMO", "Revenge", "Fear", "Overconfidence"])
                notes = st.text_area("Notes", placeholder="I removed my stop because...")

                if st.form_submit_button("GENERATE AUDIT", type="primary", use_container_width=True):
                    engine_used = "Groq Llama 3.3"
                    
                    # 1. PYTHON MATH LAYER
                    risk = abs(entry - stop)
                    stop_violation = False
                    
                    # Logic: Did they respect the stop?
                    if position == "Long" and exit_price < stop: stop_violation = True
                    if position == "Short" and exit_price > stop: stop_violation = True

                    if risk > 0:
                        r_multiple = (exit_price - entry) / risk if position == "Long" else (entry - exit_price) / risk
                    else:
                        r_multiple = 0

                    math_block = f"""
                    [METRICS]
                    Position: {position} | Risk: {risk:.2f} | R_Multiple: {r_multiple:.2f}R
                    Stop_Violation: {stop_violation} (TRUE = Critical Fail)
                    """

                    # 2. THE GOLDEN PROMPT (Logic Traps)
                    prompt = f"""
                    SYSTEM: You are a Wall Street Risk Manager.
                    USER RULES: {my_rules}
                    
                    LOGIC GATES (ENFORCE THESE):
                    1. IF Stop_Violation is True -> MAX SCORE 30. Tag: Risk Failure.
                    2. IF Notes say "removed stop" or "luck" -> MAX SCORE 20. Tag: Gambling.
                    3. IF Math is clean and rules followed -> PASS (Score > 80).
                    
                    INPUT:
                    {ticker} | {emotion} | {notes}
                    {math_block}
                    
                    OUTPUT FORMAT:
                    [SCORE] (Integer)
                    [TAGS] (List)
                    [TECH] (Sentence)
                    [PSYCH] (Sentence)
                    [RISK] (Sentence)
                    [FIX] (Imperative)
                    """
                    ready_to_run = True

        # --- EXECUTION ---
        if ready_to_run:
            with st.spinner(f"Analyzing via {engine_used}..."):
                try:
                    raw_text = ""
                    
                    # ROUTE 1: VISION (GOOGLE)
                    if "Gemini" in engine_used:
                        model = genai.GenerativeModel('gemini-2.0-flash')
                        response = model.generate_content([prompt, img_data])
                        raw_text = response.text
                        
                    # ROUTE 2: LOGIC (GROQ)
                    elif "Groq" in engine_used:
                        headers = {
                            "Authorization": f"Bearer {GROQ_KEY}",
                            "Content-Type": "application/json"
                        }
                        payload = {
                            "model": "llama-3.3-70b-versatile",
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 800,
                            "temperature": 0.1
                        }
                        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                        if res.status_code == 200:
                            raw_text = res.json()["choices"][0]["message"]["content"]
                        else:
                            st.error(f"Groq Error: {res.text}")
                            st.stop()

                    # PARSE & RENDER
                    report = parse_report(raw_text)
                    save_analysis(current_user, report)
                    
                    score_color = "#ef4444" if report['score'] < 50 else "#10b981"
                    if 50 <= report['score'] < 75: score_color = "#f59e0b"

                    st.markdown(f"""
                    <div class="report-container">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <div style="color:#888;">AUDIT SCORE ({engine_used})</div>
                                <div style="font-size:3.5rem; font-weight:900; color:{score_color};">{report['score']}</div>
                            </div>
                            <div style="text-align:right;">
                                <div style="color:#fff;">{", ".join(report['tags'])}</div>
                            </div>
                        </div>
                        <hr style="border-color:#333;">
                        <div class="analysis-card" style="border-left-color: #3b82f6;"><b>TECH:</b> {report['tech']}</div>
                        <div class="analysis-card" style="border-left-color: #f59e0b;"><b>PSYCH:</b> {report['psych']}</div>
                        <div class="analysis-card" style="border-left-color: #ef4444;"><b>RISK:</b> {report['risk']}</div>
                        <div class="analysis-card" style="border-left-color: #10b981; background:rgba(16, 185, 129, 0.05);"><b>FIX:</b> {report['fix']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"System Failure: {e}")

    # --- TAB 2 & 3 (STANDARD) ---
    with main_tab2:
        st.subheader("📜 Constitution")
        rules = supabase.table("rules").select("*").eq("user_id", current_user).execute().data
        for r in rules:
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"⛔ {r['rule_text']}")
            if c2.button("🗑️", key=r['id']):
                supabase.table("rules").delete().eq("id", r['id']).execute(); st.rerun()

    with main_tab3:
        st.subheader("📈 Performance")
        hist = supabase.table("trades").select("*").eq("user_id", current_user).order("created_at", desc=True).execute().data
        if hist:
            df = pd.DataFrame(hist)
            st.line_chart(df, x="created_at", y="score")
            st.dataframe(df[['created_at', 'score', 'mistake_tags', 'fix_action']])
        else:
            st.info("No data yet.")
