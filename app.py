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
# 0. CONFIG & SETUP
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
        st.error("ACCESS DENIED")

def logout():
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.rerun()

# ==========================================
# 1. DATABASE & API
# ==========================================
if st.session_state["authenticated"]:
    try:
        # Secrets handling
        HF_TOKEN = st.secrets.get("HF_TOKEN", "")
        SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
        SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
        
        if not all([HF_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
            st.warning("⚠️ Database secrets missing. UI Mode Only.")
            supabase = None
        else:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            API_URL = "https://router.huggingface.co/v1/chat/completions"
            
    except Exception as e:
        st.error(f"System Error: {e}")
        st.stop()

# ==========================================
# 2. FUTURISTIC UI THEME (CSS)
# ==========================================
st.markdown("""
<style>
    /* --- FONTS & BASICS --- */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    body, .stApp { 
        background-color: #030303 !important; 
        color: #e0e0e0;
        font-family: 'Space Grotesk', sans-serif;
    }

    /* --- INPUT FIELDS --- */
    .stTextInput input, .stNumberInput input, .stSelectbox, .stTextArea textarea {
        background-color: #0a0a0a !important;
        color: #fff !important;
        border: 1px solid #333 !important;
        border-radius: 4px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 10px rgba(99, 102, 241, 0.2);
    }

    /* --- MODULE CONTAINERS --- */
    .console-card {
        background: #09090b;
        border: 1px solid #27272a;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
        margin-bottom: 20px;
    }

    .header-bar {
        border-bottom: 1px solid #27272a;
        padding-bottom: 15px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* --- HUD ELEMENTS --- */
    .hud-stat {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
    }
    .hud-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #71717a;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .hud-value {
        font-family: 'JetBrains Mono';
        font-size: 1.5rem;
        font-weight: 700;
        color: white;
    }

    /* --- SCORE RING --- */
    .score-container {
        display: flex;
        align-items: center;
        justify-content: center;
        background: radial-gradient(circle, rgba(255,255,255,0.03) 0%, rgba(0,0,0,0) 70%);
        border: 1px solid #222;
        border-radius: 100%;
        width: 160px;
        height: 160px;
        margin: 0 auto;
    }

    /* --- CUSTOM BUTTON --- */
    div.stButton > button {
        background: linear-gradient(90deg, #4f46e5, #6366f1);
        color: white;
        border: none;
        padding: 12px 24px;
        font-weight: 700;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        text-transform: uppercase;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(99, 102, 241, 0.4);
    }

    /* --- ANALYSIS GRID --- */
    .analysis-box {
        background: rgba(255,255,255,0.02);
        border-left: 2px solid #555;
        padding: 15px;
        margin-bottom: 10px;
    }

    /* Hide standard UI clutter */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER LOGIC
# ==========================================
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
    if not supabase: return
    
    # 1. Save Trade
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
    
    # 2. Silent Rule Generation (Backend only now)
    if data.get('score', 0) < 50:
        supabase.table("rules").insert({"user_id": user_id, "rule_text": data.get('fix')}).execute()

def get_backend_rules(user_id):
    """Fetches rules for AI context only, not for display."""
    if not supabase: return []
    try:
        response = supabase.table("rules").select("*").eq("user_id", user_id).execute()
        return [r['rule_text'] for r in response.data]
    except:
        return []

# ==========================================
# 4. MAIN APP
# ==========================================

if not st.session_state["authenticated"]:
    # LOGIN
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center; margin-bottom:20px;">
            <div style="font-size:3rem;">🩸</div>
            <h2 style="font-weight:800; letter-spacing:-1px;">STOCK POSTMORTEM</h2>
            <p style="color:#666; font-size:0.8rem;">FORENSIC TRADING ANALYTICS</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("AUTHENTICATE"): check_login(u, p)

else:
    # DASHBOARD
    current_user = st.session_state["user"]
    
    # TOP NAVBAR
    c1, c2 = st.columns([8, 1])
    with c1:
        st.markdown(f"<div style='font-family:JetBrains Mono; color:#666;'>OPERATOR: <span style='color:#fff;'>{current_user.upper()}</span> // SYSTEM: <span style='color:#10b981;'>ONLINE</span></div>", unsafe_allow_html=True)
    with c2:
        if st.button("LOGOUT"): logout()
    
    st.markdown("---")

    # TABS
    tab_diag, tab_metrics = st.tabs(["🔎 DIAGNOSTICS", "📊 ANALYTICS"])

    # --- TAB 1: DIAGNOSTICS (THE CLEAN UI) ---
    with tab_diag:
        
        # CONTAINER 1: THE INPUT CONSOLE
        st.markdown('<div class="console-card">', unsafe_allow_html=True)
        st.markdown('<div class="header-bar"><span style="font-weight:700; color:#fff;">// INPUT VECTOR</span></div>', unsafe_allow_html=True)
        
        # Input Method Toggle
        in_mode = st.radio("SOURCE", ["MANUAL ENTRY", "CHART UPLOAD"], horizontal=True, label_visibility="collapsed")
        
        prompt = ""
        img_b64 = None
        ticker_val = "IMG"
        ready = False
        
        if in_mode == "CHART UPLOAD":
            up_file = st.file_uploader("DROP IMAGE FILE", type=["png", "jpg", "jpeg"])
            if up_file and st.button("INITIATE VISION SCAN", use_container_width=True):
                image = Image.open(up_file)
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                
                # Fetch rules silently
                hidden_rules = get_backend_rules(current_user)
                
                prompt = f"""
                ROLE: Senior Risk Manager.
                CONTEXT: User's past failures: {hidden_rules}
                TASK: Analyze chart. 
                OUTPUT: [SCORE] (0-100), [TAGS], [TECH], [PSYCH], [RISK], [FIX].
                """
                ready = True
                
        else:
            with st.form("audit_form"):
                # Row 1: The Basics
                c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
                with c1: ticker = st.text_input("TICKER", "SPY")
                with c2: position = st.selectbox("SIDE", ["LONG", "SHORT"])
                with c3: timeframe = st.selectbox("TIMEFRAME", ["1M", "5M", "15M", "1H", "4H", "D"])
                with c4: emotion = st.selectbox("MENTAL STATE", ["NEUTRAL", "FOMO", "REVENGE", "TILT", "FEAR"])
                
                # Row 2: The Numbers
                c1, c2, c3 = st.columns(3)
                with c1: entry = st.number_input("ENTRY PRICE", value=0.0)
                with c2: exit_p = st.number_input("EXIT PRICE", value=0.0)
                with c3: stop = st.number_input("STOP LOSS", value=0.0)
                
                # Row 3: The Context
                notes = st.text_area("EXECUTION NOTES", placeholder="Describe your logic...", height=70)
                
                if st.form_submit_button("RUN DIAGNOSTIC", use_container_width=True):
                    ticker_val = ticker
                    hidden_rules = get_backend_rules(current_user)
                    
                    prompt = f"""
                    ROLE: Brutally honest Trading Coach.
                    DATA: {ticker} | {position} | {timeframe} | {emotion}
                    PRICES: In: {entry} | Out: {exit_p} | Stop: {stop}
                    NOTES: {notes}
                    USER HISTORY: {hidden_rules}
                    OUTPUT FORMAT: [SCORE], [TAGS], [TECH], [PSYCH], [RISK], [FIX].
                    """
                    ready = True
        
        st.markdown('</div>', unsafe_allow_html=True)

        # CONTAINER 2: THE OUTPUT HUD
        if ready and supabase:
            with st.status("PROCESSING NEURAL AUDIT...", expanded=True) as status:
                try:
                    msgs = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
                    if img_b64: msgs[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})
                    
                    payload = {
                        "model": "Qwen/Qwen2.5-VL-7B-Instruct", 
                        "messages": msgs, 
                        "max_tokens": 600
                    }
                    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                    
                    res = requests.post(API_URL, headers=headers, json=payload)
                    
                    if res.status_code == 200:
                        data = parse_report(res.json()["choices"][0]["message"]["content"])
                        save_analysis(current_user, data, ticker_val)
                        status.update(label="AUDIT COMPLETE", state="complete", expanded=False)
                        
                        # --- RENDER RESULTS ---
                        score = data['score']
                        color = "#ef4444" if score < 50 else "#eab308" if score < 80 else "#10b981"
                        
                        st.markdown(f"""
                        <div class="console-card" style="border-top: 4px solid {color};">
                            <div class="header-bar">
                                <span style="font-weight:700; color:#fff;">// DIAGNOSTIC REPORT</span>
                                <span style="font-family:'JetBrains Mono'; color:#666;">ID: {datetime.now().strftime('%H%M%S')}</span>
                            </div>
                            
                            <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 30px; align-items: start;">
                                <div style="text-align: center;">
                                    <div class="score-container" style="border-color: {color}; box-shadow: 0 0 30px {color}20;">
                                        <div style="font-size: 3.5rem; font-weight: 800; color: {color}; font-family: 'JetBrains Mono';">{score}</div>
                                    </div>
                                    <div style="margin-top: 15px; font-size: 0.8rem; letter-spacing: 2px; color: #888;">QUALITY INDEX</div>
                                    <div style="margin-top: 20px;">
                                        {''.join([f'<span style="background:#222; border:1px solid #444; padding:4px 8px; font-size:0.7rem; border-radius:4px; margin:2px; display:inline-block;">{t}</span>' for t in data['tags']])}
                                    </div>
                                </div>
                                
                                <div>
                                    <div class="analysis-box" style="border-left-color: #3b82f6;">
                                        <div class="hud-label" style="color:#3b82f6;">TECHNICAL BREAKDOWN</div>
                                        <div style="font-size: 0.95rem; color: #ccc;">{data['tech']}</div>
                                    </div>
                                    
                                    <div class="analysis-box" style="border-left-color: #f59e0b;">
                                        <div class="hud-label" style="color:#f59e0b;">PSYCHOLOGICAL PROFILE</div>
                                        <div style="font-size: 0.95rem; color: #ccc;">{data['psych']}</div>
                                    </div>
                                    
                                    <div class="analysis-box" style="border-left-color: {color}; background: {color}10;">
                                        <div class="hud-label" style="color:{color};">SURGICAL FIX</div>
                                        <div style="font-size: 0.95rem; color: #fff; font-weight: 500;">{data['fix']}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    else:
                        st.error(f"API Error: {res.status_code}")
                except Exception as e:
                    st.error(f"Critical Error: {e}")

    # --- TAB 2: ANALYTICS (CLEAN DASHBOARD) ---
    with tab_metrics:
        if supabase:
            hist = supabase.table("trades").select("*").eq("user_id", current_user).order("created_at", desc=True).execute()
            if hist.data:
                df = pd.DataFrame(hist.data)
                df['created_at'] = pd.to_datetime(df['created_at'])

                # KPI ROW
                k1, k2, k3, k4 = st.columns(4)
                
                with k1:
                    st.markdown(f"""
                    <div class="console-card" style="padding:15px; text-align:center;">
                        <div class="hud-label">AVG SCORE</div>
                        <div class="hud-value">{int(df['score'].mean())}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with k2:
                     st.markdown(f"""
                    <div class="console-card" style="padding:15px; text-align:center;">
                        <div class="hud-label">TOTAL AUDITS</div>
                        <div class="hud-value">{len(df)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with k3:
                    win_rate = len(df[df['score'] > 70]) / len(df) * 100
                    st.markdown(f"""
                    <div class="console-card" style="padding:15px; text-align:center;">
                        <div class="hud-label">DISCIPLINE</div>
                        <div class="hud-value" style="color:#10b981;">{int(win_rate)}%</div>
                    </div>
                    """, unsafe_allow_html=True)

                with k4:
                    all_tags = [tag for sublist in df['mistake_tags'] for tag in sublist]
                    top_leak = pd.Series(all_tags).mode()[0] if all_tags else "NONE"
                    st.markdown(f"""
                    <div class="console-card" style="padding:15px; text-align:center; border-color:#ef4444;">
                        <div class="hud-label" style="color:#ef4444;">MAIN LEAK</div>
                        <div class="hud-value" style="font-size:1.2rem; color:#ef4444;">{top_leak}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # CHARTS ROW
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown('<div class="console-card">', unsafe_allow_html=True)
                    st.caption("PERFORMANCE TRAJECTORY")
                    chart_data = df.sort_values('created_at')
                    
                    chart = alt.Chart(chart_data).mark_area(
                        line={'color':'#6366f1'},
                        color=alt.Gradient(
                            gradient='linear',
                            stops=[alt.GradientStop(color='#6366f1', offset=0),
                                   alt.GradientStop(color='rgba(99, 102, 241, 0)', offset=1)],
                            x1=1, x2=1, y1=1, y2=0
                        )
                    ).encode(
                        x=alt.X('created_at', axis=None),
                        y=alt.Y('score', scale=alt.Scale(domain=[0, 100]))
                    ).properties(height=300)
                    
                    st.altair_chart(chart, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with c2:
                    st.markdown('<div class="console-card">', unsafe_allow_html=True)
                    st.caption("ERROR HEATMAP")
                    if all_tags:
                        counts = pd.Series(all_tags).value_counts().reset_index()
                        counts.columns = ['error', 'count']
                        st.dataframe(counts, hide_index=True, use_container_width=True)
                    else:
                        st.info("No data yet")
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("AWAITING DATA...")
