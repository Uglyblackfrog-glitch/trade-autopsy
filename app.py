import streamlit as st
import requests
import re
import pandas as pd
import random
import base64
import io
import json
from PIL import Image
from supabase import create_client, Client

# ==========================================
# 0. CONFIG & AUTH
# ==========================================
st.set_page_config(page_title="StockPostmortem.ai", page_icon="🩸", layout="wide")

USERS = { "trader1": "profit2026", "demo": "12345", "admin": "admin" }

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = None

def check_login(u, p):
    if u in USERS and USERS[u] == p:
        st.session_state["authenticated"] = True
        st.session_state["user"] = u
        st.rerun()
    else: st.error("Access Denied")

def logout():
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.rerun()

# ==========================================
# 1. ROBUST GROQ ENGINE
# ==========================================
def get_groq_headers(key):
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

def fetch_available_models(keys_str):
    """
    Query Groq API to find out which models are ACTUALLY active.
    """
    keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    for key in keys:
        try:
            res = requests.get("https://api.groq.com/openai/v1/models", headers=get_groq_headers(key))
            if res.status_code == 200:
                data = res.json()
                # Return list of model IDs
                return [m['id'] for m in data['data']]
        except:
            continue
    return ["Error fetching models. Check Keys."]

def run_groq_query(payload, keys_str):
    keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    random.shuffle(keys)
    last_error = ""
    
    for key in keys:
        try:
            # 60s timeout for vision models
            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=get_groq_headers(key),
                json=payload,
                timeout=60 
            )
            
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            elif res.status_code == 429:
                continue 
            else:
                error_detail = res.text
                print(f"Key failed ({res.status_code}): {error_detail}")
                last_error = f"Status {res.status_code}: {error_detail}"
                continue
                
        except Exception as e:
            last_error = str(e)
            continue
            
    st.error(f"❌ API Request Failed. Last Error: {last_error}")
    raise Exception("ALL KEYS EXHAUSTED OR FAILED")

# ==========================================
# 2. SETUP & DATABASE
# ==========================================
if st.session_state["authenticated"]:
    try:
        if "GROQ_KEYS" in st.secrets:
            GROQ_KEYS_POOL = st.secrets["GROQ_KEYS"]
        elif "groq_keys" in st.secrets:
            GROQ_KEYS_POOL = st.secrets["groq_keys"]
        else:
            st.error("❌ Missing 'GROQ_KEYS' in secrets.toml")
            st.stop()

        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
    except Exception as e:
        st.error(f"⚠️ Setup Error: {e}")
        st.stop()

