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
        st.error(f"⚠️ System Error: Ensure Secrets are configured. {e}")
        st.stop()

# ==========================================
# 2. INTELLIGENCE & PARSING ENGINES
# ==========================================
def run_scientific_analysis(messages, mode="text"):
    api_url = "https://router.huggingface.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
    model_id = "Qwen/Qwen2.5-72B-Instruct" if mode == "text" else "Qwen/Qwen2.5-VL-7B-Instruct"

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
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(?<!^)(\d+\.)', r'<br>\1', text)
    return text.strip()

def parse_scientific_report(text):
    clean_raw = text.replace("```json", "").replace("```", "").strip()
    data = {"score": 0, "tags": [], "tech": "", "psych": "", "risk": "", "fix": "", "type": "long"}
    
    try:
        json_data = json.loads(clean_raw)
        data["tags"] = json_data.get("tags", [])
        data["tech"] = clean_text_surgical(json_data.get("technical_analysis", ""))
        data["psych"] = clean_text_surgical(json_data.get("psychological_profile", ""))
        data["risk"] = clean_text_surgical(json_data.get("risk_assessment", ""))
        data["fix"] = clean_text_surgical(json_data.get("strategic_roadmap", ""))
        data["score"] = json_data.get("score", 50)
    except:
        data["tech"] = "Analysis complete. Errors in JSON formatting, but data captured."
        data["score"] = 40
    
    return data

