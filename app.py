 import streamlit as st 
 import requests 
 import base64 
 import io 
 from PIL import Image 

 # 1. PAGE CONFIG 
 st.set_page_config(page_title="StockPostmortem.ai", page_icon="🩸", layout="wide") 

 # 2. API SETUP 
 try: 
     HF_TOKEN = st.secrets["HF_TOKEN"] 
     API_URL = "https://router.huggingface.co/v1/chat/completions" 
 except Exception: 
     st.error("⚠️ HF_TOKEN is missing. Add it to Streamlit Secrets.") 
     st.stop() 

 # 3. CSS OVERRIDES (DESKTOP + MOBILE OPTIMIZED) 
 st.markdown(""" 
 <style> 
     /* --- RESET & GLOBAL --- */ 
     @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap'); 
      
     body, .stApp {  
         background-color: #0f171c !important;  
         font-family: 'Inter', sans-serif !important;  
         color: #e2e8f0 !important;  
     } 
      
     header, footer, #MainMenu { display: none !important; } 

     /* --- LAYOUT: DESKTOP DEFAULTS --- */ 
     .block-container {  
         padding-top: 2rem !important; 
         padding-bottom: 5rem !important;  
         padding-left: 5rem !important;   
         padding-right: 5rem !important;  
         max-width: 100% !important; 
     } 

     /* --- LAYOUT: ANDROID/MOBILE OVERRIDES --- */ 
     @media (max-width: 768px) { 
         .block-container {  
             padding-left: 1rem !important;  
             padding-right: 1rem !important;  
             padding-top: 1rem !important; 
         } 
         .hero-h1 { font-size: 3rem !important; margin-bottom: 1rem !important; } 
         .hero-p { font-size: 1rem !important; } 
         .nav { margin-bottom: 2rem !important; } 
         /* Make uploader smaller on mobile */ 
         [data-testid="stFileUploaderDropzone"] { min-height: 250px !important; } 

         [data-testid="stFileUploaderDropzone"]::before { top: 40px 
!important; width: 50px !important; height: 50px !important; } 
         [data-testid="stFileUploaderDropzone"]::after { top: 110px !important; font-size: 1rem !important; } 
         [data-testid="stFileUploaderDropzone"] button { bottom: 40px !important; } 
     } 

     /* --- NAVBAR --- */ 
     .nav {  
         display: flex;  
         justify-content: space-between;  
         align-items: center;  
         padding: 1rem 0;  
         border-bottom: 1px solid #2d4250;  
         margin-bottom: 5rem;  
         width: 100%;  
     } 
     .logo { font-size: 1.5rem; font-weight: 800; letter-spacing: -0.05em; color: white; } 
     .logo span { color: #ff4d4d; } 
     .cta-btn {  
         background: #dc2626; color: white; padding: 0.6rem 1.5rem;  
         border-radius: 99px; border: none; font-weight: 600; font-size: 0.9rem; 
     } 

     /* --- HERO --- */ 
     .hero-h1 {  
         font-size: 5rem;  
         font-weight: 800;  
         font-style: italic;  
         text-align: center;  
         color: white;  
         line-height: 1.1;  
         margin-bottom: 1.5rem;  
     } 
     .hero-p {  
         text-align: center;  
         color: #94a3b8;  
         font-size: 1.25rem;  
         max-width: 800px;  
         margin: 0 auto 4rem auto;  
     } 

     /* --- UPLOADER FIX (Absolute Pinning) --- */ 
     [data-testid="stFileUploaderDropzone"] { 
         background-color: rgba(31, 46, 56, 0.6) !important; 
         border: 2px dashed #475569 !important; 
         border-radius: 1rem !important; 
         min-height: 400px !important; 
         position: relative !important; 
         transition: all 0.3s ease; 
     } 
     [data-testid="stFileUploaderDropzone"]:hover { 
         border-color: #ff4d4d !important; 
         background-color: rgba(31, 46, 56, 0.8) !important; 
     } 

     /* ICON (Top) */ 
     [data-testid="stFileUploaderDropzone"]::before { 
         content: ""; 
         position: absolute; 
         top: 70px;  
         left: 50%; 
         transform: translateX(-50%); 
         width: 70px; 
         height: 70px; 

         background-image: url("data:image/svg+xml,%3Csvg 
xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' 
stroke='%23ef4444'%3E%3Cpath stroke-linecap='round' 
stroke-linejoin='round' stroke-width='1.5' d='M7 16a4 4 0 01-.88-7.903A5
 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12' 
/%3E%3C/svg%3E"); 
         background-repeat: no-repeat; 
         background-size: contain; 
         pointer-events: none; 
     } 

     /* TEXT (Middle) */ 
     [data-testid="stFileUploaderDropzone"]::after { 
         content: "Drop your P&L or Chart screenshot here\\A Supports PNG, JPG (Max 10MB). Your data is encrypted."; 
         white-space: pre-wrap; 
         position: absolute; 
         top: 160px; 
         left: 0; 
         width: 100%; 
         text-align: center; 
         color: #e2e8f0; 
         font-size: 1.5rem; 
         font-weight: 600; 
         line-height: 1.6; 
         pointer-events: none; 
     } 

     /* Hide Default */ 
     [data-testid="stFileUploaderDropzoneInstructions"] { visibility: hidden !important; height: 0 !important; } 
     [data-testid="stFileUploaderDropzone"] div > svg { display: none !important; } 

     /* BUTTON (Bottom) */ 
     [data-testid="stFileUploaderDropzone"] button { 
         visibility: visible !important; 
         position: absolute !important; 
         bottom: 70px !important; 
         left: 50% !important; 
         transform: translateX(-50%) !important; 
         background-color: white !important; 
         color: black !important; 
         border: none !important; 
         padding: 14px 40px !important; 
         border-radius: 8px !important; 
         font-weight: 700 !important; 
         font-size: 1.1rem !important; 
         width: auto !important; 
         z-index: 10 !important; 
     } 
     /* Button Text Swap */ 
     [data-testid="stFileUploaderDropzone"] button { color: transparent !important; } 
     [data-testid="stFileUploaderDropzone"] button::after { 
         content: "Select File"; 
         color: black; 
         position: absolute; 
         left: 50%; 
         top: 50%; 
         transform: translate(-50%, -50%); 
         white-space: nowrap; 
     } 
     [data-testid="stFileUploaderDropzone"] button:hover { 
         background-color: #cbd5e1 !important; 
     } 

     /* --- FEATURE GRID --- */ 
     .grid {  
         display: grid;  
         grid-template-columns: repeat(3, 1fr);  
         gap: 2.5rem;  
         margin-top: 5rem;  
     } 
     .card {  
         background: #1f2e38;  
         padding: 2.5rem;  
         border-radius: 1rem;  
         border: 1px solid #2d4250; 
     } 
     .card h3 { color: white; font-weight: 700; margin-bottom: 0.75rem; font-size: 1.25rem; } 
     .card p { color: #94a3b8; font-size: 1rem; line-height: 1.6; } 

     /* MOBILE GRID FIX */ 
     @media (max-width: 1024px) { 
         .grid { grid-template-columns: 1fr; } 
     } 
 </style> 
 """, unsafe_allow_html=True) 

 # 4. RENDER UI 

 # Navbar 
 st.markdown(""" 
 <div class="nav"> 
     <div class="logo">STOCK<span>POSTMORTEM</span>.AI</div> 
     <button class="cta-btn">Get Started</button> 
 </div> 
 <div class="hero-h1">STOP BLEEDING CAPITAL.</div> 

 <div class="hero-p">Upload your losing trade screenshots. Our AI 
identifies psychological traps, technical failures, and provides a 
surgical path to recovery.</div> 
 """, unsafe_allow_html=True) 

 # Uploader Section 
 # On Desktop: 1:4:1 ratio (Wide). On Mobile, Streamlit stacks these automatically. 
 c1, c2, c3 = st.columns([1, 4, 1])  
 with c2: 
     uploaded_file = st.file_uploader(" ", type=["png", "jpg", "jpeg"], label_visibility="collapsed") 

 # Logic 
 if uploaded_file: 
     st.markdown("<br>", unsafe_allow_html=True) 
     b1, b2, b3 = st.columns([1, 1, 1]) 
     with b2: 
         if st.button("RUN FORENSIC ANALYSIS", type="primary", use_container_width=True): 
             with st.spinner("🔍 ANALYZING CHART DATA..."): 
                 try: 
                     image = Image.open(uploaded_file) 
                     buf = io.BytesIO() 
                     image.save(buf, format="PNG") 
                     img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8') 


                     prompt = "ACT AS: Trading Psychologist. INPUT: 
