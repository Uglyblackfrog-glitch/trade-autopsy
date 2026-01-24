import streamlit as st
import requests
import base64
import io
from PIL import Image

# 1. PAGE SETUP
st.set_page_config(page_title="StockPostmortem.ai", page_icon="🩸", layout="wide")

# 2. YOUR API KEYS
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except Exception:
    st.error("⚠️ HF_TOKEN is missing in Streamlit Secrets.")
    st.stop()

# 3. EXACT UI STYLING (The Magic Fix)
st.markdown("""
<style>
    /* --- GLOBAL DARK THEME --- */
    .stApp { background-color: #0f171c; font-family: 'Inter', sans-serif; color: #e2e8f0; }
    header, footer, #MainMenu { display: none !important; }
    .block-container { padding-top: 0rem; padding-bottom: 5rem; max-width: 1000px; }

    /* --- NAVBAR --- */
    .nav { display: flex; justify-content: space-between; padding: 1.5rem 0; border-bottom: 1px solid #2d4250; margin-bottom: 4rem; }
    .logo { font-size: 1.5rem; font-weight: 800; letter-spacing: -0.05em; color: white; }
    .logo span { color: #ff4d4d; }
    .cta-btn { background: #dc2626; color: white; padding: 0.5rem 1.5rem; border-radius: 99px; font-weight: 600; border: none; }

    /* --- HERO --- */
    .hero h1 { font-size: 4rem; font-weight: 800; font-style: italic; text-align: center; margin-bottom: 1rem; line-height: 1.1; }
    .hero p { text-align: center; color: #94a3b8; font-size: 1.2rem; margin-bottom: 3rem; }

    /* --- CUSTOM UPLOADER STYLING (THE FIX) --- */
    
    /* 1. The Container Box */
    [data-testid="stFileUploader"] {
        background-color: rgba(31, 46, 56, 0.6);
        border: 2px dashed #475569;
        border-radius: 1rem;
        padding: 3rem 2rem;
        text-align: center;
        transition: border 0.3s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #ff4d4d;
        background-color: rgba(31, 46, 56, 0.8);
    }

    /* 2. Hide Default Streamlit Text */
    [data-testid="stFileUploaderDropzone"] div div::before { content: none; }
    [data-testid="stFileUploaderDropzone"] div div span { display: none; }
    
    /* 3. Style the Button to match your 'White Button' */
    button[kind="secondary"] {
        background-color: white !important;
        color: black !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        border-radius: 0.5rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        margin-top: 1rem !important;
        transition: all 0.2s !important;
    }
    button[kind="secondary"]:hover {
        background-color: #e2e8f0 !important;
        transform: scale(1.05);
    }
    
    /* 4. Center the button */
    section[data-testid="stFileUploaderDropzone"] {
        background: transparent;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

</style>
""", unsafe_allow_html=True)

# 4. RENDER HTML HEADER (Navbar + Hero)
st.markdown("""
<div class="nav">
    <div class="logo">STOCK<span>POSTMORTEM</span>.AI</div>
    <button class="cta-btn">Get Started</button>
</div>
<div class="hero">
    <h1>STOP BLEEDING CAPITAL.</h1>
    <p>Upload your losing trade screenshots. Our AI identifies psychological traps, technical failures, and provides a surgical path to recovery.</p>
</div>
""", unsafe_allow_html=True)

# 5. THE UPLOADER SECTION (With Icon & Text)
# We put the Icon and Text OUTSIDE the uploader but inside the same visual flow
col_spacer, col_main, col_spacer2 = st.columns([1, 6, 1])

with col_main:
    # Render the Icon & Text that sits "inside" the box visually
    st.markdown("""
    <div style="text-align: center; margin-bottom: -110px; position: relative; z-index: 0; pointer-events: none;">
        <svg xmlns="http://www.w3.org/2000/svg" style="width: 50px; height: 50px; color: #ff4d4d; margin-bottom: 10px;" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <h2 style="font-size: 1.5rem; font-weight: 600; color: white; margin: 0;">Drop your P&L or Chart screenshot here</h2>
        <p style="color: #64748b; margin-top: 5px; margin-bottom: 30px;">Supports PNG, JPG (Max 10MB)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # The Functional Uploader (Styled transparent so it sits on top)
    uploaded_file = st.file_uploader(" ", type=["png", "jpg"], label_visibility="collapsed")


# 6. LOGIC & RESULT
if uploaded_file:
    # Center the analyze button
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("RUN FORENSIC ANALYSIS", type="primary", use_container_width=True):
            with st.spinner("🔍 ANALYZING TRADING PSYCHOLOGY..."):
                try:
                    image = Image.open(uploaded_file)
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    
                    prompt = "ACT AS: Trading Psychologist. 1. Identify Mistake. 2. Psychology Diagnosis. 3. Fix."
                    
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
                        <div style="background: #1f2e38; border-left: 4px solid #ff4d4d; padding: 25px; border-radius: 10px; margin-top: 30px;">
                            {content}
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")

# 7. FOOTER GRID
st.markdown("""
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; margin-top: 5rem;">
    <div style="background: #1f2e38; padding: 1.5rem; border-radius: 12px;">
        <h3 style="font-weight: 700; color: white;">Pattern Recognition</h3>
        <p style="color: #94a3b8; font-size: 0.9rem;">Did you buy the top? We identify FOMO instantly.</p>
    </div>
    <div style="background: #1f2e38; padding: 1.5rem; border-radius: 12px;">
        <h3 style="font-weight: 700; color: white;">Risk Autopsy</h3>
        <p style="color: #94a3b8; font-size: 0.9rem;">Calculates if your stop-loss was too tight.</p>
    </div>
    <div style="background: #1f2e38; padding: 1.5rem; border-radius: 12px;">
        <h3 style="font-weight: 700; color: white;">Recovery Plan</h3>
        <p style="color: #94a3b8; font-size: 0.9rem;">Step-by-step adjustments for your next trade.</p>
    </div>
</div>
<div style="text-align: center; color: #475569; padding-top: 3rem; font-size: 0.8rem;">&copy; 2026 stockpostmortem.ai</div>
""", unsafe_allow_html=True)
