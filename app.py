import streamlit as st
import requests
import base64
from PIL import Image
import io

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Trade Postmortem Pro",
    page_icon="⚖️",
    layout="wide"
)

# --- 2. SECURE CREDENTIALS ---
try:
    # IMPORTANT: Ensure HF_TOKEN is in your Streamlit Secrets vault!
    HF_TOKEN = st.secrets["HF_TOKEN"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except Exception:
    st.error("🔑 HF_TOKEN missing! Go to Streamlit Settings > Secrets and add: HF_TOKEN = 'your_token'")
    st.stop()

# --- 3. PROFESSIONAL UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .report-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 25px;
        line-height: 1.7;
        color: #e6edf3;
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3 { color: #58a6ff !important; }
    .stButton>button {
        background-color: #238636;
        color: white;
        width: 100%;
        padding: 12px;
        font-weight: bold;
        border-radius: 8px;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. OPTIMIZED QUERY FUNCTION ---
def query_router(image_base64):
    # Added "X-Wait-For-Model" header to prevent "Model Loading" errors
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
        "X-Wait-For-Model": "true" 
    }
    
    payload = {
        "model": "Qwen/Qwen2-VL-7B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": "Audit this trading chart. Identify the pattern, entry quality, and potential psychological errors. Be professional and brief."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                    }
                ]
            }
        ],
        "max_tokens": 800,
        "temperature": 0.1 # Low temperature for more factual analysis
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    return response

# --- 5. MAIN UI ---
st.title("⚖️ TRADE POSTMORTEM")
st.markdown("##### AI Trading Discipline Auditor")
st.markdown("---")

left_col, right_col = st.columns([1, 1.2])

with left_col:
    st.subheader("📁 UPLOAD CHART")
    file = st.file_uploader("Drop screenshot here", type=["jpg", "png", "jpeg"])
    
    if file:
        image = Image.open(file)
        st.image(image, caption="Trade Record", use_container_width=True)
        
        # Base64 encoding
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

with right_col:
    st.subheader("🔍 FORENSIC AUDIT")
    
    if file:
        if st.button("EXECUTE ANALYSIS"):
            with st.spinner("AI is waking up and scanning the candles... (may take 20s)"):
                try:
                    res = query_router(img_b64)
                    
                    if res.status_code == 200:
                        data = res.json()
                        analysis = data['choices'][0]['message']['content']
                        st.markdown(f'<div class="report-card">{analysis}</div>', unsafe_allow_html=True)
                        st.success("Audit Complete.")
                    elif res.status_code == 401:
                        st.error("❌ Authentication Failed: Your token is invalid or expired. Create a NEW one on Hugging Face.")
                    else:
                        st.error(f"Error {res.status_code}: {res.text}")
                        
                except Exception as e:
                    st.error(f"System Crash: {e}")
    else:
        st.info("Upload a chart to begin.")
