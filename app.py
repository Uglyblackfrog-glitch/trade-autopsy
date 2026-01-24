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
    layout="wide",
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
# 3. CSS ENGINE (SURGICAL RECONSTRUCTION)
# =========================================================
st.markdown("""
    <style>
    /* --------------------------------------------------------
       FONTS & GLOBAL RESET
    -------------------------------------------------------- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    .stApp {
        background-color: #0f171c;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Default Header/Footer */
    header, footer, #MainMenu {display: none !important;}
    
    /* Layout Constraints - Fixes "Zoomed Out" feel */
    .block-container {
        max-width: 1200px;
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
        margin: 0 auto;
    }

    /* --------------------------------------------------------
       NAVBAR (Flexbox)
    -------------------------------------------------------- */
    .navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 0;
        margin-bottom: 60px;
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
        gap: 40px;
        font-size: 13px;
        font-weight: 600;
        color: #cbd5e1;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .btn-red {
        background-color: #ff4d4d;
        color: white;
        padding: 10px 24px;
        border-radius: 6px; /* Slightly squared like screenshot */
        font-weight: 600;
        font-size: 14px;
        border: none;
        cursor: pointer;
    }

    /* --------------------------------------------------------
       HERO TEXT
    -------------------------------------------------------- */
    .hero-title {
        font-size: 64px;
        font-weight: 800;
        font-style: italic;
        color: #fff;
        text-align: center;
        margin-bottom: 15px;
        line-height: 1.1;
    }
    .hero-sub {
        font-size: 16px;
        color: #94a3b8;
        text-align: center;
        max-width: 650px;
        margin: 0 auto 50px auto;
        line-height: 1.6;
    }

    /* --------------------------------------------------------
       THE UPLOADER HACK (The Magic Part)
       We target the internal Streamlit classes to force the UI.
    -------------------------------------------------------- */
    
    /* 1. The Container Box (Dashed) */
    [data-testid="stFileUploader"] {
        background-color: rgba(31, 46, 56, 0.4);
        border: 2px dashed #334155;
        border-radius: 16px;
        padding: 60px 20px; /* Tall padding to fit icon/text */
        text-align: center;
        transition: border-color 0.3s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #ff4d4d;
        background-color: rgba(31, 46, 56, 0.6);
    }

    /* 2. Hide the default "Drag and drop file here" Text & Icon */
    [data-testid="stFileUploaderDropzone"] div div::before {display: none;}
    [data-testid="stFileUploaderDropzone"] div div span {display: none;} 
    [data-testid="stFileUploaderDropzoneInstructions"] {display: none;}
    
    /* 3. Inject CUSTOM Icon and Text using Pseudo-elements on the Dropzone */
    [data-testid="stFileUploaderDropzone"]::before {
        content: "☁️"; /* Cloud Icon */
        display: block;
        font-size: 40px;
        margin-bottom: 20px;
        filter: hue-rotate(140deg); /* Adjust color if needed, or use emoji */
    }
    
    [data-testid="stFileUploaderDropzone"]::after {
        content: "Drop your P&L or Chart screenshot here\\A Supports PNG, JPG (Max 10MB). Your data is encrypted.";
        white-space: pre-wrap; /* Allows line break \A */
        display: block;
        font-weight: 700;
        font-size: 18px;
        color: white;
        margin-bottom: 20px;
        line-height: 1.5;
    }

    /* 4. Style the "Browse files" button to look like "Select File" (White) */
    button[data-testid="baseButton-secondary"] {
        background-color: white !important;
        color: #0f171c !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 24px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        margin-top: 10px !important;
    }
    button[data-testid="baseButton-secondary"]:hover {
        background-color: #f1f5f9 !important;
        transform: scale(1.02);
    }

    /* 5. Clean up the uploaded file list */
    [data-testid="stFileUploaderUploadedFiles"] {
        background: transparent;
    }

    /* --------------------------------------------------------
       FEATURE CARDS (Bottom)
    -------------------------------------------------------- */
    .feature-card {
        background-color: #1a222a; /* Exact dark slate */
        padding: 25px;
        border-radius: 8px;
        height: 100%;
        border: 1px solid #2d3748;
    }
    .f-head {
        color: #fff;
        font-weight: 700;
        font-size: 16px;
        margin-bottom: 10px;
    }
    .f-body {
        color: #8b9bb4;
        font-size: 13px;
        line-height: 1.5;
    }

    /* Result Box */
    .analysis-box {
        background: #161b22;
        border-left: 4px solid #ff4d4d;
        padding: 20px;
        border-radius: 6px;
        margin-top: 30px;
        font-family: 'Inter', monospace;
        color: #e2e8f0;
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
    <button class="btn-red">Get Started</button>
</div>
""", unsafe_allow_html=True)

# --- HERO SECTION ---
# We use columns to center the hero text tightly (fixing "zoomed out" look)
h1, h2, h3 = st.columns([1, 8, 1])
with h2:
    st.markdown('<div class="hero-title">STOP BLEEDING CAPITAL.</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="hero-sub">
            Upload your losing trade screenshots. Our AI identifies psychological traps,
            technical failures, and provides a surgical path to recovery.
        </div>
    """, unsafe_allow_html=True)

# --- UPLOAD SECTION ---
# We use a narrower column ratio for the uploader to match the screenshot width perfectly
u1, u2, u3 = st.columns([1, 2, 1]) # 1:2:1 Ratio keeps it centered and bounded

with u2:
    # This single line creates the ENTIRE dashed box UI thanks to the CSS hacks above
    uploaded_file = st.file_uploader("", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    
    if uploaded_file:
        # Generate Analysis Button
        if st.button("RUN DIAGNOSTIC", type="primary", use_container_width=True):
            with st.spinner("ANALYZING PRICE ACTION & PSYCHOLOGY..."):
                try:
                    # Image Processing
                    image = Image.open(uploaded_file)
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    
                    # Prompt Logic
                    prompt = (
                        "ACT AS: Senior Trading Psychologist & Risk Manager. "
                        "INPUT: Trading Chart or P&L. "
                        "TASK: 1. Identify the 'Kill Zone' (Mistake). 2. Diagnose Psychology (FOMO/Revenge). 3. Audit Risk. 4. Fix it."
                        "OUTPUT: Brutally honest, concise, bullet points."
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
                        st.markdown(f'<div class="analysis-box">{res.json()["choices"][0]["message"]["content"]}</div>', unsafe_allow_html=True)
                    else:
                        st.error("AI Connection Error.")
                except Exception as e:
                    st.error(f"Error: {e}")

# --- SPACER ---
st.markdown("<br><br>", unsafe_allow_html=True)

# --- FEATURE GRID ---
# Columns match the screenshot's 3-card layout
f1, f2, f3 = st.columns(3)

with f1:
    st.markdown("""
    <div class="feature-card">
        <div class="f-head">Pattern Recognition</div>
        <div class="f-body">Did you buy the top? We identify if you're falling for FOMO or revenge trading instantly.</div>
    </div>
    """, unsafe_allow_html=True)

with f2:
    st.markdown("""
    <div class="feature-card">
        <div class="f-head">Risk Autopsy</div>
        <div class="f-body">Calculates if your stop-loss was too tight or if your position sizing was reckless based on P&L.</div>
    </div>
    """, unsafe_allow_html=True)

with f3:
    st.markdown("""
    <div class="feature-card">
        <div class="f-head">Recovery Plan</div>
        <div class="f-body">Step-by-step technical adjustments to ensure the next trade is a winner, not a gamble.</div>
    </div>
    """, unsafe_allow_html=True)
