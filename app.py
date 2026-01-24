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

# --- USER CREDENTIALS (HARDCODED) ---
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
# 3. HELPER FUNCTIONS (FIXED)
# ==========================================

def get_user_rules(user_id):
    """Fetch active rules for logged-in user"""
    response = supabase.table("rules").select("*").eq("user_id", user_id).execute()
    return [r['rule_text'] for r in response.data]

def save_analysis(user_id, data):
    """Save trade to DB and Auto-create Rule if score is low"""
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

def parse_report(text):
    """
    Robust Regex Parsing (Order Independent)
    """
    sections = {
        "score": 0, "tags": [], 
        "tech": "Data unavailable.", 
        "psych": "Data unavailable.", 
        "risk": "Data unavailable.", 
        "fix": "Data unavailable."
    }
    
    # 1. Extract Score
    score_match = re.search(r'\[SCORE\]\s*(\d+)', text)
    if score_match: sections['score'] = int(score_match.group(1))
    
    # 2. Extract Tags
    tags_match = re.search(r'\[TAGS\](.*?)(?=\[|$)', text, re.DOTALL)
    if tags_match:
        raw = tags_match.group(1).replace('[', '').replace(']', '').split(',')
        sections['tags'] = [t.strip() for t in raw if t.strip()]

    # 3. Extract Text Blocks (Robust Loop)
    for key, tag in [('tech', '[TECH]'), ('psych', '[PSYCH]'), ('risk', '[RISK]'), ('fix', '[FIX]')]:
        pattern = re.escape(tag) + r"(.*?)(?=\[TECH\]|\[PSYCH\]|\[RISK\]|\[FIX\]|\[SCORE\]|\[TAGS\]|$)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            clean_text = match.group(1).strip()
            if clean_text: sections[key] = clean_text
            
    return sections

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
        # Display Active Rules
        my_rules = get_user_rules(current_user)
        if my_rules:
            with st.expander("🚨 YOUR ACTIVE RULES (AI WILL CHECK THESE)", expanded=True):
                for rule in my_rules:
                    st.markdown(f"❌ **{rule}**")

        input_method = st.radio("Evidence Type:", ["📸 Chart Image", "📝 Text Report"], horizontal=True)
        
        prompt = ""
        img_b64 = None
        ready_to_run = False

        if input_method == "📸 Chart Image":
            uploaded_file = st.file_uploader("Upload Chart", type=["png", "jpg"], label_visibility="collapsed")
            if uploaded_file:
                st.image(uploaded_file, caption="Evidence Secured", use_container_width=True)
                if st.button("RUN VISION ANALYSIS", type="primary", use_container_width=True):
                    image = Image.open(uploaded_file)
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    
                    # --- UPGRADED PROMPT FOR VISION (1000% ACCURACY TARGET) ---
                    prompt = f"""
                    ROLE: Senior Quantitative Risk Analyst (Institutional Desk).
                    TASK: Forensic audit of the provided technical chart.
                    USER RULES TO ENFORCE: {my_rules}
                    
                    STRICT AUDIT PROTOCOL:
                    1. NO HALLUCINATIONS: Do NOT mention Volume, RSI, or MACD unless explicitly visible in the pixels. If not visible, ignore.
                    2. PRIMARY DIAGNOSIS: Identify the ONE fatal technical flaw (e.g., Buying into Supply, Counter-Trend execution, Micro-structure failure).
                    3. TONE: Clinical, Financial, Direct. NO emojis. NO conversational filler ("Here is your report").
                    
                    OUTPUT FORMAT (Must match exactly):
                    [SCORE] (0-100. Be punitive.)
                    [TAGS] (e.g. Counter-Trend, Supply Zone Rejection, Structure Break)
                    [TECH] (Detailed technical breakdown of the entry failure. Use concepts like Liquidity, Market Structure, and Equilibrium.)
                    [PSYCH] (Deduce mental state ONLY from price action. e.g. "Chasing green candles indicates FOMO".)
                    [RISK] (Assess stop placement relative to structural lows/highs.)
                    [FIX] (One imperative command. e.g. "No long entries below VWAP.")
                    """
                    ready_to_run = True

        else:
            with st.form("text_form"):
                c1, c2 = st.columns(2)
                with c1: ticker = st.text_input("Ticker", "$SPY")
                with c2: emotion = st.selectbox("Mental State", ["Calm", "Anxious", "Angry", "Greedy"])
                
                entry = st.text_input("Entry Price")
                exit_price = st.text_input("Exit Price")
                stop = st.text_input("Planned Stop")
                
                setup = st.text_area("The Setup", placeholder="Why did you enter?")
                exit_reason = st.text_area("The Exit", placeholder="Why did you exit?")
                
                if st.form_submit_button("RUN NARRATIVE ANALYSIS", type="primary", use_container_width=True):
                    # --- STEP 1: PRE-CALCULATE MATH TO PREVENT AI HALLUCINATION ---
                    # We do the math in Python so the AI can't mess it up.
                    math_context = "Risk Data: Insufficient inputs."
                    deviation_flag = False
                    
                    try:
                        ep = float(entry)
                        xp = float(exit_price)
                        sl = float(stop)
                        
                        risk_per_share = abs(ep - sl)
                        loss_per_share = abs(ep - xp)
                        
                        if risk_per_share > 0:
                            slippage_pct = ((loss_per_share - risk_per_share) / risk_per_share) * 100
                            r_result = -(loss_per_share / risk_per_share)
                            
                            if slippage_pct > 10: deviation_flag = True
                            
                            math_context = f"""
                            HARD DATA (DO NOT CALCULATE, USE THESE FACTS):
                            - Planned Risk/Share: {risk_per_share:.2f}
                            - Actual Loss/Share: {loss_per_share:.2f}
                            - R-Multiple: {r_result:.2f}R
                            - Risk Deviation: {slippage_pct:.2f}% (Positive means they violated their stop loss).
                            """
                    except:
                        pass

                    # --- STEP 2: UPGRADED PROMPT FOR TEXT (INSTITUTIONAL GRADE) ---
                    prompt = f"""
                    ACT AS: Chief Risk Officer (CRO) of a Hedge Fund.
                    CONTEXT: Forensic audit of a failed trade.
                    USER RULES: {my_rules}
                    
                    CASE DATA:
                    - Asset: {ticker}
                    - Self-Reported State: {emotion}
                    - Thesis: {setup}
                    - Exit Reason: {exit_reason}
                    {math_context}
                    
                    LOGIC GATES (MANDATORY):
                    1. ENTRY PRIORITY: Evaluate Entry Quality first. If the entry was "Impulsive" or "Chasing", the trade is a failure regardless of the exit.
                    2. PSYCHOLOGY LOCK: Only diagnose "Fear/Greed" if the user admitted it ({emotion}) OR if "Risk Deviation" is > 0%.
                    3. NO HALLUCINATIONS: Do not assume "Volume" or "Indicators" unless the user wrote them in the 'Setup'.
                    
                    OUTPUT FORMAT (Strictly follow tags):
                    [SCORE] (0-100 Integer. Penalize heavily for Risk Deviation.)
                    [TAGS] (e.g. Impulsive Entry, Risk Violation, Revenge Trading, Thesis Drift)
                    [TECH] (Analyze the setup validity. Was it a high-probability structure or a gamble? Be harsh.)
                    [PSYCH] (Behavioral profiling based on the 'Mental State' and 'Exit Reason'. Use terms like 'Confirmation Bias', 'Sunk Cost Fallacy'.)
                    [RISK] (Cite the Calculated Risk Metrics provided above. Did they adhere to the stop loss?)
                    [FIX] (A singular, bold, imperative rule. e.g. "**Hard stop at -1R. No exceptions.**")
                    """
                    ready_to_run = True

        # Execution Logic
        if ready_to_run:
            with st.spinner("Consulting the database of market failures..."):
                try:
                    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
                    if img_b64:
                        messages[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})

                    payload = {
                        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                        "messages": messages,
                        "max_tokens": 1000
                    }
                    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                    res = requests.post(API_URL, headers=headers, json=payload)

                    if res.status_code == 200:
                        content = res.json()["choices"][0]["message"]["content"]
                        report = parse_report(content)
                        save_analysis(current_user, report)
                        
                        score_color = "#ef4444" if report['score'] < 50 else "#10b981"
                        st.markdown(f"""
                        <div class="report-container">
                            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; padding-bottom:15px; margin-bottom:20px;">
                                <div style="font-size:1.2rem; font-weight:bold;">TRADE QUALITY SCORE</div>
                                <div style="font-size:3rem; font-weight:900; color:{score_color};">{report['score']}</div>
                            </div>
                            <div class="analysis-card" style="border-left-color: #3b82f6;"><b>📉 TECHNICALS:</b> {report['tech']}</div>
                            <div class="analysis-card" style="border-left-color: #f59e0b;"><b>🧠 PSYCHOLOGY:</b> {report['psych']}</div>
                            <div class="analysis-card" style="border-left-color: #ef4444;"><b>💸 RISK AUDIT:</b> {report['risk']}</div>
                            <div class="analysis-card" style="border-left-color: #10b981;"><b>💉 THE FIX:</b> {report['fix']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"Analysis Failed: {res.status_code}")
                except Exception as e:
                    st.error(f"Error: {e}")

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
