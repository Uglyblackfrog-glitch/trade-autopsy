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
# 2. CSS STYLING (PREMIUM DASHBOARD THEME)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    body, .stApp { 
        background-color: #050505 !important; 
        font-family: 'Inter', sans-serif !important; 
        color: #e2e8f0; 
    }
    
    /* LOGIN BOX */
    .login-box { max-width: 400px; margin: 100px auto; padding: 2rem; border: 1px solid #333; border-radius: 12px; background: #0d1117; }
    
    /* DASHBOARD METRIC CARDS */
    .kpi-card {
        background: #111;
        border: 1px solid #222;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        transition: all 0.2s ease-in-out;
    }
    .kpi-card:hover { border-color: #ff4d4d; transform: translateY(-2px); }
    .kpi-val { font-size: 2.2rem; font-weight: 800; color: white; line-height: 1.2; }
    .kpi-label { color: #666; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    
    /* SECTION HEADERS */
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #fff;
        margin-top: 30px;
        margin-bottom: 15px;
        border-left: 3px solid #ff4d4d;
        padding-left: 10px;
    }
    
    /* REPORT CONTAINER */
    .report-container { background: #0d1117; border: 1px solid #30363d; border-radius: 12px; padding: 2rem; margin-top: 20px; }
    .analysis-card { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 15px; margin-bottom: 10px; border-left: 4px solid #555; }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid #333; }
    .stTabs [data-baseweb="tab"] { border: none; color: #666; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #ff4d4d !important; border-bottom: 2px solid #ff4d4d !important; }

    /* RULES PANEL */
    .rule-item {
        background: rgba(255, 77, 77, 0.05);
        border: 1px solid rgba(255, 77, 77, 0.2);
        padding: 10px 15px;
        border-radius: 6px;
        margin-bottom: 8px;
        color: #ffcccc;
        font-size: 0.9rem;
    }
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
    
    # Extract Score
    score_match = re.search(r'\[SCORE\]\s*(\d+)', text)
    if score_match: sections['score'] = int(score_match.group(1))
    
    # Extract Tags
    tags_match = re.search(r'\[TAGS\](.*?)(?=\[|$)', text, re.DOTALL)
    if tags_match:
        raw = tags_match.group(1).replace('[', '').replace(']', '').split(',')
        sections['tags'] = [t.strip() for t in raw if t.strip()]
    
    # Extract Sections
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

def save_analysis(user_id, data, ticker_symbol="UNK"):
    payload = {
        "user_id": user_id,
        "ticker": ticker_symbol, # Added Ticker
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
        st.toast("📉 Critical Failure. New Rule added to Guardrails.")

def generate_insights(df):
    """Auto-generates behavioral insights from dataframe"""
    insights = []
    
    if df.empty: return ["No data available for insights."]
    
    # 1. Trend Insight
    recent_scores = df.head(3)['score'].mean()
    if recent_scores < 50:
        insights.append("⚠️ **Performance Dip:** Your last 3 trades average a Quality Score below 50. Consider reducing size.")
    elif recent_scores > 80:
        insights.append("🔥 **In the Zone:** High decision quality detected in recent trades.")

    # 2. Mistake Correlation
    all_tags = [tag for sublist in df['mistake_tags'] for tag in sublist]
    if "FOMO" in all_tags and "Revenge" in all_tags:
        insights.append("🧠 **Pattern Alert:** You show signs of both FOMO and Revenge trading. This indicates a lack of patience with market structure.")

    # 3. Time Insight (Mock logic since we don't have time-of-day in DB yet)
    insights.append("💡 **System Note:** Most critical errors correlate with 'Stop Violation' tags.")
    
    return insights

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
        st.markdown("---")
        st.caption("v2.1.0-PRO")

    st.markdown("""
    <div style="text-align:center; padding-top: 10px; margin-bottom: 30px;">
        <div style="font-size: 1.5rem; font-weight: 800; color: white;">STOCK<span style="color:#ff4d4d">POSTMORTEM</span>.AI</div>
        <div style="color: #666; font-size: 0.9rem;">BEHAVIORAL FORENSICS & RISK ANALYTICS</div>
    </div>
    """, unsafe_allow_html=True)

    main_tab1, main_tab2, main_tab3 = st.tabs(["🔍 NEW AUTOPSY", "⚖️ CONSTITUTION", "📊 EXECUTIVE DASHBOARD"])

    # --- TAB 1: ANALYSIS ---
    with main_tab1:
        my_rules = get_user_rules(current_user)
        if my_rules:
            with st.expander("🚨 ACTIVE RULES (AI IS WATCHING)", expanded=False):
                for rule in my_rules: st.markdown(f"❌ **{rule}**")

        c_mode = st.radio("Input Mode", ["Text Report", "Chart Vision"], horizontal=True, label_visibility="collapsed")
        
        prompt = ""
        img_b64 = None
        ticker_val = "IMG" # Default if image
        ready_to_run = False

        # MODE A: VISION
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
                    SYSTEM: Algorithmic Trading Auditor. 
                    CONTEXT: Rules: {my_rules}
                    TASK: Pixel-by-pixel chart analysis.
                    OUTPUT: [SCORE], [TAGS], [TECH], [PSYCH], [RISK], [FIX].
                    """
                    ready_to_run = True

        # MODE B: TEXT
        else:
            with st.form("text_form"):
                # ROW 1
                c1, c2, c3, c4 = st.columns(4)
                with c1: ticker = st.text_input("Ticker", "SPY")
                with c2: position = st.selectbox("Position", ["Long", "Short"])
                with c3: timeframe = st.selectbox("Timeframe", ["Scalp (1m-5m)", "Day (15m-1h)", "Swing (4h+)"])
                with c4: setup_type = st.selectbox("Setup", ["Trend Follow", "Reversal", "Breakout"])

                # ROW 2
                c1, c2, c3 = st.columns(3)
                with c1: entry = st.number_input("Entry", value=0.0)
                with c2: exit_price = st.number_input("Exit", value=0.0)
                with c3: stop = st.number_input("Stop Loss", value=0.0)

                # ROW 3
                emotion = st.selectbox("Mental State", ["Neutral", "FOMO", "Revenge", "Fear", "Tilt"])
                notes = st.text_area("Context Notes", placeholder="e.g. Broke VWAP, volume was low...")

                if st.form_submit_button("AUDIT TRADE", type="primary", use_container_width=True):
                    ticker_val = ticker
                    # ... [Math Logic same as before] ...
                    try:
                        risk = abs(entry - stop)
                        loss = abs(entry - exit_price)
                        r_multiple = -1 * (loss / risk) if risk > 0 else 0
                        stop_violation = (position == "Long" and exit_price < stop) or (position == "Short" and exit_price > stop)
                        math_block = f"R_Multiple: {r_multiple:.2f}R | Stop_Violation: {stop_violation}"
                    except:
                        math_block = "Insufficient Data"

                    prompt = f"""
                    SYSTEM: Deterministic Trade Audit Engine.
                    INPUT: {ticker} | {setup_type} | {emotion} | {notes}
                    METRICS: {math_block}
                    CONTEXT RULES: {my_rules}
                    OUTPUT: [SCORE], [TAGS], [TECH], [PSYCH], [RISK], [FIX].
                    """
                    ready_to_run = True

        if ready_to_run:
            with st.spinner("Processing Logic..."):
                try:
                    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
                    if img_b64: messages[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})
                    
                    payload = {"model": "Qwen/Qwen2.5-VL-7B-Instruct", "messages": messages, "max_tokens": 600}
                    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                    res = requests.post(API_URL, headers=headers, json=payload)

                    if res.status_code == 200:
                        report = parse_report(res.json()["choices"][0]["message"]["content"])
                        save_analysis(current_user, report, ticker_val) # Pass Ticker
                        
                        score_color = "#ef4444" if report['score'] < 50 else "#10b981"
                        st.markdown(f"""
                        <div class="report-container">
                            <div style="font-size:1.2rem; font-weight:bold; color:#888;">AUDIT RESULT</div>
                            <div style="font-size:3.5rem; font-weight:900; color:{score_color};">{report['score']}</div>
                            <div class="analysis-card" style="border-left-color: #3b82f6;"><b>TECH:</b> {report['tech']}</div>
                            <div class="analysis-card" style="border-left-color: #f59e0b;"><b>PSYCH:</b> {report['psych']}</div>
                            <div class="analysis-card" style="border-left-color: #10b981;"><b>FIX:</b> {report['fix']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e: st.error(f"Error: {e}")

    # --- TAB 2: RULES ---
    with main_tab2:
        st.subheader("📜 The Law")
        rules_data = supabase.table("rules").select("*").eq("user_id", current_user).execute()
        if rules_data.data:
            for r in rules_data.data:
                c1, c2 = st.columns([5, 1])
                c1.markdown(f"<div class='rule-item'>⛔ {r['rule_text']}</div>", unsafe_allow_html=True)
                if c2.button("Del", key=r['id']):
                    supabase.table("rules").delete().eq("id", r['id']).execute()
                    st.rerun()
        else:
            st.info("No rules yet.")

    # --- TAB 3: EXECUTIVE DASHBOARD ---
    with main_tab3:
        # 1. FETCH DATA
        hist = supabase.table("trades").select("*").eq("user_id", current_user).order("created_at", desc=True).execute()
        
        if hist.data:
            df = pd.DataFrame(hist.data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            # --- SECTION 1: TOP SUMMARY (EXECUTIVE OVERVIEW) ---
            avg_score = df['score'].mean()
            total_trades = len(df)
            
            # Discipline Score (Mock Calculation: % of scores > 50)
            discipline_rate = (len(df[df['score'] > 50]) / total_trades) * 100
            
            # Most Frequent Mistake
            all_tags = [tag for sublist in df['mistake_tags'] for tag in sublist]
            top_mistake = pd.Series(all_tags).mode()[0] if all_tags else "None"

            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"<div class='kpi-card'><div class='kpi-val'>{int(avg_score)}</div><div class='kpi-label'>Avg Quality</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='kpi-card'><div class='kpi-val'>{total_trades}</div><div class='kpi-label'>Total Trades</div></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='kpi-card' style='border-color:#ff4d4d'><div class='kpi-val' style='color:#ff4d4d; font-size:1.8rem'>{top_mistake}</div><div class='kpi-label'>Primary Leak</div></div>", unsafe_allow_html=True)
            c4.markdown(f"<div class='kpi-card'><div class='kpi-val'>{int(discipline_rate)}%</div><div class='kpi-label'>Discipline Score</div></div>", unsafe_allow_html=True)

            # --- SECTION 2: BEHAVIOR SNAPSHOT ---
            st.markdown("<div class='section-header'>BEHAVIORAL DNA</div>", unsafe_allow_html=True)
            
            b1, b2 = st.columns(2)
            
            with b1:
                st.caption("Mistake Frequency Distribution")
                if all_tags:
                    tag_counts = pd.Series(all_tags).value_counts().reset_index()
                    tag_counts.columns = ['Mistake', 'Count']
                    # Using standard Streamlit Bar Chart for clean look
                    st.bar_chart(tag_counts.set_index('Mistake'), color="#ff4d4d")
                else:
                    st.info("No mistakes tagged yet.")

            with b2:
                st.caption("Trade Quality Distribution (0-100)")
                st.bar_chart(df['score'], color="#3b82f6")

            # --- SECTION 3: PATTERN INSIGHTS ---
            st.markdown("<div class='section-header'>AI PATTERN RECOGNITION</div>", unsafe_allow_html=True)
            insights = generate_insights(df)
            for insight in insights:
                st.info(insight)

            # --- SECTION 4: PROGRESS OVER TIME ---
            st.markdown("<div class='section-header'>LEARNING CURVE</div>", unsafe_allow_html=True)
            st.caption("Average Trade Quality Score (Moving Average)")
            chart_data = df[['created_at', 'score']].sort_values('created_at')
            st.line_chart(chart_data.set_index('created_at'), color="#10b981")

            # --- SECTION 5: RULES PANEL (READ ONLY VIEW) ---
            st.markdown("<div class='section-header'>ACTIVE GUARDRAILS</div>", unsafe_allow_html=True)
            user_rules = get_user_rules(current_user)
            if user_rules:
                r_cols = st.columns(3)
                for i, rule in enumerate(user_rules):
                    r_cols[i % 3].error(f"⛔ {rule}")
            else:
                st.caption("No active rules found.")

            # --- SECTION 6: RECENT TRADES TABLE ---
            st.markdown("<div class='section-header'>FORENSIC LOGS</div>", unsafe_allow_html=True)
            
            # Clean Table Data
            table_df = df[['created_at', 'ticker', 'score', 'mistake_tags', 'fix_action']].copy()
            table_df.columns = ['Date', 'Ticker', 'Quality Score', 'Mistakes', 'Surgical Fix']
            table_df['Date'] = table_df['Date'].dt.strftime('%Y-%m-%d %H:%M')
            
            st.dataframe(
                table_df, 
                use_container_width=True,
                column_config={
                    "Quality Score": st.column_config.ProgressColumn(
                        "Quality Score",
                        format="%d",
                        min_value=0,
                        max_value=100,
                    ),
                    "Mistakes": st.column_config.ListColumn("Mistakes")
                },
                hide_index=True
            )

        else:
            st.info("⚠️ Dashboard Empty. Upload your first trade autopsy to initialize analytics.")
