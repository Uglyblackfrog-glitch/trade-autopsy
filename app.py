import streamlit as st
import requests
import base64
import io
import re
import pandas as pd
import time
from PIL import Image
from supabase import create_client, Client

# ==========================================
# 0. CONFIGURATION & SETUP
# ==========================================
st.set_page_config(
    page_title="StockPostmortem.ai", 
    page_icon="🧬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        st.error("⚠️ Access Denied.")

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
        "temperature": 0.3, 
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
# 3. PARSING & DISPLAY LOGIC (FINAL POLISH)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    body, .stApp { background-color: #0E1117 !important; color: #E0E0E0; font-family: 'Inter', sans-serif; }
    .report-box { background: #161B22; border: 1px solid #30363D; border-radius: 12px; padding: 25px; margin-top: 20px; }
    .section-title { color: #58A6FF; font-family: 'JetBrains Mono', monospace; font-weight: bold; font-size: 1.1rem; border-bottom: 1px solid #30363D; padding-bottom: 5px; margin-top: 25px; margin-bottom: 10px; }
    .score-circle { font-size: 4rem; font-weight: 800; line-height: 1; }
    button[kind="primary"] { background: #238636 !important; border: none; font-family: 'JetBrains Mono', monospace; }
</style>
""", unsafe_allow_html=True)

def get_user_rules(user_id):
    try:
        res = supabase.table("rules").select("*").eq("user_id", user_id).execute()
        return [r['rule_text'] for r in res.data]
    except: return []

def parse_scientific_report(text):
    # Remove clutter that confuses the parser
    text = text.replace("**", "").replace("##", "").replace("(Detailed paragraph)", "").replace("(Deep psychoanalysis)", "").strip()
    
    sections = { 
        "score": 0, 
        "tags": [], 
        "tech": "Analysis failed.", 
        "psych": "Analysis failed.", 
        "risk": "Analysis failed.", 
        "fix": "Analysis failed." 
    }
    
    # 1. Extract Score
    score_match = re.search(r'(?:\[SCORE\]|Score:?)\s*(\d+)', text, re.IGNORECASE)
    if score_match: sections['score'] = int(score_match.group(1))

    # 2. Extract Tags (Cleaned)
    tags_match = re.search(r'(?:\[TAGS\]|Tags:?)(.*?)(?=\[|\n[A-Z]|$)', text, re.DOTALL | re.IGNORECASE)
    if tags_match:
        raw_tags = tags_match.group(1)
        # Remove parentheses and split by commas
        clean_tags_str = re.sub(r'[\(\)]', '', raw_tags) 
        sections['tags'] = [t.strip() for t in clean_tags_str.split(',') if t.strip() and len(t) < 30]

    # 3. Extract Sections - STRICT PATTERNS
    patterns = {
        "tech": r"(?:\[TECHNICAL FORENSICS\]|Technical Forensics:)(.*?)(?=\[PSYCH|\[RISK|\[STRAT|\[SCORE|Psychological|Risk Assessment|$)",
        "psych": r"(?:\[PSYCHOLOGICAL PROFILE\]|Psychological Profile:)(.*?)(?=\[RISK|\[STRAT|\[SCORE|Risk Assessment|Strategic Roadmap|$)",
        "risk": r"(?:\[RISK ASSESSMENT\]|Risk Assessment:)(.*?)(?=\[STRAT|\[SCORE|Strategic Roadmap|$)",
        "fix": r"(?:\[STRATEGIC ROADMAP\]|Strategic Roadmap:)(.*?)(?=\[SCORE|\[TAGS|$)"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            clean_content = match.group(1).strip().replace("\n", "<br>")
            sections[key] = clean_content
            
    return sections

def render_report_html(report):
    # "List-Join" method to prevent indentation errors
    c_score = "#ff4d4d" if report['score'] < 50 else "#00e676"
    
    tags_html = "".join([
        f'<span style="background:#262626; border:1px solid #444; padding:4px 8px; border-radius:4px; font-size:0.8rem; margin-right:5px; display:inline-block; margin-bottom:5px;">{t}</span>' 
        for t in report['tags']
    ])
    
    html_parts = [
        f'<div class="report-box">',
        f'  <div style="display:flex; justify-content:space-between; border-bottom:1px solid #444;">',
        f'      <h2 style="color:#fff; margin:0;">DIAGNOSTIC REPORT</h2>',
        f'      <div class="score-circle" style="color:{c_score};">{report["score"]}</div>',
        f'  </div>',
        f'  <div style="margin:10px 0;">{tags_html}</div>',
        
        f'  <div class="section-title">📊 TECHNICAL FORENSICS</div>',
        f'  <div style="color:#d0d7de; line-height:1.6;">{report["tech"]}</div>',
        
        f'  <div class="section-title">🧠 PSYCHOLOGICAL PROFILE</div>',
        f'  <div style="color:#d0d7de; line-height:1.6;">{report["psych"]}</div>',
        
        f'  <div class="section-title">⚖️ RISK ASSESSMENT</div>',
        f'  <div style="color:#d0d7de; line-height:1.6;">{report["risk"]}</div>',
        
        f'  <div class="section-title">🚀 STRATEGIC ROADMAP</div>',
        f'  <div style="background:rgba(46, 160, 67, 0.1); border-left:4px solid #2ea043; padding:15px; color:#fff;">{report["fix"]}</div>',
        f'</div>'
    ]
    
    return "".join(html_parts)

def save_to_lab_records(user_id, data):
    payload = {
        "user_id": user_id,
        "score": data.get('score', 0),
        "mistake_tags": data.get('tags', []),
        "technical_analysis": data.get('tech', ''),
        "psych_analysis": data.get('psych', ''),
        "risk_analysis": data.get('risk', ''),
        "fix_action": data.get('fix', '')
    }
    try:
        supabase.table("trades").insert(payload).execute()
        if data.get('score', 0) < 50:
            clean_fix = data.get('fix', 'Follow Protocol').split('.')[0][:100]
            supabase.table("rules").insert({"user_id": user_id, "rule_text": clean_fix}).execute()
            st.toast("🧬 Violation Recorded.")
    except Exception as e:
        st.error(f"DB Error: {e}")

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
if not st.session_state["authenticated"]:
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><br><h1 style='text-align:center'>🧬 STOCK<br>POSTMORTEM</h1>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Investigator ID"); p = st.text_input("Access Key", type="password")
            if st.form_submit_button("AUTHENTICATE", type="primary", use_container_width=True): check_login(u, p)
else:
    user = st.session_state["user"]
    with st.sidebar:
        st.title(f"Operator: {user}")
        if st.button("🔒 TERMINATE SESSION"): logout()

    st.markdown("<h1>🧬 FORENSIC <span style='color:#58A6FF'>TRADING LAB</span></h1>", unsafe_allow_html=True)
    
    tab_audit, tab_laws, tab_data = st.tabs(["🔬 DIAGNOSTIC AUDIT", "⚖️ PROTOCOLS", "📊 DATA VAULT"])

    with tab_audit:
        my_rules = get_user_rules(user)
        if my_rules:
            with st.expander(f"⚠️ ACTIVE PROTOCOLS ({len(my_rules)})"):
                for r in my_rules: st.markdown(f"🔴 {r}")

        mode = st.radio("Input Source", ["Detailed Text Log", "Visual Evidence (Chart/P&L)"], horizontal=True, label_visibility="collapsed")
        
        # --- VISION ANALYSIS ---
        if "Visual Evidence" in mode:
            st.info("Supported: Candlestick Charts OR P&L Dashboards")
            up_file = st.file_uploader("Upload Evidence", type=["png", "jpg", "jpeg"])
            
            if up_file:
                st.image(up_file, width=500)
                if st.button("INITIATE FORENSIC SCAN", type="primary"):
                    image = Image.open(up_file)
                    if image.mode != 'RGB': image = image.convert('RGB')
                    buf = io.BytesIO()
                    image.save(buf, format="JPEG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    
                    # STRICT PROMPT TO PREVENT "PARROTING"
                    prompt = f"""
                    You are Dr. Market, a Chief Investment Officer.
                    Your Task: Audit this image (Chart or P&L).
                    
                    USER RULES: {my_rules}

                    IF P&L DASHBOARD:
                    1. [TECHNICAL FORENSICS]: Extract the data. Calculate the drawdown %. Identify the "Toxic Asset" (biggest loser). 
                    2. [PSYCHOLOGICAL PROFILE]: Diagnose the behavior (e.g., "Disposition Effect" if holding losers, "Gambling" if portfolio is red).
                    3. [SCORE]: If Unrealized Loss > 15%, Score MUST be < 30.
                    
                    IF CHART:
                    1. [TECHNICAL FORENSICS]: Analyze Market Structure, Liquidity Sweeps, and Volume.
                    2. [SCORE]: Grade the setup quality (0-100).

                    STRICT OUTPUT FORMAT (Clean text only, NO extra instructions in output):
                    [SCORE] 0-100
                    [TAGS] Tag1, Tag2, Tag3
                    [TECHNICAL FORENSICS] ...
                    [PSYCHOLOGICAL PROFILE] ...
                    [RISK ASSESSMENT] ...
                    [STRATEGIC ROADMAP] ...
                    """
                    
                    messages = [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                        ]
                    }]
                    
                    with st.spinner("🔬 Running Spectral Analysis..."):
                        try:
                            raw = run_scientific_analysis(messages, mode="vision")
                            report = parse_scientific_report(raw)
                            save_to_lab_records(user, report)
                            
                            final_html = render_report_html(report)
                            st.markdown(final_html, unsafe_allow_html=True)
                            
                        except Exception as e: st.error(str(e))

        # --- TEXT LOG ANALYSIS ---
        else:
            with st.form("text_audit"):
                c1,c2 = st.columns(2)
                with c1: tick = st.text_input("Ticker", "BTC/USD")
                with c2: context = st.text_area("Context/Notes")
                c1,c2,c3 = st.columns(3)
                with c1: ent = st.number_input("Entry", 0.0)
                with c2: ex = st.number_input("Exit", 0.0)
                with c3: stp = st.number_input("Stop", 0.0)
                
                if st.form_submit_button("SUBMIT", type="primary"):
                    math_block = f"Entry: {ent}, Exit: {ex}, Stop: {stp}"
                    prompt = f"""
                    You are Dr. Market. Audit this trade text log. Rules: {my_rules}.
                    Data: {math_block}. Context: {context}.
                    STRICT OUTPUT FORMAT (No Markdown headers):
                    [SCORE] ...
                    [TAGS] Tag1, Tag2, Tag3
                    [TECHNICAL FORENSICS] ...
                    [PSYCHOLOGICAL PROFILE] ...
                    [RISK ASSESSMENT] ...
                    [STRATEGIC ROADMAP] ...
                    """
                    messages = [{"role": "user", "content": prompt}]
                    
                    with st.spinner("Computing..."):
                        try:
                            raw = run_scientific_analysis(messages, mode="text")
                            report = parse_scientific_report(raw)
                            save_to_lab_records(user, report)
                            
                            final_html = render_report_html(report)
                            st.markdown(final_html, unsafe_allow_html=True)
                        except Exception as e: st.error(str(e))

    with tab_laws:
        rules = supabase.table("rules").select("*").eq("user_id", user).execute().data
        for r in rules:
            c1,c2 = st.columns([5,1])
            c1.error(f"⛔ {r['rule_text']}")
            if c2.button("🗑️", key=r['id']):
                supabase.table("rules").delete().eq("id", r['id']).execute(); st.rerun()

    with tab_data:
        hist = supabase.table("trades").select("*").eq("user_id", user).order("created_at", desc=True).execute().data
        if hist: st.dataframe(pd.DataFrame(hist)[['created_at', 'score', 'mistake_tags', 'fix_action']])
