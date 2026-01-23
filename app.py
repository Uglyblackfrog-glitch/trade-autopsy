import streamlit as st
import requests
import base64
import json
from PIL import Image
import io

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Trade Postmortem | HUD",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SECURE CREDENTIALS ---
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    API_URL = "https://router.huggingface.co/v1/chat/completions"
except Exception:
    st.error("🔑 HF_TOKEN missing! Add it to Streamlit Secrets.")
    st.stop()

# --- 3. CYBERPUNK HUD CSS ---
st.markdown("""
    <style>
    /* MAIN BACKGROUND */
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 50%, #0a0a0a 0%, #000000 100%);
        color: #e0e0e0;
    }
    
    /* SIDEBAR STYLING */
    [data-testid="stSidebar"] {
        background-color: #080808;
        border-right: 1px solid #333;
    }
    
    /* NEON CARDS */
    .hud-card {
        background-color: #0f1116;
        border: 1px solid #1e2329;
        border-left: 3px solid #00f2ff; /* Cyan Accent */
        border-radius: 6px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    .risk-card {
        background-color: #0f1116;
        border: 1px solid #1e2329;
        border-left: 3px solid #ff2b2b; /* Red Accent */
        border-radius: 6px;
        padding: 20px;
        text-align: center;
    }

    /* TYPOGRAPHY */
    h1, h2, h3 {
        font-family: 'Courier New', monospace;
        letter-spacing: -1px;
    }
    .big-stat {
        font-size: 2.5rem;
        font-weight: 700;
        color: #fff;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
    }
    .neon-text { color: #00f2ff; font-weight: bold; letter-spacing: 1px; }
    .neon-red { color: #ff2b2b; font-weight: bold; }
    .neon-green { color: #00ff41; font-weight: bold; }
    
    /* BUTTON STYLING */
    .stButton>button {
        background: linear-gradient(45deg, #004d00, #008000);
        color: #fff;
        border: 1px solid #00ff41;
        font-family: 'Courier New', monospace;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        box-shadow: 0 0 15px #00ff41;
        transform: scale(1.02);
    }
    
    /* HIDE DEFAULT ELEMENTS */
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. INTELLIGENT QUERY FUNCTION (JSON MODE) ---
def query_router(image_base64):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
        "X-Wait-For-Model": "true" 
    }
    
    # We ask the AI for JSON specifically to populate our UI cards
    system_logic = (
        "ACT AS: Senior Risk Algo. "
        "TASK: Analyze chart/portfolio. Calculate Net P/L = (Realised + Unrealised). "
        "OUTPUT FORMAT: Return a valid JSON object with these exact keys: "
        "{'risk_score': (0-100 int), 'net_pl': 'string with currency', 'primary_diagnosis': 'One Word (e.g. FOMO)', "
        "'discipline_score': (0-100 int), 'key_errors': ['point 1', 'point 2'], 'corrective_plan': ['step 1', 'step 2']}"
    )
    
    payload = {
        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": system_logic},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                    }
                ]
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.1
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    return response

# --- 5. SIDEBAR (SECURITY CLEARANCE) ---
with st.sidebar:
    st.markdown("### 🛡️ SECURITY CLEARANCE")
    st.markdown("<div style='color:#00ff41; font-size:0.8rem;'>● NEURAL LINK: ACTIVE</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    uploaded_file = st.file_uploader("DROP EVIDENCE", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="FILE: 0b2a9fee...jpg", use_container_width=True)
        
        # Prepare Data
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    st.markdown("---")
    st.caption("SYSTEM v2.5 // QWEN-VL")

# --- 6. MAIN DASHBOARD ---
st.markdown("## ⚡ TRADE POSTMORTEM <span style='font-size:0.5em; vertical-align:middle; color:#666;'>INSTITUTIONAL GRADE AUDIT</span>", unsafe_allow_html=True)

# Layout: Left (Chart/Input Placeholder) | Right (HUD Metrics)
col_main, col_hud = st.columns([1.5, 1])

with col_main:
    st.markdown('<div class="hud-card" style="height: 400px; display:flex; align-items:center; justify-content:center; color:#555;">DATA VISUALIZATION MATRIX</div>', unsafe_allow_html=True)
    
    if uploaded_file:
        if st.button("INITIATE ANALYTICAL ENGINE", use_container_width=True):
            with st.spinner("Decrypting Market Patterns..."):
                try:
                    res = query_router(img_b64)
                    
                    if res.status_code == 200:
                        # Parse the JSON response
                        content = res.json()['choices'][0]['message']['content']
                        # Cleaning logic in case AI wraps json in ```json ... ```
                        clean_json = content.replace("```json", "").replace("```", "").strip()
                        data = json.loads(clean_json)
                        
                        # --- DISPLAY RESULTS (THE HUD) ---
                        with col_hud:
                            # Row 1: Scores
                            r1, r2 = st.columns(2)
                            with r1:
                                st.markdown(f"""
                                    <div class="risk-card">
                                        <div style="font-size:0.8rem; color:#aaa;">RISK SCORE</div>
                                        <div class="big-stat" style="color:#ff2b2b;">{data.get('risk_score', 'N/A')}</div>
                                        <div style="font-size:0.7rem;">CRITICAL LEVEL</div>
                                    </div>
                                """, unsafe_allow_html=True)
                            with r2:
                                st.markdown(f"""
                                    <div class="hud-card" style="text-align:center;">
                                        <div style="font-size:0.8rem; color:#aaa;">NET P/L</div>
                                        <div class="big-stat" style="color:#00ff41; font-size:1.8rem;">{data.get('net_pl', 'N/A')}</div>
                                        <div style="font-size:0.7rem;">CALCULATED TRUTH</div>
                                    </div>
                                """, unsafe_allow_html=True)
                            
                            # Row 2: Diagnosis
                            st.markdown(f"""
                                <div class="hud-card">
                                    <div class="neon-text">⚠️ BEHAVIORAL DIAGNOSIS</div>
                                    <h1 style="color:#ff2b2b; margin:0;">{data.get('primary_diagnosis', 'UNKNOWN')}</h1>
                                    <div style="margin-top:10px;">
                                        Discipline Score: <b style="color:#fff">{data.get('discipline_score', 0)}/100</b>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Row 3: Corrective Protocol
                            protocols = "".join([f"<li>{p}</li>" for p in data.get('corrective_plan', [])])
                            st.markdown(f"""
                                <div class="hud-card" style="border-left: 3px solid #00ff41;">
                                    <div class="neon-green">🛠️ CORRECTIVE PROTOCOL</div>
                                    <ul style="padding-left:20px; color:#ccc; margin-top:10px;">
                                        {protocols}
                                    </ul>
                                </div>
                            """, unsafe_allow_html=True)
                            
                    else:
                        st.error(f"System Malfunction: {res.text}")
                        
                except Exception as e:
                    st.error(f"Neural Link Failure: {e}")
                    # Fallback for demo if JSON parsing fails
                    st.info("Raw Data Received (JSON Parse Failed): Check logs.")

    else:
        with col_hud:
            st.info("Awaiting visual input to activate HUD...")
            # Placeholder Empty HUD
            st.markdown("""
                <div class="hud-card" style="opacity:0.5;">
                    <div>SYSTEM STANDBY</div>
                    <div style="font-size:0.8rem; color:#666;">Waiting for chart data...</div>
                </div>
            """, unsafe_allow_html=True)
