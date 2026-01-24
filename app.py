import streamlit as st
import requests
import base64
import io
from PIL import Image

# 1. PAGE CONFIG
st.set_page_config(page_title="StockPostmortem.ai", page_icon="🩸", layout="wide")

# 2. API SETUP
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except Exception:
    st.error("⚠️ HF_TOKEN is missing. Add it to Streamlit Secrets.")
    st.stop()

# 3. CSS OVERRIDES (THE FIX)
st.markdown("""
<style>
    /* RESET & FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    body, .stApp { 
        background-color: #0f171c !important; 
        font-family: 'Inter', sans-serif !important; 
        color: #e2e8f0 !important; 
    }
    
    /* HIDE DEFAULT HEADER/FOOTER */
    header, footer, #MainMenu { display: none !important; }
    .block-container { padding-top: 0rem !important; max-width: 1000px !important; }

    /* --- NAV --- */
    .nav { 
        display: flex; justify-content: space-between; align-items: center; 
        padding: 1.5rem 0; border-bottom: 1px solid #2d4250; margin-bottom: 4rem; 
    }
    .logo { font-size: 1.5rem; font-weight: 800; letter-spacing: -0.05em; color: white; }
    .logo span { color: #ff4d4d; }
    .cta-btn { 
        background: #dc2626; color: white; padding: 0.6rem 1.5rem; 
        border-radius: 99px; border: none; font-weight: 600; 
    }

    /* --- HERO --- */
    .hero-h1 { 
        font-size: 4rem; font-weight: 800; font-style: italic; 
        text-align: center; color: white; line-height: 1.1; margin-bottom: 1rem; 
    }
    .hero-p { 
        text-align: center; color: #94a3b8; font-size: 1.2rem; 
        max-width: 700px; margin: 0 auto 3rem auto; 
    }

    /* ============================================================
       PIXEL PERFECT UPLOADER STYLING
       ============================================================ */

    /* 1. THE CONTAINER (Glass Card) */
    [data-testid="stFileUploaderDropzone"] {
        background-color: rgba(31, 46, 56, 0.6) !important;
        border: 2px dashed #475569 !important;
        border-radius: 1rem !important;
        min-height: 350px !important; /* Fixed height for spacing */
        
        /* FLEXBOX MAGIC: Centers everything vertically */
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 1.5rem !important; /* Space between Icon, Text, Button */
        padding: 2rem !important;
    }

    /* Hover State */
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #ff4d4d !important;
        background-color: rgba(31, 46, 56, 0.8) !important;
    }

    /* 2. THE ICON (Your Red Cloud) */
    /* We inject this via ::before on the container */
    [data-testid="stFileUploaderDropzone"]::before {
        content: "";
        display: block;
        width: 60px;
        height: 60px;
        /* The exact SVG from your HTML encoded */
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23ef4444'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12' /%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: center;
        background-size: contain;
        order: 1; /* Force to Top */
    }

    /* 3. THE TEXT (Replacements) */
    /* Hide the ugly default "Drag and drop..." text container */
    [data-testid="stFileUploaderDropzoneInstructions"] {
        display: none !important; 
    }
    
    /* Inject YOUR Text using ::after on the container so it sits under the icon */
    [data-testid="stFileUploaderDropzone"]::after {
        content: "Drop your P&L or Chart screenshot here\\A Supports PNG, JPG (Max 10MB). Your data is encrypted.";
        white-space: pre-wrap; /* Allows line break */
        text-align: center;
        color: #e2e8f0;
        font-size: 1.25rem;
        font-weight: 600;
        line-height: 1.6;
        order: 2; /* Sits below Icon */
    }
    
    /* 4. THE BUTTON ("Select File") */
    [data-testid="stFileUploaderDropzone"] button {
        order: 3; /* Sits at bottom */
        background-color: white !important;
        border: none !important;
        padding: 12px 30px !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        color: black !important;
        transition: all 0.2s;
        margin-top: 10px !important;
        
        /* Fix width to match design */
        width: auto !important;
        display: inline-block !important;
    }

    /* Button Hover */
    [data-testid="stFileUploaderDropzone"] button:hover {
        background-color: #cbd5e1 !important;
        transform: scale(1.05);
    }

    /* HIDE DEFAULT ICONS (The small cloud icon from Streamlit) */
    [data-testid="stFileUploaderDropzone"] div[role="button"] > div > svg {
        display: none !important;
    }
    
    /* Fix: Button Text Replacement Hack */
    /* Streamlit button says "Browse files". We hide that text and overlay "Select File" */
    [data-testid="stFileUploaderDropzone"] button {
        color: transparent !important;
        position: relative;
    }
    [data-testid="stFileUploaderDropzone"] button::after {
        content: "Select File";
        position: absolute;
        color: black;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        white-space: nowrap;
    }

    /* --- FEATURE GRID --- */
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; margin-top: 4rem; }
    .card { background: #1f2e38; padding: 1.5rem; border-radius: 0.75rem; }
    .card h3 { color: white; font-weight: 700; margin-bottom: 0.5rem; }
    .card p { color: #94a3b8; font-size: 0.9rem; }

</style>
""", unsafe_allow_html=True)

# 4. UI RENDER
# Navbar
st.markdown("""
<div class="nav">
    <div class="logo">STOCK<span>POSTMORTEM</span>.AI</div>
    <button class="cta-btn">Get Started</button>
</div>
<div class="hero-h1">STOP BLEEDING CAPITAL.</div>
<div class="hero-p">Upload your losing trade screenshots. Our AI identifies psychological traps, technical failures, and provides a surgical path to recovery.</div>
""", unsafe_allow_html=True)

# Uploader Section
c1, c2, c3 = st.columns([1, 8, 1])
with c2:
    uploaded_file = st.file_uploader(" ", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

# Logic
if uploaded_file:
    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1, 1, 1])
    with b2:
        if st.button("RUN FORENSIC ANALYSIS", type="primary", use_container_width=True):
            with st.spinner("🔍 ANALYZING CHART..."):
                try:
                    image = Image.open(uploaded_file)
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

                    prompt = "ACT AS: Trading Psychologist. INPUT: Chart Image. OUTPUT: 1. Technical Mistake. 2. Emotional Trap. 3. Risk Management Fail. Be brutal and concise."
                    
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
                        st.markdown(f"""<div style="background: #161b22; border-left: 5px solid #ff4d4d; padding: 25px; border-radius: 8px; margin-top: 20px;">{content}</div>""", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")

# Footer Grid
st.markdown("""
<div class="grid">
    <div class="card">
        <h3>Pattern Recognition</h3>
        <p>Did you buy the top? We identify if you're falling for FOMO or revenge trading.</p>
    </div>
    <div class="card">
        <h3>Risk Autopsy</h3>
        <p>Calculates if your stop-loss was too tight or if your position sizing was reckless.</p>
    </div>
    <div class="card">
        <h3>Recovery Plan</h3>
        <p>Step-by-step technical adjustments to ensure the next trade is a winner.</p>
    </div>
</div>
<div style="text-align: center; margin-top: 4rem; color: #64748b; font-size: 0.8rem;">
    &copy; 2026 stockpostmortem.ai | Trading involves risk.
</div>
""", unsafe_allow_html=True)
