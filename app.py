import streamlit as st
import requests
import base64
import io
import re
from PIL import Image

# 1. PAGE CONFIG
st.set_page_config(page_title="StockPostmortem.ai", page_icon="🩸", layout="wide")

# 2. API SETUP
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    # Using a high-performance Vision model
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except Exception:
    st.error("⚠️ HF_TOKEN is missing. Add it to Streamlit Secrets.")
    st.stop()

# 3. CSS OVERRIDES (STYLING FOR MAXIMUM IMPACT)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500;700&display=swap');
    
    body, .stApp { 
        background-color: #080a0c !important; 
        font-family: 'Space Grotesk', sans-serif !important; 
        color: #e2e8f0 !important; 
    }

    /* Forensic Report Styling */
    .report-container {
        background: linear-gradient(145deg, #161b22, #0d1117);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 2rem;
        margin-top: 2rem;
    }
    
    .report-header {
        border-bottom: 2px solid #ff4d4d;
        padding-bottom: 10px;
        margin-bottom: 20px;
        color: #ff4d4d;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    .analysis-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 4px solid #444;
    }

    .tech-fail { border-left-color: #3b82f6; } /* Blue */
    .psych-trap { border-left-color: #f59e0b; } /* Orange */
    .risk-fail { border-left-color: #ef4444; } /* Red */
    .recovery-path { border-left-color: #10b981; } /* Green */

    .card-title {
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 5px;
        display: block;
    }

    /* Same CSS as your original for Hero/Uploader... */
    .hero-h1 { font-size: 5rem; font-weight: 800; font-style: italic; text-align: center; color: white; line-height: 1.1; margin-bottom: 1.5rem; }
    .hero-p { text-align: center; color: #94a3b8; font-size: 1.25rem; max-width: 800px; margin: 0 auto 4rem auto; }
    
    [data-testid="stFileUploaderDropzone"] {
        background-color: rgba(31, 46, 56, 0.4) !important;
        border: 2px dashed #ff4d4d !important;
        min-height: 300px !important;
    }
    
    [data-testid="stFileUploaderDropzone"]:hover { border-color: #ff0000 !important; }
    [data-testid="stFileUploaderDropzone"]::before { content: "CASE EVIDENCE"; color: #ff4d4d; font-weight: bold; position: absolute; top: 10px; left: 10px; }
</style>
""", unsafe_allow_html=True)

# 4. HELPER FUNCTION: PARSE AI OUTPUT
def parse_forensic_report(text):
    """
    Splits the AI's response into dictionary chunks for the UI.
    """
    sections = {
        "tech": "No technical analysis found.",
        "psych": "No psychological profile found.",
        "risk": "No risk audit found.",
        "fix": "No recovery plan found."
    }
    
    # Regex to find content between tags
    tech_match = re.search(r'\[TECH\](.*?)(?=\[PSYCH\]|\[RISK\]|\[FIX\]|$)', text, re.DOTALL)
    psych_match = re.search(r'\[PSYCH\](.*?)(?=\[RISK\]|\[FIX\]|$)', text, re.DOTALL)
    risk_match = re.search(r'\[RISK\](.*?)(?=\[FIX\]|$)', text, re.DOTALL)
    fix_match = re.search(r'\[FIX\](.*?)$', text, re.DOTALL)

    if tech_match: sections["tech"] = tech_match.group(1).strip()
    if psych_match: sections["psych"] = psych_match.group(1).strip()
    if risk_match: sections["risk"] = risk_match.group(1).strip()
    if fix_match: sections["fix"] = fix_match.group(1).strip()
    
    return sections

# 5. UI RENDER
st.markdown("""
<div style="text-align:center; padding-top: 50px;">
    <div style="font-size: 1.5rem; font-weight: 800; color: white; margin-bottom: 20px;">STOCK<span style="color:#ff4d4d">POSTMORTEM</span>.AI</div>
    <div class="hero-h1">THE TRUTH HURTS. <br>LOSE LESS.</div>
    <p class="hero-p">Generic AI gives you advice. We give you an autopsy. Upload your trade and let's find where the bleeding starts.</p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 3, 1])
with c2:
    uploaded_file = st.file_uploader(" ", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

if uploaded_file:
    # Preview Image
    st.image(uploaded_file, caption="Evidence Captured.", use_container_width=True)
    
    # Action Button
    b1, b2, b3 = st.columns([1, 1, 1])
    with b2:
        start_analysis = st.button("EXECUTE FORENSIC ANALYSIS", type="primary", use_container_width=True)

    if start_analysis:
        with st.spinner("Analyzing Liquidity, Psychology, and Entry/Exit markers..."):
            try:
                # Image Prep
                image = Image.open(uploaded_file)
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

                # THE "ELITE" PROMPT
                # We force the AI to use specific tags so we can parse them into beautiful cards later.
                prompt = """
                ACT AS: Senior Institutional Trader & Behavioral Psychologist.
                TASK: Conduct a brutal postmortem of this trade screenshot.
                
                REQUIREMENTS:
                1. Identify the exact technical failure (e.g., buying into resistance, ignoring EMA, late entry, divergence).
                2. Diagnose the psychological bias (e.g., FOMO, Revenge Trading, Sunk Cost Fallacy, Gambler's Fallacy).
                3. Audit the Risk Management (e.g., bad R:R ratio, stop-loss placement, position sizing).
                4. Provide a 1-sentence surgical fix for the next trade.

                FORMAT RULES (MANDATORY):
                You must strictly follow this format with these exact tags:
                
                [TECH]
                (Write the technical analysis here)
                
                [PSYCH]
                (Write the psychological profile here)
                
                [RISK]
                (Write the risk audit here)
                
                [FIX]
                (Write the surgical fix here)
                """
                
                payload = {
                    "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                    "messages": [{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                    ]}],
                    "max_tokens": 1200,
                    "temperature": 0.2 
                }
                headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                res = requests.post(API_URL, headers=headers, json=payload)
                
                if res.status_code == 200:
                    raw_content = res.json()["choices"][0]["message"]["content"]
                    
                    # Parse the raw text into sections
                    report = parse_forensic_report(raw_content)

                    # Display the "Dashboard"
                    st.markdown(f"""
                    <div class="report-container">
                        <div class="report-header">💀 AUTOPSY REPORT #001</div>
                        
                        <div class="analysis-card tech-fail">
                            <span class="card-title" style="color:#3b82f6;">📉 TECHNICAL FAILURE</span>
                            {report['tech']}
                        </div>

                        <div class="analysis-card psych-trap">
                            <span class="card-title" style="color:#f59e0b;">🧠 PSYCHOLOGICAL TRAP</span>
                            {report['psych']}
                        </div>

                        <div class="analysis-card risk-fail">
                            <span class="card-title" style="color:#ef4444;">💸 RISK MANAGEMENT AUDIT</span>
                            {report['risk']}
                        </div>

                        <div class="analysis-card recovery-path">
                            <span class="card-title" style="color:#10b981;">💉 THE SURGICAL FIX</span>
                            <b>{report['fix']}</b>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                else:
                    st.error(f"Server Error: {res.status_code}")
            except Exception as e:
                st.error(f"Analysis Failed: {e}")

# Footer (Same as before)
st.markdown("""
<br><br>
<div style="text-align: center; color: #64748b; font-size: 0.8rem; border-top: 1px solid #333; padding-top: 20px;">
    &copy; 2026 stockpostmortem.ai | <b>Trading involves risk. Lose responsibly.</b>
</div>
""", unsafe_allow_html=True)
