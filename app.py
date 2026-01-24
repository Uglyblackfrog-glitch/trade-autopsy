import streamlit as st
import requests
import base64
import io
import re
import pandas as pd
from PIL import Image
from supabase import create_client, Client

# ... [Keep your AUTH/CSS/CONFIG sections exactly the same] ...

# ==========================================
# 3. HELPER FUNCTIONS (RE-ENGINEERED)
# ==========================================

def clean_text(text):
    """
    STRICT FILTER: Removes emojis, markdown bolding (optional), 
    and conversational filler to ensure professional output.
    """
    # Remove emojis (Unicode range for symbols/pictographs)
    text = re.sub(r'[^\w\s,.:;!?()\[\]\-\'\"]', '', text) 
    return text.strip()

def parse_report(text):
    """
    Robust Parsing with Fallback.
    """
    sections = {
        "score": 0, "tags": [], 
        "tech": "N/A", "psych": "N/A", "risk": "N/A", "fix": "N/A"
    }
    
    # Clean the input first
    text = clean_text(text)

    # 1. Extract Score
    score_match = re.search(r'\[SCORE\]\s*(\d+)', text)
    if score_match: 
        sections['score'] = int(score_match.group(1))
    
    # 2. Extract Tags
    tags_match = re.search(r'\[TAGS\](.*?)(?=\[|$)', text, re.DOTALL)
    if tags_match:
        raw = tags_match.group(1).replace('[', '').replace(']', '').split(',')
        sections['tags'] = [t.strip() for t in raw if t.strip()]

    # 3. Extract Analysis Blocks
    patterns = {
        "tech": r"\[TECH\](.*?)(?=\[PSYCH\]|\[RISK\]|\[FIX\]|\[SCORE\]|\[TAGS\]|$)",
        "psych": r"\[PSYCH\](.*?)(?=\[RISK\]|\[FIX\]|\[SCORE\]|\[TAGS\]|$)",
        "risk": r"\[RISK\](.*?)(?=\[FIX\]|\[SCORE\]|\[TAGS\]|$)",
        "fix": r"\[FIX\](.*?)(?=\[SCORE\]|\[TAGS\]|$)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL)
        if match:
            sections[key] = match.group(1).strip()
            
    return sections

# ==========================================
# 4. MAIN APP LOGIC (TAB 1 ONLY)
# ==========================================
# ... [Keep Login Logic] ...

# Inside the 'else' block (Logged In Dashboard):
# ... [Keep Sidebar and Header] ...

    # Tabs
    main_tab1, main_tab2, main_tab3 = st.tabs(["🔍 NEW AUTOPSY", "⚖️ CONSTITUTION", "📈 PERFORMANCE"])

    # --- TAB 1: ANALYSIS (REPLACED) ---
    with main_tab1:
        my_rules = get_user_rules(current_user)
        
        # UI Layout
        c_mode = st.radio("Input Mode", ["Text Report", "Chart Vision"], horizontal=True, label_visibility="collapsed")
        
        prompt = ""
        img_b64 = None
        ready_to_run = False
        payload_data = {}

        # --- MODE A: VISION ANALYSIS ---
        if c_mode == "Chart Vision":
            uploaded_file = st.file_uploader("Upload Chart", type=["png", "jpg"])
            if uploaded_file:
                st.image(uploaded_file, width=400)
                if st.button("RUN VISION AUDIT", type="primary"):
                    image = Image.open(uploaded_file)
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    
                    # SYSTEM PROMPT FOR VISION
                    prompt = f"""
                    SYSTEM: You are an Algorithmic Trading Auditor. 
                    TASK: Analyze the image pixel-by-pixel.
                    
                    STRICT CONSTRAINTS:
                    1. Output is BINARY and FACTUAL. Do not infer "emotions".
                    2. IGNORE indicators not clearly visible.
                    3. NO conversational filler. NO emojis.
                    
                    OUTPUT FORMAT:
                    [SCORE] 0-100
                    [TAGS] Tag1, Tag2
                    [TECH] Specific candle/structure failure identified.
                    [PSYCH] Implied intent based on entry location (e.g., FOMO if far from EMA).
                    [RISK] Visual stop loss placement analysis.
                    [FIX] One imperative correction rule.
                    """
                    ready_to_run = True

        # --- MODE B: TEXT ANALYSIS (THE CRITICAL PART) ---
        else:
            with st.form("text_form"):
                c1, c2, c3 = st.columns(3)
                with c1: ticker = st.text_input("Ticker", "SPY")
                with c2: emotion = st.selectbox("State", ["Neutral", "FOMO", "Revenge", "Fear", "Tilt"])
                with c3: setup_type = st.selectbox("Setup", ["Trend Follow", "Reversal", "Breakout", "Impulse"])

                c4, c5, c6 = st.columns(3)
                with c4: entry = st.number_input("Entry", value=0.0)
                with c5: exit_price = st.number_input("Exit", value=0.0)
                with c6: stop = st.number_input("Stop Loss", value=0.0)

                notes = st.text_area("Context Notes", placeholder="e.g. Broke VWAP, volume was low...")

                if st.form_submit_button("AUDIT TRADE", type="primary", use_container_width=True):
                    
                    # 1. PYTHON CALCULATION LAYER (Deterministic)
                    # We calculate math here so the AI cannot hallucinate numbers.
                    try:
                        risk = abs(entry - stop)
                        loss = abs(entry - exit_price)
                        r_multiple = -1 * (loss / risk) if risk > 0 else 0
                        
                        # Logic: Did they respect the stop?
                        stop_violation = False
                        if (entry > stop and exit_price < stop) or (entry < stop and exit_price > stop):
                            stop_violation = True
                        
                        math_block = f"""
                        [CALCULATED_METRICS]
                        Risk_Per_Share: {risk:.2f}
                        Actual_Loss: {loss:.2f}
                        R_Multiple: {r_multiple:.2f}R
                        Stop_Violation: {stop_violation} (TRUE = Critical Failure)
                        """
                    except:
                        math_block = "[CALCULATED_METRICS] Insufficient numeric data."

                    # 2. THE SYSTEM PROMPT (Professional & Merciless)
                    prompt = f"""
                    SYSTEM INSTRUCTION:
                    You are a Deterministic Trade Audit Engine. You are NOT a chatbot. 
                    You analyze input parameters and output a JSON-like structured report.
                    
                    RULES:
                    1. TONE: Clinical, Harsh, Professional. NO EMOJIS. NO "I think".
                    2. DATA PRIORITY: Use the [CALCULATED_METRICS] above. Do not recalculate.
                    3. SCORING: 
                       - If Stop_Violation == True, Max Score is 30.
                       - If Emotion == 'Revenge' or 'Tilt', Max Score is 40.
                    4. USER RULES: Check against: {my_rules}. If violated, mention it.

                    INPUT DATA:
                    Ticker: {ticker} | Setup: {setup_type} | Emotion: {emotion}
                    Notes: {notes}
                    {math_block}

                    REQUIRED OUTPUT FORMAT:
                    [SCORE] (Integer 0-100)
                    [TAGS] (Comma separated lists of errors, e.g., Stop Violation, Tilt, Poor R:R)
                    [TECH] (Technical reason for failure based on setup type)
                    [PSYCH] (Diagnosis of the reported emotion vs action)
                    [RISK] (Comment solely on R-Multiple and Stop Adherence)
                    [FIX] (One short imperative command. Max 10 words.)
                    """
                    ready_to_run = True

        # --- EXECUTION ENGINE ---
        if ready_to_run:
            with st.spinner("Processing Logic..."):
                try:
                    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
                    
                    if img_b64:
                        messages[0]["content"].append({
                            "type": "image_url", 
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                        })

                    # 3. API CONFIGURATION (The "Randomness Killer")
                    payload = {
                        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                        "messages": messages,
                        "max_tokens": 600,
                        "temperature": 0.1,  # <--- CRITICAL: Removes creativity/randomness
                        "top_p": 0.85,       # <--- CRITICAL: Focuses on high-probability logic
                        "frequency_penalty": 0.5 # <--- Reduces repetitive phrasing
                    }
                    
                    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                    res = requests.post(API_URL, headers=headers, json=payload)

                    if res.status_code == 200:
                        raw_content = res.json()["choices"][0]["message"]["content"]
                        
                        # 4. POST-PROCESSING (The "Emoji Killer")
                        # Even if AI adds emojis, we strip them before showing user.
                        report = parse_report(raw_content) 
                        save_analysis(current_user, report)
                        
                        # DISPLAY
                        score_color = "#ef4444" if report['score'] < 50 else "#10b981"
                        st.markdown(f"""
                        <div class="report-container">
                            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; padding-bottom:15px; margin-bottom:20px;">
                                <div style="font-size:1.2rem; font-weight:bold; color:#888;">AUDIT RESULT</div>
                                <div style="font-size:3.5rem; font-weight:900; color:{score_color};">{report['score']}</div>
                            </div>
                            <div class="analysis-card" style="border-left-color: #3b82f6;"><b>TECH:</b> {report['tech']}</div>
                            <div class="analysis-card" style="border-left-color: #f59e0b;"><b>PSYCH:</b> {report['psych']}</div>
                            <div class="analysis-card" style="border-left-color: #ef4444;"><b>RISK:</b> {report['risk']}</div>
                            <div class="analysis-card" style="border-left-color: #10b981; background:rgba(16, 185, 129, 0.1);"><b>FIX:</b> {report['fix']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"API Error: {res.status_code}")
                
                except Exception as e:
                    st.error(f"System Failure: {e}")
