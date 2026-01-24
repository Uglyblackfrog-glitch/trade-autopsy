import streamlit as st
import requests
import base64
import io
import re
from PIL import Image

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="StockPostmortem.ai", 
    page_icon="🩸", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. API & SECURITY SETUP
# ==========================================
try:
    # Ensure you have HF_TOKEN in your .streamlit/secrets.toml file
    HF_TOKEN = st.secrets["HF_TOKEN"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except Exception:
    st.error("⚠️ HF_TOKEN is missing. Please add it to Streamlit Secrets.")
    st.stop()

# ==========================================
# 3. CSS STYLING (THE "PRO" LOOK)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    /* GLOBAL THEME */
    body, .stApp { 
        background-color: #050505 !important; 
        font-family: 'Space Grotesk', sans-serif !important; 
        color: #e2e8f0 !important; 
    }

    /* CUSTOM TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background-color: transparent;
        border-bottom: 1px solid #333;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0 0;
        color: #888;
        font-weight: 600;
        border: none;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #fff; background: #111; }
    .stTabs [aria-selected="true"] {
        color: #ff4d4d !important;
        border-bottom: 2px solid #ff4d4d !important;
        background: rgba(255, 77, 77, 0.05);
    }

    /* FORENSIC REPORT CARDS */
    .report-container {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 2rem;
        margin-top: 2rem;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    }
    .report-header {
        border-bottom: 2px solid #ff4d4d;
        padding-bottom: 15px;
        margin-bottom: 25px;
        color: #ff4d4d;
        font-size: 1.2rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 3px;
    }
    .analysis-card {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 4px solid #444;
        transition: transform 0.2s;
    }
    .analysis-card:hover { transform: translateX(5px); }
    
    .tech-fail { border-left-color: #3b82f6; }   /* Blue */
    .psych-trap { border-left-color: #f59e0b; }  /* Orange */
    .risk-fail { border-left-color: #ef4444; }   /* Red */
    .recovery-path { border-left-color: #10b981; } /* Green */

    .card-title {
        font-weight: 800;
        font-size: 0.9rem;
        margin-bottom: 8px;
        display: block;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* TEXT INPUT FORM STYLING */
    div[data-testid="stForm"] {
        background-color: #0e1216;
        border: 1px solid #30363d;
        padding: 2rem;
        border-radius: 12px;
    }

    /* HERO & TYPOGRAPHY */
    .hero-h1 { 
        font-size: 4rem; 
        font-weight: 800; 
        font-style: italic; 
        text-align: center; 
        color: white; 
        line-height: 1.1; 
        margin-bottom: 1rem; 
    }
    .hero-p { 
        text-align: center; 
        color: #8b949e; 
        font-size: 1.1rem; 
        max-width: 600px; 
        margin: 0 auto 3rem auto; 
    }
    
    /* UPLOADER */
    [data-testid="stFileUploaderDropzone"] {
        background-color: rgba(22, 27, 34, 0.5) !important;
        border: 2px dashed #30363d !important;
        min-height: 250px !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover { border-color: #ff4d4d !important; }

</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. HELPER FUNCTIONS (THE PARSER)
# ==========================================
def parse_forensic_report(text):
    """
    Parses the AI output to extract content between specific tags.
    """
    sections = {
        "tech": "Analysis failed to generate specific technical data.",
        "psych": "Analysis failed to generate psychological profile.",
        "risk": "Analysis failed to generate risk audit.",
        "fix": "Analysis failed to generate recovery step."
    }
    
    # Regex to find content between tags
    tech_match = re.search(r'\[TECH\](.*?)(?=\[PSYCH\]|\[RISK\]|\[FIX\]|$)', text, re.DOTALL)
    psych_match = re.search(r'\[PSYCH\](.*?)(?=\[RISK\]|\[FIX\]|$)', text, re.DOTALL)
    risk_match = re.search(r'\[RISK\](.*?)(?=\[FIX\]|$)', text, re.DOTALL)
    fix_match = re.search(r'\[FIX\](.*?)$', text, re.DOTALL)

    if tech_match: sections["tech"] = tech_match.group(1).strip()
    if psych_match: sections["psych"] = psych_match.group(1).strip()
    if risk_match: sections["risk"] = risk_match.group(1).strip()
    if fix_match: sections["fix"] = fix_match.group(1).strip()
    
    return sections

def display_report(report_data, title_suffix=""):
    """
    Renders the parsed data into the HTML Card UI.
    """
    st.markdown(f"""
    <div class="report-container">
        <div class="report-header">💀 FORENSIC AUTOPSY REPORT {title_suffix}</div>
        
        <div class="analysis-card tech-fail">
            <span class="card-title" style="color:#3b82f6;">📉 TECHNICAL FAILURE</span>
            {report_data['tech']}
        </div>

        <div class="analysis-card psych-trap">
            <span class="card-title" style="color:#f59e0b;">🧠 PSYCHOLOGICAL TRAP</span>
            {report_data['psych']}
        </div>

        <div class="analysis-card risk-fail">
            <span class="card-title" style="color:#ef4444;">💸 RISK MANAGEMENT AUDIT</span>
            {report_data['risk']}
        </div>

        <div class="analysis-card recovery-path">
            <span class="card-title" style="color:#10b981;">💉 THE SURGICAL FIX</span>
            <b>{report_data['fix']}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 5. UI RENDER (HEADER & TABS)
# ==========================================

# HEADER
st.markdown("""
<div style="text-align:center; padding-top: 40px;">
    <div style="font-size: 1.2rem; font-weight: 800; color: white; margin-bottom: 10px; letter-spacing: 2px;">
        STOCK<span style="color:#ff4d4d">POSTMORTEM</span>.AI
    </div>
    <div class="hero-h1">THE TRUTH HURTS.</div>
    <p class="hero-p">
        Upload your losing charts or confess your trade details. 
        We analyze the failure so you don't repeat it.
    </p>
</div>
""", unsafe_allow_html=True)

# TABS
tab1, tab2 = st.tabs(["📸 UPLOAD EVIDENCE", "📝 WRITTEN CONFESSION"])

# --- TAB 1: IMAGE ANALYSIS ---
with tab1:
    c1, c2, c3 = st.columns([1, 4, 1])
    with c2:
        uploaded_file = st.file_uploader(" ", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
        
        if uploaded_file:
            st.image(uploaded_file, caption="Evidence Secured", use_container_width=True)
            
            if st.button("RUN FORENSIC ANALYSIS (VISION)", type="primary", use_container_width=True):
                with st.spinner("Analyzing candles, indicators, and market structure..."):
                    try:
                        # Process Image
                        image = Image.open(uploaded_file)
                        buf = io.BytesIO()
                        image.save(buf, format="PNG")
                        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

                        # Prompt
                        prompt = """
                        ACT AS: Senior Institutional Trader.
                        TASK: Brutal technical and psychological breakdown of this chart.
                        
                        REQUIREMENTS:
                        1. [TECH] Identify technical failure (e.g., buying resistance, divergence, liquidity sweep).
                        2. [PSYCH] Identify emotional bias (e.g., FOMO, revenge trading, panic).
                        3. [RISK] Audit risk (e.g., stop loss too tight, risk-reward ratio).
                        4. [FIX] One actionable rule for next time.

                        MANDATORY FORMAT:
                        [TECH] ...
                        [PSYCH] ...
                        [RISK] ...
                        [FIX] ...
                        """
                        
                        # API Call
                        payload = {
                            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                            "messages": [{"role": "user", "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                            ]}],
                            "max_tokens": 1000
                        }
                        headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                        res = requests.post(API_URL, headers=headers, json=payload)
                        
                        if res.status_code == 200:
                            content = res.json()["choices"][0]["message"]["content"]
                            report = parse_forensic_report(content)
                            display_report(report, "(VISION)")
                        else:
                            st.error(f"Analysis Failed. Error: {res.status_code}")
                            
                    except Exception as e:
                        st.error(f"System Error: {e}")

# --- TAB 2: TEXT ANALYSIS ---
with tab2:
    st.markdown("<div style='max-width: 800px; margin: 0 auto;'>", unsafe_allow_html=True)
    
    with st.form("text_analysis_form"):
        st.write("### 📂 CASE FILE DETAILS")
        st.caption("Be specific. The more honest you are, the better the diagnosis.")
        
        # Inputs
        c1, c2, c3 = st.columns(3)
        with c1: ticker = st.text_input("Ticker", placeholder="$NVDA")
        with c2: position = st.selectbox("Position", ["Long (Buy)", "Short (Sell)"])
        with c3: timeframe = st.selectbox("Timeframe", ["Scalp (1m-5m)", "Day (15m-1h)", "Swing (4h+)"])
        
        c1, c2, c3 = st.columns(3)
        with c1: entry = st.text_input("Entry Price", placeholder="100.00")
        with c2: exit = st.text_input("Exit Price", placeholder="95.00")
        with c3: stop = st.text_input("Planned Stop", placeholder="98.00")
        
        st.markdown("---")
        setup_desc = st.text_area("The Setup (Why did you enter?)", placeholder="Ex: Bull flag breakout above VWAP...")
        emotion_desc = st.text_area("The Exit (Why did you close?)", placeholder="Ex: I got scared when it wicked down...")
        
        submit_text = st.form_submit_button("RUN FORENSIC ANALYSIS (TEXT)", type="primary", use_container_width=True)

    if submit_text:
        if not ticker or not setup_desc:
            st.error("⚠️ Case file incomplete. Please provide Ticker and Setup details.")
        else:
            with st.spinner("Reconstructing trade scenario..."):
                try:
                    # Construct Narrative Prompt
                    prompt = f"""
                    ACT AS: Senior Risk Manager.
                    TASK: Analyze this losing trade report.
                    
                    DATA:
                    - Trade: {ticker} ({position}) on {timeframe}.
                    - Prices: Entry {entry}, Exit {exit}, Stop {stop}.
                    - CONTEXT: {setup_desc}
                    - OUTCOME: {emotion_desc}
                    
                    REQUIREMENTS:
                    1. [TECH] Diagnose the technical error based on the setup description.
                    2. [PSYCH] Diagnose the emotional trap based on the exit description.
                    3. [RISK] Audit the math (Entry vs Stop vs Exit).
                    4. [FIX] One surgical rule to prevent this.

                    MANDATORY FORMAT:
                    [TECH] ...
                    [PSYCH] ...
                    [RISK] ...
                    [FIX] ...
                    """
                    
                    # API Call (Text Only)
                    payload = {
                        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 1000
                    }
                    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                    res = requests.post(API_URL, headers=headers, json=payload)
                    
                    if res.status_code == 200:
                        content = res.json()["choices"][0]["message"]["content"]
                        report = parse_forensic_report(content)
                        display_report(report, "(TEXT EVIDENCE)")
                    else:
                        st.error(f"Analysis Failed. Error: {res.status_code}")
                except Exception as e:
                    st.error(f"System Error: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

# FOOTER
st.markdown("""
<div style="text-align: center; margin-top: 5rem; color: #484f58; font-size: 0.8rem;">
    &copy; 2026 stockpostmortem.ai | Trading involves financial risk.
</div>
""", unsafe_allow_html=True)
