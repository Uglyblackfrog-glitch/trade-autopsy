import streamlit as st
import requests
import base64
import io
from PIL import Image

# 1. PAGE SETUP
st.set_page_config(page_title="StockPostmortem.ai", page_icon="🩸", layout="wide")

# 2. API KEYS
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except Exception:
    st.error("⚠️ HF_TOKEN is missing in Streamlit Secrets.")
    st.stop()

# 3. THE "NUCLEAR" CSS OVERRIDE
st.markdown("""
<style>
    /* --- FONTS & BASICS --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    .stApp { 
        background-color: #0f171c; 
        font-family: 'Inter', sans-serif; 
        color: #e2e8f0; 
    }
    
    /* Hide Streamlit Header/Footer */
    header, footer, #MainMenu { display: none !important; }
    
    /* Layout Constraints */
    .block-container { 
        padding-top: 0rem; 
        padding-bottom: 5rem; 
        max-width: 1000px; 
    }

    /* --- NAVBAR --- */
    .nav { 
        display: flex; 
        justify-content: space-between; 
        align-items: center;
        padding: 1.5rem 0; 
        border-bottom: 1px solid #2d4250; 
        margin-bottom: 5rem; 
    }
    .logo { font-size: 1.5rem; font-weight: 800; letter-spacing: -0.05em; color: white; }
    .logo span { color: #ff4d4d; }
    .cta-btn { 
        background: #dc2626; 
        color: white; 
        padding: 0.6rem 1.5rem; 
        border-radius: 99px; 
        font-weight: 600; 
        font-size: 0.9rem;
        border: none; 
    }

    /* --- HERO TEXT --- */
    .hero-title {
        font-size: 4.5rem;
        font-weight: 800;
        font-style: italic;
        text-align: center;
        margin-bottom: 1.5rem;
        line-height: 1;
        color: white;
    }
    .hero-sub {
        text-align: center;
        color: #94a3b8;
        font-size: 1.25rem;
        margin-bottom: 4rem;
        max-width: 700px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.6;
    }

    /* ============================================================
       THE UPLOADER HACK - PIXEL PERFECT
       ============================================================ */

    /* 1. The Container Box - Exact Glass Card Styling */
    [data-testid="stFileUploaderDropzone"] {
        background-color: rgba(31, 46, 56, 0.6);
        border: 2px dashed #475569;
        border-radius: 1rem;
        padding: 4rem 2rem;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 320px;
        transition: border 0.3s ease;
    }
    
    /* Hover Effect on Box */
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #ff4d4d;
        background-color: rgba(31, 46, 56, 0.8);
    }

    /* 2. Hide Default Streamlit Icon & Text COMPLETELY */
    [data-testid="stFileUploaderDropzone"] div svg { display: none !important; }
    [data-testid="stFileUploaderDropzone"] small { display: none !important; }
    [data-testid="stFileUploaderDropzone"] span { display: none !important; }

    /* 3. Inject YOUR Red Cloud Icon */
    [data-testid="stFileUploaderDropzone"]::before {
        content: "";
        display: block;
        width: 64px;
        height: 64px;
        margin-bottom: 1.5rem;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23ef4444'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12' /%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: center;
        background-size: contain;
    }

    /* 4. Inject YOUR Header & Subtext */
    [data-testid="stFileUploaderDropzone"]::after {
        content: "Drop your P&L or Chart screenshot here\\A Supports PNG, JPG (Max 10MB). Your data is encrypted.";
        white-space: pre-wrap;
        color: white;
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 2rem;
        line-height: 1.5;
    }
    /* Note: Subtext styling is tricky in one block, so we keep it simple or use JS (but CSS is safer here) */

    /* 5. STYLE THE BUTTON - The "Select File" Hack */
    [data-testid="stFileUploaderDropzone"] button {
        background-color: white !important;
        border: none !important;
        padding: 12px 32px !important;
        border-radius: 8px !important;
        margin-top: 10px !important;
        transition: all 0.2s !important;
        
        /* HACK: Make original text transparent */
        color: transparent !important; 
        position: relative !important;
        width: auto !important;
        min-width: 140px !important;
    }
    
    /* 6. Inject "Select File" Text over the button */
    [data-testid="stFileUploaderDropzone"] button::after {
        content: "Select File" !important;
        color: black !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        white-space: nowrap;
    }

    [data-testid="stFileUploaderDropzone"] button:hover {
        background-color: #cbd5e1 !important;
        transform: scale(1.02);
    }

    /* --- GRID --- */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 2rem;
        margin-top: 5rem;
    }
    .feature-card {
        background: #1f2e38;
        padding: 1.5rem;
        border-radius: 12px;
    }
    .feature-title { font-weight: 700; color: white; margin-bottom: 0.5rem; font-size: 1.1rem; }
    .feature-desc { color: #64748b; font-size: 0.9rem; line-height: 1.5; }
    
    /* Mobile Responsive */
    @media (max-width: 768px) {
        .grid-container { grid-template-columns: 1fr; }
        .hero-title { font-size: 3rem; }
    }
</style>
""", unsafe_allow_html=True)

