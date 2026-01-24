import streamlit as st
import requests
import base64
import io
from PIL import Image

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="StockPostmortem.ai", page_icon="🩸", layout="wide")

# 2. SYSTEM CONSTANTS
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except Exception:
    st.error("SYSTEM ERROR: HF_TOKEN is missing from Streamlit Secrets.")
    st.stop()

# 3. INTERFACE STYLING (INSTITUTIONAL GRADE)
st.markdown("""
<style>
    /* GLOBAL THEME */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    body, .stApp { 
        background-color: #0b0e11 !important; 
        font-family: 'Inter', sans-serif !important; 
        color: #cfd8dc !important; 
    }
    
    /* REMOVE STREAMLIT BRANDING */
    header, footer, #MainMenu { display: none !important; }

    /* LAYOUT OPTIMIZATION */
    .block-container { 
        padding-top: 3rem !important;
        padding-bottom: 5rem !important; 
        max-width: 1200px !important;
    }

    /* NAVIGATION */
    .nav { 
        display: flex; justify-content: space-between; align-items: center; 
        padding-bottom: 2rem; border-bottom: 1px solid #1e293b; margin-bottom: 3rem; 
    }
    .logo { font-size: 1.25rem; font-weight: 700; color: #ffffff; letter-spacing: 0.05em; }
    .logo span { color: #ef4444; }

    /* TYPOGRAPHY */
    .hero-h1 { 
        font-size: 3.5rem; font-weight: 800; text-align: center; 
        color: #ffffff; letter-spacing: -0.02em; margin-bottom: 1rem; 
    }
    .hero-p { 
        text-align: center; color: #94a3b8; font-size: 1.1rem; 
        max-width: 600px; margin: 0 auto 4rem auto; line-height: 1.6;
    }

    /* COMPONENT STYLING */
    div[data-baseweb="input"] { background-color: #151b23 !important; border: 1px solid #334155 !important; }
    div[data-baseweb="select"] > div { background-color: #151b23 !important; border: 1px solid #334155 !important; }
    .stTextArea textarea { background-color: #151b23 !important; border: 1px solid #334155 !important; }
    
    /* REPORT CONTAINER */
    .report-container {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-left: 4px solid #ef4444;
        border-radius: 6px;
        padding: 2rem;
        margin-top: 2rem;
        font-family: 'Inter', sans-serif;
    }
    .report-header {
        color: #ef4444;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 1rem;
    }
    .report-content {
        color: #e6edf3;
        font-size: 1rem;
        line-height: 1.7;
        white-space: pre-line;
    }

    /* UPLOADER */
    [data-testid="stFileUploaderDropzone"] {
        background-color: #151b23 !important;
        border: 1px dashed #334155 !important;
    }
    
    /* GRID */
    .grid-container {
        display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem; margin-top: 6rem;
    }
    .feature-card {
        background: #151b23; padding: 2rem; border-radius: 8px; border: 1px solid #1e293b;
    }
    .feature-title { color: white; font-weight: 600; margin-bottom: 0.5rem; font-size: 1.1rem; }
    .feature-text { color: #94a3b8; font-size: 0.9rem; line-height: 1.5; }

    @media (max-width: 768px) {
        .grid-container { grid-template-columns: 1fr; }
        .hero-h1 { font-size: 2.5rem; }
    }
</style>
""", unsafe_allow_html=True)

# 4. RENDER UI LAYOUT
st.markdown("""
<div class="nav">
    <div class="logo">TRADE<span>POSTMORTEM</span></div>
    <div style="font-size: 0.8rem; color: #64748b; font-weight: 500;">INSTITUTIONAL AUDIT SUITE v2.0</div>
</div>
<div class="hero-h1">Algorithmic Trade Autopsy</div>
<div class="hero-p">A deterministic audit system for financial losses. We identify structural insolvency and behavioral execution errors without the fluff.</div>
""", unsafe_allow_html=True)

# 5. MAIN LOGIC CONTAINER
main_container = st.container()

