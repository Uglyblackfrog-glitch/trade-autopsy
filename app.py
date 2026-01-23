import streamlit as st
import google.generativeai as genai
from PIL import Image
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Trade Postmortem | Pro",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. PROFESSIONAL DARK MODE CSS ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0f1116;
        color: #e0e0e0;
    }
    .metric-card {
        background-color: #1e2329;
        border: 1px solid #2d333b;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 10px;
        line-height: 1.6;
    }
    h1, h2, h3 {
        color: #58a6ff !important;
        font-family: 'Segoe UI', sans-serif;
    }
    .stButton>button {
        background-color: #238636;
        color: white;
        border: none;
        width: 100%;
        padding: 12px;
        font-weight: 600;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #2ea043;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (API KEY) ---
with st.sidebar:
    st.header("🔐 SECURITY CLEARANCE")
    # Check Streamlit Secrets first
    if 'GEMINI_API_KEY' in st.secrets:
        api_key = st.secrets['GEMINI_API_KEY']
        st.success("Neural Link: ACTIVE 🟢")
    else:
        api_key = st.text_input("Enter Gemini API Key", type="password")
        if not api_key:
            st.info("Obtain a key at aistudio.google.com")

# --- 4. MAIN UI LAYOUT ---
st.title("⚖️ TRADE POSTMORTEM")
st.markdown("#### Institutional-Grade Forensic Analysis Engine")
st.markdown("---")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📁 EVIDENCE UPLOAD")
    uploaded_file = st.file_uploader("Drop Trade Screenshot (JPG/PNG)", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Trade Artifact for Analysis", use_container_width=True)

with col2:
    st.subheader("🔍 FORENSIC AUDIT REPORT")
    
    if uploaded_file and api_key:
        # Initialize Gemini with the API Key
        genai.configure(api_key=api_key)
        
        # Use the most stable 2026 model string
        model = genai.GenerativeModel("gemini-1.5-flash") 

        system_prompt = """
        ACT AS: A Senior Risk Manager at a top-tier Hedge Fund (Goldman Sachs/Citadel style).
        TASK: Conduct a forensic audit of this trade execution.
        TONE: Cold, Professional, Analytical. Use financial terminology (Liquidity, Delta, FVGs, etc.).
        
        OUTPUT FORMAT (Strict Markdown):
        
        ## 📋 EXECUTIVE SUMMARY
        * **Market Structure:** (Trending/Ranging/Reversal)
        * **Setup Identified:** (Identify the specific pattern)
        
        ## 📉 RISK ASSESSMENT
        * **Entry Efficiency:** (Grade A-F)
        * **Stop Loss Placement:** (Technical vs Arbitrary)
        * **Risk/Reward Profile:** (Estimated ratio)

        ## 🧠 BEHAVIORAL DIAGNOSIS
        * **Psychological Trigger:** (e.g., FOMO, Revenge, Impatience)
        * **Discipline Score:** [ 0-100 ]
        
        ## 🛠️ CORRECTIVE PROTOCOL
        * (One non-negotiable rule for the trader's next session).
        """

        if st.button("INITIATE ANALYTICAL ENGINE"):
            with st.spinner("COMMUNICATING WITH NEURAL NETWORK..."):
                # RETRY LOGIC for Quota/Speed limits
                success = False
                for attempt in range(3):
                    try:
                        response = model.generate_content([system_prompt, image])
                        st.markdown(f'<div class="metric-card">{response.text}</div>', unsafe_allow_html=True)
                        st.success("Audit Complete.")
                        success = True
                        break
                    except Exception as e:
                        if "429" in str(e):
                            st.warning(f"Server Busy. Retry {attempt+1}/3 in 5s...")
                            time.sleep(5)
                        else:
                            st.error(f"Audit Failed: {e}")
                            break
                if not success:
                    st.error("Maximum retries reached. Check your API Quota.")
    
    elif not uploaded_file:
        st.info("Awaiting visual data for processing...")
    elif not api_key:
        st.warning("⚠️ ACCESS DENIED: Neural Link Key Missing.")
