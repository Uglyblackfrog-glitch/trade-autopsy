import streamlit as st
import requests
import base64
import re
import pandas as pd
import time
import json
from supabase import create_client, Client

# ==========================================
# 0. CONFIGURATION & SETUP
# ==========================================
st.set_page_config(
    page_title="StockPostmortem.ai", 
    page_icon="🧬", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Login Credentials
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
        st.error("⚠️ ACCESS DENIED: Invalid Credentials")

def logout():
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.rerun()

# ==========================================
# 1. API CONNECTIONS
# ==========================================
if st.session_state["authenticated"]:
    try:
        HF_TOKEN = st.secrets["HF_TOKEN"]
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        supabase = None
        HF_TOKEN = None

# ==========================================
# 2. INTELLIGENCE ENGINE
# ==========================================
def run_scientific_analysis(messages, mode="text"):
    if not HF_TOKEN: return '{"score": 50, "tags": ["Demo"], "technical_analysis": "Demo Mode", "psychological_profile": "Demo Mode", "risk_assessment": "Demo", "strategic_roadmap": "Fix secrets"}'
    
    api_url = "https://router.huggingface.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
    
    if mode == "text":
        model_id = "Qwen/Qwen2.5-72B-Instruct" 
    else:
        model_id = "Qwen/Qwen2.5-VL-7B-Instruct"

    payload = {
        "model": model_id,
        "messages": messages,
        "max_tokens": 2048,
        "temperature": 0.1, 
    }

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

def clean_text_surgical(text):
    if not isinstance(text, str): return str(text)
    text = text.replace('\n', ' ')
    text = re.sub(r'(\d),(\s+)(\d)', r'\1,\3', text)
    text = re.sub(r'-\s+(\d)', r'-\1', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(?<!^)(\d+\.)', r'<br>\1', text)
    return text.strip()

def fix_mashed_tags_surgical(tags_input):
    raw_list = []
    if isinstance(tags_input, str):
        try: raw_list = json.loads(tags_input)
        except: raw_list = tags_input.split(',')
    elif isinstance(tags_input, list):
        raw_list = tags_input
    else:
        return []

    final_tags = []
    for tag in raw_list:
        tag = str(tag).strip()
        split_tag = re.sub(r'([a-z])([A-Z])', r'\1,\2', tag)
        for sub_tag in split_tag.split(','):
            clean = sub_tag.strip()
            if clean and len(clean) < 40:
                final_tags.append(clean)
    return final_tags

def parse_scientific_report(text):
    clean_raw = text.replace("```json", "").replace("```", "").strip()
    data = { "score": 0, "tags": [], "tech": "", "psych": "", "risk": "", "fix": "", "outcome": "unknown", "type": "long", "reality": "Real" }
    try:
        json_data = json.loads(clean_raw)
        data["tags"] = json_data.get("tags", [])
        data["tech"] = json_data.get("technical_analysis", "")
        data["psych"] = json_data.get("psychological_profile", "")
        data["risk"] = json_data.get("risk_assessment", "")
        data["fix"] = json_data.get("strategic_roadmap", "")
        data["outcome"] = json_data.get("outcome", "unknown").lower()
        data["type"] = json_data.get("trade_direction", "long").lower()
        data["reality"] = json_data.get("reality_check", "Real")
    except:
        patterns = {"tech": r'"technical_analysis":\s*"(.*?)"', "psych": r'"psychological_profile":\s*"(.*?)"', "risk": r'"risk_assessment":\s*"(.*?)"', "fix": r'"strategic_roadmap":\s*"(.*?)"', "tags": r'"tags":\s*\[(.*?)\]'}
        for k, p in patterns.items():
            m = re.search(p, clean_raw, re.DOTALL)
            if m: data[k] = m.group(1)

    data["tags"] = fix_mashed_tags_surgical(data["tags"])
    data["tech"] = clean_text_surgical(data["tech"])
    data["psych"] = clean_text_surgical(data["psych"])
    data["risk"] = clean_text_surgical(data["risk"])
    data["fix"] = clean_text_surgical(data["fix"])

    score = 100
    if "loss" in clean_raw.lower(): score = 45
    
    data["score"] = max(0, min(100, int(score)))
    return data

def save_to_lab_records(user_id, data):
    if not supabase: return
    try:
        payload = {"user_id": user_id, "score": data.get('score', 0), "mistake_tags": data.get('tags', []), "technical_analysis": data.get('tech', ''), "psych_analysis": data.get('psych', ''), "risk_analysis": data.get('risk', ''), "fix_action": data.get('fix', '')}
        supabase.table("trades").insert(payload).execute()
    except: pass

def get_user_rules(user_id):
    if not supabase: return []
    try:
        res = supabase.table("rules").select("*").eq("user_id", user_id).execute()
        return [r['rule_text'] for r in res.data]
    except: return []

def render_report_html(report):
    c_score = "#f85149" if report['score'] < 50 else "#3fb950"
    tags_html = "".join([f'<span style="background:#21262d; border:1px solid #30363d; padding:4px 12px; border-radius:99px; font-size:0.7rem; margin-right:5px; color:#8b949e;">{t}</span>' for t in report['tags']])
    return f"""
    <div class="report-box">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #30363d; padding-bottom:20px;">
            <h2 style="color:white; margin:0; font-weight:800; font-style:italic;">AUTOPSY COMPLETE</h2>
            <div style="color:{c_score}; font-size:4rem; font-weight:800;">{report["score"]}</div>
        </div>
        <div style="margin:20px 0;">{tags_html}</div>
        <div class="section-title" style="color:#f85149; font-weight:800;">Technical Forensics</div><p style="color:#8b949e;">{report["tech"]}</p>
        <div class="section-title" style="color:#f85149; font-weight:800;">Psychological Profile</div><p style="color:#8b949e;">{report["psych"]}</p>
        <div class="section-title" style="color:#f85149; font-weight:800;">Risk Assessment</div><p style="color:#8b949e;">{report["risk"]}</p>
        <div class="section-title" style="color:#f85149; font-weight:800;">Recovery Roadmap</div>
        <div style="background:rgba(248, 81, 73, 0.1); border-left:4px solid #f85149; padding:15px; border-radius:4px; color:white; margin-top:10px;">{report["fix"]}</div>
    </div>"""

# ==========================================
# 3. UI RENDERING & STYLING (UPDATED)
# ==========================================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap" rel="stylesheet">
<style>
    /* GLOBAL RESET */
    .stApp { background-color: #0d1117 !important; color: #c9d1d9; font-family: 'Inter', sans-serif; margin: 0; padding: 0;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    
    .block-container {
        padding-top: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }

    /* --- FIXED FULL-WIDTH HEADER --- */
    .custom-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 70px;
        background-color: #0d1117;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 50px;
        box-sizing: border-box;
        z-index: 999999;
    }

    .header-logo {
        font-size: 1.4rem;
        font-weight: 800;
        color: white !important;
        letter-spacing: -0.5px;
        text-decoration: none !important;
    }
    .header-logo span { color: #f85149; }

    .nav-menu { display: flex; gap: 40px; align-items: center; height: 100%; }

    /* LINKS - GREY ONLY */
    a.nav-link, div.nav-link {
        color: #8b949e !important;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        cursor: pointer;
        position: relative;
        display: flex;
        align-items: center;
        height: 100%;
        transition: color 0.2s;
        letter-spacing: 0.5px;
        text-decoration: none !important;
    }
    a.nav-link:hover, div.nav-link:hover { color: white !important; }
    .nav-link span { margin-left: 5px; font-size: 10px; } 

    .dropdown-box {
        display: none;
        position: absolute;
        top: 60px;
        left: -10px;
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        min-width: 200px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        padding: 5px 0;
        z-index: 1000000;
    }
    .nav-link:hover .dropdown-box { display: block; }

    a.dropdown-item {
        padding: 12px 20px;
        color: #c9d1d9 !important;
        font-size: 0.75rem;
        font-weight: 600;
        display: block;
        transition: background 0.2s;
        text-decoration: none !important;
    }
    a.dropdown-item:hover { background-color: #21262d; color: white !important; }

    .btn-started {
        background-color: #da3633;
        color: white;
        padding: 8px 20px;
        border-radius: 99px;
        font-weight: 700;
        font-size: 0.85rem;
        border: none;
        text-transform: capitalize;
        cursor: pointer;
    }
    .btn-started:hover { background-color: #f85149; }

    .header-spacer { height: 120px; }
    .main-container { max-width: 1000px; margin: 0 auto; padding: 0 20px; }

    /* --- THE BEAUTIFUL UPLOAD BOX STYLES --- */
    
    /* 1. The Container */
    [data-testid="stFileUploader"] {
        border: 2px dashed #30363d;
        border-radius: 20px;
        padding: 40px 20px;
        background-color: #0e1218; 
        text-align: center;
        transition: border-color 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #586069;
    }
    
    /* 2. The 'Browse Files' Button - MADE WHITE */
    [data-testid="stBaseButton-secondary"] {
        background-color: white !important;
        color: black !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 10px 30px !important;
        text-transform: capitalize !important;
        margin-top: 15px;
        transition: all 0.2s;
    }
    [data-testid="stBaseButton-secondary"]:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 15px rgba(255,255,255,0.2);
    }
    
    /* 3. Hide default tiny text to declutter */
    [data-testid="stFileUploader"] section > div:first-child span {
        display: none;
    }

    [data-testid="stForm"], .report-box { 
        background-color: #161b22 !important; border: 1px solid #30363d !important; 
        border-radius: 24px !important; padding: 40px !important; margin-bottom: 20px;
    }

    div.stButton > button { 
        background-color: #da3633 !important; color: white !important; font-weight: 800 !important;
        border-radius: 99px !important; border: none !important; padding: 12px 30px !important;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. MAIN LAYOUT
# ==========================================
if not st.session_state["authenticated"]:
    # LOGIN SCREEN
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;'><h1 style='font-size:2.5rem;'>STOCK<span style='color:#f85149'>POSTMORTEM</span>.AI</h1></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Operator ID")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Authenticate"): check_login(u, p)
else:
    user = st.session_state["user"]
    current_view = st.query_params.get("view", "visual")

    # --- HEADER ---
    st.markdown("""
    <div class="custom-header">
        <a href="?view=visual" class="header-logo">STOCK<span>POSTMORTEM</span>.AI</a>
        <div class="nav-menu">
            <div class="nav-link">
                ANALYZE <span>&#9662;</span>
                <div class="dropdown-box">
                    <a href="?view=visual" class="dropdown-item" target="_self">VISUAL EVIDENCE</a>
                    <a href="?view=text" class="dropdown-item" target="_self">DETAILED TEXT LOG</a>
                </div>
            </div>
            <a href="?view=vault" class="nav-link" target="_self">DATA VAULT</a>
            <a href="#" class="nav-link">PRICING</a>
        </div>
        <button class="btn-started">Get Started</button>
    </div>
    <div class="header-spacer"></div>
    """, unsafe_allow_html=True)

    # --- BODY ---
    with st.container():
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # Logout Utility
        col_utils_1, col_utils_2 = st.columns([10, 1])
        with col_utils_2:
            if st.button("Logout", key="logout_btn"): logout()

        # VIEW 1: VISUAL (MATCHING THE SCREENSHOT EXACTLY)
        if current_view == "visual":
            # 1. Main Headline - EXACT MATCH
            st.markdown("""
                <div style='text-align:center; padding-top: 40px; padding-bottom: 50px;'>
                    <h1 style='font-size: 5rem; font-weight: 900; font-style: italic; text-transform: uppercase; margin: 0; line-height: 0.9; letter-spacing: -2px;'>
                        STOP <span style='color:#da3633'>BLEEDING</span> CAPITAL.
                    </h1>
                    <p style='color:#8b949e; font-size: 1.1rem; max-width: 700px; margin: 30px auto 0 auto; line-height: 1.6;'>
                        Upload your losing trade screenshots. Our AI identifies psychological traps,
                        technical failures, and provides a surgical path to recovery.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            # 2. VISUAL HEADER FOR UPLOAD BOX
            # This renders the Icon and Text *inside* the area visually, right before the button
            st.markdown("""
            <div style="text-align: center; margin-bottom: -110px; position: relative; z-index: 10; pointer-events: none;">
                <div style="display: flex; justify-content: center; margin-bottom: 15px;">
                     <div style="background: rgba(218, 54, 51, 0.1); padding: 15px; border-radius: 50%;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#da3633" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.2 15c.7-1.2 1-2.5 1-3.9 0-4.4-3.6-8-8-8-3.2 0-6 1.9-7.2 4.8C3.4 8.2 1 11 1 14.5c0 3.6 2.9 6.5 6.5 6.5h13"></path><polyline points="17 19 12 15 7 19"></polyline><line x1="12" y1="15" x2="12" y2="25"></line></svg>
                     </div>
                </div>
                <h3 style='color:white; margin:0; font-size: 1.2rem; font-weight: 700; margin-bottom:5px;'>Drop your P&L or Chart screenshot here</h3>
                <p style='color:#6e7681; font-size:0.85rem; margin-top: 0px;'>Supports PNG, JPG (Max 10MB). Your data is encrypted.</p>
            </div>
            <div style="height: 80px;"></div> 
            """, unsafe_allow_html=True)
            
            # 3. ACTUAL UPLOADER (Styled via CSS to look like the container)
            up_file = st.file_uploader("Upload", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
            
            if up_file:
                st.image(up_file, use_container_width=True)
                if st.button("Initiate Forensic Scan"):
                    my_rules = get_user_rules(user)
                    img_b64 = base64.b64encode(up_file.getvalue()).decode('utf-8')
                    prompt = f"Audit this chart. Rules: {my_rules}. Output JSON."
                    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}]}]
                    with st.spinner("Scanning..."):
                        raw = run_scientific_analysis(messages, mode="vision")
                        report = parse_scientific_report(raw)
                        save_to_lab_records(user, report)
                        st.markdown(render_report_html(report), unsafe_allow_html=True)

        # VIEW 2: TEXT LOG
        elif current_view == "text":
            st.markdown("""
                <div style='text-align:center; margin-bottom:40px;'>
                    <h1 style='font-size:3rem; margin:0;'>TEXT <span style='color:#f85149'>AUTOPSY</span></h1>
                    <p style='color:#8b949e;'>Detailed Trade Logging</p>
                </div>
            """, unsafe_allow_html=True)
            
            with st.form("text_audit"):
                c1, c2, c3 = st.columns(3)
                with c1: tick = st.text_input("Ticker", placeholder="$NVDA")
                with c2: pos = st.selectbox("Position", ["Long (Buy)", "Short (Sell)"])
                with c3: tf = st.selectbox("Timeframe", ["Scalp", "Day Trade", "Swing"])
                c4, c5, c6 = st.columns(3)
                with c4: ent = st.number_input("Entry", min_value=0.0)
                with c5: ex = st.number_input("Exit", min_value=0.0)
                with c6: stp = st.number_input("Stop", min_value=0.0)
                setup = st.text_area("Setup Details")
                exit_rsn = st.text_area("Exit Reason")
                if st.form_submit_button("Run Analysis"):
                    my_rules = get_user_rules(user)
                    prompt = f"Audit Trade. Ticker: {tick}, Pos: {pos}, TF: {tf}, Entry: {ent}, Exit: {ex}, Stop: {stp}, Setup: {setup}, Exit Reason: {exit_rsn}. Rules: {my_rules}. Output JSON."
                    messages = [{"role": "user", "content": prompt}]
                    with st.spinner("Analyzing..."):
                        raw = run_scientific_analysis(messages, mode="text")
                        report = parse_scientific_report(raw)
                        save_to_lab_records(user, report)
                        st.markdown(render_report_html(report), unsafe_allow_html=True)

        # VIEW 3: VAULT
        elif current_view == "vault":
            st.markdown("""
                <div style='text-align:center; margin-bottom:40px;'>
                    <h1 style='font-size:3rem; margin:0;'>DATA <span style='color:#f85149'>VAULT</span></h1>
                    <p style='color:#8b949e;'>Historical Performance Records</p>
                </div>
            """, unsafe_allow_html=True)
            
            if supabase:
                hist = supabase.table("trades").select("*").eq("user_id", user).order("created_at", desc=True).execute().data
                if hist: st.dataframe(pd.DataFrame(hist), use_container_width=True)
                else: st.info("No records found in the vault.")
            else:
                st.info("Data Vault unavailable (Database not connected).")
        
        st.markdown('</div>', unsafe_allow_html=True)