Image. OUTPUT: 1. Technical Mistake. 2. Emotional Trap. 3. Risk 
Management Fail. Be brutal." 
                      
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

                         st.markdown(f"""<div style="background: 
#161b22; border-left: 5px solid #ff4d4d; padding: 30px; border-radius: 
8px; margin-top: 20px;">{content}</div>""", 
unsafe_allow_html=True) 
                 except Exception as e: 
                     st.error(f"Error: {e}") 

 # Footer Grid 
 st.markdown(""" 
 <div class="grid"> 
     <div class="card"> 
         <h3>Pattern Recognition</h3> 
         <p>Did you buy the top? We identify if you're falling for FOMO or revenge trading instantly.</p> 
     </div> 
     <div class="card"> 
         <h3>Risk Autopsy</h3> 
         <p>Calculates if your stop-loss was too tight or if your position sizing was reckless.</p> 
     </div> 
     <div class="card"> 
         <h3>Recovery Plan</h3> 
         <p>Step-by-step technical adjustments to ensure the next trade is a winner, not a gamble.</p> 
     </div> 
 </div> 
 <div style="text-align: center; margin-top: 6rem; color: #64748b; font-size: 0.9rem;"> 
     &copy; 2026 stockpostmortem.ai | Trading involves risk. 
 </div> 
 """, unsafe_allow_html=True)
