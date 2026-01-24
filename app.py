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
    API_URL = "[https://router.huggingface.co/v1/chat/completions](https://router.huggingface.co/v1/chat/completions)"
except Exception:
    st.error("⚠️ HF_TOKEN is missing. Add it to Streamlit Secrets.")
    st.stop()

# 3. CSS OVERRIDES
st.markdown("""
<style>
    @import url('[https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap](https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap)');
    
    body, .stApp { 
        background-color: #0f171c !important; 
        font-family: 'Inter', sans-serif !important; 
        color: #e2e8f0 !important; 
    }
    
    header, footer, #MainMenu { display: none !important; }

    .block-container { 
        padding-top: 2rem !important;
        padding-bottom: 5rem !important; 
        max-width: 100% !important;
    }

    /* Navbar */
    .nav { 
        display: flex; justify-content: space-between; align-items: center; 
        padding: 1rem 0; border-bottom: 1px solid #2d4250; margin-bottom: 4rem; 
    }
    .logo { font-size: 1.5rem; font-weight: 800; color: white; }
    .logo span { color: #ff4d4d; }

    /* Hero Section */
    .hero-h1 { font-size: 4rem; font-weight: 800; font-style: italic; text-align: center; color: white; line-height: 1.1; margin-bottom: 1.5rem; }
    .hero-p { text-align: center; color: #94a3b8; font-size: 1.2rem; max-width: 800px; margin: 0 auto 3rem auto; }

    /* The Autopsy Box */
    .report-box {
        background: #161b22;
        border-left: 5px solid #ff4d4d;
        padding: 30px;
        border-radius: 8px;
        margin-top: 20px;
        color: #ffffff !important;
        font-size: 1.1rem;
        line-height: 1.7;
        white-space: pre-wrap; /* Keeps the AI's formatting clean */
    }
</style>
""", unsafe_allow_html=True)

# 4. RENDER UI
st.markdown("""
<div class="nav">
    <div class="logo">STOCK<span>POSTMORTEM</span>.AI</div>
</div>
<div class="hero-h1">STOP BLEEDING CAPITAL.</div>
<div class="hero-p">Upload your losing trade screenshots. Our AI identifies psychological traps, technical failures, and provides a surgical path to recovery.</div>
""", unsafe_allow_html=True)

# Uploader Column
c1, c2, c3 = st.columns([1, 3, 1]) 
with c2:
    uploaded_file = st.file_uploader(" ", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

if uploaded_file:
    st.image(uploaded_file, caption="Evidence for Autopsy", use_container_width=True)
    
    if st.button("RUN FORENSIC ANALYSIS", type="primary", use_container_width=True):
        with st.spinner("🔍 ANALYZING CHART DATA..."):
            try:
                # Process Image
                image = Image.open(uploaded_file)
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

                # NEW BRUTAL PROMPT (Instructions to avoid code blocks)
                prompt = """
                ACT AS: A Brutal Trading Psychologist and Technical Forensic Analyst.
                INPUT: Image of a chart or P&L.
                TASK: Diagnose why this trade was a failure.
                
                OUTPUT FORMAT:
                🚩 TECHNICAL MISTAKE: [Analyze entry/exit]
                🧠 EMOTIONAL TRAP: [Analyze FOMO, greed, or fear]
                📉 RISK AUTOPSY: [Analyze sizing or stops]
                💉 SURGICAL RECOVERY: [One rule to fix it next time]

                IMPORTANT: Output plain text only. DO NOT use markdown code blocks (```). Be extremely blunt.
                """
                
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
                    raw_content = res.json()["choices"][0]["message"]["content"]
                    
                    # --- FAILSAFE: REMOVE CODE BLOCK SYMBOLS ---
                    clean_content = raw_content.replace("```markdown", "").replace("```", "").strip()

                    st.markdown("### 🩸 AUTOPSY REPORT")
                    st.markdown(f'<div class="report-box">{clean_content}</div>', unsafe_allow_html=True)
                    st.download_button("Download Report", clean_content, file_name="autopsy.txt")
                else:
                    st.error(f"Error: AI Server is busy (Code: {res.status_code}). Try again in 10 seconds.")
            except Exception as e:
                st.error(f"Error: {e}")

# Features
st.markdown("""
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2rem; margin-top: 5rem;">
    <div style="background: #1f2e38; padding: 2.5rem; border-radius: 1rem; border: 1px solid #2d4250;">
        <h3 style="color:white">Pattern Recognition</h3>
        <p style="color:#94a3b8">Identify if you're falling for FOMO or revenge trading instantly.</p>
    </div>
    <div style="background: #1f2e38; padding: 2.5rem; border-radius: 1rem; border: 1px solid #2d4250;">
        <h3 style="color:white">Risk Autopsy</h3>
        <p style="color:#94a3b8">Calculates if your stop-loss was too tight or if your sizing was reckless.</p>
    </div>
    <div style="background: #1f2e38; padding: 2.5rem; border-radius: 1rem; border: 1px solid #2d4250;">
        <h3 style="color:white">Recovery Plan</h3>
        <p style="color:#94a3b8">Step-by-step adjustments to ensure your next trade is a winner.</p>
    </div>
</div>
""", unsafe_allow_html=True)
