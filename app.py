import streamlit as st
import requests
import base64
from PIL import Image
import io

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Trade Postmortem | Pro OSS",
    page_icon="⚖️",
    layout="wide"
)

# --- 2. THE TOKEN (HARDCODED FOR INSTANT ACCESS) ---
HF_TOKEN = "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"
MODEL_ID = "Qwen/Qwen2-VL-7B-Instruct"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# --- 3. PROFESSIONAL DARK MODE CSS ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .report-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 25px;
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
        color: #e6edf3;
    }
    h1, h2, h3 {
        color: #58a6ff !important;
    }
    .stButton>button {
        background-color: #238636;
        color: white;
        border: none;
        width: 100%;
        padding: 12px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #2ea043;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. HELPER FUNCTION ---
def query_vision_model(image_bytes):
    # Convert image to Base64 string
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    
    # Structure the prompt for professional analysis
    prompt = (
        "Analyze this trading chart screenshot like a senior risk manager. "
        "Identify the trend, the entry point, and the specific technical mistake. "
        "Provide a discipline score from 0-100 and a professional corrective action."
    )
    
    payload = {
        "inputs": f"data:image/png;base64,{encoded_image}",
        "parameters": {"max_new_tokens": 500},
        "context": prompt
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

# --- 5. MAIN UI ---
st.title("⚖️ TRADE POSTMORTEM")
st.markdown("##### Open-Source Institutional Forensic Engine")
st.markdown("---")

left_col, right_col = st.columns([1, 1.2])

with left_col:
    st.subheader("📁 EVIDENCE UPLOAD")
    uploaded_file = st.file_uploader("Upload Chart Screenshot", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Trade Record", use_container_width=True)
        
        # Prepare image bytes
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        image_bytes = buf.getvalue()

with right_col:
    st.subheader("🔍 DIAGNOSTIC AUDIT")
    
    if uploaded_file:
        if st.button("EXECUTE FORENSIC ANALYSIS"):
            with st.spinner("AI IS SCANNING PIXELS AND MARKET STRUCTURE..."):
                try:
                    output = query_vision_model(image_bytes)
                    
                    # Hugging Face output parsing
                    if isinstance(output, list) and 'generated_text' in output[0]:
                        analysis = output[0]['generated_text']
                    elif isinstance(output, dict) and 'generated_text' in output:
                        analysis = output['generated_text']
                    else:
                        analysis = str(output)

                    st.markdown(f"""
                        <div class="report-card">
                        {analysis}
                        </div>
                    """, unsafe_allow_html=True)
                    st.success("Analysis Complete.")
                    
                except Exception as e:
                    st.error(f"System Error: {e}")
    else:
        st.info("Awaiting chart upload to begin analysis.")

st.markdown("---")
st.caption("Running on Open-Source Qwen2-VL via Hugging Face Inference API.")
