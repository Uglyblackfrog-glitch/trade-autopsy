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
# 3. CSS ENGINE (PIXEL-PERFECT RECONSTRUCTION)
# =========================================================
st.markdown("""
    <style>
    /* --------------------------------------------------------
       FONTS & GLOBAL RESET
    -------------------------------------------------------- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,600;0,700;0,800;1,800&display=swap');

    .stApp {
        background-color: #0f171c;
        font-family: 'Inter', sans-serif;
    }
    
    /* REMOVE DEFAULT STREAMLIT PADDING/MARGINS */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 5rem !important;
        max-width: 1400px;
    }
    header, footer, #MainMenu {visibility: hidden;}

    /* --------------------------------------------------------
       NAVBAR (Exact Match)
    -------------------------------------------------------- */
    .navbar-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 0;
        margin-bottom: 80px;
    }
    .logo {
        font-size: 20px;
        font-weight: 800;
        color: #fff;
        letter-spacing: 0.5px;
    }
    .logo span { color: #ff4d4d; }
    
    .nav-links {
        display: flex;
        gap: 40px;
        font-size: 13px;
        font-weight: 600;
        color: #e2e8f0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .get-started-btn {
        background-color: #ff4d4d;
        color: white;
        padding: 10px 24px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 14px;
        text-decoration: none;
        border: none;
    }

    /* --------------------------------------------------------
       HERO TEXT
    -------------------------------------------------------- */
    .hero-title {
        font-size: 68px;
        font-weight: 800;
        font-style: italic;
        color: #fff;
        text-align: center;
        margin-bottom: 10px;
        line-height: 1.1;
        letter-spacing: -1px;
    }
    .hero-sub {
        font-size: 18px;
        color: #94a3b8;
        text-align: center;
        max-width: 750px;
        margin: 0 auto 60px auto;
        line-height: 1.6;
    }

    /* --------------------------------------------------------
       CUSTOM UPLOADER CONTAINER
       We create a visual box, then hack the Streamlit uploader
       to fit inside it perfectly.
    -------------------------------------------------------- */
    .upload-box {
        border: 2px dashed #334155;
        background-color: rgba(31, 46, 56, 0.4);
        border-radius: 16px;
        padding: 50px 20px 30px 20px; /* Top padding for icon/text */
        text-align: center;
        max-width: 800px;
        margin: 0 auto 80px auto;
        position: relative;
    }
    .upload-icon {
        font-size: 40px;
        color: #ff4d4d;
        margin-bottom: 15px;
    }
    .upload-title {
        font-size: 20px;
        font-weight: 700;
        color: white;
        margin-bottom: 8px;
    }
    .upload-desc {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 20px;
    }

    /* --------------------------------------------------------
       OVERRIDING STREAMLIT FILE UPLOADER
    -------------------------------------------------------- */
    /* Target the dropzone to make it invisible but present */
    div[data-testid="stFileUploader"] {
        width: 100%;
        margin: 0 auto;
    }
    section[data-testid="stFileUploaderDropzone"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        min-height: 0px !important;
    }
    /* Hide the default drag-and-drop text/icon */
    div[data-testid="stFileUploaderDropzoneInstructions"] {
        display: none;
    }
    /* Style the Browse Button to look like "Select File" */
    button[data-testid="baseButton-secondary"] {
        background-color: #ffffff !important;
        color: #0f171c !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        padding: 10px 24px !important;
        font-size: 14px !important;
        transition: transform 0.2s;
        margin: 0 auto !important;
        display: block !important;
    }
    button[data-testid="baseButton-secondary"]:hover {
        transform: scale(1.05);
        background-color: #f1f5f9 !important;
    }
    /* Small text below button (Limit 200MB) styling */
    small {
        color: #475569 !important;
        font-size: 12px !important;
    }

    /* --------------------------------------------------------
       FEATURE CARDS (Bottom Grid)
    -------------------------------------------------------- */
    .feature-grid {
        display: flex;
        gap: 20px;
        justify-content: center;
        max-width: 1100px;
        margin: 0 auto;
    }
    .feature-card {
        background-color: #1a232b; /* Slightly lighter than bg */
        border: 1px solid #2d3748; /* Subtle border */
        padding: 30px;
        border-radius: 8px;
        flex: 1;
        text-align: left;
    }
    .f-title {
        color: white;
        font-weight: 700;
        font-size: 16px;
        margin-bottom: 12px;
    }
    .f-desc {
        color: #94a3b8;
        font-size: 14px;
        line-height: 1.5;
    }
    
    /* Result Box Styling */
    .result-container {
        background: #161b22; 
        border-left: 4px solid #ff4d4d;
        padding: 25px; 
        border-radius: 6px; 
        margin-top: 30px; 
        color: #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 4. AI LOGIC (Unchanged)
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
<div class="navbar-container">
    <div class="logo">STOCKPOSTMORTEM<span>.AI</span></div>
    <div class="nav-links">
        <span>Analyze</span>
        <span>Case Studies</span>
        <span>Pricing</span>
    </div>
    <button class="get-started-btn">Get Started</button>
</div>
""", unsafe_allow_html=True)