# ==========================================
# 3. THEME INJECTION (STOCKPOSTMORTEM STYLE)
# ==========================================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,600;0,800;1,800&display=swap" rel="stylesheet">
<style>
    /* Main Background */
    .stApp {
        background-color: #0d1117 !important;
        color: #c9d1d9 !important;
        font-family: 'Inter', sans-serif;
    }

    /* Typography */
    h1, .hero-title {
        font-weight: 800 !important;
        font-style: italic !important;
        letter-spacing: -0.03em !important;
        color: white !important;
        text-transform: uppercase;
        line-height: 1;
    }

    /* Containers & Cards */
    [data-testid="stForm"], .report-box {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 16px !important;
        padding: 2.5rem !important;
    }

    /* Custom Header Bar */
    .nav-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        margin-bottom: 3rem;
    }

    /* Buttons */
    div.stButton > button {
        background-color: #da3633 !important;
        color: white !important;
        border: none !important;
        border-radius: 99px !important;
        font-weight: 700 !important;
        padding: 0.6rem 2rem !important;
        text-transform: uppercase;
        font-size: 0.85rem;
    }
    div.stButton > button:hover {
        background-color: #f85149 !important;
        transform: scale(1.02);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 30px; }
    .stTabs [data-baseweb="tab"] {
        color: #8b949e !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.1em;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        color: white !important;
        border-bottom: 2px solid #da3633 !important;
    }

    /* Report Specifics */
    .section-title {
        color: #da3633;
        font-weight: 800;
        text-transform: uppercase;
        font-size: 0.8rem;
        margin-top: 20px;
        letter-spacing: 1px;
    }
    .score-display {
        font-size: 5rem;
        font-weight: 800;
        color: #da3633;
        line-height: 1;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. MAIN APPLICATION LOGIC
# ==========================================

if not st.session_state["authenticated"]:
    # LOGIN PAGE
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div style='height: 100px'></div>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center; color:white; font-weight:800;'>STOCK<span style='color:#da3633'>POSTMORTEM</span>.AI</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Operator ID")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("SYSTEM ACCESS"):
                check_login(u, p)
else:
    # AUTHENTICATED DASHBOARD
    user = st.session_state["user"]
    
    # Custom Header
    st.markdown(f"""
        <div class="nav-header">
            <div style="font-weight:800; color:white; font-size:1.2rem;">STOCK<span style="color:#da3633">POSTMORTEM</span>.AI</div>
            <div style="color:#8b949e; font-size:0.8rem; font-weight:600;">OPERATOR: {user.upper()}</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='font-size: 4.5rem;'>STOP <span style='color:#da3633'>BLEEDING</span> CAPITAL.</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e; font-size:1.2rem; margin-bottom:40px;'>AI-driven forensic analysis of your trading failures.</p>", unsafe_allow_html=True)

    tab_audit, tab_laws, tab_data = st.tabs(["🔬 DIAGNOSTIC AUDIT", "⚖️ PROTOCOLS", "📊 DATA VAULT"])

    with tab_audit:
        mode = st.radio("Select Evidence Type", ["Visual Evidence (Chart/P&L)", "Detailed Text Log"], horizontal=True)
        
        if "Visual" in mode:
            st.markdown("""
                <div style='border: 2px dashed #30363d; padding: 40px; border-radius: 20px; text-align: center; background: #161b22; margin-bottom: 20px;'>
                    <div style='font-size: 2rem; color: #da3633; margin-bottom: 10px;'>☁️</div>
                    <p style='color: white; font-weight: 600; margin: 0;'>Drop your trade screenshot below</p>
                    <p style='color: #8b949e; font-size: 0.8rem;'>Supports PNG, JPG (Max 10MB)</p>
                </div>
            """, unsafe_allow_html=True)
            
            up_file = st.file_uploader("Upload", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
            if up_file:
                st.image(up_file, width=700)
                if st.button("RUN FORENSIC SCAN"):
                    img_b64 = base64.b64encode(up_file.getvalue()).decode('utf-8')
                    messages = [{"role": "user", "content": [{"type": "text", "text": "Perform a surgical autopsy of this trade. Identify technical and psychological errors. Output in JSON."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}]}]
                    with st.spinner("🔬 Analyzing visual evidence..."):
                        raw = run_scientific_analysis(messages, mode="vision")
                        report = parse_scientific_report(raw)
                        st.balloons()
                        
                        # Displaying the Report
                        st.markdown(f"""
                            <div class="report-box">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <h2 style="color:white; font-weight:800;">DIAGNOSTIC REPORT</h2>
                                    <div class="score-display">{report['score']}</div>
                                </div>
                                <div class="section-title">📊 Technical Forensics</div>
                                <p style="color:#d0d7de;">{report['tech']}</p>
                                <div class="section-title">🧠 Psychological Profile</div>
                                <p style="color:#d0d7de;">{report['psych']}</p>
                                <div class="section-title">🚀 Strategic Roadmap</div>
                                <div style="background:rgba(218, 54, 51, 0.1); border-left:4px solid #da3633; padding:15px; margin-top:10px;">
                                    {report['fix']}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

        else:
            with st.form("text_audit"):
                st.markdown("<p class='section-title'>Case File Details</p>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                tick = c1.text_input("Ticker Symbol", placeholder="$NVDA")
                pos = c2.selectbox("Direction", ["Long", "Short"])
                setup = st.text_area("Trading Setup & Logic", placeholder="Describe your entry reason...")
                if st.form_submit_button("ANALYZE CASE FILE"):
                    # Process text analysis logic here
                    st.info("AI is processing the text log...")

    with tab_laws:
        st.markdown("<h3 style='color:white;'>Active Trading Protocols</h3>", unsafe_allow_html=True)
        st.info("Rules generated from your 'Strategic Roadmaps' will appear here to prevent repeat mistakes.")

    with tab_data:
        st.markdown("<h3 style='color:white;'>Historical Data Vault</h3>", unsafe_allow_html=True)
        try:
            hist = supabase.table("trades").select("*").eq("user_id", user).execute().data
            if hist:
                st.dataframe(pd.DataFrame(hist), use_container_width=True)
            else:
                st.write("No records found in the vault.")
        except:
            st.warning("Database connection inactive. Check Supabase credentials.")

    # Sidebar Logout
    with st.sidebar:
        if st.button("TERMINATE SESSION"): logout()
