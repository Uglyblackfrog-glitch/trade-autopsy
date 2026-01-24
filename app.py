import streamlit as st
import requests
import base64
import io
from PIL import Image

# =========================================================
# 1. CONFIG: WIDE LAYOUT & HIDE DEFAULT JUNK
# =========================================================
st.set_page_config(
    page_title="StockPostmortem.ai",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# 2. YOUR CREDENTIALS (FROM SECRETS)
# =========================================================
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except Exception:
    st.error("⚠️ HF_TOKEN is missing in Streamlit Secrets.")
    st.stop()

# =========================================================
# 3. INJECT YOUR EXACT HTML & CSS (THE HYBRID METHOD)
# =========================================================
# We include Tailwind CSS via CDN so your classes work instantly.
st.markdown("""
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* GLOBAL RESET & FONTS */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
        
        body { background-color: #0f171c; color: #e2e8f0; font-family: 'Inter', sans-serif; }
        .stApp { background-color: #0f171c; } /* Streamlit background fix */
        
        /* HIDE STREAMLIT HEADER/FOOTER */
        header {visibility: hidden;}
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        .block-container { padding-top: 0rem; padding-bottom: 0rem; }
        
        /* CUSTOM UTILS FROM YOUR FILE */
        .bg-brand { background-color: #1f2e38; }
        .accent-red { color: #ff4d4d; }
        
        /* THE GLASS CARD STYLING FOR UPLOADER */
        .glass-card-style {
            background: rgba(31, 46, 56, 0.6);
            backdrop-filter: blur(10px);
            border: 2px dashed #475569;
            border-radius: 1rem;
            padding: 3rem;
            text-align: center;
            transition: all 0.3s ease;
        }
        .glass-card-style:hover {
            border-color: #ff4d4d;
            background: rgba(31, 46, 56, 0.8);
        }

        /* FORCE STREAMLIT UPLOADER TO BE INVISIBLE BUT CLICKABLE */
        /* We style the container to look like your HTML card */
        [data-testid="stFileUploader"] {
            width: 100%;
            padding: 0;
            margin: 0;
        }
        [data-testid="stFileUploaderDropzone"] {
            background: transparent;
            border: none;
            color: transparent;
        }
        /* Hide the default text */
        [data-testid="stFileUploaderDropzoneInstructions"] { display: none; }
        [data-testid="stFileUploaderUploadedFiles"] { display: none; }
        
        /* Button Styling */
        div.stButton > button {
            background-color: #ff4d4d;
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 9999px;
            font-weight: 600;
            transition: all 0.2s;
        }
        div.stButton > button:hover {
            background-color: #dc2626;
            transform: scale(1.05);
        }

    </style>
""", unsafe_allow_html=True)

# =========================================================
# 4. RENDER VISUALS (NAVBAR + HERO)
# =========================================================

# --- NAVBAR (HTML) ---
st.markdown("""
    <nav class="p-6 flex justify-between items-center border-b border-[#2d4250] max-w-7xl mx-auto">
        <div class="text-2xl font-bold tracking-tighter text-white">STOCK<span class="text-[#ff4d4d]">POSTMORTEM</span>.AI</div>
        <div class="hidden md:flex space-x-8 text-sm uppercase tracking-widest text-slate-300">
            <span class="cursor-pointer hover:text-[#ff4d4d]">Analyze</span>
            <span class="cursor-pointer hover:text-[#ff4d4d]">Case Studies</span>
            <span class="cursor-pointer hover:text-[#ff4d4d]">Pricing</span>
        </div>
        <button class="bg-[#ff4d4d] text-white px-5 py-2 rounded-full font-semibold hover:bg-red-700 transition">Get Started</button>
    </nav>
""", unsafe_allow_html=True)

# --- HERO SECTION (HTML) ---
st.markdown("""
    <header class="max-w-6xl mx-auto pt-20 pb-12 text-center px-4">
        <h1 class="text-5xl md:text-7xl font-extrabold mb-6 italic text-white">STOP BLEEDING CAPITAL.</h1>
        <p class="text-xl text-slate-400 max-w-2xl mx-auto">
            Upload your losing trade screenshots. Our AI identifies psychological traps, technical failures, and provides a surgical path to recovery.
        </p>
    </header>
""", unsafe_allow_html=True)

# =========================================================
# 5. THE UPLOADER (STREAMLIT LOGIC DISGUISED AS HTML)
# =========================================================

# We use columns to center it perfectly like your "max-w-4xl" container
spacer_left, main_content, spacer_right = st.columns([1, 2, 1])

with main_content:
    # 1. We create a container that looks exactly like your "glass-card"
    st.markdown("""
    <div class="glass-card-style mb-4">
        <div class="mb-6 inline-block p-4 bg-[#1f2e38] rounded-full">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-[#ff4d4d]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
        </div>
        <h2 class="text-2xl font-semibold mb-2 text-white">Drop your P&L or Chart here</h2>
        <p class="text-slate-500 mb-6">Supports PNG, JPG. Encrypted & Private.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. THE ACTUAL STREAMLIT UPLOADER (Placed right below the visual cue)
    uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    
    # 3. LOGIC: If file is uploaded, show the "Analyze" button
    if uploaded_file:
        st.success("✅ Image Loaded Securely")
        if st.button("RUN FORENSIC ANALYSIS", type="primary", use_container_width=True):
            with st.spinner("🔍 ANALYZING MARKET STRUCTURE & PSYCHOLOGY..."):
                try:
                    # Prepare Image
                    image = Image.open(uploaded_file)
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

                    # AI Prompt
                    prompt = (
                        "ACT AS: Senior Trading Psychologist & Risk Manager. "
                        "INPUT: Trading Chart or P&L. "
                        "TASK: 1. Identify the 'Kill Zone' (Mistake). 2. Diagnose Psychology (FOMO/Revenge). 3. Audit Risk. 4. Fix it."
                        "OUTPUT: Brutally honest, concise, bullet points. Use bolding."
                    )
                    
                    payload = {
                        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                        "messages": [
                            {"role": "user", "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                            ]}
                        ],
                        "max_tokens": 1000
                    }
                    
                    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                    res = requests.post(API_URL, headers=headers, json=payload)
                    
                    if res.status_code == 200:
                        content = res.json()["choices"][0]["message"]["content"]
                        # Render Result in a nice box
                        st.markdown(f"""
                        <div style="background: #161b22; border-left: 4px solid #ff4d4d; padding: 20px; border-radius: 8px; margin-top: 20px; color: #e2e8f0;">
                            {content}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("AI Server Busy. Please try again.")
                except Exception as e:
                    st.error(f"Error: {e}")

# =========================================================
# 6. FEATURE GRID (HTML)
# =========================================================
st.markdown("""
    <div class="max-w-5xl mx-auto px-4 pb-20 mt-20">
        <div class="grid md:grid-cols-3 gap-8">
            <div class="p-6 rounded-xl bg-[#1f2e38]">
                <h3 class="font-bold text-lg mb-2 text-white">Pattern Recognition</h3>
                <p class="text-sm text-slate-400">Did you buy the top? We identify if you're falling for FOMO or revenge trading.</p>
            </div>
            <div class="p-6 rounded-xl bg-[#1f2e38]">
                <h3 class="font-bold text-lg mb-2 text-white">Risk Autopsy</h3>
                <p class="text-sm text-slate-400">Calculates if your stop-loss was too tight or if your position sizing was reckless.</p>
            </div>
            <div class="p-6 rounded-xl bg-[#1f2e38]">
                <h3 class="font-bold text-lg mb-2 text-white">Recovery Plan</h3>
                <p class="text-sm text-slate-400">Step-by-step technical adjustments to ensure the next trade is a winner.</p>
            </div>
        </div>
    </div>
    
    <footer class="border-t border-[#2d4250] py-10 text-center text-slate-600 text-sm">
        &copy; 2026 stockpostmortem.ai | Trading involves risk. Keep your head cool.
    </footer>
""", unsafe_allow_html=True)
