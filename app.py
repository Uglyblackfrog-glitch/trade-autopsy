import streamlit as st
import pandas as pd
import re
import io
import base64
import time
import requests
import json
from PIL import Image
from supabase import create_client, Client
from huggingface_hub import InferenceClient

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
# 1. ROBUST HF ENGINE (Requests & Client)
# ==========================================
def get_hf_token():
    token = st.secrets.get("HF_TOKEN") or st.secrets.get("hf_token")
    if not token:
        st.error("❌ Missing 'HF_TOKEN' in secrets.toml")
        st.stop()
    return token

def run_hf_vision_manual(prompt, image_b64, model_id):
    """
    Uses direct HTTP requests to avoid library formatting issues.
    This is often more reliable for Vision on the free tier.
    """
    token = get_hf_token()
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Qwen-VL specific formatting for the raw API
    payload = {
        "inputs": {
            "text": prompt,
            "image": image_b64
        },
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.1,
            "return_full_text": False
        }
    }

    # Alternative: Standard Chat Payload (Try this first as it's cleaner)
    chat_payload = {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.1
    }
    
    # We use the Chat Completion endpoint URL for standard models
    chat_url = f"https://api-inference.huggingface.co/models/{model_id}/v1/chat/completions"
    
    try:
        response = requests.post(chat_url, headers=headers, json=chat_payload, timeout=45)
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"Status {response.status_code}: {response.text}")
            
    except Exception as e:
        raise Exception(f"Direct Request Failed: {e}")

def run_hf_text(messages, model_id):
    """Standard Text Inference using the Library (Works well for text)"""
    client = InferenceClient(api_key=get_hf_token())
    try:
        output = client.chat.completions.create(
            model=model_id,
            messages=messages,
            max_tokens=2048,
            temperature=0.1
        )
        return output.choices[0].message.content
    except Exception as e:
        # Fallback to older generation method if chat fails
        if "404" in str(e):
             st.warning("Trying legacy generation method...")
             prompt = messages[-1]['content']
             return client.text_generation(prompt, model=model_id, max_new_tokens=1000)
        raise e

# ==========================================
# 2. SETUP & DATABASE
# ==========================================
if st.session_state["authenticated"]:
    try:
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"⚠️ Database Error: {e}")
        st.stop()

