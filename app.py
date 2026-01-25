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
        # st.error(f"⚠️ System Error: {e}") # Suppress visible errors in UI for clean look
        pass

# ==========================================
# 2. INTELLIGENCE ENGINE (LOGIC KEPT)
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
# 3. SURGICAL PARSING (LOGIC KEPT)
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
# 4. THE UI (EXACT REPLICATION)
# ==========================================

# 4A. GLOBAL CSS TO OVERRIDE STREAMLIT AND MATCH HTML
st.markdown("""
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<style>
    /* 1. Global Reset & Colors */
    .stApp {
        background-color: #0d1117 !important;
        font-family: 'Inter', sans-serif !important;
        color: #d1d5db !important; /* text-gray-300 */
    }
    
    /* 2. Hide Standard Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }
    
    /* 3. Button Override */
    div.stButton > button {
        background-color: #dc2626 !important; /* red-600 */
        color: white !important;
        border: none !important;
        border-radius: 9999px !important; /* rounded-full */
        font-weight: 700 !important;
        padding: 0.5rem 1.25rem !important;
        transition: all 0.2s !important;
    }
    div.stButton > button:hover {
        background-color: #b91c1c !important; /* red-700 */
    }

    /* 4. File Uploader Styling to Match "Dashed Box" */
    [data-testid='stFileUploader'] {
        width: 100% !important;
    }
    [data-testid='stFileUploader'] section {
        background-color: transparent !important;
        border: none !important; /* We use the wrapper for the border */
    }
    /* Hide the upload icon inside streamlit widget to use our own */
    [data-testid='stFileUploader'] section > div > div > span {
        display: none !important; 
    }
    [data-testid='stFileUploader'] small {
        display: none !important;
    }
    [data-testid='stFileUploader'] button {
        background-color: white !important;
        color: black !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
    }

    /* 5. Custom Classes injected via Markdown */
    .hero-title {
        font-style: italic;
        letter-spacing: -0.02em;
    }
    .upload-dashed {
        border: 2px dashed #30363d;
        background-color: #161b22;
        border-radius: 1.5rem; /* rounded-3xl */
    }
</style>
""", unsafe_allow_html=True)

# 4B. AUTHENTICATION VIEW
if not st.session_state["authenticated"]:
    # Simple login UI that fits the theme
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <span style="font-size: 1.5rem; font-weight: 800; color: white;">STOCK<span style="color: #ef4444;">POSTMORTEM</span>.AI</span>
            <p style="color: #6b7280; font-size: 0.8rem; margin-top: 0.5rem;">OPERATOR AUTHENTICATION</p>
        </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("ID", placeholder="trader1")
            p = st.text_input("KEY", type="password", placeholder="•••••••")
            sub = st.form_submit_button("ENTER VAULT")
            if sub: check_login(u, p)

