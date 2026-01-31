import streamlit as st

CSS_THEME = """
<style>
    /* --- PREMIUM FONTS --- */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* --- DARK PREMIUM BACKGROUND --- */
    body, .stApp { 
        background: #0a0a0f !important;
        background-image: 
            radial-gradient(ellipse at 10% 0%, rgba(16, 185, 129, 0.08) 0%, transparent 40%),
            radial-gradient(ellipse at 90% 100%, rgba(59, 130, 246, 0.08) 0%, transparent 40%),
            radial-gradient(ellipse at 50% 50%, rgba(139, 92, 246, 0.04) 0%, transparent 50%);
        font-family: 'Space Grotesk', -apple-system, sans-serif !important; 
        color: #e5e7eb; 
        line-height: 1.7;
    }
    
    /* --- CONTAINER SPACING --- */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1400px !important;
    }

    /* --- HIDE STREAMLIT ELEMENTS --- */
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    
    /* --- PREMIUM NAVIGATION BAR --- */
    .premium-navbar {
        background: rgba(15, 15, 20, 0.8);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 16px 28px;
        margin-bottom: 32px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.03);
    }
    
    .nav-brand { display: flex; align-items: center; gap: 12px; }
    
    .nav-logo {
        font-size: 1.8rem;
        filter: drop-shadow(0 0 16px rgba(16, 185, 129, 0.4));
    }
    
    .nav-title {
        font-size: 1.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
    }
    
    .nav-subtitle {
        font-size: 0.7rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 600;
    }
    
    .nav-menu { display: flex; gap: 32px; align-items: center; }
    
    .nav-link {
        color: #9ca3af;
        text-decoration: none;
        font-size: 0.95rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        position: relative;
        padding: 8px 0;
        cursor: pointer;
    }
    
    .nav-link::after {
        content: '';
        position: absolute;
        bottom: 0; left: 0;
        width: 0; height: 2px;
        background: linear-gradient(90deg, #10b981, #3b82f6);
        transition: width 0.3s ease;
    }
    
    .nav-link:hover { color: #10b981; }
    .nav-link:hover::after { width: 100%; }
    .nav-link.active { color: #10b981; }
    .nav-link.active::after { width: 100%; }
    
    /* --- RADIO BUTTONS - GREEN THEME --- */
    .stRadio > div[role="radiogroup"] > label > div[data-testid="stMarkdownContainer"] { color: #9ca3af !important; }
    .stRadio > div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child { background-color: transparent !important; border-color: rgba(255, 255, 255, 0.2) !important; }
    .stRadio > div[role="radiogroup"] > label[data-baseweb="radio"][data-selected="true"] > div:first-child { background-color: #10b981 !important; border-color: #10b981 !important; }
    .stRadio > div[role="radiogroup"] > label[data-baseweb="radio"][data-selected="true"] > div:first-child::after { background-color: white !important; }
    input[type="radio"]:checked { accent-color: #10b981 !important; }
    
    /* --- PREMIUM GLASS PANELS --- */
    .glass-panel {
        background: rgba(15, 15, 20, 0.75);
        backdrop-filter: blur(24px) saturate(200%);
        -webkit-backdrop-filter: blur(24px) saturate(200%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 36px;
        margin-bottom: 24px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        position: relative;
        overflow: hidden;
    }
    
    .glass-panel::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.5), transparent);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    
    .glass-panel:hover {
        border-color: rgba(255, 255, 255, 0.12);
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        transform: translateY(-2px);
    }
    .glass-panel:hover::before { opacity: 1; }
    
    /* --- PREMIUM KPI CARDS --- */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 20px;
        margin-bottom: 32px;
    }
    
    .kpi-card {
        background: linear-gradient(135deg, rgba(20, 20, 28, 0.9) 0%, rgba(10, 10, 15, 0.95) 100%);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 32px 28px;
        border-radius: 20px;
        text-align: center;
        transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
        position: relative;
        overflow: hidden;
    }
    
    .kpi-card::after {
        content: '';
        position: absolute; inset: 0;
        background: radial-gradient(circle at 50% 0%, rgba(16, 185, 129, 0.15), transparent 70%);
        opacity: 0;
        transition: opacity 0.5s ease;
    }
    
    .kpi-card:hover {
        border-color: rgba(16, 185, 129, 0.4);
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 60px -12px rgba(16, 185, 129, 0.3), 0 0 0 1px rgba(16, 185, 129, 0.2);
    }
    .kpi-card:hover::after { opacity: 1; }
    
    .kpi-val { 
        font-family: 'JetBrains Mono', monospace;
        font-size: 3rem; font-weight: 700; 
        background: linear-gradient(135deg, #ffffff 0%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 10px;
        letter-spacing: -0.03em;
        position: relative; z-index: 1;
    }
    
    .kpi-label { 
        color: #9ca3af; font-size: 0.7rem; 
        text-transform: uppercase; letter-spacing: 2.5px; font-weight: 600;
        position: relative; z-index: 1;
    }

    /* --- PREMIUM LOGIN --- */
    .login-container {
        max-width: 480px;
        margin: 10vh auto;
        padding: 56px;
        background: rgba(15, 15, 20, 0.9);
        backdrop-filter: blur(24px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 32px;
        box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .login-container::before {
        content: '';
        position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
        background: radial-gradient(circle, rgba(16, 185, 129, 0.1) 0%, transparent 70%);
        animation: rotate 20s linear infinite;
    }
    
    @keyframes rotate { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    
    .login-logo {
        font-size: 4rem;
        margin-bottom: 20px;
        filter: drop-shadow(0 0 24px rgba(16, 185, 129, 0.4));
        position: relative; z-index: 1;
    }

    /* --- SECTION TITLES --- */
    .section-title {
        font-size: 0.95rem; font-weight: 700; color: #f8fafc;
        margin-bottom: 28px;
        display: flex; align-items: center; gap: 14px;
        text-transform: uppercase; letter-spacing: 2px;
    }
    
    .section-title::before {
        content: '';
        display: block; width: 4px; height: 24px;
        background: linear-gradient(180deg, #10b981 0%, #3b82f6 100%);
        border-radius: 3px;
        box-shadow: 0 0 16px rgba(16, 185, 129, 0.5);
    }

    /* --- REPORT GRID --- */
    .report-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px; margin-top: 32px;
    }
    
    .report-item {
        background: rgba(255, 255, 255, 0.03);
        border-left: 4px solid rgba(100, 100, 100, 0.4);
        padding: 24px;
        border-radius: 0 16px 16px 0;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        font-size: 0.92rem; line-height: 1.8;
    }
    
    .report-item:hover { background: rgba(255, 255, 255, 0.06); border-left-color: currentColor; transform: translateX(4px); }
    
    .report-label { font-weight: 700; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 14px; display: block; }

    /* --- PREMIUM TABS --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: rgba(20, 20, 28, 0.5);
        border-radius: 16px; padding: 8px; margin-bottom: 32px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent; border-radius: 12px; color: #9ca3af;
        font-weight: 600; padding: 14px 28px;
        transition: all 0.3s ease; font-size: 0.9rem; letter-spacing: 0.5px;
    }
    
    .stTabs [data-baseweb="tab"]:hover { background: rgba(255, 255, 255, 0.06); color: #f8fafc; }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(59, 130, 246, 0.2) 100%) !important;
        color: #10b981 !important;
        box-shadow: 0 0 24px rgba(16, 185, 129, 0.3);
    }
    
    .stTabs [data-baseweb="tab-highlight"] { background-color: #10b981 !important; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 0 !important; }
    
    /* --- RADIO BUTTONS (extended) --- */
    .stRadio { background: transparent !important; }
    .stRadio > div { background: transparent !important; padding: 0 !important; }
    .stRadio > label { display: none !important; }
    .stRadio div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] { color: #9ca3af !important; transition: color 0.3s ease !important; }
    .stRadio div[role="radiogroup"] label[data-baseweb="radio"] div:first-child { border: 2px solid rgba(255, 255, 255, 0.2) !important; background: transparent !important; }
    .stRadio div[role="radiogroup"] label[data-baseweb="radio"]:hover div:first-child { border-color: rgba(16, 185, 129, 0.5) !important; }
    .stRadio div[role="radiogroup"] label div:first-child[data-checked="true"],
    .stRadio div[role="radiogroup"] label[aria-checked="true"] div:first-child { background: #10b981 !important; border-color: #10b981 !important; }
    .stRadio div[role="radiogroup"] label div:first-child[data-checked="true"]::after,
    .stRadio div[role="radiogroup"] label[aria-checked="true"] div:first-child::after { background: white !important; }
    .stRadio div[role="radiogroup"] label[aria-checked="true"] div[data-testid="stMarkdownContainer"] { color: #10b981 !important; font-weight: 600 !important; }
    [data-baseweb="radio"] input[type="radio"]:checked { accent-color: #10b981 !important; }

    /* --- PREMIUM BUTTONS --- */
    .stButton button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 14px; color: white; font-weight: 600;
        padding: 14px 32px;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.2);
        letter-spacing: 0.5px; font-size: 0.9rem;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.25);
        transform: translateY(-3px);
    }
    
    .stButton button[kind="primary"], button[type="submit"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        border: 1px solid rgba(16, 185, 129, 0.4) !important;
        border-radius: 14px !important; color: white !important; font-weight: 600 !important;
        padding: 14px 32px !important;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1) !important;
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
        letter-spacing: 0.5px !important; font-size: 0.9rem !important;
    }
    
    .stButton button[kind="primary"]:hover, button[type="submit"]:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.25) !important;
        transform: translateY(-3px) !important;
    }
    
    .stButton button[kind="secondary"] {
        background: transparent !important; border: none !important; box-shadow: none !important;
        color: #9ca3af !important; padding: 8px 16px !important;
        font-size: 0.95rem !important; font-weight: 600 !important;
        letter-spacing: 0.5px !important; position: relative;
        transition: all 0.3s ease !important;
    }
    
    .stButton button[kind="secondary"]::after {
        content: ''; position: absolute; bottom: 4px; left: 16px; right: 16px; height: 2px;
        background: linear-gradient(90deg, #10b981, #3b82f6);
        transform: scaleX(0); transition: transform 0.3s ease;
    }
    
    .stButton button[kind="secondary"]:hover { color: #10b981 !important; background: rgba(16, 185, 129, 0.05) !important; transform: none !important; }
    .stButton button[kind="secondary"]:hover::after { transform: scaleX(1); }

    /* --- PREMIUM INPUTS --- */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox select {
        background: rgba(20, 20, 28, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important; color: #f8fafc !important;
        padding: 14px 18px !important; font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus {
        border-color: rgba(16, 185, 129, 0.5) !important;
        box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.15) !important;
        background: rgba(20, 20, 28, 0.9) !important;
    }

    /* --- PREMIUM FILE UPLOADER --- */
    [data-testid="stFileUploader"] { background: transparent !important; }
    [data-testid="stFileUploader"] > div { background: transparent !important; border: none !important; }
    
    [data-testid="stFileUploader"] section {
        background: rgba(15, 15, 20, 0.7) !important;
        backdrop-filter: blur(16px);
        border: 2px dashed rgba(16, 185, 129, 0.4) !important;
        border-radius: 24px !important; padding: 72px 48px !important;
        transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1) !important;
        position: relative;
    }
    
    [data-testid="stFileUploader"] section::before {
        content: ''; position: absolute; inset: 0; border-radius: 24px;
        background: radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.1), transparent 70%);
        opacity: 0; transition: opacity 0.5s ease;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(16, 185, 129, 0.7) !important;
        background: rgba(20, 20, 28, 0.8) !important;
        transform: translateY(-4px);
        box-shadow: 0 12px 48px rgba(16, 185, 129, 0.25);
    }
    [data-testid="stFileUploader"] section:hover::before { opacity: 1; }
    
    [data-testid="stFileUploader"] section button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        border: none !important; border-radius: 14px !important; color: white !important;
        font-weight: 600 !important; padding: 16px 36px !important; font-size: 0.95rem !important;
        transition: all 0.4s ease !important;
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3) !important; margin-top: 24px !important;
    }
    
    [data-testid="stFileUploader"] section button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.5) !important; transform: translateY(-2px);
    }
    
    .upload-icon {
        font-size: 4rem; margin-bottom: 28px; display: block; opacity: 0.9;
        animation: float 3s ease-in-out infinite;
        filter: drop-shadow(0 0 20px rgba(16, 185, 129, 0.3));
    }
    
    @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-12px); } }
    
    .upload-text { font-size: 1.5rem; font-weight: 700; color: #f8fafc; margin-bottom: 14px; letter-spacing: -0.01em; }
    .upload-subtext { font-size: 0.92rem; color: #9ca3af; line-height: 1.7; }

    /* --- DATAFRAME --- */
    .stDataFrame { background: rgba(15, 15, 20, 0.7); border-radius: 16px; overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.06); }

    /* --- SCORE DISPLAY --- */
    .score-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }
    .score-value { font-family: 'JetBrains Mono', monospace; font-size: 5.5rem; font-weight: 800; line-height: 1; letter-spacing: -0.04em; }
    .score-meta { text-align: right; }
    
    .ticker-badge {
        background: rgba(16, 185, 129, 0.15);
        padding: 10px 20px; border-radius: 10px; display: inline-block;
        font-weight: 600; font-size: 0.95rem; letter-spacing: 1px; margin-bottom: 10px;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    /* --- UTILITY --- */
    .divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent); margin: 32px 0; }
    .accent-text { color: #10b981; font-weight: 600; }
    
    /* === ANIMATIONS === */
    @keyframes slideInUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes scaleIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
    @keyframes slideInRight { from { opacity: 0; transform: translateX(-30px); } to { opacity: 1; transform: translateX(0); } }
    @keyframes shimmer { 0% { background-position: -1000px 0; } 100% { background-position: 1000px 0; } }
    
    .animate-slide-up { animation: slideInUp 0.6s cubic-bezier(0.23, 1, 0.32, 1) forwards; }
    .animate-fade-in { animation: fadeIn 0.8s ease forwards; }
    .animate-scale-in { animation: scaleIn 0.5s cubic-bezier(0.23, 1, 0.32, 1) forwards; }
    .animate-slide-right { animation: slideInRight 0.6s cubic-bezier(0.23, 1, 0.32, 1) forwards; }
    
    .result-card {
        background: rgba(15, 15, 20, 0.75); backdrop-filter: blur(24px);
        border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px;
        padding: 28px; margin-bottom: 20px;
        transition: all 0.4s ease; position: relative; overflow: hidden;
    }
    
    .result-card::before {
        content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.1), transparent);
        animation: shimmer 2s infinite;
    }
    
    .result-card:hover { border-color: rgba(16, 185, 129, 0.3); transform: translateY(-4px); box-shadow: 0 12px 40px rgba(16, 185, 129, 0.2); }
    
    .metric-circle {
        width: 120px; height: 120px; border-radius: 50%;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        position: relative; margin: 0 auto;
    }
    
    .metric-circle::before {
        content: ''; position: absolute; inset: -4px; border-radius: 50%; padding: 4px;
        background: linear-gradient(135deg, #10b981, #3b82f6);
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor; mask-composite: exclude;
        animation: spin 3s linear infinite;
    }
    
    @keyframes spin { to { transform: rotate(360deg); } }
    
    .grade-badge {
        display: inline-block; padding: 8px 20px; border-radius: 12px;
        font-size: 1.1rem; font-weight: 700; letter-spacing: 1px;
        animation: pulse 2s ease infinite;
    }
    
    @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
    
    .progress-bar-container { width: 100%; height: 12px; background: rgba(255, 255, 255, 0.05); border-radius: 6px; overflow: hidden; position: relative; }
    
    .progress-bar { height: 100%; border-radius: 6px; transition: width 1.5s cubic-bezier(0.23, 1, 0.32, 1); position: relative; overflow: hidden; }
    .progress-bar::after { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent); animation: shimmer 1.5s infinite; }
    
    /* --- CUSTOM SCROLLBAR --- */
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: rgba(20, 20, 28, 0.5); }
    ::-webkit-scrollbar-thumb { background: rgba(16, 185, 129, 0.3); border-radius: 5px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(16, 185, 129, 0.5); }
    
    /* === GLOBAL RED REMOVAL === */
    button[kind="primary"], button[type="submit"],
    .stButton > button[kind="primary"],
    [data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        border-color: rgba(16, 185, 129, 0.4) !important;
    }
    
    button[kind="primary"]:hover, button[type="submit"]:hover,
    .stButton > button[kind="primary"]:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    }
    
    .stAlert, .element-container .stException { border-left-color: #f59e0b !important; }
    
    input[type="radio"]:checked, input[type="checkbox"]:checked { accent-color: #10b981 !important; background-color: #10b981 !important; border-color: #10b981 !important; }
    .stSlider [role="slider"], .stProgress > div > div { background-color: #10b981 !important; }
    
    *[style*="background: red"], *[style*="background-color: red"],
    *[style*="background: #ef4444"], *[style*="background-color: #ef4444"],
    *[style*="background: #dc2626"], *[style*="background-color: #dc2626"],
    *[style*="background: rgb(239, 68, 68)"], *[style*="background-color: rgb(239, 68, 68)"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        background-color: #10b981 !important;
    }
</style>
"""


def inject_css():
    """Call once at the top of app.py to inject the full theme."""
    st.markdown(CSS_THEME, unsafe_allow_html=True)
