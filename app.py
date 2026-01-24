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
# 2. YOUR API CREDENTIALS
# =========================================================
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except Exception:
    st.error("⚠️ HF_TOKEN is missing in Streamlit Secrets.")
    st.stop()

# =========================================================
# 3. CSS ENGINE (HARDCODED - NO EXTERNAL SCRIPTS)
# =========================================================
st.markdown("""
<style>
    /* RESET & BASICS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    * { box-sizing: border-box; }
    
    .stApp {
        background-color: #0f171c !important;
        font-family: 'Inter', sans-serif !important;
        color: #e2e8f0;
    }

    /* HIDE DEFAULT STREAMLIT BLOAT */
    #MainMenu, header, footer { display: none !important; }
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 5rem !important;
        max-width: 1200px !important;
    }

    /* -------------------------------------------------------
       NAVBAR STYLES
    ------------------------------------------------------- */
    .nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.5rem 0;
        border-bottom: 1px solid #2d4250;
        margin-bottom: 4rem;
    }
    .logo {
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: -0.05em;
        color: white;
    }
    .logo span { color: #ff4d4d; }
    
    .nav-links {
        display: flex;
        gap: 2rem;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #cbd5e1;
    }
    .btn-cta {
        background-color: #dc2626;
        color: white;
        padding: 0.5rem 1.25rem;
        border-radius: 9999px;
        font-weight: 600;
        border: none;
        cursor: pointer;
    }

    /* -------------------------------------------------------
       HERO TEXT
    ------------------------------------------------------- */
    .hero-h1 {
        font-size: 4rem;
        font-weight: 800;
        font-style: italic;
        text-align: center;
        margin-bottom: 1.5rem;
        line-height: 1.1;
    }
    @media (max-width: 768px) { .hero-h1 { font-size: 2.5rem; } }
    
    .hero-p {
        font-size: 1.25rem;
        color: #94a3b8;
        text-align: center;
        max-width: 42rem;
        margin: 0 auto 3rem auto;
        line-height: 1.6;
    }

    /* -------------------------------------------------------
       CUSTOM UPLOADER STYLING
       This hacks the Streamlit uploader to look like your card
    ------------------------------------------------------- */
    [data-testid="stFileUploader"] {
        background-color: rgba(31, 46, 56, 0.6);
        border: 2px dashed #475569;
        border-radius: 1rem;
        padding: 3rem 1rem;
        text-align: center;
        transition: all 0.3s;
        max-width: 800px;
        margin: 0 auto;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #ff4d4d;
        background-color: rgba(31, 46, 56, 0.8);
    }
    /* Hide the small "Drag and drop" text */
    [data-testid="stFileUploaderDropzoneInstructions"] { display: none; }
    
    /* Center the button inside */
    [data-testid="stBaseButton-secondary"] {
        margin: 0 auto;
    }

    /* -------------------------------------------------------
       GRID LAYOUT
    ------------------------------------------------------- */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 2rem;
        margin-top: 5rem;
    }
    .feature-card {
        background-color: #1f2e38;
        padding: 1.5rem;
        border-radius: 0.75rem;
    }
    .f-title {
        font-weight: 700;
        font-size: 1.125rem;
        margin-bottom: 0.5rem;
        color: white;
    }
    .f-desc {
        font-size: 0.875rem;
        color: #94a3b8;
    }

    /* -------------------------------------------------------
       AI RESULT BOX
    ------------------------------------------------------- */
    .result-box {
        background: #161b22;
        border-left: 5px solid #ff4d4d;
        padding: 2rem;
        margin-top: 2rem;
        border-radius: 8px;
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 4. RENDER UI
# =========================================================

# --- NAVBAR ---
st.markdown("""
<div class="nav-container">
    <div class="logo">STOCK<span>POSTMORTEM</span>.AI</div>
    <div class="nav-links">
        <span>Analyze</span>
        <span>Case Studies</span>
        <span>Pricing</span>
    </div>
    <button class="btn-cta">Get Started</button>
</div>
""", unsafe_allow_html=True)

# --- HERO ---
st.markdown("""
<h1 class="hero-h1">STOP BLEEDING CAPITAL.</h1>
<p class="hero-p">Upload your losing trade screenshots. Our AI identifies psychological traps, technical failures, and provides a surgical path to recovery.</p>
""", unsafe_allow_html=True)

# --- UPLOADER SECTION ---
# We use standard Streamlit uploader, but the CSS above forces it to look like your card
uploaded_file = st.file_uploader(" ", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

# Visual guide text inside the uploader area (since we hid the default text)
if not uploaded_file:
    st.markdown("""
    <div style="text-align: center; margin-top: -80px; margin-bottom: 40px; pointer-events: none; position: relative; z-index: 1;">
        <div style="font-size: 3rem; margin-bottom: 10px;">☁️</div>
        <div style="font-weight: 600; font-size: 1.2rem; color: white;">Drop your P&L or Chart screenshot here</div>
        <div style="color: #64748b; font-size: 0.9rem;">Supports PNG, JPG (Max 10MB)</div>
    </div>
    """, unsafe_allow_html=True)

# --- ANALYSIS LOGIC ---
if uploaded_file:
    # Centered "Run Analysis" Button
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("RUN FORENSIC ANALYSIS", type="primary", use_container_width=True):
            with st.spinner("🔍 DECRYPTING MARKET DATA..."):
                try:
                    # Process Image
                    image = Image.open(uploaded_file)
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    
                    # AI Prompt
                    prompt = (
                        "ACT AS: Senior Trading Psychologist & Risk Manager. "
                        "INPUT: Trading Chart or P&L. "
                        "TASK: 1. Identify the 'Kill Zone' (Mistake). 2. Diagnose Psychology (FOMO/Revenge). 3. Audit Risk. 4. Fix it."
                        "OUTPUT: Brutally honest, concise, bullet points. Use bolding."
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
                    
                    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                    res = requests.post(API_URL, headers=headers, json=payload)
                    
                    if res.status_code == 200:
                        content = res.json()["choices"][0]["message"]["content"]
                        st.markdown(f'<div class="result-box">{content}</div>', unsafe_allow_html=True)
                    else:
                        st.error("AI Server Error. Please try again.")
                except Exception as e:
                    st.error(f"Error: {e}")

# --- FEATURE GRID ---
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="f-title">Pattern Recognition</div>
        <div class="f-desc">Did you buy the top? We identify if you're falling for FOMO or revenge trading instantly.</div>
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
<br><br>
<div style="text-align: center; color: #475569; font-size: 0.8rem; border-top: 1px solid #2d4250; padding-top: 2rem;">
    &copy; 2026 stockpostmortem.ai | Trading involves risk. Keep your head cool.
</div>
""", unsafe_allow_html=True)
