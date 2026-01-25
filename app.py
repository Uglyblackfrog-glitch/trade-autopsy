import streamlit as st
import requests
import base64
import re
import pandas as pd
import time
import json
from supabase import create_client, Client

# ==========================================
# 0. CONFIGURATION & SETUP
# ==========================================
st.set_page_config(
    page_title="StockPostmortem.ai", 
    page_icon="🧬", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Authentication State
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = None

# API Setup (Only if authenticated)
if st.session_state["authenticated"]:
    try:
        HF_TOKEN = st.secrets["HF_TOKEN"]
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"⚠️ System Error: {e}")

# ==========================================
# 1. THEME & EXACT UI OVERRIDE
# ==========================================
st.markdown("""
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,600;0,800;1,800&display=swap" rel="stylesheet">
    <style>
        /* Hide Streamlit Header/Footer/Menus */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        [data-testid="stHeader"] {display:none;}
        
        /* Global Background */
        .stApp {
            background-color: #0d1117 !important;
            font-family: 'Inter', sans-serif !important;
        }

        /* Custom Dropdown Trigger */
        .group:hover .group-hover\:visible {
            visibility: visible !important;
            opacity: 1 !important;
        }

        /* Hero Title Italic */
        .hero-title {
            font-style: italic;
            letter-spacing: -0.02em;
        }

        /* Upload Area Styling */
        .upload-dashed {
            border: 2px dashed #30363d;
            border-radius: 1.5rem;
        }

        /* Hide Default File Uploader UI but keep functionality */
        .stFileUploader section {
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
        }
        
        /* Sidebar/Tab Overrides to match theme */
        .stTabs [data-baseweb="tab-list"] { gap: 24px; border-bottom: 1px solid #30363d; }
        .stTabs [data-baseweb="tab"] { 
            color: #8b949e; 
            background: transparent !important;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.1em;
        }
        .stTabs [aria-selected="true"] { color: white !important; border-bottom-color: #ef4444 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. NAV & HEADER (EXACT HTML)
# ==========================================
st.markdown(f"""
    <nav class="flex items-center justify-between px-8 py-6 max-w-7xl mx-auto relative">
        <div class="flex items-center gap-1">
            <span class="text-white font-extrabold text-xl tracking-tighter">STOCK<span class="text-red-500">POSTMORTEM</span>.AI</span>
        </div>
        
        <div class="hidden md:flex items-center gap-8 text-xs font-semibold uppercase tracking-widest text-gray-400">
            <div class="relative group">
                <button class="hover:text-white transition flex items-center gap-1 uppercase outline-none">
                    Analyze
                    <svg class="w-3 h-3 text-gray-500 group-hover:text-white transition" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                </button>
                <div class="absolute left-0 mt-4 w-52 bg-[#161b22] border border-gray-800 rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 overflow-hidden">
                    <div class="flex flex-col">
                        <p class="px-5 py-4 text-[10px] tracking-widest text-gray-500 border-b border-gray-800">Visual Evidence</p>
                        <p class="px-5 py-4 text-[10px] tracking-widest text-gray-500">Detailed Text Log</p>
                    </div>
                </div>
            </div>
            <a href="#" class="hover:text-white transition">Data Vault</a>
            <a href="#" class="hover:text-white transition">Pricing</a>
        </div>
        <div class="text-white text-xs font-bold uppercase tracking-widest">{st.session_state["user"] if st.session_state["authenticated"] else "Guest"}</div>
    </nav>
""", unsafe_allow_html=True)

# ==========================================
# 3. MAIN CONTENT
# ==========================================
if not st.session_state["authenticated"]:
    # Login View
    st.markdown("""
        <main class="flex flex-col items-center justify-center text-center px-4 mt-16">
            <h1 class="text-5xl md:text-7xl font-extrabold text-white hero-title mb-6">OPERATOR LOGIN.</h1>
        </main>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            u = st.text_input("Operator ID")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("AUTHENTICATE"):
                if u == "demo" and p == "12345": # Replace with USERS logic
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = u
                    st.rerun()
                else:
                    st.error("Invalid ID")

else:
    # Authenticated Landing Page
    st.markdown("""
        <main class="flex flex-col items-center justify-center text-center px-4 mt-16">
            <h1 class="text-5xl md:text-7xl font-extrabold text-white hero-title mb-6">STOP BLEEDING CAPITAL.</h1>
            <p class="max-w-2xl text-gray-400 text-lg leading-relaxed mb-12">
                Upload your losing trade screenshots. Our AI identifies psychological traps, technical failures, and provides a surgical path to recovery.
            </p>
        </main>
    """, unsafe_allow_html=True)

    # Use Tabs for Analyze vs Data Vault
    tab_analyze, tab_vault = st.tabs(["🔬 Analyze", "📊 Data Vault"])

    with tab_analyze:
        col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
        with col2:
            # Re-creating the Upload Box exactly
            st.markdown("""
                <div class="w-full bg-[#161b22] rounded-3xl p-12 upload-dashed flex flex-col items-center border-[#30363d] text-center">
                    <div class="bg-red-500/10 p-4 rounded-full mb-6 mx-auto w-fit">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                    </div>
                    <h2 class="text-2xl font-bold text-white mb-2">Drop your P&L or Chart screenshot here</h2>
                    <p class="text-gray-500 text-sm mb-8">Supports PNG, JPG (Max 10MB). Your data is encrypted and deleted after analysis.</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Invisible Streamlit Uploader sitting on top/bottom
            up_file = st.file_uploader("Select File", type=["png", "jpg"], label_visibility="collapsed")
            
            if up_file:
                st.image(up_file, caption="Scan Ready", use_container_width=True)
                if st.button("RUN POST-MORTEM"):
                    with st.spinner("Surgical Analysis in Progress..."):
                        time.sleep(2) # Fake processing
                        st.success("Analysis Complete. Check Data Vault.")

    with tab_vault:
        st.markdown("<h3 class='text-white font-bold mb-4'>Post-Mortem Logs</h3>", unsafe_allow_html=True)
        # Display Data Table matching theme
        # dummy data
        df = pd.DataFrame({'Date': ['2026-01-25'], 'Ticker': ['$NVDA'], 'Score': [42], 'Mistake': ['FOMO Entry']})
        st.dataframe(df, use_container_width=True)

    # Bottom Grid (Exactly like HTML)
    st.markdown("""
        <div class="max-w-7xl mx-auto px-8">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 w-full mb-20">
                <div class="bg-[#161b22] p-8 rounded-xl border border-gray-800 text-left">
                    <h3 class="text-white font-bold mb-3 text-lg">Pattern Recognition</h3>
                    <p class="text-gray-500 text-sm leading-relaxed">
                        Did you buy the top? We identify if you're falling for FOMO or revenge trading.
                    </p>
                </div>
                <div class="bg-[#161b22] p-8 rounded-xl border border-gray-800 text-left">
                    <h3 class="text-white font-bold mb-3 text-lg">Risk Autopsy</h3>
                    <p class="text-gray-500 text-sm leading-relaxed">
                        Calculates if your stop-loss was too tight or if your position sizing was reckless.
                    </p>
                </div>
                <div class="bg-[#161b22] p-8 rounded-xl border border-gray-800 text-left">
                    <h3 class="text-white font-bold mb-3 text-lg">Recovery Plan</h3>
                    <p class="text-gray-500 text-sm leading-relaxed">
                        Step-by-step technical adjustments to ensure the next trade is a winner.
                    </p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Footer Logout
if st.session_state["authenticated"]:
    if st.button("Terminate Session"):
        st.session_state["authenticated"] = False
        st.rerun()
