import streamlit as st
import requests
import base64
import io
from PIL import Image

# 1. PAGE CONFIG
st.set_page_config(page_title="StockPostmortem.ai", page_icon="🩸", layout="wide")

# 2. API SETUP
# We move the token check inside the execution to prevent app crashing on load
try:
    # Check if key exists in secrets, otherwise set to None to handle later
    HF_TOKEN = st.secrets.get("HF_TOKEN", None)
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except Exception:
    HF_TOKEN = None

# 3. CSS OVERRIDES (Global + Form Styling)
st.markdown("""
<style>
    /* --- RESET & GLOBAL --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    body, .stApp { 
        background-color: #0f171c !important; 
        font-family: 'Inter', sans-serif !important; 
        color: #e2e8f0 !important; 
    }
    
    header, footer, #MainMenu { display: none !important; }

    /* --- LAYOUT --- */
    .block-container { 
        padding-top: 2rem !important;
        padding-bottom: 5rem !important; 
        padding-left: 5rem !important;  
        padding-right: 5rem !important; 
        max-width: 100% !important;
    }

    /* --- MOBILE OVERRIDES --- */
    @media (max-width: 768px) {
        .block-container { padding: 1rem !important; }
        .hero-h1 { font-size: 3rem !important; margin-bottom: 1rem !important; }
        .hero-p { font-size: 1rem !important; }
        .nav { margin-bottom: 2rem !important; }
        [data-testid="stFileUploaderDropzone"] { min-height: 250px !important; }
    }

    /* --- NAVBAR --- */
    .nav { 
        display: flex; justify-content: space-between; align-items: center; 
        padding: 1rem 0; border-bottom: 1px solid #2d4250; margin-bottom: 4rem; 
    }
    .logo { font-size: 1.5rem; font-weight: 800; letter-spacing: -0.05em; color: white; }
    .logo span { color: #ff4d4d; }
    .cta-btn { 
        background: #dc2626; color: white; padding: 0.6rem 1.5rem; 
        border-radius: 99px; border: none; font-weight: 600; font-size: 0.9rem;
    }

    /* --- HERO --- */
    .hero-h1 { 
        font-size: 5rem; font-weight: 800; font-style: italic; text-align: center; 
        color: white; line-height: 1.1; margin-bottom: 1.5rem; 
    }
    .hero-p { 
        text-align: center; color: #94a3b8; font-size: 1.25rem; 
        max-width: 800px; margin: 0 auto 4rem auto; 
    }

    /* --- TABS STYLING --- */
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center;
        gap: 2rem;
        border-bottom: 1px solid #2d4250;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.2rem;
        font-weight: 600;
        color: #94a3b8;
        background-color: transparent;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        color: #ff4d4d !important;
        border-bottom: 2px solid #ff4d4d !important;
    }

    /* --- INPUT FORM STYLING (Dark Theme) --- */
    div[data-baseweb="input"] { background-color: #1f2e38 !important; border: 1px solid #475569 !important; border-radius: 8px !important; }
    div[data-baseweb="select"] > div { background-color: #1f2e38 !important; border: 1px solid #475569 !important; border-radius: 8px !important; }
    input { color: white !important; }
    textarea { background-color: #1f2e38 !important; border: 1px solid #475569 !important; color: white !important; border-radius: 8px !important; }
    label { color: #cbd5e1 !important; font-weight: 600 !important; }

    /* --- UPLOADER STYLING --- */
    [data-testid="stFileUploaderDropzone"] {
        background-color: rgba(31, 46, 56, 0.6) !important;
        border: 2px dashed #475569 !important;
        border-radius: 1rem !important;
        min-height: 400px !important;
        position: relative !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover { border-color: #ff4d4d !important; background-color: rgba(31, 46, 56, 0.8) !important; }
    
    [data-testid="stFileUploaderDropzone"]::before {
        content: ""; position: absolute; top: 70px; left: 50%; transform: translateX(-50%);
        width: 70px; height: 70px;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23ef4444'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12' /%3E%3C/svg%3E");
        background-repeat: no-repeat; background-size: contain; pointer-events: none;
    }
    [data-testid="stFileUploaderDropzone"]::after {
        content: "Drop your P&L or Chart screenshot here\\A Supports PNG, JPG (Max 10MB). Your data is encrypted.";
        white-space: pre-wrap; position: absolute; top: 160px; left: 0; width: 100%;
        text-align: center; color: #e2e8f0; font-size: 1.5rem; font-weight: 600; pointer-events: none;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] { visibility: hidden !important; height: 0 !important; }
    [data-testid="stFileUploaderDropzone"] div > svg { display: none !important; }
    [data-testid="stFileUploaderDropzone"] button {
        visibility: visible !important; position: absolute !important; bottom: 70px !important; left: 50% !important;
        transform: translateX(-50%) !important; background-color: white !important; color: transparent !important;
        border: none !important; padding: 14px 40px !important; border-radius: 8px !important;
    }
    [data-testid="stFileUploaderDropzone"] button::after {
        content: "Select File"; color: black; position: absolute; left: 50%; top: 50%;
        transform: translate(-50%, -50%); white-space: nowrap;
    }

    /* --- GRID --- */
    .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2.5rem; margin-top: 5rem; }
    .card { background: #1f2e38; padding: 2.5rem; border-radius: 1rem; border: 1px solid #2d4250; }
    .card h3 { color: white; font-weight: 700; margin-bottom: 0.75rem; font-size: 1.25rem; }
    .card p { color: #94a3b8; font-size: 1rem; line-height: 1.6; }
    @media (max-width: 1024px) { .grid { grid-template-columns: 1fr; } }
</style>
""", unsafe_allow_html=True)

