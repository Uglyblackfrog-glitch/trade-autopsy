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
st.set_page_config(
    page_title="StockPostmortem.ai", 
    page_icon="🩸", 
    layout="wide",
    initial_sidebar_state="collapsed" # Default collapsed
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
            API_URL = "https://router.huggingface.co/v1/chat/completions"
            
    except Exception as e:
        st.error(f"⚠️ Configuration Error: {e}")
        st.stop()

# ==========================================
# 2. ULTRA-MODERN CSS THEME
# ==========================================
st.markdown("""
<style>
    /* --- GLOBAL FONTS & RESET --- */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;800&display=swap');
    
    body, .stApp { 
        background-color: #000000 !important; 
        background-image: radial-gradient(circle at 50% 0%, #1a0b0b 0%, #000000 70%);
        font-family: 'Inter', sans-serif !important; 
        color: #e2e8f0; 
    }

    /* --- HIDE SIDEBAR COMPLETELY --- */
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    
    /* --- HEADER STYLES --- */
    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 0;
        margin-bottom: 30px;
        border-bottom: 1px solid #333;
    }

    /* --- GLASSMORPHISM MODULES --- */
    .glass-panel {
        background: rgba(20, 20, 20, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    
    /* --- KPI CARDS --- */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 15px;
        margin-bottom: 25px;
    }
    
    .kpi-card {
        background: linear-gradient(145deg, #111, #0a0a0a);
        border: 1px solid #222;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        position: relative;
        overflow: hidden;
    }
    
    .kpi-card:hover {
        border-color: #ff3333;
        transform: translateY(-5px);
        box-shadow: 0 10px 30px -10px rgba(255, 51, 51, 0.3);
    }
    
    .kpi-val { 
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.5rem; 
        font-weight: 700; 
        color: #fff; 
        margin-bottom: 5px;
    }
    
    .kpi-label { 
        color: #888; 
        font-size: 0.75rem; 
        text-transform: uppercase; 
        letter-spacing: 1.5px; 
        font-weight: 600; 
    }

    /* --- LOGIN BOX --- */
    .login-container {
        max-width: 400px;
        margin: 15vh auto;
        padding: 40px;
        background: rgba(10, 10, 10, 0.9);
        border: 1px solid #333;
        border-radius: 20px;
        box-shadow: 0 0 50px rgba(255, 50, 50, 0.1);
        text-align: center;
    }

    /* --- UTILITY CLASSES --- */
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #fff;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .section-title::before {
        content: '';
        display: block;
        width: 4px;
        height: 18px;
        background: #ff4d4d;
        border-radius: 2px;
    }

    /* --- ANALYSIS REPORT --- */
    .report-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        margin-top: 15px;
    }
    
    .report-item {
        background: rgba(255,255,255,0.02);
        border-left: 3px solid #555;
        padding: 15px;
        border-radius: 0 8px 8px 0;
    }

    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
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

def save_analysis(user_id, data, ticker_symbol="UNK"):
    if not supabase: return
    payload = {
        "user_id": user_id,
        "ticker": ticker_symbol,
        "score": data.get('score', 0),
        "mistake_tags": data.get('tags', []),
        "technical_analysis": data.get('tech', ''),
        "psych_analysis": data.get('psych', ''),
        "risk_analysis": data.get('risk', ''),
        "fix_action": data.get('fix', '')
    }
    supabase.table("trades").insert(payload).execute()

def generate_insights(df):
    insights = []
    if df.empty: return ["Awaiting data to generate neural patterns."]
    
    recent_scores = df.head(3)['score'].mean()
    if recent_scores < 50:
        insights.append("⚠️ **Tilt Detected:** Last 3 trades avg < 50. Suggest 24h trading halt.")
    elif recent_scores > 80:
        insights.append("🔥 **Flow State:** High decision quality detected. Increase risk tolerance slightly.")

    all_tags = [tag for sublist in df['mistake_tags'] for tag in sublist]
    if "FOMO" in all_tags and "Revenge" in all_tags:
        insights.append("🧠 **Toxic Loop:** 'FOMO' leading to 'Revenge' detected 3x this month.")
    
    return insights

# ==========================================
# 4. MAIN APP LOGIC
# ==========================================

# --- LOGIN VIEW ---
if not st.session_state["authenticated"]:
    st.markdown("""
    <div class="login-container">
        <div style="font-size: 3rem;">🩸</div>
        <h1 style="margin-top: 10px; margin-bottom: 0;">StockPostmortem</h1>
        <p style="color: #666; font-size: 0.9rem; margin-bottom: 30px;">Algorithmic Behavioral Forensics</p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        with st.form("login_form"):
            username = st.text_input("Operator ID")
            password = st.text_input("Access Key", type="password")
            if st.form_submit_button("INITIALIZE TERMINAL", type="primary", use_container_width=True):
                check_login(username, password)

# --- DASHBOARD VIEW ---
else:
    current_user = st.session_state["user"]
    
    # --- CUSTOM HEADER (Replaces Sidebar) ---
    col_logo, col_spacer, col_profile = st.columns([2, 5, 1], gap="small")
    
    with col_logo:
        st.markdown(f"""
        <div style="display:flex; align-items:center; height: 100%;">
            <span style="font-size: 1.8rem; margin-right: 10px;">🩸</span>
            <div>
                <div style="font-weight: 900; font-size: 1.2rem; line-height: 1.1;">STOCK<span style="color:#ff4d4d">POSTMORTEM</span></div>
                <div style="font-size: 0.7rem; color: #666; letter-spacing: 1px;">FORENSICS UNIT</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_profile:
        # Profile Popover Button
        with st.popover(f"👤 {current_user}", use_container_width=True):
            st.markdown(f"**Operator:** {current_user}")
            st.caption("Access Level: PRO")
            st.markdown("---")
            if st.button("🔴 DISCONNECT", type="primary", use_container_width=True):
                logout()

    st.markdown("---")

    # TABS
    main_tab1, main_tab2 = st.tabs(["🔎 FORENSIC AUDIT", "📊 PERFORMANCE METRICS"])

    # --- TAB 1: AUDIT (INPUT) ---
    with main_tab1:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Case Data Input</div>', unsafe_allow_html=True)
        
        c_mode = st.radio("Input Vector", ["Text Parameters", "Chart Vision"], horizontal=True, label_visibility="collapsed")
        
        prompt = ""
        img_b64 = None
        ticker_val = "IMG"
        ready_to_run = False

        if c_mode == "Chart Vision":
            uploaded_file = st.file_uploader("Upload Chart Screenshot", type=["png", "jpg"])
            if uploaded_file:
                st.image(uploaded_file, width=600)
                if st.button("RUN OPTICAL ANALYSIS", type="primary"):
                    image = Image.open(uploaded_file)
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    prompt = f"""
                    SYSTEM: Hedge Fund Risk Manager.
                    TASK: Analyze chart for technical/psychological errors.
                    OUTPUT: [SCORE], [TAGS], [TECH], [PSYCH], [RISK], [FIX].
                    """
                    ready_to_run = True

        else:
            with st.form("audit_form"):
                col_a, col_b, col_c = st.columns(3)
                with col_a: ticker = st.text_input("Ticker", "SPY")
                with col_b: setup_type = st.selectbox("Setup", ["Trend", "Reversal", "Breakout"])
                with col_c: emotion = st.selectbox("State", ["Neutral", "FOMO", "Revenge", "Tilt"])
                
                col_d, col_e, col_f = st.columns(3)
                with col_d: entry = st.number_input("Entry", 0.0)
                with col_e: exit_price = st.number_input("Exit", 0.0)
                with col_f: stop = st.number_input("Stop", 0.0)
                
                notes = st.text_area("Execution Notes", height=80, placeholder="e.g. hesitated on entry, widened stop...")
                
                if st.form_submit_button("EXECUTE AUDIT", type="primary", use_container_width=True):
                    ticker_val = ticker
                    prompt = f"""
                    SYSTEM: Trading Coach.
                    DATA: {ticker} | {setup_type} | {emotion} | Note: {notes}
                    ENTRY: {entry} | EXIT: {exit_price} | STOP: {stop}
                    OUTPUT: [SCORE], [TAGS], [TECH], [PSYCH], [RISK], [FIX].
                    """
                    ready_to_run = True
        st.markdown('</div>', unsafe_allow_html=True)

        # RESULTS AREA
        if ready_to_run and supabase:
            with st.spinner("🧠 AI Forensic Analysis in progress..."):
                try:
                    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
                    if img_b64: messages[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})
                    
                    payload = {"model": "Qwen/Qwen2.5-VL-7B-Instruct", "messages": messages, "max_tokens": 600}
                    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                    res = requests.post(API_URL, headers=headers, json=payload)

                    if res.status_code == 200:
                        report = parse_report(res.json()["choices"][0]["message"]["content"])
                        save_analysis(current_user, report, ticker_val)
                        
                        score_color = "#ff4d4d" if report['score'] < 50 else "#00e676"
                        
                        st.markdown(f"""
                        <div class="glass-panel" style="border-top: 4px solid {score_color}">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div>
                                    <div style="color:#888; letter-spacing:2px; font-size:0.8rem;">AUDIT SCORE</div>
                                    <div style="font-size:4rem; font-weight:800; line-height:1; color:{score_color}">{report['score']}</div>
                                </div>
                                <div style="text-align:right;">
                                    <div style="background:rgba(255,255,255,0.1); padding:5px 10px; border-radius:4px; display:inline-block; margin-bottom:5px;">{ticker_val}</div>
                                </div>
                            </div>
                            <div class="report-grid">
                                <div class="report-item" style="border-left-color: #3b82f6;">
                                    <div style="color:#3b82f6; font-weight:bold; font-size:0.8rem;">TECHNICAL</div>
                                    {report['tech']}
                                </div>
                                <div class="report-item" style="border-left-color: #f59e0b;">
                                    <div style="color:#f59e0b; font-weight:bold; font-size:0.8rem;">PSYCHOLOGY</div>
                                    {report['psych']}
                                </div>
                                <div class="report-item" style="border-left-color: #ef4444;">
                                    <div style="color:#ef4444; font-weight:bold; font-size:0.8rem;">RISK</div>
                                    {report['risk']}
                                </div>
                                <div class="report-item" style="border-left-color: #10b981;">
                                    <div style="color:#10b981; font-weight:bold; font-size:0.8rem;">CORRECTIVE ACTION</div>
                                    {report['fix']}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Analysis Failed: {e}")

    # --- TAB 2: DASHBOARD ---
    with main_tab2:
        if supabase:
            hist = supabase.table("trades").select("*").eq("user_id", current_user).order("created_at", desc=True).execute()
            
            if hist.data:
                df = pd.DataFrame(hist.data)
                df['created_at'] = pd.to_datetime(df['created_at'])
                
                # METRICS CALC
                avg_score = df['score'].mean()
                total_trades = len(df)
                all_tags = [tag for sublist in df['mistake_tags'] for tag in sublist]
                top_mistake = pd.Series(all_tags).mode()[0] if all_tags else "None"
                
                # 1. KPI ROW
                st.markdown(f"""
                <div class="kpi-container">
                    <div class="kpi-card">
                        <div class="kpi-val">{int(avg_score)}</div>
                        <div class="kpi-label">Avg Quality</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-val">{total_trades}</div>
                        <div class="kpi-label">Total Audits</div>
                    </div>
                    <div class="kpi-card" style="border-color: rgba(255, 77, 77, 0.4);">
                        <div class="kpi-val" style="color:#ff4d4d; font-size:1.8rem; margin-top:10px;">{top_mistake}</div>
                        <div class="kpi-label">Primary Leak</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-val">{len(all_tags)}</div>
                        <div class="kpi-label">Total Errors</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 2. SPLIT LAYOUT
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">Performance Trend</div>', unsafe_allow_html=True)
                    
                    chart_data = df[['created_at', 'score']].sort_values('created_at')
                    base = alt.Chart(chart_data).encode(x=alt.X('created_at', axis=None))
                    line = base.mark_line(color='#00e676', strokeWidth=3).encode(y=alt.Y('score', scale=alt.Scale(domain=[0, 100])))
                    area = base.mark_area(color='#00e676', opacity=0.1).encode(y='score')
                    
                    st.altair_chart((line + area).properties(height=250), use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # LOGS
                    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">Forensic Log</div>', unsafe_allow_html=True)
                    table_df = df[['created_at', 'ticker', 'score', 'mistake_tags']].copy()
                    table_df.columns = ['Time', 'Asset', 'Score', 'Tags']
                    st.dataframe(
                        table_df, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            "Score": st.column_config.ProgressColumn("Quality", min_value=0, max_value=100, format="%d"),
                            "Time": st.column_config.DatetimeColumn("Time", format="MM-DD HH:mm")
                        }
                    )
                    st.markdown('</div>', unsafe_allow_html=True)

                with col_right:
                    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">AI Insights</div>', unsafe_allow_html=True)
                    insights = generate_insights(df)
                    for insight in insights:
                        st.markdown(f"<div style='font-size:0.9rem; margin-bottom:10px; padding-bottom:10px; border-bottom:1px solid #333;'>{insight}</div>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">Mistake Distribution</div>', unsafe_allow_html=True)
                    if all_tags:
                        tag_counts = pd.Series(all_tags).value_counts().reset_index()
                        tag_counts.columns = ['Mistake', 'Count']
                        c = alt.Chart(tag_counts).mark_arc(innerRadius=40).encode(
                            theta=alt.Theta("Count", stack=True), 
                            color=alt.Color("Mistake", scale=alt.Scale(scheme='reds'))
                        )
                        st.altair_chart(c, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No data available. Perform your first audit.")
