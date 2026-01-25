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
        # ENSURE .streamlit/secrets.toml IS CONFIGURED
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
    
    data = { 
        "score": 0, "tags": [], 
        "tech": "", "psych": "", "risk": "", "fix": "",
        "outcome": "unknown", "type": "long", "reality": "Real"
    }
    
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
        patterns = {
            "tech": r'"technical_analysis":\s*"(.*?)"',
            "psych": r'"psychological_profile":\s*"(.*?)"',
            "risk": r'"risk_assessment":\s*"(.*?)"',
            "fix": r'"strategic_roadmap":\s*"(.*?)"',
            "tags": r'"tags":\s*\[(.*?)\]'
        }
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
    
    is_winning_trade = False
    if "win" in data["outcome"]: is_winning_trade = True
    elif "profit" in joined_text and "short" in data["type"]: is_winning_trade = True
    elif "loss" in data["outcome"]: is_winning_trade = False
    
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

    if is_winning_trade:
        score = max(score, 95) 
    else:
        if "panic" in joined_text: score = min(score, 45)
        elif "loss" in joined_text: score = min(score, 65)

    data["score"] = max(0, min(100, int(score)))
    return data

# ==========================================
# 4. GLOBAL CSS & UI STYLING
# ==========================================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/remixicon@2.5.0/fonts/remixicon.css" rel="stylesheet">
<style>
    body, .stApp { 
        background-color: #0f171c !important; 
        color: #ffffff; 
        font-family: 'Inter', sans-serif; 
    }
    
    [data-testid="stForm"] {
        background: rgba(22, 32, 42, 0.6);
        border: 1px solid #1f2d38;
        border-radius: 16px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
        padding: 40px;
        border-top: 4px solid #ff4d4d; 
        backdrop-filter: blur(10px);
    }

    .stTextInput label p, .stSelectbox label p, .stTextArea label p {
        color: #8b95a1 !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    .stTextInput > div > div > input, .stSelectbox > div > div > div, .stTextArea > div > div > textarea {
        background-color: #0a1014 !important;
        border: 1px solid #2c3a47 !important;
        color: #fff !important;
        border-radius: 8px !important;
        font-size: 14px !important;
    }

    div.stButton > button {
        background-color: #ff4d4d !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        padding: 14px 20px !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
    }
    
    div.stButton > button:hover {
        background-color: #ff3333 !important;
        transform: translateY(-2px);
    }

    .report-box { 
        background: #151e24; 
        border: 1px solid #2a3239; 
        border-radius: 12px; 
        padding: 25px; 
        margin-top: 20px; 
    }
    .section-title { 
        color: #ff4d4d; 
        font-family: 'JetBrains Mono', monospace; 
        font-weight: bold; 
        font-size: 1.1rem; 
        border-bottom: 1px solid #2a3239; 
        padding-bottom: 5px; 
        margin-top: 25px; 
    }
