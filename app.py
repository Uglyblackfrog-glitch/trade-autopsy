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
# 0. AUTH & CONFIG
# ==========================================
st.set_page_config(page_title="StockPostmortem.ai", page_icon="🩸", layout="wide")

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
        st.error("Incorrect credentials.")

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
    except Exception as e:
        st.error(f"⚠️ Config Error: {e}")
        st.stop()

# ==========================================
# 2. THE NEW INTELLIGENCE ENGINE
# ==========================================

def run_smart_inference(messages, mode="text"):
    """
    Routes traffic to the correct specialist model.
    """
    api_url = "https://router.huggingface.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
    
    # SELECTION LOGIC:
    if mode == "text":
        model_id = "Qwen/Qwen2.5-72B-Instruct"  # Logic Expert
    else:
        model_id = "Qwen/Qwen2.5-VL-7B-Instruct" # Vision Expert (Reads P&L screenshots better)

    payload = {
        "model": model_id,
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.2, # Lower temperature for stricter grading
    }

    # Retry logic
    for attempt in range(3):
        try:
            res = requests.post(api_url, headers=headers, json=payload, timeout=60)
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
# 3. PARSERS & HELPERS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;800&display=swap');
    body, .stApp { background-color: #050505 !important; font-family: 'Space Grotesk', sans-serif !important; color: #e2e8f0; }
    .report-container { background: #0d1117; border: 1px solid #30363d; border-radius: 12px; padding: 2rem; margin-top: 20px; }
    .analysis-card { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 15px; margin-bottom: 10px; border-left: 4px solid #555; }
    button[kind="primary"] { background-color: #ff4d4d !important; color: white !important; font-weight: bold; border:none; }
</style>
""", unsafe_allow_html=True)

def get_user_rules(user_id):
    try:
        res = supabase.table("rules").select("*").eq("user_id", user_id).execute()
        return [r['rule_text'] for r in res.data]
    except: return []

def parse_report(text):
    text = text.replace("**", "").replace("##", "")
    sections = { "score": 0, "tags": [], "tech": "N/A", "psych": "N/A", "risk": "N/A", "fix": "N/A" }
    
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
    for k, p in patterns.items():
        m = re.search(p, text, re.DOTALL)
        if m: sections[k] = m.group(1).strip()
    return sections

def save_analysis(user_id, data):
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
            clean_fix = data.get('fix', 'Follow process').replace('"', '')
            supabase.table("rules").insert({"user_id": user_id, "rule_text": clean_fix}).execute()
            st.toast("📉 New Rule Added")
    except Exception as e:
        st.error(f"DB Error: {e}")

# ==========================================
# 4. MAIN APP
# ==========================================
if not st.session_state["authenticated"]:
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><br><h1 style='text-align:center'>🩸 STOCKPOSTMORTEM</h1>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.form_submit_button("ENTER", type="primary", use_container_width=True): check_login(u, p)
else:
    user = st.session_state["user"]
    with st.sidebar:
        st.header(f"👤 {user}")
        if st.button("LOGOUT"): logout()

    st.markdown("<h1 style='text-align:center'>STOCK<span style='color:#ff4d4d'>POSTMORTEM</span>.AI</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["🔍 AUDIT", "⚖️ LAWS", "📈 STATS"])

    with t1:
        my_rules = get_user_rules(user)
        if my_rules:
            with st.expander(f"🚨 ACTIVE RULES ({len(my_rules)})"):
                for r in my_rules: st.markdown(f"❌ {r}")

        mode = st.radio("Mode", ["Text Report", "Chart/P&L Vision"], horizontal=True, label_visibility="collapsed")
        
        # --- MODE A: VISION (UPDATED PROMPT) ---
        if "Chart/P&L Vision" in mode:
            up_file = st.file_uploader("Upload Chart or P&L Screenshot", type=["png", "jpg", "jpeg"])
            if up_file:
                st.image(up_file, width=400)
                if st.button("RUN VISION AUDIT", type="primary"):
                    image = Image.open(up_file)
                    if image.mode != 'RGB': image = image.convert('RGB')
                    buf = io.BytesIO()
                    image.save(buf, format="JPEG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    
                    # --- UPDATED PROMPT FOR P&L DETECTION ---
                    prompt = f"""
                    You are a Brutal Hedge Fund Risk Manager.
                    
                    TASK: Analyze the image. It is either a Candle Chart OR a P&L Dashboard.
                    
                    CRITICAL GRADING LOGIC:
                    1. IF P&L DASHBOARD (Unrealized P/L, Holdings, Red Numbers):
                       - If "Unrealized P/L" is negative (Red), Score MUST be under 40.
                       - If Loss is > 20%, Score MUST be under 20.
                       - If "Total Loss" is visible, roast the user for bag-holding.
                    
                    2. IF CANDLE CHART:
                       - Check for technical breakdowns.
                       - If Stop Loss was ignored, Score under 30.

                    User's Active Rules (Check for violations): {my_rules}

                    OUTPUT FORMAT (Strict): 
                    [SCORE] 0-100
                    [TAGS] Tag1, Tag2 (e.g., Bagholding, No Stop Loss)
                    [TECH] (If Chart: Patterns. If P&L: Analyze the % drawdown depth)
                    [PSYCH] (Diagnose the behavior: Denial, Hope, Gambling)
                    [RISK] (Calculate implied risk deviation)
                    [FIX] (One short imperative command)
                    """
                    
                    messages = [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                        ]
                    }]
                    
                    with st.spinner("Analyzing Losses..."):
                        try:
                            raw = run_smart_inference(messages, mode="vision")
                            report = parse_report(raw)
                            save_analysis(user, report)
                            
                            c = "#ef4444" if report['score'] < 50 else "#10b981"
                            st.markdown(f"""
                            <div class="report-container">
                                <div style="display:flex; justify-content:space-between;">
                                    <div><div style="color:#888;">SCORE</div><div style="font-size:3.5rem; font-weight:900; color:{c};">{report['score']}</div></div>
                                </div>
                                <div class="analysis-card" style="border-left-color:#3b82f6"><b>TECH:</b> {report['tech']}</div>
                                <div class="analysis-card" style="border-left-color:#f59e0b"><b>PSYCH:</b> {report['psych']}</div>
                                <div class="analysis-card" style="border-left-color:#ef4444"><b>RISK:</b> {report['risk']}</div>
                                <div class="analysis-card" style="border-left-color:#10b981"><b>FIX:</b> {report['fix']}</div>
                            </div>""", unsafe_allow_html=True)
                        except Exception as e: st.error(str(e))

        # --- MODE B: TEXT ---
        else:
            with st.form("audit"):
                c1,c2,c3 = st.columns(3)
                with c1: tick = st.text_input("Ticker", "SPY")
                with c2: emo = st.selectbox("Emotion", ["Neutral", "FOMO", "Revenge", "Fear"])
                with c3: setup = st.selectbox("Setup", ["Trend", "Reversal", "Breakout"])
                c1,c2,c3 = st.columns(3)
                with c1: ent = st.number_input("Entry", 0.0)
                with c2: ex = st.number_input("Exit", 0.0)
                with c3: stp = st.number_input("Stop", 0.0)
                note = st.text_area("Notes")
                
                if st.form_submit_button("AUDIT", type="primary", use_container_width=True):
                    risk = abs(ent - stp)
                    viol = (ent > stp and ex < stp) or (ent < stp and ex > stp)
                    rm = (ex - ent)/risk if risk > 0 and ent > stp else (ent - ex)/risk if risk > 0 else 0
                    
                    math_data = f"Risk: {risk:.2f} | R-Multiple: {rm:.2f}R | Stop Violation: {viol}"
                    
                    prompt = f"""
                    You are a Ruthless Trading Performance Coach. Rules: {my_rules}.
                    INPUT: {tick}, {emo}, {note}. MATH: {math_data}.
                    LOGIC: If Stop Violation=True -> Score<30. If Revenge -> Score<40.
                    OUTPUT: [SCORE], [TAGS], [TECH], [PSYCH], [RISK], [FIX].
                    """
                    
                    messages = [{"role": "user", "content": prompt}]
                    
                    with st.spinner("Consulting Senior Trader..."):
                        try:
                            raw = run_smart_inference(messages, mode="text")
                            report = parse_report(raw)
                            save_analysis(user, report)
                            
                            c = "#ef4444" if report['score'] < 50 else "#10b981"
                            st.markdown(f"""
                            <div class="report-container">
                                <div style="display:flex; justify-content:space-between;">
                                    <div><div style="color:#888;">SCORE</div><div style="font-size:3.5rem; font-weight:900; color:{c};">{report['score']}</div></div>
                                </div>
                                <div class="analysis-card" style="border-left-color:#3b82f6"><b>TECH:</b> {report['tech']}</div>
                                <div class="analysis-card" style="border-left-color:#f59e0b"><b>PSYCH:</b> {report['psych']}</div>
                                <div class="analysis-card" style="border-left-color:#ef4444"><b>RISK:</b> {report['risk']}</div>
                                <div class="analysis-card" style="border-left-color:#10b981"><b>FIX:</b> {report['fix']}</div>
                            </div>""", unsafe_allow_html=True)
                        except Exception as e: st.error(str(e))

    with t2:
        st.subheader("📜 Constitution")
        rules = supabase.table("rules").select("*").eq("user_id", user).execute().data
        for r in rules:
            c1,c2 = st.columns([5,1])
            c1.markdown(f"⛔ {r['rule_text']}")
            if c2.button("🗑️", key=r['id']):
                supabase.table("rules").delete().eq("id", r['id']).execute(); st.rerun()

    with t3:
        st.subheader("📈 Performance")
        hist = supabase.table("trades").select("*").eq("user_id", user).order("created_at", desc=True).execute().data
        if hist:
            st.dataframe(pd.DataFrame(hist)[['created_at', 'score', 'mistake_tags', 'fix_action']])
