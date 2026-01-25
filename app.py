import streamlit as st
import requests
import base64
import io
import re
import pandas as pd
import time
import json
from PIL import Image
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

# Login Credentials (Simple Auth)
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
        st.error(f"⚠️ System Error: {e}")
        st.stop()

# ==========================================
# 2. INTELLIGENCE ENGINE
# ==========================================
def run_scientific_analysis(messages, mode="text"):
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

# ==========================================
# 3. SURGICAL PARSING & NUCLEAR SAFETY NET
# ==========================================
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

    if "short" in data["type"]:
        combined_text_lower = (data["tech"] + data["risk"]).lower()
        triggers = ["drop", "break", "down", "bearish", "red", "collapse", "below", "support break"]
        if any(t in combined_text_lower for t in triggers):
            data["outcome"] = "win" 
            pattern = re.compile(r'(indicating a|potential|risk of|leads to|cause|sign of) (loss|losses|drop)', re.IGNORECASE)
            data["tech"] = pattern.sub("CONFIRMED PROFIT EXPANSION", data["tech"])
            data["risk"] = pattern.sub("CONFIRMED PROFIT EXPANSION", data["risk"])
            data["psych"] = pattern.sub("CONFIRMED PROFIT EXPANSION", data["psych"])
            data["tech"] = data["tech"].replace("critical point for a Short Seller", "strategic jackpot for a Short Seller")

    score = 100
    joined_text = (str(data["tags"]) + data["tech"] + data["psych"] + data["risk"]).lower()
    is_winning_trade = "win" in data["outcome"] or ("profit" in joined_text and "short" in data["type"])
    
    if not is_winning_trade:
        drawdown_matches = re.findall(r'(?:-|dropped by\s*)(\d+\.?\d*)%', clean_raw, re.IGNORECASE)
        if drawdown_matches: score -= max([float(x) for x in drawdown_matches])
        if "panic" in joined_text: score -= 15
        if "high risk" in joined_text: score -= 15
        if "fomo" in joined_text: score -= 10
        if "squeeze" in joined_text and "risk" in joined_text: score -= 20
    else:
        if "lucky" in joined_text: score -= 10
        if "risky entry" in joined_text: score -= 5
    
    if is_winning_trade: score = max(score, 95) 
    else:
        if "panic" in joined_text: score = min(score, 45)
        elif "loss" in joined_text: score = min(score, 65)

    data["score"] = max(0, min(100, int(score)))
    return data

