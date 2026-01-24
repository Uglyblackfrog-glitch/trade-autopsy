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

# 3. CSS OVERRIDES
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    body, .stApp { background-color: #0f171c !important; font-family: 'Inter', sans-serif !important; color: #e2e8f0 !important; }
    header, footer, #MainMenu { display: none !important; }
    .block-container { padding-top: 2rem !important; padding-bottom: 5rem !important; max-width: 100% !important; }
    
    .nav { display: flex; justify-content: space-between; align-items: center; padding: 1rem 0; border-bottom: 1px solid #2d4250; margin-bottom: 4rem; }
    .logo { font-size: 1.5rem; font-weight: 800; letter-spacing: -0.05em; color: white; }
    .logo span { color: #ff4d4d; }
    
    .hero-h1 { font-size: 4rem; font-weight: 800; font-style: italic; text-align: center; color: white; line-height: 1.1; margin-bottom: 1rem; }
    .hero-p { text-align: center; color: #94a3b8; font-size: 1.2rem; max-width: 800px; margin: 0 auto 3rem auto; }

    /* Custom Report Styling */
    .report-box { 
        background: #161b22; 
        border-left: 5px solid #ff4d4d; 
        padding: 25px; 
        border-radius: 8px; 
        margin-top: 20px; 
        font-size: 1.1rem;
        line-height: 1.6;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

# 4. RENDER UI
st.markdown("""
<div class="nav"><div class="logo">STOCK<span>POSTMORTEM</span>.AI</div></div>
<div class="hero-h1">STOP BLEEDING CAPITAL.</div>
<div class="hero-p">Upload your losing trade screenshots. Our AI identifies psychological traps and technical failures.</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 3, 1])
with c2:
    uploaded_file = st.file_uploader("Upload Chart/P&L", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

if uploaded_file:
    st.image(uploaded_file, caption="Target for Autopsy", use_container_width=True)
    
    if st.button("RUN FORENSIC ANALYSIS", type="primary", use_container_width=True):
        with st.spinner("🔍 SURGICAL ANALYSIS IN PROGRESS..."):
            try:
                # Prepare Image
                image = Image.open(uploaded_file)
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

                # UPDATED BRUTAL PROMPT
                prompt = """
                ACT AS: A Brutal Trading Psychologist and Forensic Technical Analyst.
                INPUT: Image of a trade or chart.
                TASK: Be extremely direct and honest. 
                FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
                
                🚩 TECHNICAL MISTAKE: [Explain the entry/exit error]
                🧠 EMOTIONAL TRAP: [Identify FOMO, Greed, or Fear]
                📉 RISK AUTOPSY: [Analyze position size or stop-loss logic]
                💉 SURGICAL RECOVERY: [One specific rule for next time]
                
                Do not include any conversational filler or 'Here is your analysis'. Start immediately with the flags.
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
                    analysis = res.json()["choices"][0]["message"]["content"]
                    
                    st.markdown("### 🩸 AUTOPSY COMPLETE")
                    # Rendering the analysis inside a styled div
                    st.markdown(f'<div class="report-box">{analysis}</div>', unsafe_allow_html=True)
                    st.download_button("Download Death Certificate", analysis, file_name="autopsy_report.txt")
                else:
                    st.error(f"API Error: {res.status_code}. Try again in a minute.")
                    
            except Exception as e:
                st.error(f"Error: {e}")

# Features Grid
st.markdown("""
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; margin-top: 5rem;">
    <div style="background: #1f2e38; padding: 2rem; border-radius: 1rem; border: 1px solid #2d4250;">
        <h3>Pattern Recognition</h3><p>Stop buying the top. We catch FOMO before it wipes your account.</p>
    </div>
    <div style="background: #1f2e38; padding: 2rem; border-radius: 1rem; border: 1px solid #2d4250;">
        <h3>Risk Autopsy</h3><p>Did you size too big? We calculate your recklessness.</p>
    </div>
    <div style="background: #1f2e38; padding: 2rem; border-radius: 1rem; border: 1px solid #2d4250;">
        <h3>Recovery Plan</h3><p>Data-driven rules to ensure your next trade isn't a gamble.</p>
    </div>
</div>
""", unsafe_allow_html=True)
