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

# 3. THE MAGIC CSS (Replaces Streamlit UI with Your UI)
st.markdown("""
<style>
    /* GLOBAL RESET */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    body, .stApp { background-color: #0f171c !important; font-family: 'Inter', sans-serif !important; color: #e2e8f0 !important; }
    
    /* HIDE STREAMLIT CHROME */
    header, footer, #MainMenu { display: none !important; }
    .block-container { padding-top: 0rem !important; max-width: 1100px !important; }

    /* NAVBAR styling */
    .nav { display: flex; justify-content: space-between; align-items: center; padding: 1.5rem 0; border-bottom: 1px solid #2d4250; margin-bottom: 4rem; }
    .nav-logo { font-size: 1.5rem; font-weight: 800; letter-spacing: -0.05em; color: white; }
    .nav-logo span { color: #ff4d4d; }
    .nav-links { display: flex; gap: 2rem; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.1em; color: #cbd5e1; }
    .btn-red { background: #dc2626; color: white; padding: 0.5rem 1.5rem; border-radius: 99px; border: none; font-weight: 600; }

    /* HERO styling */
    .hero { text-align: center; padding: 2rem 0 4rem 0; }
    .hero h1 { font-size: 4rem; font-weight: 800; font-style: italic; margin-bottom: 1rem; color: white; line-height: 1.1; }
    .hero p { color: #94a3b8; font-size: 1.2rem; max-width: 700px; margin: 0 auto; }

    /* ==============================================
       THE UPLOADER TRANSFORMATION (The Critical Fix)
       ============================================== */
    
    /* 1. Target the Dropzone Area -> Make it the Glass Card */
    [data-testid="stFileUploaderDropzone"] {
        background-color: rgba(31, 46, 56, 0.6); /* bg-glass */
        border: 2px dashed #475569;
        border-radius: 1rem;
        padding: 4rem 2rem 2rem 2rem; /* Top padding makes room for the icon */
        min-height: 300px;
        align-content: center;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #ff4d4d; /* Red border on hover */
        background-color: rgba(31, 46, 56, 0.8);
    }

    /* 2. INJECT THE RED CLOUD ICON (As a background image) */
    [data-testid="stFileUploaderDropzone"]::before {
        content: "";
        display: block;
        width: 60px;
        height: 60px;
        margin: 0 auto 1rem auto;
        /* The Red Cloud SVG Encoded */
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23ff4d4d'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12' /%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: center;
        background-size: contain;
    }

    /* 3. INJECT THE TEXT (Replaces 'Drag and drop file here') */
    [data-testid="stFileUploaderDropzone"]::after {
        content: "Drop your P&L or Chart screenshot here\\A Supports PNG, JPG (Max 10MB)"; 
        white-space: pre-wrap; /* Allows the \A newline to work */
        display: block;
        text-align: center;
        color: white;
        font-weight: 600;
        font-size: 1.25rem;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }
    
    /* 4. HIDE THE DEFAULT STREAMLIT ICON & TEXT */
    [data-testid="stFileUploaderDropzone"] div > div > svg { display: none; } /* Hide default cloud */
    [data-testid="stFileUploaderDropzoneInstructions"] { display: none; } /* Hide default text */
    
    /* 5. STYLE THE BUTTON (White with Black Text) */
    [data-testid="stFileUploaderDropzone"] button {
        background-color: white !important;
        color: black !important;
        border: none !important;
        padding: 0.75rem 2.5rem !important;
        border-radius: 0.5rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        margin-top: 10px !important;
        transition: all 0.2s;
    }
    [data-testid="stFileUploaderDropzone"] button:hover {
        background-color: #cbd5e1 !important; /* Light gray hover */
        transform: scale(1.05);
    }

    /* GRID & FOOTER */
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; margin-top: 4rem; }
    .card { background: #1f2e38; padding: 1.5rem; border-radius: 0.75rem; }
    .card h3 { color: white; font-weight: 700; margin-bottom: 0.5rem; }
    .card p { color: #94a3b8; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# 4. RENDER UI
# --- Navbar ---
st.markdown("""
<div class="nav">
    <div class="nav-logo">STOCK<span>POSTMORTEM</span>.AI</div>
    <div class="nav-links">
        <span>Analyze</span><span>Case Studies</span><span>Pricing</span>
    </div>
    <button class="btn-red">Get Started</button>
</div>
""", unsafe_allow_html=True)

# --- Hero ---
st.markdown("""
<div class="hero">
    <h1>STOP BLEEDING CAPITAL.</h1>
    <p>Upload your losing trade screenshots. Our AI identifies psychological traps, technical failures, and provides a surgical path to recovery.</p>
</div>
""", unsafe_allow_html=True)

# --- Uploader (Logic Wrapped in Styling) ---
# We use a centered column to control width
c1, c2, c3 = st.columns([1, 6, 1])
with c2:
    uploaded_file = st.file_uploader(" ", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

# --- AI Analysis Logic ---
if uploaded_file:
    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1, 1, 1])
    with b2:
        run_btn = st.button("RUN FORENSIC ANALYSIS", type="primary", use_container_width=True)
    
    if run_btn:
        with st.spinner("🔍 ANALYZING CHART DATA & PSYCHOLOGY..."):
            try:
                # Prepare Image
                image = Image.open(uploaded_file)
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

                # Prompt
                prompt = (
                    "ACT AS: Senior Trading Psychologist. "
                    "INPUT: Trading Chart/P&L. "
                    "TASK: 1. Identify the 'Kill Zone' (Mistake). 2. Diagnose Psychology. 3. Risk Audit. 4. Fix."
                    "OUTPUT: Brutally honest, concise bullet points."
                )
                
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
                    st.markdown(f"""
                    <div style="background: #161b22; border-left: 5px solid #ff4d4d; padding: 25px; border-radius: 8px; margin-top: 20px; color: #e2e8f0;">
                        {content}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("AI Service is busy. Try again.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- Feature Grid ---
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
<div style="text-align: center; margin-top: 4rem; padding-top: 2rem; border-top: 1px solid #2d4250; font-size: 0.8rem; color: #64748b;">
    &copy; 2026 stockpostmortem.ai | Trading involves risk. Keep your head cool.
</div>
""", unsafe_allow_html=True)
