import streamlit as st
import requests
import base64
from PIL import Image
import io

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Trade Postmortem | Pro Router",
    page_icon="⚖️",
    layout="wide"
)

# --- 2. SECURE CREDENTIALS ---
# This pulls the token from the "Secrets" vault so GitHub bots can't see it.
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except Exception:
    st.error("🔑 HF_TOKEN not found in Secrets. Please add it to Streamlit Cloud Settings.")
    st.stop()

# --- 3. PROFESSIONAL DARK MODE CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .report-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 25px;
        line-height: 1.6;
        color: #e6edf3;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    h1, h2, h3 { color: #58a6ff !important; }
    .stButton>button {
        background-color: #238636;
        color: white;
        width: 100%;
        padding: 12px;
        font-weight: bold;
        border: none;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #2ea043;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. NEW ROUTER QUERY FUNCTION ---
def query_router(image_base64):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "Qwen/Qwen2-VL-7B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": "Perform a professional forensic audit on this trading chart. Identify the setup, assess entry quality, and diagnose psychological errors (e.g., FOMO). Tone: Senior Risk Manager."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                    }
                ]
            }
        ],
        "max_tokens": 600
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

# --- 5. MAIN UI ---
st.title("⚖️ TRADE POSTMORTEM")
st.markdown("##### 2026 Institutional Risk Analysis Interface")
st.markdown("---")

left_col, right_col = st.columns([1, 1.2])

with left_col:
    st.subheader("📁 EVIDENCE UPLOAD")
    uploaded_file = st.file_uploader("Upload Chart Screenshot", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Trade Record for Analysis", use_container_width=True)
        
        # Convert to Base64 for the Router
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

with right_col:
    st.subheader("🔍 DIAGNOSTIC AUDIT")
    
    if uploaded_file:
        if st.button("EXECUTE FORENSIC ANALYSIS"):
            with st.spinner("ROUTING TO NEURAL NETWORK..."):
                try:
                    output = query_router(image_base64)
                    
                    if 'choices' in output:
                        analysis = output['choices'][0]['message']['content']
                        st.markdown(f'<div class="report-card">{analysis}</div>', unsafe_allow_html=True)
                        st.success("Audit Complete.")
                    else:
                        error_msg = output.get('error', 'Authentication failed or Model loading.')
                        st.error(f"Router Error: {error_msg}")
                        st.info("Tip: If the error says 'Model loading', wait 10 seconds and click analyze again.")
                        
                except Exception as e:
                    st.error(f"System Error: {e}")
    else:
        st.info("Awaiting visual evidence to initiate audit...")

st.markdown("---")
st.caption("Secure Professional Edition • Powered by Qwen-VL Vision Engine")