# 4. RENDER PAGE STRUCTURE
st.markdown("""
<div class="nav">
    <div class="logo">STOCK<span>POSTMORTEM</span>.AI</div>
    <button class="cta-btn">Get Started</button>
</div>

<div class="hero-title">STOP BLEEDING CAPITAL.</div>
<div class="hero-sub">Upload your losing trade screenshots. Our AI identifies psychological traps, technical failures, and provides a surgical path to recovery.</div>
""", unsafe_allow_html=True)

# 5. THE UPLOADER
# We use columns to center-align the width perfectly
c1, c2, c3 = st.columns([1, 8, 1])

with c2:
    uploaded_file = st.file_uploader(" ", type=["png", "jpg"], label_visibility="collapsed")

# 6. LOGIC & OUTPUT
if uploaded_file:
    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1, 2, 1])
    with b2:
        if st.button("RUN FORENSIC ANALYSIS", type="primary", use_container_width=True):
            with st.spinner("🔍 ANALYZING..."):
                try:
                    image = Image.open(uploaded_file)
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    
                    prompt = "ACT AS: Trading Psychologist. INPUT: Image. OUTPUT: 1. Mistake Identified. 2. Psychology Fix. 3. Risk Plan."
                    
                    payload = {
                        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                        "messages": [{"role": "user", "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                        ]}],
                        "max_tokens": 800
                    }
                    
                    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                    res = requests.post(API_URL, headers=headers, json=payload)
                    
                    if res.status_code == 200:
                        content = res.json()["choices"][0]["message"]["content"]
                        st.markdown(f"""
                        <div style="background: #1f2e38; border-left: 4px solid #ff4d4d; padding: 20px; border-radius: 8px; margin-top: 20px;">
                            {content}
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(str(e))

# 7. FEATURE GRID FOOTER
st.markdown("""
<div class="grid-container">
    <div class="feature-card">
        <div class="feature-title">Pattern Recognition</div>
        <div class="feature-desc">Did you buy the top? We identify if you're falling for FOMO or revenge trading instantly.</div>
    </div>
    <div class="feature-card">
        <div class="feature-title">Risk Autopsy</div>
        <div class="feature-desc">Calculates if your stop-loss was too tight or if your position sizing was reckless based on P&L.</div>
    </div>
    <div class="feature-card">
        <div class="feature-title">Recovery Plan</div>
        <div class="feature-desc">Step-by-step technical adjustments to ensure the next trade is a winner, not a gamble.</div>
    </div>
</div>
<div style="text-align: center; margin-top: 4rem; color: #475569; font-size: 0.8rem;">
    &copy; 2026 stockpostmortem.ai | Trading involves risk.
</div>
""", unsafe_allow_html=True)
