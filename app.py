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

# --- 2. THE NEW ROUTER CREDENTIALS ---
HF_TOKEN = "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"
# New 2026 Router Endpoint
API_URL = "https://router.huggingface.co/v1/chat/completions"

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
    }
    h1, h2, h3 { color: #58a6ff !important; }
    .stButton>button {
        background-color: #238636;
        color: white;
        width: 100%;
        padding: 12px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. NEW ROUTER QUERY FUNCTION ---
def query_router(image_base64):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Standard OpenAI-style payload for the HF Router
    payload = {
        "model": "Qwen/Qwen2-VL-7B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this trading chart. Identify the setup, entry quality, and potential psychological errors like FOMO. Be professional and brief."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                    }
                ]
            }
        ],
        "max_tokens": 500
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

# --- 5. MAIN UI ---
st.title("⚖️ TRADE POSTMORTEM")
st.markdown("##### Powered by the 2026 Hugging Face Router")
st.markdown("---")

left_col, right_col = st.columns([1, 1.2])

with left_col:
    st.subheader("📁 EVIDENCE UPLOAD")
    uploaded_file = st.file_uploader("Upload Chart Screenshot", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Trade Record", use_container_width=True)
        
        # Convert to Base64 for the Router
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

with right_col:
    st.subheader("🔍 DIAGNOSTIC AUDIT")
    
    if uploaded_file:
        if st.button("EXECUTE FORENSIC ANALYSIS"):
            with st.spinner("ROUTING REQUEST TO NEURAL NETWORK..."):
                try:
                    output = query_router(image_base64)
                    
                    # Parse the new standard response format
                    if 'choices' in output:
                        analysis = output['choices'][0]['message']['content']
                        st.markdown(f'<div class="report-card">{analysis}</div>', unsafe_allow_html=True)
                        st.success("Analysis Complete.")
                    else:
                        st.error(f"Router Error: {output.get('error', 'Unknown Error')}")
                        
                except Exception as e:
                    st.error(f"System Error: {e}")
    else:
        st.info("Awaiting chart upload...")