# 4C. MAIN INTERFACE (EXACT HTML REPLICATION)
else:
    user = st.session_state["user"]
    
    # --- NAVIGATION BAR ---
    st.markdown(f"""
    <nav class="flex items-center justify-between px-8 py-6 max-w-7xl mx-auto relative">
        <div class="flex items-center gap-1">
            <span class="text-white font-extrabold text-xl tracking-tighter">STOCK<span class="text-red-500">POSTMORTEM</span>.AI</span>
        </div>
        
        <div class="hidden md:flex items-center gap-8 text-xs font-semibold uppercase tracking-widest text-gray-400">
            <div class="relative group">
                <button class="hover:text-white transition flex items-center gap-1 uppercase outline-none">
                    Analyze ({user})
                    <svg class="w-3 h-3 text-gray-500 group-hover:text-white transition" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                </button>
            </div>
            <a href="#" class="hover:text-white transition">Data Vault</a>
            <a href="#" class="hover:text-white transition">Pricing</a>
        </div>

        <button class="bg-red-600 hover:bg-red-700 text-white px-5 py-2 rounded-full text-sm font-bold transition">
            Get Started
        </button>
    </nav>
    """, unsafe_allow_html=True)

    # --- HERO SECTION ---
    st.markdown("""
    <main class="flex flex-col items-center justify-center text-center px-4 mt-16">
        <h1 class="text-5xl md:text-7xl font-extrabold text-white hero-title mb-6">
            STOP BLEEDING CAPITAL.
        </h1>
        <p class="max-w-2xl text-gray-400 text-lg leading-relaxed">
            Upload your losing trade screenshots. Our AI identifies psychological traps,<br class="hidden md:block"> 
            technical failures, and provides a surgical path to recovery.
        </p>
    </main>
    """, unsafe_allow_html=True)

    # --- UPLOAD SECTION (The "Dashed Box") ---
    # We use a container and columns to center the functional file uploader inside the "Visual" design
    
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True) # Spacer
    
    # Center the upload box
    col_l, col_m, col_r = st.columns([1, 2, 1]) 
    
    with col_m:
        # We create the "Box" visually using HTML, but embed the file uploader inside
        container = st.container()
        
        # Start of Box Styling
        st.markdown("""
        <div class="mt-4 w-full bg-[#161b22] rounded-3xl p-8 upload-dashed flex flex-col items-center border-[#30363d] relative">
            <div class="bg-red-500/10 p-4 rounded-full mb-6 mx-auto w-fit">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
            </div>
            <h2 class="text-2xl font-bold text-white mb-2 text-center">Drop your P&L or Chart screenshot here</h2>
            <p class="text-gray-500 text-sm mb-4 text-center">Supports PNG, JPG (Max 10MB).</p>
        """, unsafe_allow_html=True)

        # THE FUNCTIONAL WIDGET
        up_file = st.file_uploader("Upload", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
        
        # End of Box Styling
        st.markdown("</div>", unsafe_allow_html=True)

        # LOGIC TRIGGER ON UPLOAD
        if up_file:
            st.markdown("<div class='text-center mt-4 text-white font-bold animate-pulse'>SCANNING EVIDENCE...</div>", unsafe_allow_html=True)
            try:
                img_b64 = base64.b64encode(up_file.getvalue()).decode('utf-8')
                my_rules = get_user_rules(user)
                prompt = f"Audit this chart. Rules: {my_rules}. Output JSON."
                messages = [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}]}]
                
                # Run Logic
                raw = run_scientific_analysis(messages, mode="vision")
                report = parse_scientific_report(raw)
                save_to_lab_records(user, report)
                
                # RENDER RESULT (In simple HTML styled box below)
                c_score = "#ef4444" if report['score'] < 50 else "#22c55e"
                st.markdown(f"""
                <div class="mt-8 bg-[#161b22] border border-[#30363d] rounded-2xl p-8 text-left">
                    <div class="flex justify-between items-center border-b border-[#30363d] pb-4 mb-4">
                        <h2 class="text-white font-extrabold italic text-xl">AUTOPSY COMPLETE</h2>
                        <span class="text-5xl font-extrabold" style="color: {c_score}">{report['score']}</span>
                    </div>
                    <div class="space-y-4">
                        <div>
                             <h4 class="text-red-500 font-bold text-xs uppercase tracking-widest mb-1">Technical Forensics</h4>
                             <p class="text-gray-400 text-sm">{report['tech']}</p>
                        </div>
                        <div>
                             <h4 class="text-red-500 font-bold text-xs uppercase tracking-widest mb-1">Psychological Profile</h4>
                             <p class="text-gray-400 text-sm">{report['psych']}</p>
                        </div>
                         <div>
                             <h4 class="text-red-500 font-bold text-xs uppercase tracking-widest mb-1">Recovery Plan</h4>
                             <div class="bg-red-500/10 border-l-4 border-red-500 p-3 text-white text-sm">{report['fix']}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error("Error analyzing image. Try again.")

    # --- FEATURE GRID (STATIC HTML) ---
    st.markdown("""
    <div class="flex justify-center w-full px-4">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 w-full max-w-5xl mb-20">
            <div class="bg-[#161b22] p-8 rounded-xl border border-gray-800 text-left">
                <h3 class="text-white font-bold mb-3 text-lg">Pattern Recognition</h3>
                <p class="text-gray-500 text-sm leading-relaxed">
                    Did you buy the top? We identify if you're falling for FOMO or revenge trading.
                </p>
            </div>

            <div class="bg-[#161b22] p-8 rounded-xl border border-gray-800 text-left">
                <h3 class="text-white font-bold mb-3 text-lg">Risk Autopsy</h3>
                <p class="text-gray-500 text-sm leading-relaxed">
                    Calculates if your stop-loss was too tight or if your position sizing was reckless.
                </p>
            </div>

            <div class="bg-[#161b22] p-8 rounded-xl border border-gray-800 text-left">
                <h3 class="text-white font-bold mb-3 text-lg">Recovery Plan</h3>
                <p class="text-gray-500 text-sm leading-relaxed">
                    Step-by-step technical adjustments to ensure the next trade is a winner.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