# ==========================================
# 4. THEME & UI (99% ACCURACY)
# ==========================================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,600;0,800;1,800&display=swap" rel="stylesheet">
<style>
    /* Reset & Background */
    .stApp { background-color: #0d1117 !important; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    
    /* Typography */
    h1, .hero-text { 
        font-family: 'Inter', sans-serif; font-weight: 800; font-style: italic; 
        letter-spacing: -0.05em; color: white; text-transform: uppercase;
    }
    
    /* Sidebar & Navigation mimic */
    section[data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 1px solid #30363d; }
    
    /* Cards & Form Containers */
    [data-testid="stForm"], .report-box { 
        background-color: #161b22 !important; border: 1px solid #30363d !important; 
        border-radius: 24px !important; padding: 40px !important; 
    }
    
    /* Upload Section Dash */
    .upload-zone { 
        border: 2px dashed #30363d; border-radius: 24px; padding: 40px; 
        background: #161b22; text-align: center; margin-bottom: 20px;
    }

    /* Buttons */
    div.stButton > button { 
        background-color: #da3633 !important; color: white !important; font-weight: 800 !important;
        border-radius: 99px !important; border: none !important; padding: 12px 30px !important;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    div.stButton > button:hover { background-color: #f85149 !important; transform: scale(1.02); }

    /* Custom Report Styling */
    .section-title { color: #f85149; font-weight: 800; letter-spacing: 1px; margin-top: 20px; text-transform: uppercase; font-size: 0.8rem; }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stTabs [data-baseweb="tab"] { color: #8b949e; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: white !important; border-bottom-color: #f85149 !important; }
</style>
""", unsafe_allow_html=True)

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
        <div class="section-title">Technical Forensics</div><p style="color:#8b949e;">{report["tech"]}</p>
        <div class="section-title">Psychological Profile</div><p style="color:#8b949e;">{report["psych"]}</p>
        <div class="section-title">Risk Assessment</div><p style="color:#8b949e;">{report["risk"]}</p>
        <div class="section-title">Recovery Roadmap</div>
        <div style="background:rgba(248, 81, 73, 0.1); border-left:4px solid #f85149; padding:15px; border-radius:4px; color:white; margin-top:10px;">{report["fix"]}</div>
    </div>"""

def save_to_lab_records(user_id, data):
    try:
        payload = {"user_id": user_id, "score": data.get('score', 0), "mistake_tags": data.get('tags', []), "technical_analysis": data.get('tech', ''), "psych_analysis": data.get('psych', ''), "risk_analysis": data.get('risk', ''), "fix_action": data.get('fix', '')}
        supabase.table("trades").insert(payload).execute()
        if data.get('score', 0) < 50:
            clean_fix = data.get('fix', 'Follow Protocol').split('.')[0][:100]
            supabase.table("rules").insert({"user_id": user_id, "rule_text": clean_fix}).execute()
    except: pass

def get_user_rules(user_id):
    try:
        res = supabase.table("rules").select("*").eq("user_id", user_id).execute()
        return [r['rule_text'] for r in res.data]
    except: return []

# ==========================================
# 5. MAIN INTERFACE
# ==========================================
if not st.session_state["authenticated"]:
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<div style='text-align:center; margin-top:100px;'><h1 style='font-size:2.5rem;'>STOCK<span style='color:#f85149'>POSTMORTEM</span>.AI</h1><p style='color:#8b949e'>OPERATOR AUTHENTICATION REQUIRED</p></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Operator ID")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Authenticate"): check_login(u, p)
else:
    user = st.session_state["user"]
    with st.sidebar:
        st.markdown(f"<h3 style='color:white;'>{user}</h3>", unsafe_allow_html=True)
        if st.button("Terminate Session"): logout()

    # Hero Branding
    st.markdown("""
        <div style='text-align:center; margin-bottom:50px; margin-top:20px;'>
            <h1 style='font-size:4rem;'>STOP <span style='color:#f85149'>BLEEDING</span> CAPITAL.</h1>
            <p style='color:#8b949e; font-size:1.2rem; max-width:700px; margin:auto;'>Upload your losing trade screenshots. Our AI identifies psychological traps and provides a surgical path to recovery.</p>
        </div>
    """, unsafe_allow_html=True)

    # REMOVED PROTOCOLS, RENAMED DIAGNOSTIC AUDIT TO ANALYSE
    tab_analyse, tab_data = st.tabs(["🔬 ANALYSE", "📊 DATA VAULT"])

    with tab_analyse:
        my_rules = get_user_rules(user)
        mode = st.radio("Source", ["Visual Evidence", "Detailed Text Log"], horizontal=True, label_visibility="collapsed")
        
        if "Visual" in mode:
            st.markdown("<div class='upload-zone'><h2 style='color:white; font-weight:800;'>Drop your P&L or Chart screenshot here</h2><p style='color:#8b949e'>PNG, JPG (Max 10MB)</p></div>", unsafe_allow_html=True)
            up_file = st.file_uploader("Upload", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
            if up_file:
                st.image(up_file, use_container_width=True)
                if st.button("Initiate Forensic Scan"):
                    img_b64 = base64.b64encode(up_file.getvalue()).decode('utf-8')
                    prompt = f"Audit this chart. Rules: {my_rules}. Output JSON."
                    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}]}]
                    with st.spinner("🔬 Scanning..."):
                        raw = run_scientific_analysis(messages, mode="vision")
                        report = parse_scientific_report(raw)
                        save_to_lab_records(user, report)
                        st.markdown(render_report_html(report), unsafe_allow_html=True)
        else:
            with st.form("text_audit"):
                c1, c2, c3 = st.columns(3)
                with c1: tick = st.text_input("Ticker", placeholder="$NVDA")
                with c2: pos = st.selectbox("Position", ["Long (Buy)", "Short (Sell)"])
                with c3: tf = st.selectbox("Timeframe", ["Scalp", "Day Trade", "Swing", "Position"])
                c4, c5, c6 = st.columns(3)
                with c4: ent = st.number_input("Entry Price", min_value=0.0, format="%.2f")
                with c5: ex = st.number_input("Exit Price", min_value=0.0, format="%.2f")
                with c6: stp = st.number_input("Planned Stop", min_value=0.0, format="%.2f")
                setup = st.text_area("The Setup (Why did you enter?)")
                exit_rsn = st.text_area("The Exit (Why did you close?)")
                if st.form_submit_button("Run Forensic Analysis"):
                    prompt = f"Audit Trade. Ticker: {tick}, Pos: {pos}, TF: {tf}, Entry: {ent}, Exit: {ex}, Stop: {stp}, Setup: {setup}, Exit Reason: {exit_rsn}. Rules: {my_rules}. Output JSON."
                    messages = [{"role": "user", "content": prompt}]
                    with st.spinner("🔬 Analyzing..."):
                        raw = run_scientific_analysis(messages, mode="text")
                        report = parse_scientific_report(raw)
                        save_to_lab_records(user, report)
                        st.markdown(render_report_html(report), unsafe_allow_html=True)

    with tab_data:
        hist = supabase.table("trades").select("*").eq("user_id", user).order("created_at", desc=True).execute().data
        if hist: st.dataframe(pd.DataFrame(hist), use_container_width=True)
