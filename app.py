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

# --- USER CREDENTIALS (SIMPLE AUTH) ---
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
        # Load Secrets
        HF_TOKEN = st.secrets["HF_TOKEN"]
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
        
        # Connect
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        API_URL = "https://router.huggingface.co/v1/chat/completions"
        
    except Exception as e:
        st.error(f"⚠️ Configuration Error: {e}")
        st.stop()

# ==========================================
# 2. CSS STYLING (DARK & CLEAN)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;800&display=swap');
    
    /* Global Styles */
    body, .stApp { background-color: #050505 !important; font-family: 'Space Grotesk', sans-serif !important; color: #e2e8f0; }
    
    /* Login Box */
    .login-box { max-width: 400px; margin: 100px auto; padding: 2rem; border: 1px solid #333; border-radius: 12px; background: #0d1117; }
    
    /* Dashboard Stats */
    .stat-card { background: #0d1117; border: 1px solid #30363d; padding: 15px; border-radius: 8px; text-align: center; }
    .stat-val { font-size: 2rem; font-weight: 800; color: white; }
    .stat-label { color: #888; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Report Card */
    .report-container { background: #0d1117; border: 1px solid #30363d; border-radius: 12px; padding: 2rem; margin-top: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
    .analysis-card { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 15px; margin-bottom: 10px; border-left: 4px solid #555; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid #333; }
    .stTabs [data-baseweb="tab"] { border: none; color: #888; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #ff4d4d !important; border-bottom: 2px solid #ff4d4d !important; }
    
    /* Buttons */
    button[kind="primary"] { background-color: #ff4d4d !important; border: none; color: white !important; font-weight: bold; letter-spacing: 1px; }
    button[kind="primary"]:hover { background-color: #ff3333 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNCTIONS (ROBUST LOGIC)
# ==========================================
def get_user_rules(user_id):
    """Fetch user's Constitution from Supabase."""
    try:
        response = supabase.table("rules").select("*").eq("user_id", user_id).execute()
        return [r['rule_text'] for r in response.data]
    except:
        return []

def clean_text(text):
    """Remove special characters but keep punctuation."""
    return re.sub(r'[^\w\s,.:;!?()\[\]\-\'\"%]', '', text).strip()

def parse_report(text):
    """
    Robust Parser V5:
    Uses multiple regex patterns to find the score even if the AI formatting drifts.
    """
    sections = { "score": 0, "tags": [], "tech": "N/A", "psych": "N/A", "risk": "N/A", "fix": "N/A" }
    text = clean_text(text)
    
    # --- SMARTER SCORE FINDER ---
    # 1. Look for standard [SCORE] 50
    score_match = re.search(r'\[SCORE\]\s*(\d+)', text)
    if not score_match:
        # 2. Fallback: Look for just [50] at the start of a line
        score_match = re.search(r'(?:^|\n)\[(\d+)\]', text)
        
    if score_match: 
        sections['score'] = int(score_match.group(1))

    # --- TAGS FINDER ---
    tags_match = re.search(r'\[TAGS\](.*?)(?=\[|$)', text, re.DOTALL)
    if tags_match:
        raw = tags_match.group(1).replace('[', '').replace(']', '').split(',')
        sections['tags'] = [t.strip().replace('"', '') for t in raw if t.strip()]
    
    # --- SECTION FINDER ---
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
    """Save result to Supabase and update Constitution if score is low."""
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
    
    # Auto-Update Constitution for failures
    if data.get('score', 0) < 50:
        clean_fix = data.get('fix', 'Follow the plan').replace('"', '')
        supabase.table("rules").insert({"user_id": user_id, "rule_text": clean_fix}).execute()
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
        st.caption("Institutional Grade Audit Terminal")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("UNLOCK DASHBOARD", type="primary", use_container_width=True):
                check_login(username, password)
        st.markdown("</div>", unsafe_allow_html=True)

else:
    # --- DASHBOARD ---
    current_user = st.session_state["user"]
    
    # Sidebar
    with st.sidebar:
        st.header(f"👤 {current_user}")
        if st.button("LOGOUT", use_container_width=True): logout()
        st.divider()
        st.caption("v5.2.0 | Stable Build")

    # Header
    st.markdown("""
    <div style="text-align:center; padding-top: 20px;">
        <div style="font-size: 1.8rem; font-weight: 800; color: white; letter-spacing: -1px;">STOCK<span style="color:#ff4d4d">POSTMORTEM</span>.AI</div>
        <div style="color: #666; font-size: 0.9rem; margin-bottom: 20px;">AUTOMATED RISK MANAGER</div>
    </div>
    """, unsafe_allow_html=True)

    main_tab1, main_tab2, main_tab3 = st.tabs(["🔍 NEW AUTOPSY", "⚖️ CONSTITUTION", "📈 PERFORMANCE"])

    # --- TAB 1: ANALYSIS ---
    with main_tab1:
        # Load user rules to context
        my_rules = get_user_rules(current_user)
        
        # Display Active Rules Warning
        if my_rules:
            with st.expander(f"🚨 ACTIVE RULES ({len(my_rules)}) - AI IS WATCHING", expanded=False):
                for rule in my_rules: st.markdown(f"❌ **{rule}**")

        c_mode = st.radio("Input Mode", ["Text Report", "Chart Vision"], horizontal=True, label_visibility="collapsed")
        
        prompt = ""
        img_b64 = None
        ready_to_run = False

        # --- MODE A: VISION ANALYSIS ---
        if c_mode == "Chart Vision":
            uploaded_file = st.file_uploader("Upload Chart (PNG/JPG)", type=["png", "jpg"])
            if uploaded_file:
                st.image(uploaded_file, caption="Analysis Target", use_container_width=True)
                if st.button("RUN VISION AUDIT", type="primary"):
                    # Process Image
                    image = Image.open(uploaded_file)
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    
                    # Vision Prompt
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

        # --- MODE B: TEXT ANALYSIS (THE ROBUST LOGIC) ---
        else:
            with st.form("text_form"):
                # ROW 1: Context
                c1, c2, c3, c4 = st.columns(4)
                with c1: ticker = st.text_input("Ticker", "SPY")
                with c2: position = st.selectbox("Position", ["Long", "Short"])
                with c3: timeframe = st.selectbox("Timeframe", ["Scalp (1m-5m)", "Day (15m-1h)", "Swing (4h+)"])
                with c4: setup_type = st.selectbox("Setup", ["Trend Follow", "Reversal", "Breakout", "Impulse"])

                # ROW 2: Math
                c1, c2, c3 = st.columns(3)
                with c1: entry = st.number_input("Entry Price", value=0.0, format="%.2f")
                with c2: exit_price = st.number_input("Exit Price", value=0.0, format="%.2f")
                with c3: stop = st.number_input("Stop Loss", value=0.0, format="%.2f")

                # ROW 3: Psychology
                emotion = st.selectbox("Mental State", ["Neutral", "FOMO", "Revenge", "Fear", "Tilt", "Overconfidence"])
                notes = st.text_area("Context Notes", placeholder="e.g. I moved my stop because I thought it would bounce...")

                if st.form_submit_button("GENERATE AUDIT", type="primary", use_container_width=True):
                    try:
                        # 1. PYTHON CALCULATION LAYER (THE TRUTH)
                        risk = abs(entry - stop)
                        loss = abs(entry - exit_price)
                        
                        if risk > 0:
                            r_multiple = (exit_price - entry) / (entry - stop) if position == "Long" else (entry - exit_price) / (stop - entry)
                        else:
                            r_multiple = 0
                        
                        # Stop Violation Logic
                        stop_violation = False
                        if position == "Long" and exit_price < stop: stop_violation = True
                        elif position == "Short" and exit_price > stop: stop_violation = True
                        
                        math_block = f"""
                        [CALCULATED_METRICS]
                        Position: {position}
                        Risk_Per_Share: {risk:.2f}
                        R_Multiple: {r_multiple:.2f}R
                        Stop_Violation: {stop_violation}
                        """
                    except:
                        math_block = "[CALCULATED_METRICS] Error in calculation."

                    # 2. THE GOLDEN PROMPT (With Examples)
                    prompt = f"""
                    SYSTEM: You are a Wall Street Risk Manager.
                    Your job is to audit this trade. Be harsh, clinical, and mathematical.
                    
                    USER RULES TO ENFORCE: {my_rules}
                    
                    Here are 3 Examples of how to grade (MIMIC THIS EXACTLY):
                    
                    Example 1 (Bad Risk):
                    Input: [METRICS] Stop_Violation: True
                    Output:
                    [SCORE] 10
                    [TAGS] Risk Failure, Stop Violation
                    [TECH] Entry was fine, but execution failed.
                    [PSYCH] Total loss of discipline.
                    [RISK] You held a loser. This is gambling.
                    [FIX] Never hold a loser past your stop.
                    
                    Example 2 (Lucky Idiot):
                    Input: [METRICS] Stop_Violation: False | Notes: "I removed stop and got lucky."
                    Output:
                    [SCORE] 20
                    [TAGS] Bad Process, Gambling
                    [TECH] Setup was random.
                    [PSYCH] Dangerous overconfidence.
                    [RISK] Result was profit, but process was ruin.
                    [FIX] Do not remove stops; luck is not a strategy.
                    
                    Example 3 (Good Loss):
                    Input: [METRICS] Stop_Violation: False | Notes: "Exited as planned."
                    Output:
                    [SCORE] 85
                    [TAGS] Discipline, System Followed
                    [TECH] Setup invalidated correctly.
                    [PSYCH] Calm and professional.
                    [RISK] 1R loss accepted. Good job.
                    [FIX] Good execution. No fix needed.
                    
                    ---
                    
                    CURRENT TASK:
                    Input:
                    Ticker: {ticker} | Setup: {setup_type} | Emotion: {emotion}
                    Notes: {notes}
                    {math_block}
                    
                    OUTPUT FORMAT:
                    [SCORE] (Integer)
                    [TAGS] (List)
                    [TECH] (Sentence)
                    [PSYCH] (Sentence)
                    [RISK] (Sentence)
                    [FIX] (Imperative command)
                    """
                    ready_to_run = True

        # --- EXECUTION ENGINE ---
        if ready_to_run:
            with st.spinner("Analyzing Trade Data..."):
                try:
                    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
                    if img_b64:
                        messages[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})

                    payload = {
                        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                        "messages": messages,
                        "max_tokens": 500,
                        "temperature": 0.1 # Low temp for strict logic
                    }
                    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                    
                    res = requests.post(API_URL, headers=headers, json=payload, timeout=20)

                    if res.status_code == 200:
                        raw_content = res.json()["choices"][0]["message"]["content"]
                        
                        # Parse
                        report = parse_report(raw_content)
                        
                        # Save
                        save_analysis(current_user, report)
                        
                        # Render Report
                        score_color = "#ef4444" if report['score'] < 50 else "#10b981"
                        if report['score'] >= 50 and report['score'] < 75: score_color = "#f59e0b" # Orange for average

                        st.markdown(f"""
                        <div class="report-container">
                            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; padding-bottom:15px; margin-bottom:20px;">
                                <div>
                                    <div style="font-size:1rem; color:#888;">AUDIT SCORE</div>
                                    <div style="font-size:3.5rem; font-weight:900; line-height:1; color:{score_color};">{report['score']}</div>
                                </div>
                                <div style="text-align:right;">
                                    <div style="font-size:0.9rem; color:#888;">TAGS</div>
                                    <div style="color:#fff; max-width:200px;">{", ".join(report['tags'][:3])}</div>
                                </div>
                            </div>
                            
                            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                                <div class="analysis-card" style="border-left-color: #3b82f6;">
                                    <div style="color:#3b82f6; font-size:0.8rem; font-weight:bold;">TECHNICAL</div>
                                    {report['tech']}
                                </div>
                                <div class="analysis-card" style="border-left-color: #f59e0b;">
                                    <div style="color:#f59e0b; font-size:0.8rem; font-weight:bold;">PSYCHOLOGY</div>
                                    {report['psych']}
                                </div>
                            </div>
                            
                            <div class="analysis-card" style="border-left-color: #ef4444; margin-top:10px;">
                                <div style="color:#ef4444; font-size:0.8rem; font-weight:bold;">RISK ANALYSIS</div>
                                {report['risk']}
                            </div>
                            
                            <div class="analysis-card" style="border-left-color: #10b981; background:rgba(16, 185, 129, 0.05); margin-top:10px;">
                                <div style="color:#10b981; font-size:0.8rem; font-weight:bold;">CORRECTIVE ACTION</div>
                                <div style="font-size:1.1rem; font-weight:600;">{report['fix']}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Raw Output (Hidden by default)
                        with st.expander("View Raw API Response"):
                            st.code(raw_content)
                            
                    else:
                        st.error(f"API Error ({res.status_code}): {res.text}")
                except Exception as e:
                    st.error(f"System Failure: {e}")

    # --- TAB 2: CONSTITUTION (UNCHANGED) ---
    with main_tab2:
        st.subheader("📜 The Constitution")
        st.caption("Rules written in blood (losses). Break them, and the AI will fail you.")
        rules_data = supabase.table("rules").select("*").eq("user_id", current_user).execute()
        if rules_data.data:
            for r in rules_data.data:
                c1, c2 = st.columns([5, 1])
                c1.markdown(f"⛔ **{r['rule_text']}**")
                if c2.button("🗑️", key=r['id']):
                    supabase.table("rules").delete().eq("id", r['id']).execute()
                    st.rerun()
        else:
            st.info("No rules yet. Fail a trade to generate one.")

    # --- TAB 3: PERFORMANCE (UNCHANGED) ---
    with main_tab3:
        st.subheader("📈 Performance Metrics")
        hist = supabase.table("trades").select("*").eq("user_id", current_user).order("created_at", desc=True).execute()
        if hist.data:
            df = pd.DataFrame(hist.data)
            
            # Key Metrics
            avg_score = df['score'].mean()
            # Flatten tags list
            all_tags = []
            for tags in df['mistake_tags']:
                if isinstance(tags, list): all_tags.extend(tags)
                elif isinstance(tags, str): all_tags.append(tags) # Handle legacy string data
                
            demon = pd.Series(all_tags).mode()[0] if all_tags else "Clean"
            
            k1, k2, k3 = st.columns(3)
            k1.markdown(f"<div class='stat-card'><div class='stat-val'>{int(avg_score)}</div><div class='stat-label'>Avg Score</div></div>", unsafe_allow_html=True)
            k2.markdown(f"<div class='stat-card'><div class='stat-val'>{len(df)}</div><div class='stat-label'>Trades Logged</div></div>", unsafe_allow_html=True)
            k3.markdown(f"<div class='stat-card' style='border-color:#ff4d4d'><div class='stat-val' style='color:#ff4d4d; font-size:1.5rem'>{demon}</div><div class='stat-label'>Main Weakness</div></div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Chart
            st.line_chart(df, x="created_at", y="score")
            
            # History Table
            st.markdown("### Trade History")
            for i, row in df.iterrows():
                with st.expander(f"{row['created_at'][:10]} | Score: {row['score']} | {row['fix_action']}"):
                    st.write(f"**Analysis:** {row['technical_analysis']}")
        else:
            st.write("No trade data available yet.")