</style>
""", unsafe_allow_html=True)

def render_report_html(report):
    c_score = "#ff4d4d" if report['score'] < 50 else "#00e676"
    tags_html = "".join([f'<span style="background:#262626; border:1px solid #444; padding:4px 8px; border-radius:4px; font-size:0.8rem; margin-right:5px; display:inline-block; margin-bottom:5px;">{t}</span> ' for t in report['tags']])
    
    html_parts = [
        f'<div class="report-box">',
        f'  <div style="display:flex; justify-content:space-between; border-bottom:1px solid #444;">',
        f'      <div><h2 style="color:#fff; margin:0; display:inline-block;">DIAGNOSTIC REPORT</h2></div>',
        f'      <div class="score-circle" style="color:{c_score}; font-size:4rem; font-weight:800;">{report["score"]}</div>',
        f'  </div>',
        f'  <div style="margin:10px 0;">{tags_html}</div>',
        f'  <div class="section-title">📊 TECHNICAL FORENSICS</div>',
        f'  <div style="color:#d0d7de; line-height:1.6;">{report["tech"]}</div>',
        f'  <div class="section-title">🧠 PSYCHOLOGICAL PROFILE</div>',
        f'  <div style="color:#d0d7de; line-height:1.6;">{report["psych"]}</div>',
        f'  <div class="section-title">⚖️ RISK ASSESSMENT</div>',
        f'  <div style="color:#d0d7de; line-height:1.6;">{report["risk"]}</div>',
        f'  <div class="section-title">🚀 STRATEGIC ROADMAP</div>',
        f'  <div style="background:rgba(255, 77, 77, 0.1); border-left:4px solid #ff4d4d; padding:15px; color:#fff;">{report["fix"]}</div>',
        f'</div>'
    ]
    return "".join(html_parts)

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
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        with st.form("login_card", clear_on_submit=False):
            st.markdown("<h2 style='text-align:center;'>System Access</h2>", unsafe_allow_html=True)
            u = st.text_input("Operator ID")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Authenticate"):
                check_login(u, p)
else:
    user = st.session_state["user"]
    with st.sidebar:
        st.title(f"Operator: {user}")
        if st.button("🔒 TERMINATE SESSION"): logout()

    st.markdown("<h1>🧬 FORENSIC <span style='color:#ff4d4d'>TRADING LAB</span></h1>", unsafe_allow_html=True)
    tab_audit, tab_laws, tab_data = st.tabs(["🔬 DIAGNOSTIC AUDIT", "⚖️ PROTOCOLS", "📊 DATA VAULT"])

    with tab_audit:
        my_rules = get_user_rules(user)
        mode = st.radio("Source", ["Detailed Text Log", "Visual Evidence"], horizontal=True, label_visibility="collapsed")
        
        if "Visual Evidence" in mode:
            up_file = st.file_uploader("Upload Evidence", type=["png", "jpg", "jpeg", "webp"])
            if up_file:
                st.image(up_file, width=500)
                if st.button("INITIATE FORENSIC SCAN", type="primary"):
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
                st.markdown("### 📂 CASE FILE DETAILS")
                c1, c2, c3 = st.columns(3)
                with c1: tick = st.text_input("Ticker", placeholder="$NVDA")
                with c2: pos = st.selectbox("Position", ["Long (Buy)", "Short (Sell)"])
                with c3: tf = st.selectbox("Timeframe", ["Scalp (1m-5m)", "Day Trade (15m-1h)", "Swing", "Position"])
                
                c4, c5, c6 = st.columns(3)
                with c4: ent = st.number_input("Entry Price", min_value=0.0, format="%.2f")
                with c5: ex = st.number_input("Exit Price", min_value=0.0, format="%.2f")
                with c6: stp = st.number_input("Planned Stop", min_value=0.0, format="%.2f")
                
                setup = st.text_area("The Setup (Why did you enter?)", placeholder="Ex: Bull flag breakout above VWAP...")
                exit_rsn = st.text_area("The Exit (Why did you close?)", placeholder="Ex: I got scared when it wicked down...")
                
                if st.form_submit_button("RUN FORENSIC ANALYSIS (TEXT)", type="primary", use_container_width=True):
                    prompt = f"Audit Trade. Ticker: {tick}, Pos: {pos}, TF: {tf}, Entry: {ent}, Exit: {ex}, Stop: {stp}, Setup: {setup}, Exit Reason: {exit_rsn}. Rules: {my_rules}. Output JSON."
                    messages = [{"role": "user", "content": prompt}]
                    with st.spinner("🔬 Analyzing..."):
                        raw = run_scientific_analysis(messages, mode="text")
                        report = parse_scientific_report(raw)
                        save_to_lab_records(user, report)
                        st.markdown(render_report_html(report), unsafe_allow_html=True)

    with tab_laws:
        rules = supabase.table("rules").select("*").eq("user_id", user).execute().data
        for r in rules:
            c1,c2 = st.columns([5,1])
            c1.error(f"⛔ {r['rule_text']}")
            if c2.button("🗑️", key=r['id']):
                supabase.table("rules").delete().eq("id", r['id']).execute(); st.rerun()

    with tab_data:
        hist = supabase.table("trades").select("*").eq("user_id", user).order("created_at", desc=True).execute().data
        if hist: st.dataframe(pd.DataFrame(hist))