# ==========================================
# 3. STYLING & PARSERS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;800&display=swap');
    body, .stApp { background-color: #050505 !important; font-family: 'Space Grotesk', sans-serif !important; color: #e2e8f0; }
    .report-container { background: #0d1117; border: 1px solid #30363d; border-radius: 12px; padding: 2rem; margin-top: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
    .analysis-card { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 15px; margin-bottom: 10px; border-left: 4px solid #555; }
    button[kind="primary"] { background-color: #ff4d4d !important; border: none; color: white !important; font-weight: bold; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

def get_user_rules(user_id):
    try:
        res = supabase.table("rules").select("*").eq("user_id", user_id).execute()
        return [r['rule_text'] for r in res.data]
    except: return []

def parse_report(text):
    text = re.sub(r'\*\*', '', text) 
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
    try:
        supabase.table("trades").insert(payload).execute()
        if data.get('score', 0) < 50:
            clean_fix = data.get('fix', 'Follow process').replace('"', '')
            supabase.table("rules").insert({"user_id": user_id, "rule_text": clean_fix}).execute()
            st.toast("📉 New Rule added to Constitution.")
    except Exception as e: st.error(f"DB Save Error: {e}")

# ==========================================
# 4. MAIN APPLICATION
# ==========================================
if not st.session_state["authenticated"]:
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><br><div class='login-box'>", unsafe_allow_html=True)
        st.title("🩸 StockPostmortem")
        st.caption("v15.0 | Robust Hugging Face")
        with st.form("login"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.form_submit_button("ENTER", type="primary", use_container_width=True): check_login(u, p)
        st.markdown("</div>", unsafe_allow_html=True)

else:
    user = st.session_state["user"]
    
    with st.sidebar:
        st.header(f"👤 {user}")
        if st.button("LOGOUT"): logout()
        st.divider()
        st.success("HF Status: Connected")
        # Defaulting to Qwen2-VL as it's the best free vision model
        vision_model = st.text_input("Vision Model", "Qwen/Qwen2-VL-7B-Instruct")
        text_model = st.text_input("Text Model", "Qwen/Qwen2.5-72B-Instruct")

    st.markdown("<h1 style='text-align:center'>STOCK<span style='color:#ff4d4d'>POSTMORTEM</span>.AI</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["🔍 AUTOPSY", "⚖️ LAWS", "📈 STATS"])

    with t1:
        my_rules = get_user_rules(user)
        if my_rules:
            with st.expander(f"🚨 ACTIVE RULES ({len(my_rules)})"):
                for r in my_rules: st.markdown(f"❌ {r}")

        mode = st.radio("Mode", ["Text Report", "Chart Vision"], horizontal=True, label_visibility="collapsed")
        
        # --- MODE A: ROBUST VISION ---
        if "Chart Vision" in mode:
            st.info(f"📸 Using {vision_model}. Image will be optimized to prevent API errors.")
            up_file = st.file_uploader("Upload Chart", type=["png", "jpg", "jpeg"])
            
            if up_file:
                st.image(up_file, width=400)
                if st.button("RUN VISION AUDIT", type="primary"):
                    with st.status("Processing...") as status:
                        try:
                            # 1. OPTIMIZE IMAGE (Fixes 400 Bad Request)
                            status.update(label="Optimizing Image...", state="running")
                            image = Image.open(up_file)
                            if image.mode != 'RGB': image = image.convert('RGB')
                            
                            # RESIZE: Strict 800px limit for Free Tier Bandwidth
                            max_dim = 800
                            if max(image.size) > max_dim:
                                ratio = max_dim / max(image.size)
                                new_size = (int(image.width * ratio), int(image.height * ratio))
                                image = image.resize(new_size, Image.Resampling.LANCZOS)
                            
                            # COMPRESS: 85 quality JPEG
                            buf = io.BytesIO()
                            image.save(buf, format="JPEG", quality=85)
                            img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

                            # 2. SEND REQUEST
                            status.update(label="Sending to Hugging Face...", state="running")
                            prompt_text = f"Analyze this trading chart. RULES: {my_rules}. Output strictly: [SCORE] 0-100, [TAGS] list, [TECH] text, [PSYCH] text, [RISK] text, [FIX] command."
                            
                            raw_text = run_hf_vision_manual(prompt_text, img_b64, vision_model)
                            
                            # 3. PARSE
                            report = parse_report(raw_text)
                            save_analysis(user, report)
                            status.update(label="Complete!", state="complete")
                            
                            # 4. DISPLAY
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
                            status.update(label="Failed", state="error")
                            st.error(f"Error details: {str(e)}")
                            st.caption("Tip: If 'Bad Request', try a smaller image or a different model ID.")

        # --- MODE B: TEXT ---
        else:
            with st.form("audit"):
                c1,c2 = st.columns(2)
                with c1: tick = st.text_input("Ticker", "SPY")
                with c2: emo = st.selectbox("Emotion", ["Neutral", "FOMO", "Fear"])
                note = st.text_area("Notes")
                if st.form_submit_button("AUDIT", type="primary", use_container_width=True):
                    prompt = f"Analyze trade: {tick} | {emo} | {note}. Rules: {my_rules}. Output: [SCORE], [TAGS], [TECH], [PSYCH], [RISK], [FIX]."
                    messages = [{"role": "user", "content": prompt}]
                    
                    with st.spinner("Analyzing..."):
                        try:
                            raw = run_hf_text(messages, text_model)
                            report = parse_report(raw)
                            save_analysis(user, report)
                            st.success(f"Score: {report['score']} - {report['fix']}")
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
