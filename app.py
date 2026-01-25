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
    initial_sidebar_state="collapsed" # Collapsed by default for cleaner login
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

    # ☢️ NUCLEAR LOGIC PATCH (Updated with Trigger List)
    if "short" in data["type"]:
        combined_text_lower = (data["tech"] + data["risk"]).lower()
        # Updated Trigger List per our conversation
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
        # Regex updated to catch "dropped by 66%"
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
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    
    /* MAIN BACKGROUND */
    body, .stApp { 
        background-color: #0f171c !important; 
        color: #E0E0E0; 
        font-family: 'Inter', sans-serif; 
    }
    
    /* REPORT BOXES */
    .report-box { 
        background: #151e24; 
        border: 1px solid #2a3239; 
        border-radius: 12px; 
        padding: 25px; 
        margin-top: 20px; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    /* TITLES & HEADERS */
    .section-title { 
        color: #ff4d4d; /* ACCENT COLOR */
        font-family: 'JetBrains Mono', monospace; 
        font-weight: bold; 
        font-size: 1.1rem; 
        border-bottom: 1px solid #2a3239; 
        padding-bottom: 5px; 
        margin-top: 25px; 
        margin-bottom: 10px; 
    }
    
    /* BUTTONS */
    div.stButton > button {
        background-color: #ff4d4d !important;
        color: white !important;
        border: none !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        background-color: #ff1a1a !important;
        box-shadow: 0 0 10px rgba(255, 77, 77, 0.4);
    }
    
    /* INPUT FIELDS */
    .stTextInput > div > div > input {
        background-color: #151e24 !important;
        color: #fff !important;
        border: 1px solid #2a3239 !important;
        border-radius: 6px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #ff4d4d !important;
        box-shadow: 0 0 5px rgba(255, 77, 77, 0.2);
    }
    
    /* LOGIN CONTAINER */
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 40px;
        background: #151e24;
        border: 1px solid #2a3239;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .login-logo {
        font-size: 4rem;
        margin-bottom: 10px;
    }
    .login-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.5rem;
        font-weight: 700;
        color: #fff;
        margin-bottom: 5px;
        letter-spacing: -1px;
    }
    .login-subtitle {
        color: #ff4d4d;
        font-size: 0.9rem;
        font-weight: 600;
        letter-spacing: 2px;
        margin-bottom: 30px;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

def render_report_html(report):
    c_score = "#ff4d4d" if report['score'] < 50 else "#00e676"
    
    tags_html = "".join([
        f'<span style="background:#262626; border:1px solid #444; padding:4px 8px; border-radius:4px; font-size:0.8rem; margin-right:5px; display:inline-block; margin-bottom:5px;">{t}</span> ' 
        for t in report['tags']
    ])
    
    direction_badge = ""
    if "short" in report.get("type", ""):
        direction_badge = '<span style="background:#8b0000; color:#fff; padding:2px 6px; border-radius:3px; font-size:0.7rem; margin-left:10px; font-family:monospace;">SHORT POS</span>'
    elif "long" in report.get("type", ""):
        direction_badge = '<span style="background:#006400; color:#fff; padding:2px 6px; border-radius:3px; font-size:0.7rem; margin-left:10px; font-family:monospace;">LONG POS</span>'

    reality_warning = ""
    if "simulated" in str(report.get("reality", "")).lower() or "fictional" in str(report.get("reality", "")).lower():
        reality_warning = '<div style="background:#3d1818; color:#ff8b8b; padding:10px; border-radius:5px; margin-bottom:15px; font-size:0.9rem;">⚠️ <b>SIMULATION DETECTED:</b> This asset appears to be fictional or simulated. Market data may not match real-world feeds.</div>'

    html_parts = [
        f'<div class="report-box">',
        f'{reality_warning}',
        f'  <div style="display:flex; justify-content:space-between; border-bottom:1px solid #444;">',
        f'      <div><h2 style="color:#fff; margin:0; display:inline-block;">DIAGNOSTIC REPORT</h2>{direction_badge}</div>',
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
            st.toast("🧬 Violation Recorded & Rule Added.")
    except: pass

def get_user_rules(user_id):
    try:
        res = supabase.table("rules").select("*").eq("user_id", user_id).execute()
        return [r['rule_text'] for r in res.data]
    except: return []

# ==========================================
# 5. MAIN INTERFACE
# ==========================================

# 🔒 LOGIN PAGE (New Custom UI)
if not st.session_state["authenticated"]:
    # Using columns to center the login box perfectly
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        st.markdown("""
        <div class="login-container">
            <div class="login-logo">🧬</div>
            <div class="login-title">STOCK POSTMORTEM</div>
            <div class="login-subtitle">FORENSIC TRADING INTELLIGENCE</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login"):
            u = st.text_input("OPERATOR ID", placeholder="Enter your ID")
            p = st.text_input("ACCESS KEY", type="password", placeholder="Enter your Key")
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("INITIATE SESSION", use_container_width=True)
            
            if submitted:
                check_login(u, p)
                
    st.markdown("""
    <div style="text-align:center; margin-top:50px; color:#444; font-size:0.8rem;">
        SECURE CONNECTION • ENCRYPTED VIA SUPABASE • VERSION 2.4.1
    </div>
    """, unsafe_allow_html=True)

# 🔓 DASHBOARD PAGE
else:
    user = st.session_state["user"]
    with st.sidebar:
        st.title(f"Operator: {user}")
        st.markdown("---")
        if st.button("🔒 TERMINATE SESSION"): logout()

    # Dashboard Header
    st.markdown("""
    <div style="border-bottom: 1px solid #2a3239; padding-bottom: 20px; margin-bottom: 20px;">
        <h1 style="margin:0;">🧬 FORENSIC <span style='color:#ff4d4d'>TRADING LAB</span></h1>
        <p style="color:#666; margin:0;">Active Session // Monitoring Real-Time Diagnostics</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_audit, tab_laws, tab_data = st.tabs(["🔬 DIAGNOSTIC AUDIT", "⚖️ PROTOCOLS", "📊 DATA VAULT"])

    # --- TAB 1: AUDIT ---
    with tab_audit:
        my_rules = get_user_rules(user)
        if my_rules:
            with st.expander(f"⚠️ ACTIVE PROTOCOLS ({len(my_rules)})"):
                for r in my_rules: st.markdown(f"🔴 {r}")

        mode = st.radio("Input Source", ["Detailed Text Log", "Visual Evidence (Chart/P&L)"], horizontal=True, label_visibility="collapsed")
        
        # --- VISION ANALYSIS ---
        if "Visual Evidence" in mode:
            st.info("Supported: Candlestick Charts, P&L Dashboards (PNG, JPG, WEBP)")
            up_file = st.file_uploader("Upload Evidence", type=["png", "jpg", "jpeg", "webp"])
            
            if up_file:
                st.image(up_file, width=500)
                if st.button("INITIATE FORENSIC SCAN", type="primary"):
                    image = Image.open(up_file)
                    if image.mode != 'RGB': image = image.convert('RGB')
                    buf = io.BytesIO()
                    image.save(buf, format="JPEG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    
                    # === THE "ANGRY MANAGER" PROMPT (STEP 1) ===
                    prompt = f"""
                    You are Dr. Market, a Chief Investment Officer.
                    Audit this image (Chart or P&L). Rules: {my_rules}.
                    
                    CRITICAL PHYSICS ENGINE (DO NOT FAIL THIS):
                    1. IDENTIFY DIRECTION: Look for "Open Short", "Sell", "Put" vs "Buy", "Long".
                    
                    2. APPLY THE LAWS OF PHYSICS:
                       - IF SHORT: 
                         - RED Candle / Price Drop / Support Break = MASSIVE PROFIT (WIN).
                         - GREEN Candle / Price Rally = LOSS (DANGER).
                         - ⚠️ NEVER say "Support Break is a risk" to a Short Seller. It is a JACKPOT.
                         
                       - IF LONG:
                         - GREEN Candle / Price Up = PROFIT (WIN).
                         - RED Candle / Price Down = LOSS.
                    
                    3. REALITY CHECK: Is the ticker (e.g. OmniVerse, Solaris) real or simulated?
                    
                    OUTPUT FORMAT: JSON ONLY (No Markdown).
                    {{
                        "trade_direction": "Long" or "Short",
                        "outcome": "Win" or "Loss",
                        "score": 100,
                        "tags": ["Tag1", "Tag2"], 
                        "technical_analysis": "Text...",
                        "psychological_profile": "Text...",
                        "risk_assessment": "Text...",
                        "strategic_roadmap": "Text...",
                        "reality_check": "Real or Simulated"
                    }}
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
                            report = parse_scientific_report(raw) # Uses Nuclear Logic
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
                    You are Dr. Market. Audit this trade log. Rules: {my_rules}.
                    Data: {math_block}. Context: {context}.
                    OUTPUT FORMAT: JSON ONLY (No Markdown).
                    {{
                        "trade_direction": "Long" or "Short", 
                        "outcome": "Win" or "Loss",
                        "score": 100,
                        "tags": ["Mistake1", "Mistake2"],
                        "technical_analysis": "Text...",
                        "psychological_profile": "Text...",
                        "risk_assessment": "Text...",
                        "strategic_roadmap": "Text...",
                        "reality_check": "Real"
                    }}
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

    # --- TAB 2 & 3 ---
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