# 4. RENDER UI

# Navbar
st.markdown("""
<div class="nav">
    <div class="logo">STOCK<span>POSTMORTEM</span>.AI</div>
    <button class="cta-btn">Get Started</button>
</div>
<div class="hero-h1">STOP BLEEDING CAPITAL.</div>
<div class="hero-p">Upload your losing trade screenshots. Our AI identifies psychological traps, technical failures, and provides a surgical path to recovery.</div>
""", unsafe_allow_html=True)

# --- MAIN CONTENT AREA ---
c_main = st.container()

with c_main:
    # 5. TABS LOGIC
    tab_image, tab_manual = st.tabs(["📸 UPLOAD SCREENSHOT", "📂 MANUAL CASE FILE"])

    # --- TAB 1: IMAGE UPLOAD ---
    with tab_image:
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 4, 1]) 
        with c2:
            uploaded_file = st.file_uploader(" ", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

            if uploaded_file:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("RUN INSTITUTIONAL ANALYSIS (IMAGE)", type="primary", use_container_width=True):
                    
                    if not HF_TOKEN:
                        st.error("❌ API ERROR: HF_TOKEN is missing in Streamlit Secrets.")
                    else:
                        with st.spinner("🔍 CONDUCTING TECHNICAL AUDIT..."):
                            try:
                                image = Image.open(uploaded_file)
                                buf = io.BytesIO()
                                image.save(buf, format="PNG")
                                img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

                                prompt = """
                                ROLE: Senior Quantitative Risk Analyst at a Proprietary Trading Firm.
                                TASK: Conduct a forensic audit of the provided financial chart.
                                
                                STRICT AUDIT RULES:
                                1. DO NOT HALLUCINATE: Do not assume the existence of indicators unless visible.
                                2. PRIMARY DIAGNOSIS: Identify the singular, most critical failure point.
                                3. PRIORITY ORDER: Evaluate Market Structure first, then Risk Management, then Exit.
                                
                                OUTPUT FORMAT (Financial Report Style):
                                **1. PRIMARY FAILURE MECHANISM**
                                [Identify root cause]

                                **2. TECHNICAL SOLVENCY AUDIT**
                                [Analyze entry/exit precision]

                                **3. BEHAVIORAL RISK ASSESSMENT**
                                [Diagnose psychology if evident]

                                **4. REMEDIATION PROTOCOL**
                                [One specific, actionable rule]
                                """
                                
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
                                    st.markdown(f"""<div style="background: #161b22; border-left: 5px solid #ff4d4d; padding: 30px; border-radius: 8px; margin-top: 20px;">{content}</div>""", unsafe_allow_html=True)
                                elif res.status_code == 401:
                                    st.error("❌ 401 UNAUTHORIZED: This usually means your Token is invalid OR you haven't accepted the Model License.")
                                    st.warning("FIX: Go to https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct and click 'Agree and Access Repository'.")
                                else:
                                    st.error(f"❌ API Error {res.status_code}: {res.text}")

                            except Exception as e:
                                st.error(f"System Error: {e}")

    # --- TAB 2: MANUAL INPUT ---
    with tab_manual:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container():
            col_form_1, col_form_2, col_form_3 = st.columns([1, 6, 1])
            with col_form_2:
                with st.container():
                    st.markdown("### 📂 CASE FILE DETAILS")
                    st.markdown("<p style='color:#64748b; font-size:0.9rem; margin-bottom:20px;'>Provide precise data for an institutional-grade audit.</p>", unsafe_allow_html=True)
                    
                    r1c1, r1c2, r1c3 = st.columns(3)
                    with r1c1:
                        ticker = st.text_input("Ticker", placeholder="$NVDA")
                    with r1c2:
                        position = st.selectbox("Position", ["Long (Buy)", "Short (Sell)"])
                    with r1c3:
                        timeframe = st.selectbox("Timeframe", ["Scalp (1m-5m)", "Day Trade (15m-1h)", "Swing (4h-Daily)", "Investing (Weekly)"])
                    
                    r2c1, r2c2, r2c3 = st.columns(3)
                    with r2c1:
                        entry_price = st.text_input("Entry Price", placeholder="100.00")
                    with r2c2:
                        exit_price = st.text_input("Exit Price", placeholder="95.00")
                    with r2c3:
                        planned_stop = st.text_input("Planned Stop", placeholder="98.00")

                    intent = st.selectbox("Pre-Trade Intent", 
                                            ["Planned & Rule-Based (I had a plan)", 
                                             "Impulsive / FOMO (I chased price)", 
                                             "Revenge / Tilt (Recovering losses)", 
                                             "Unsure / No Plan"])
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    setup_desc = st.text_area("Thesis (Entry Logic)", placeholder="Describe market structure, indicators, and catalysts...")
                    exit_desc = st.text_area("Execution (Exit Logic)", placeholder="Describe price action at exit and emotional state...")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if st.button("RUN INSTITUTIONAL ANALYSIS (TEXT)", type="primary", use_container_width=True):
                        if not ticker or not setup_desc:
                            st.warning("⚠️ Data insufficient for audit. Please complete the case file.")
                        elif not HF_TOKEN:
                            st.error("❌ API ERROR: HF_TOKEN is missing.")
                        else:
                            with st.spinner("🧠 CALCULATING RISK METRICS & BEHAVIORAL BIAS..."):
                                try:
                                    # --- BACKGROUND MATH CALCULATION ---
                                    math_context = ""
                                    try:
                                        ep = float(entry_price)
                                        xp = float(exit_price)
                                        sl = float(planned_stop)
                                        
                                        risk_per_share = abs(ep - sl)
                                        loss_per_share = abs(ep - xp)
                                        
                                        if risk_per_share == 0:
                                            math_context = "Risk Metrics: Invalid (Entry Price equals Stop Loss)."
                                        else:
                                            slippage_pct = ((loss_per_share - risk_per_share) / risk_per_share) * 100
                                            math_context = f"""
                                            CALCULATED RISK METRICS:
                                            - Planned Risk Per Share: {risk_per_share:.2f}
                                            - Actual Loss Per Share: {loss_per_share:.2f}
                                            - Deviation from Plan: {slippage_pct:.2f}% (If positive, they ignored their stop).
                                            """
                                    except:
                                        math_context = "Risk Metrics: Insufficient numerical data to calculate."

                                    manual_prompt = f"""
                                    ROLE: Chief Risk Officer (CRO) at a Quantitative Hedge Fund.
                                    CONTEXT: A trader has submitted a failed trade for forensic audit.
                                    
                                    CASE FILE DATA:
                                    - Asset: {ticker}
                                    - Direction: {position} ({timeframe})
                                    - Trade Intent: {intent}
                                    - Entry Thesis: {setup_desc}
                                    - Exit Reality: {exit_desc}
                                    
                                    {math_context}
                                    
                                    STRICT AUDIT RULES:
                                    1. DO NOT INVENT CONTEXT.
                                    2. HIERARCHY OF ERROR: Evaluate ENTRY first.
                                    3. PSYCHOLOGY GATE: Only diagnose Fear/Greed if evident.
                                    
                                    OUTPUT FORMAT (Financial Report Style):
                                    **1. EXECUTIVE DIAGNOSIS**
                                    [Identify singular reason for failure]
                                    
                                    **2. TRADE EXPECTANCY AUDIT**
                                    [Analyze mathematical edge]
                                    
                                    **3. BEHAVIORAL ECONOMICS PROFILE**
                                    [Identify cognitive biases]
                                    
                                    **4. INSTITUTIONAL MANDATE**
                                    [ONE imperative rule in bold]
                                    """
                                    
                                    payload = {
                                        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                                        "messages": [{"role": "user", "content": manual_prompt}],
                                        "max_tokens": 1000
                                    }
                                    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                                    res = requests.post(API_URL, headers=headers, json=payload)
                                    
                                    if res.status_code == 200:
                                        content = res.json()["choices"][0]["message"]["content"]
                                        st.markdown(f"""<div style="background: #161b22; border-left: 5px solid #ff4d4d; padding: 30px; border-radius: 8px; margin-top: 20px;">{content}</div>""", unsafe_allow_html=True)
                                    elif res.status_code == 401:
                                        st.error("❌ 401 UNAUTHORIZED: Access to Qwen/Qwen2.5-VL-7B-Instruct is likely restricted.")
                                        st.warning("FIX: Log in to HuggingFace, search for 'Qwen2.5-VL-7B-Instruct', and click 'Agree and Access Repository'.")
                                        st.info("Debugging: You can also try changing the model to 'meta-llama/Llama-3.2-11B-Vision-Instruct' in the code.")
                                    else:
                                        st.error(f"❌ API Server Status: {res.status_code}")
                                        st.code(res.text) # Print actual error message
                                except Exception as e:
                                    st.error(f"System Error: {e}")

# Footer Grid
st.markdown("""
<div class="grid">
    <div class="card">
        <h3>Pattern Recognition</h3>
        <p>Did you buy the top? We identify if you're falling for FOMO or revenge trading instantly.</p>
    </div>
    <div class="card">
        <h3>Risk Autopsy</h3>
        <p>Calculates if your stop-loss was too tight or if your position sizing was reckless.</p>
    </div>
    <div class="card">
        <h3>Recovery Plan</h3>
        <p>Step-by-step technical adjustments to ensure the next trade is a winner, not a gamble.</p>
    </div>
</div>
<div style="text-align: center; margin-top: 6rem; color: #64748b; font-size: 0.9rem;">
    &copy; 2026 stockpostmortem.ai | Trading involves risk.
</div>
""", unsafe_allow_html=True)
