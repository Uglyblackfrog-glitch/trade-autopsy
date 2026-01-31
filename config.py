import streamlit as st
import requests
import base64
import io
import re
import pandas as pd
import altair as alt
from PIL import Image
from supabase import create_client, Client
from datetime import datetime
import json
import uuid

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="StockPostmortem.ai",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# USER CREDENTIALS
# ==========================================
USERS = {
    "trader1": "profit2026",
    "demo_user": "12345",
    "admin": "adminpass"
}

# ==========================================
# SESSION STATE INIT
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.session_state["current_page"] = "analyze"

# Check for URL parameters
try:
    params = st.query_params
    if "page" in params:
        st.session_state["current_page"] = params["page"]
except:
    pass

# ==========================================
# LOGIN / LOGOUT
# ==========================================
def check_login(username, password):
    if username in USERS and USERS[username] == password:
        st.session_state["authenticated"] = True
        st.session_state["user"] = username
        st.rerun()
    else:
        st.error("Access Denied: Invalid Credentials")

def logout():
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.rerun()

# ==========================================
# DATABASE & API SETUP (runs only when authenticated)
# ==========================================
# These are set as module-level so other files can import them
supabase = None
HF_TOKEN = ""
API_URL = ""

def init_db_and_api():
    """Call this once after auth succeeds. Sets global supabase / HF_TOKEN / API_URL."""
    global supabase, HF_TOKEN, API_URL
    try:
        HF_TOKEN = st.secrets.get("HF_TOKEN", "")
        SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
        SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

        if not all([HF_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
            st.warning("⚠️ Secrets missing. Running in UI-only mode.")
            supabase = None
        else:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            API_URL = "https://router.huggingface.co/v1/chat/completions"
    except Exception as e:
        st.error(f"⚠️ Configuration Error: {e}")
        st.stop()
