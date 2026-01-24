import streamlit as st
import requests
import base64
import io
from PIL import Image

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="StockPostmortem.ai",
    page_icon="🩸",
    layout="wide", # We keep this wide, but constrain it with CSS below
    initial_sidebar_state="collapsed"
)

# =========================================================
# 2. SECURE CREDENTIALS
# =========================================================
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except Exception:
    st.error("🔑 HF_TOKEN missing in Streamlit Secrets!")
    st.stop()

# =========================================================
# 3. CSS ENGINE (ZOOM & FOCUS FIX)
# =========================================================
st.markdown("""
    <style>
    /* --------------------------------------------------------
       FONTS & GLOBAL RESET
    -------------------------------------------------------- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp {
        background-color: #0f171c;
        font-family: 'Inter', sans-serif;
    }
    
    /* HIDE DEFAULT STREAMLIT ELEMENTS */
    header, footer, #MainMenu {display: none !important;}
    
    /* THE ZOOM FIX: 
       We constrain the main container to 1000px.
       This forces the content to be large and centered, 
       eliminating the "zoomed out" look on large monitors.
    */
    .block-container {
        max-width: 1000px !important;
        padding-top: 3rem !important;
        padding-bottom: 5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        margin: 0 auto !important;
    }

    /* --------------------------------------------------------
       NAVBAR
    -------------------------------------------------------- */
    .navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        margin-bottom: 50px;
    }
    .logo {
        font-size: 22px;
        font-weight: 800;
        color: #fff;
        letter-spacing: -0.5px;
    }
    .logo span { color: #ff4d4d; }
    
    .nav-links {
        display: flex;
        gap: 30px;
        font-size: 13px;
        font-weight: 600;
        color: #cbd5e1;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .btn-cta {
        background-color: #ff4d4d;
        color: white;
        padding: 10px 22px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 14px;
        border: none;
        cursor: pointer;
        text-decoration: none;
    }

    /* --------------------------------------------------------
       HERO TYPOGRAPHY (SCALED UP)
    -------------------------------------------------------- */
    .hero-title {
        font-size: 72px; /* Larger font to fill space */
        font-weight: 800;
        font-style: italic;
        color: #fff;
        text-align: center;
        margin-bottom: 15px;
        line-height: 1.05;
        letter-spacing: -1.5px;
    }
    .hero-sub {
        font-size: 19px; /* Larger for readability */
        color: #94a3b8;
        text-align: center;
        max-width: 700px;
        margin: 0 auto 50px auto;
        line-height: 1.6;
        font-weight: 400;
    }

    /* --------------------------------------------------------
       THE UPLOADER (PERFECTLY CENTERED)
    -------------------------------------------------------- */
    /* 1. The Container Box */
    [data-testid="stFileUploader"] {
        background-color: rgba(31, 46, 56, 0.4);
        border: 2px dashed #334155;
        border-radius: 16px;
        padding: 50px 0px; /* Vertical padding */
        text-align: center;
        transition: border-color 0.3s;
        max-width: 750px; /* Enforce width */
        margin: 0 auto;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #ff4d4d;
        background-color: rgba(31, 46, 56, 0.6);
    }

    /* 2. Hide Native Elements */
    [data-testid="stFileUploaderDropzone"] div div::before {display: none;}
    [data-testid="stFileUploaderDropzone"] div div span {display: none;}
    [data-testid="stFileUploaderDropzoneInstructions"] {display: none;}
    
    /* 3. Inject Custom Icon & Text (Centered Flex Logic) */
    [data-testid="stFileUploaderDropzone"] {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 15px;
        min-height: 200px; /* Ensure height matches screenshot */
    }
    
    [data-testid="stFileUploaderDropzone"]::before {
        content: "☁️"; 
        font-size: 48px;
        margin-bottom: 5px;
        line-height: 1;
    }
    
    [data-testid="stFileUploaderDropzone"]::after {
        content: "Drop your P&L or Chart screenshot here\\A Supports PNG, JPG (Max 10MB). Encrypted.";
        white-space: pre-wrap;
        font-weight: 700;
        font-size: 18px;
        color: white;
        text-align: center;
        margin-bottom: 10px;
    }

    /* 4. Style the Button (White, Centered) */
    button[data-testid="baseButton-secondary"] {
        background-color: white !important;
        color: #0f171c !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 28px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        margin-top: 10px !important;
        width: auto !important;
    }
    button[data-testid="baseButton-secondary"]:hover {
        background-color: #e2e8f0 !important;
        transform: translateY(-1px);
    }
    
    /* Remove file list bg */
    [data-testid="stFileUploaderUploadedFiles"] {
        background: transparent;
    }

    /* --------------------------------------------------------
       FEATURE CARDS
    -------------------------------------------------------- */
    .feature-card {
        background-color: #1a222a;
        padding: 25px;
        border-radius: 10px;
        height: 100%;
        border: 1px solid #2d3748;
    }
    .f-head {
        color: #fff;
        font-weight: 700;
        font-size: 17px;
        margin-bottom: 8px;
    }
    .f-body {
        color: #8b9bb4;
        font-size: 14px;
        line-height: 1.5;
    }
    
    /* Analysis Box */
    .analysis-result {
        background: #161b22;
        border-left: 5px solid #ff4d4d;
        padding: 25px;
        border-radius: 8px;
        margin-top: 30px;
        font-family: 'Inter', monospace;
        color: #e2e8f0;
        font-size: 15px;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 4. AI BACKEND
# =========================================================
def query_router(payload):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
        "X-Wait-For-Model": "true" 
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        return response
    except Exception as e:
        return None

# =========================================================
# 5. UI LAYOUT
# =========================================================

# --- NAVBAR ---
st.markdown("""
<div class="navbar">
    <div class="logo">STOCK<span>POSTMORTEM</span>.AI</div>
    <div class="nav-links">
        <span>Analyze</span>
        <span>Case Studies</span>
        <span>Pricing</span>
    </div>
    <button class="btn-cta">Get Started</button>
</div>
""", unsafe_allow_html=True)

# --- HERO SECTION ---
st.markdown('<div class="hero-title">STOP BLEEDING CAPITAL.</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Upload your losing trade screenshots. Our AI identifies psychological traps, technical failures, and provides a surgical path to recovery.</div>', unsafe_allow_html=True)

# --- UPLOAD SECTION ---
# We treat this as a single block. The CSS above handles the centering.
uploaded_file = st.file_uploader("", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

if uploaded_file:
    # Use columns to center the 'Analyze' button nicely
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("RUN FORENSIC DIAGNOSTIC", type="primary", use_container_width=True):
            with st.spinner("DECRYPTING TRADE PATTERNS..."):
                try:
                    # Image Processing
                    image = Image.open(uploaded_file)
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    
                    # Analysis Prompt
                    prompt = (
                        "ACT AS: Senior Hedge Fund Risk Manager. "
                        "INPUT: A trading chart or P&L screenshot. "
                        "TASK: "
                        "1. Identify the 'Kill Zone' (Where the trade failed). "
                        "2. Detect Psychological Errors (FOMO, Greed, Revenge). "
                        "3. Audit Position Sizing & Stop Loss. "
                        "4. Prescribe a 3-Step Recovery Protocol. "
                        "OUTPUT: Brutally honest, direct, professional tone."
                    )
                    
                    payload = {
                        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                        "messages": [
                            {"role": "user", "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                            ]}
                        ],
                        "max_tokens": 1000
                    }
                    
                    res = query_router(payload)
                    if res and res.status_code == 200:
                        content = res.json()["choices"][0]["message"]["content"]
                        st.markdown(f'<div class="analysis-result">{content}</div>', unsafe_allow_html=True)
                    else:
                        st.error("AI Analysis Failed. Please try again.")
                except Exception as e:
                    st.error(f"Error: {e}")

# --- SPACER ---
st.markdown("<br><br>", unsafe_allow_html=True)

# --- FEATURE GRID ---
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div class="feature-card">
        <div class="f-head">Pattern Recognition</div>
        <div class="f-body">Did you buy the top? We identify if you're falling for FOMO or revenge trading instantly.</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="feature-card">
        <div class="f-head">Risk Autopsy</div>
        <div class="f-body">Calculates if your stop-loss was too tight or if your position sizing was reckless based on P&L.</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="feature-card">
        <div class="f-head">Recovery Plan</div>
        <div class="f-body">Step-by-step technical adjustments to ensure the next trade is a winner, not a gamble.</div>
    </div>
    """, unsafe_allow_html=True)