# ==========================================
# 3. STYLING & PARSERS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;800&display=swap');
    body, .stApp { background-color: #050505 !important; font-family: 'Space Grotesk', sans-serif !important; color: #e2e8f0; }
    .login-box { max-width: 400px; margin: 100px auto; padding: 2rem; border: 1px solid #333; background: #0d1117; border-radius: 12px; }
    .report-container { background: #0d1117; border: 1px solid #30363d; border-radius: 12px; padding: 2rem; margin-top: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
    .analysis-card { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 15px; margin-bottom: 10px; border-left: 4px solid #555; }
    button[kind="primary"] { background-color: #ff4d4d !important; border: none; color: white !important; font-weight: bold; letter-spacing: 1px; }
    .stTextInput input { color: #facc15 !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def get_user_rules(user_id):
    try:
        res = supabase.table("rules").select("*").eq("user_id", user_id).execute()
        return [r['rule_text'] for r in res.data]
    except: return []

def parse_report(text):
    text = re.sub(r'[^\w\s,.:;!?()\[\]\-\'\"%]', '', text).strip()
    sections = { "score": 0, "tags": [], "tech": "N/A", "psych": "N/A", "risk": "N/A", "fix": "N/A" }
    
    score_match = re.search(r'\[SCORE\]\s*(\d+)', text)
    if not score_match: score_match = re.search(r'(?:^|\n)\[(\d+)\]', text)
    if score_match: sections['score'] = int(score_match.group(1))

    tags_match = re.search(r'\[TAGS\](.*?)(?=\[|$)', text, re.DOTALL)
    if tags_match:
        raw = tags_match.group(1).replace('[', '').replace(']', '').split(',')
        sections['tags'] = [t.strip().replace('"', '') for t in raw if t.strip()]
    
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
    supabase.table("trades").insert(payload).execute()
    if data.get('score', 0) < 50:
        clean_fix = data.get('fix', 'Follow process').replace('"', '')
        supabase.table("rules").insert({"user_id": user_id, "rule_text": clean_fix}).execute()
        st.toast("📉 New Rule added to Constitution.")

# ==========================================
# 4. MAIN APPLICATION
# ==========================================
if not st.session_state["authenticated"]:
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><br><div class='login-box'>", unsafe_allow_html=True)
        st.title("🩸 StockPostmortem")
        st.caption("v10.0 | Bulletproof Model Selector")
        with st.form("login"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.form_submit_button("ENTER", type="primary", use_container_width=True): check_login(u, p)
        st.markdown("</div>", unsafe_allow_html=True)

else:
    user = st.session_state["user"]
    
    # --- SIDEBAR CONFIGURATION ---
    with st.sidebar:
        st.header(f"👤 {user}")
        if st.button("LOGOUT"): logout()
        st.divider()
        st.subheader("⚙️ Model Config")
        
        # MODEL DEBUGGER
        if st.button("🔎 Get Available Models"):
            with st.spinner("Fetching list from Groq..."):
                active_models = fetch_available_models(GROQ_KEYS_POOL)
                st.write(active_models)
                
        # USER EDITABLE MODELS
        st.caption("Paste a valid ID from the list above if these fail:")
        vision_model = st.text_input("Vision Model ID", value="llama-3.2-11b-vision-preview")
        text_model = st.text_input("Text Model ID", value="llama-3.3-70b-versatile")
        
        st.divider()
        st.caption("Engine Status:")
        st.success(f"👁️ {vision_model}")
        st.success(f"🧠 {text_model}")

    st.markdown("<h1 style='text-align:center'>STOCK<span style='color:#ff4d4d'>POSTMORTEM</span>.AI</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["🔍 AUTOPSY", "⚖️ LAWS", "📈 STATS"])

    # --- TAB 1: AUTOPSY ---
    with t1:
        my_rules = get_user_rules(user)
        if my_rules:
            with st.expander(f"🚨 ACTIVE RULES ({len(my_rules)})"):
                for r in my_rules: st.markdown(f"❌ {r}")

        mode = st.radio("Mode", ["Text Report", "Chart Vision"], horizontal=True, label_visibility="collapsed")
        
        ready = False
        payload = {}

        # --- MODE A: VISION ---
        if "Chart Vision" in mode:
            up_file = st.file_uploader("Upload Chart", type=["png", "jpg", "jpeg"])
            if up_file:
                st.image(up_file, width=400)
                if st.button("RUN VISION AUDIT", type="primary"):
                    with st.status("Processing Image...") as status:
                        # 1. Image Optimization
                        image = Image.open(up_file)
                        if image.mode != 'RGB': image = image.convert('RGB')
                        
                        max_dim = 1024
                        if max(image.size) > max_dim:
                            ratio = max_dim / max(image.size)
                            new_size = (int(image.width * ratio), int(image.height * ratio))
                            image = image.resize(new_size, Image.Resampling.LANCZOS)
                        
                        buf = io.BytesIO()
                        image.save(buf, format="JPEG", quality=85)
                        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                        
                        prompt_text = f"Analyze chart. RULES: {my_rules}. Output: [SCORE] 0-100, [TAGS] list, [TECH] text, [PSYCH] text, [RISK] text, [FIX] imperative."
                        
                        payload = {
                            "model": vision_model, # Uses Sidebar Input
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": prompt_text},
                                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                                    ]
                                }
                            ],
                            "max_tokens": 1024,
                            "temperature": 0.1
                        }
                        ready = True
                        status.update(label="Sending to Groq...", state="complete")

        # --- MODE B: TEXT ---
        else:
            with st.form("audit"):
                c1,c2,c3,c4 = st.columns(4)
                with c1: tick = st.text_input("Ticker", "SPY")
                with c2: pos = st.selectbox("Position", ["Long", "Short"])
                with c3: tf = st.selectbox("Timeframe", ["Scalp", "Day", "Swing"])
                with c4: setup = st.selectbox("Setup", ["Trend", "Reversal", "Breakout"])
                c1,c2,c3 = st.columns(3)
                with c1: ent = st.number_input("Entry", 0.0)
                with c2: ex = st.number_input("Exit", 0.0)
                with c3: stp = st.number_input("Stop", 0.0)
                emo = st.selectbox("Emotion", ["Neutral", "FOMO", "Revenge", "Fear"])
                note = st.text_area("Notes")
                
                if st.form_submit_button("AUDIT", type="primary", use_container_width=True):
                    risk = abs(ent - stp)
                    viol = False
                    if (pos == "Long" and ex < stp) or (pos == "Short" and ex > stp): viol = True
                    rm = (ex - ent)/risk if risk > 0 and pos == "Long" else (ent - ex)/risk if risk > 0 else 0
                    
                    math_txt = f"[METRICS] Pos: {pos} | Risk: {risk:.2f} | R: {rm:.2f}R | Stop_Viol: {viol}"
                    
                    prompt_text = f"""
                    SYSTEM: You are a Ruthless Trading Auditor.
                    USER RULES: {my_rules}
                    LOGIC:
                    1. IF Stop_Viol is True -> MAX SCORE 30.
                    2. IF Notes imply "removed stop" or "luck" -> MAX SCORE 20.
                    INPUT: {tick} | {emo} | {note} \n {math_txt}
                    OUTPUT FORMAT:
                    [SCORE] (Integer)
                    [TAGS] (List)
                    [TECH] (Sentence)
                    [PSYCH] (Sentence)
                    [RISK] (Sentence)
                    [FIX] (Imperative)
                    """
                    
                    payload = {
                        "model": text_model, # Uses Sidebar Input
                        "messages": [{"role": "user", "content": prompt_text}],
                        "max_tokens": 800,
                        "temperature": 0.1
                    }
                    ready = True

        # --- EXECUTION ---
        if ready:
            with st.spinner(f"Routing to Groq ({payload['model']})..."):
                try:
                    raw_text = run_groq_query(payload, GROQ_KEYS_POOL)
                    report = parse_report(raw_text)
                    save_analysis(user, report)
                    
                    c = "#ef4444" if report['score'] < 50 else "#10b981"
                    st.markdown(f"""
                    <div class="report-container">
                        <div style="display:flex; justify-content:space-between;">
                            <div><div style="color:#888;">SCORE</div><div style="font-size:3.5rem; font-weight:900; color:{c};">{report['score']}</div></div>
                            <div style="text-align:right;"><div style="color:#fff;">{", ".join(report['tags'])}</div></div>
                        </div>
                        <hr style="border-color:#333;">
                        <div class="analysis-card" style="border-left-color:#3b82f6"><b>TECH:</b> {report['tech']}</div>
                        <div class="analysis-card" style="border-left-color:#f59e0b"><b>PSYCH:</b> {report['psych']}</div>
                        <div class="analysis-card" style="border-left-color:#ef4444"><b>RISK:</b> {report['risk']}</div>
                        <div class="analysis-card" style="border-left-color:#10b981"><b>FIX:</b> {report['fix']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    # Detailed error is already printed by run_groq_query
                    st.warning("Analysis interrupted. Check logs or change Model ID in Sidebar.")

    # --- TAB 2: LAWS ---
    with t2:
        st.subheader("📜 Constitution")
        rules = supabase.table("rules").select("*").eq("user_id", user).execute().data
        for r in rules:
            c1,c2 = st.columns([5,1])
            c1.markdown(f"⛔ {r['rule_text']}")
            if c2.button("🗑️", key=r['id']):
                supabase.table("rules").delete().eq("id", r['id']).execute(); st.rerun()

    # --- TAB 3: STATS ---
    with t3:
        st.subheader("📈 Performance")
        hist = supabase.table("trades").select("*").eq("user_id", user).order("created_at", desc=True).execute().data
        if hist:
            df = pd.DataFrame(hist)
            st.line_chart(df, x="created_at", y="score")
            st.dataframe(df[['created_at', 'score', 'mistake_tags', 'fix_action']])
