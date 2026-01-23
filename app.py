import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Trade Postmortem | Pro",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- PROFESSIONAL DARK MODE CSS ---
st.markdown("""
    <style>
    /* Main Background: Deep Slate */
    .stApp {
        background-color: #0f1116;
        color: #e0e0e0;
    }
    /* Cards/Containers */
    .metric-card {
        background-color: #1e2329;
        border: 1px solid #2d333b;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
    }
    /* Headers */
    h1, h2, h3 {
        color: #58a6ff !important;
        font-family: 'Segoe UI', sans-serif;
    }
    /* Professional Button */
    .stButton>button {
        background-color: #238636;
        color: white;
        border: none;
        width: 100%;
        padding: 10px;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #2ea043;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR (API KEY) ---
with st.sidebar:
    st.header("🔐 SECURITY CLEARANCE")
    # Tries to get key from Secrets first, otherwise asks user
    if 'GEMINI_API_KEY' in st.secrets:
        api_key = st.secrets['GEMINI_API_KEY']
        st.success("API Key Loaded from Secrets")
    else:
        api_key = st.text_input("Enter Gemini API Key", type="password")

# --- MAIN UI ---
st.title("⚖️ TRADE POSTMORTEM")
st.markdown("### Institutional Grade Risk Analysis")
st.markdown("---")

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("1. UPLOAD EVIDENCE")
    uploaded_file = st.file_uploader("Upload Chart Screenshot", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Trade Artifact", use_container_width=True)

with col2:
    st.subheader("2. FORENSIC AUDIT")
    
    if uploaded_file and api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")

        # --- THE PROFESSIONAL PROMPT ---
        system_prompt = """
        ACT AS: A Senior Risk Manager at a top-tier Hedge Fund.
        TASK: Audit this junior trader's trade based on the screenshot.
        TONE: Cold, Professional, Analytical. No slang. Use financial terminology.
        
        OUTPUT FORMAT (Strict Markdown):
        
        ## 📋 EXECUTIVE SUMMARY
        * **Setup Identified:** (e.g., Bull Flag, Support Bounce)
        * **Market Structure:** (Trending, Ranging, Choppy)
        
        ## 📉 RISK ASSESSMENT
        * **Entry Efficiency:** (Grade A to F - Did they enter late?)
        * **Stop Loss Logic:** (Was it technical or arbitrary?)
        * **Risk/Reward Ratio:** (Estimate visually)

        ## 🧠 BEHAVIORAL DIAGNOSIS
        * **Primary Error:** (e.g., FOMO, Counter-trend, Revenge Trading)
        * **Psychology Score:** [ 0-100 ]
        
        ## 🛠️ CORRECTIVE PROTOCOL
        * (One specific, actionable rule they must follow next time).
        """

        if st.button("RUN DIAGNOSTIC AUDIT"):
            with st.spinner("ANALYZING MARKET STRUCTURE..."):
                try:
                    response = model.generate_content([system_prompt, image])
                    
                    # Display Raw Report
                    st.markdown(f"""
                        <div class="metric-card">
                        {response.text}
                        </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"System Error: {e}")
    
    elif not api_key:
        st.warning("⚠️ API KEY REQUIRED IN SIDEBAR")