with main_container:
    tab_image, tab_manual = st.tabs(["📸 OPTICAL CHARACTER RECOGNITION (OCR)", "📝 MANUAL CASE ENTRY"])

    # --- TAB 1: IMAGE ANALYSIS ---
    with tab_image:
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 4, 1]) 
        with c2:
            uploaded_file = st.file_uploader("Upload Chart/P&L Evidence", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

            if uploaded_file:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("INITIATE OPTICAL AUDIT", type="primary", use_container_width=True):
                    with st.spinner("PROCESSING MARKET STRUCTURE & LIQUIDITY ZONES..."):
                        try:
                            image = Image.open(uploaded_file)
                            buf = io.BytesIO()
                            image.save(buf, format="PNG")
                            img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

                            # PROFESSIONAL PROMPT - IMAGE
                            prompt = """
                            ROLE: Senior Quantitative Risk Auditor.
                            TASK: Forensic analysis of the provided financial chart/P&L.
                            
                            STRICT CONSTRAINTS (ANTI-HALLUCINATION):
                            1. Do NOT assume volume, order flow, or news unless clearly visible.
                            2. Do NOT use emotional language (fear, panic) unless the visual evidence proves irrational exits (e.g., exit at exact bottom).
                            3. DEFAULT to "Structural Failure" if no clear psychological error is visible.

                            OUTPUT SCHEMA:
                            [PRIMARY CAUSE]: (Select ONE: Execution Latency, Structural Insolvency, Liquidity Trap, Impulsive Entry).
                            [EVIDENCE]: (Cite specific visual elements: e.g., "Entry executed 3 bars after signal").
                            [RISK CALCULATION]: (Estimate the R:R based on visual stop placement).
                            [INSTITUTIONAL MANDATE]: (A single, corrective algorithmic rule).

                            TONE: Clinical, Mathematical, Objective.
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
                                st.markdown(f"""
                                <div class="report-container">
                                    <div class="report-header">OCR FORENSIC RESULT // REF: {hash(content) % 10000}</div>
                                    <div class="report-content">{content}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"OCR PROCESSING ERROR: {e}")

    # --- TAB 2: MANUAL ENTRY (DETERMINISTIC LOGIC) ---
    with tab_manual:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container():
            col_form_1, col_form_2, col_form_3 = st.columns([1, 6, 1])
            with col_form_2:
                st.markdown("### CASE FILE PARAMETERS")
                
                # ROW 1: CORE DATA
                r1c1, r1c2, r1c3 = st.columns(3)
                with r1c1: ticker = st.text_input("Asset Ticker", placeholder="e.g. BTCUSDT")
                with r1c2: position = st.selectbox("Direction", ["Long", "Short"])
                with r1c3: intent = st.selectbox("Execution Intent", ["Systematic (Planned)", "Discretionary (Impulsive)", "Hybrid"])

                # ROW 2: PRICE DATA
                r2c1, r2c2, r2c3 = st.columns(3)
                with r2c1: entry_px = st.text_input("Entry Price", placeholder="0.00")
                with r2c2: exit_px = st.text_input("Exit Price", placeholder="0.00")
                with r2c3: stop_px = st.text_input("Stop Loss Price", placeholder="0.00")

                st.markdown("<br>", unsafe_allow_html=True)
                
                # CONTEXTUAL DATA
                setup_desc = st.text_area("Structural Thesis (Entry Logic)", placeholder="Define market structure, key levels, and confirmation triggers.")
                exit_desc = st.text_area("Liquidation Context (Exit Logic)", placeholder="Describe the conditions at the moment of exit.")

                st.markdown("<br>", unsafe_allow_html=True)

                if st.button("EXECUTE DIAGNOSTIC ALGORITHM", type="primary", use_container_width=True):
                    if not ticker or not entry_px or not exit_px:
                        st.warning("INSUFFICIENT DATA: Price coordinates required for audit.")
                    else:
                        with st.spinner("CALCULATING VARIANCE & EXPECTANCY..."):
                            try:
                                # 1. DETERMINISTIC MATH LAYER (Python Logic, not AI)
                                try:
                                    e_val = float(entry_px)
                                    x_val = float(exit_px)
                                    s_val = float(stop_px)
                                    
                                    risk_magnitude = abs(e_val - s_val)
                                    loss_magnitude = abs(e_val - x_val)
                                    
                                    # Calculate Deviation
                                    slippage_ratio = 0
                                    if risk_magnitude > 0:
                                        slippage_ratio = (loss_magnitude - risk_magnitude) / risk_magnitude
                                    
                                    math_context = f"Calculated Risk Deviation: {slippage_ratio:.2f}R."
                                except:
                                    math_context = "Risk Calculation Failed: Invalid numeric input."

                                # 2. SYSTEM PROMPT (Professional/Institutional)
                                system_prompt = f"""
                                ROLE: Chief Investment Officer (CIO) / Risk Auditor.
                                OBJECTIVE: Determine the PRIMARY CAUSE of trade failure based on the provided data.

                                INPUT DATA:
                                - Asset: {ticker} ({position})
                                - Intent Class: {intent}
                                - Math Audit: {math_context}
                                - Entry Context: {setup_desc}
                                - Exit Context: {exit_desc}

                                LOGIC TREE (STRICT PRIORITY):
                                1. IF Intent is "Impulsive" -> Primary Cause = "Discretionary Violation".
                                2. IF Setup Context is vague (e.g., "it looked good") -> Primary Cause = "Confirmation Bias".
                                3. IF Risk Deviation > 0.2R (User lost more than planned) -> Primary Cause = "Risk Management Failure".
                                4. IF Entry was technically sound but market reversed -> Primary Cause = "Probabilistic Variance".

                                RULES:
                                - NO HALLUCINATIONS: Do not assume volume, indicators, or news if not listed.
                                - NO PSYCHOLOGY FLUFF: Do not mention "fear" or "greed" unless explicitly stated in Exit Context.
                                - SINGLE DIAGNOSIS: You must choose ONE primary failure point.

                                OUTPUT FORMAT:
                                **DIAGNOSTIC CODE:** [Select: EXECUTION_ERROR | STRUCTURAL_INSOLVENCY | PROBABILISTIC_LOSS]
                                
                                **PRIMARY FAILURE MECHANISM:**
                                (One sentence defining exactly what broke: The Entry, The Risk Model, or The Psychology).

                                **AUDIT FINDINGS:**
                                - Evidence A: (Direct quote or data point).
                                - Evidence B: (Math deviation or logic gap).

                                **CORRECTIVE MANDATE:**
                                (A specific, binary rule to prevent this specific error type).
                                """

                                payload = {
                                    "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                                    "messages": [{"role": "user", "content": system_prompt}],
                                    "max_tokens": 800
                                }
                                headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                                res = requests.post(API_URL, headers=headers, json=payload)
                                
                                if res.status_code == 200:
                                    content = res.json()["choices"][0]["message"]["content"]
                                    st.markdown(f"""
                                    <div class="report-container">
                                        <div class="report-header">ALGORITHMIC DIAGNOSIS // ID: {ticker.upper()}-{position.upper()}</div>
                                        <div class="report-content">{content}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.error(f"API GATEWAY ERROR: {res.status_code}")
                            except Exception as e:
                                st.error(f"RUNTIME EXCEPTION: {e}")

# 6. FOOTER GRID (Professional)
st.markdown("""
<div class="grid-container">
    <div class="feature-card">
        <div class="feature-title">Variance Analysis</div>
        <div class="feature-text">Distinguish between poor execution and standard probabilistic drawdown.</div>
    </div>
    <div class="feature-card">
        <div class="feature-title">Structural Audit</div>
        <div class="feature-text">Identify insolvency in trade thesis relative to market microstructure.</div>
    </div>
    <div class="feature-card">
        <div class="feature-title">Behavioral Drift</div>
        <div class="feature-text">Quantify deviations from your systematic trading mandate.</div>
    </div>
</div>
<div style="text-align: center; margin-top: 5rem; color: #475569; font-size: 0.8rem; font-family: monospace;">
    TRADEPOSTMORTEM.AI // SYSTEM 2.0 // INSTITUTIONAL RELEASE
</div>
""", unsafe_allow_html=True)