# --- HERO SECTION ---
st.markdown('<div class="hero-title">STOP BLEEDING CAPITAL.</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Upload your losing trade screenshots. Our AI identifies psychological traps, technical failures, and provides a surgical path to recovery.</div>', unsafe_allow_html=True)

# --- THE "PERFECT" UPLOADER BOX ---
# We create the visual container first
st.markdown('<div class="upload-box">', unsafe_allow_html=True)

# Inner visual elements (Cloud, Text)
st.markdown("""
    <div class="upload-icon">☁️</div>
    <div class="upload-title">Drop your P&L or Chart screenshot here</div>
    <div class="upload-desc">Supports PNG, JPG (Max 10MB). Your data is encrypted and deleted after analysis.</div>
""", unsafe_allow_html=True)

# The Functional Streamlit Uploader (Styled to blend in via CSS)
uploaded_file = st.file_uploader("", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

st.markdown('</div>', unsafe_allow_html=True) # Close box

# --- ANALYSIS LOGIC ---
if uploaded_file:
    # We place the button outside/below the box or just trigger immediately
    # To keep UI clean, let's show a big button once file is ready
    col_c = st.columns([1,2,1])
    with col_c[1]:
        if st.button("RUN FORENSIC ANALYSIS", type="primary", use_container_width=True):
            with st.spinner("Deciphering Trade Data..."):
                try:
                    image = Image.open(uploaded_file)
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    
                    system_logic = (
                        "ACT AS: A Wall Street Trading Psychologist & Risk Manager. "
                        "INPUT: A trading chart or P&L screenshot. "
                        "TASK: "
                        "1. Identify the 'Kill Zone' (Where the trade went wrong). "
                        "2. Diagnose the Psychology (FOMO, Revenge, Greed). "
                        "3. Audit the Risk (Stop loss placement, sizing). "
                        "4. Provide a 3-step Recovery Protocol. "
                        "OUTPUT STYLE: Brutally honest, direct, professional."
                    )
                    
                    payload = {
                        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                        "messages": [
                            {"role": "user", "content": [
                                {"type": "text", "text": system_logic},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                            ]}
                        ],
                        "max_tokens": 1000
                    }
                    
                    res = query_router(payload)
                    if res and res.status_code == 200:
                        analysis = res.json()['choices'][0]['message']['content']
                        st.markdown(f'<div class="result-container">{analysis}</div>', unsafe_allow_html=True)
                    else:
                        st.error("AI Connection Failed.")
                except Exception as e:
                    st.error(f"Error: {e}")

# --- FEATURE GRID ---
# Using standard HTML columns for exact spacing match
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="f-title">Pattern Recognition</div>
        <div class="f-desc">Did you buy the top? We identify if you're falling for FOMO or revenge trading.</div>
    </div>
    <div class="feature-card">
        <div class="f-title">Risk Autopsy</div>
        <div class="f-desc">Calculates if your stop-loss was too tight or if your position sizing was reckless.</div>
    </div>
    <div class="feature-card">
        <div class="f-title">Recovery Plan</div>
        <div class="f-desc">Step-by-step technical adjustments to ensure the next trade is a winner.</div>
    </div>
</div>
""", unsafe_allow_html=True)
