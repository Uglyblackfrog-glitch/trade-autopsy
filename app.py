import streamlit as st

# 1. PAGE CONFIG (Must be the very first command)
st.set_page_config(page_title="StockPostmortem.ai", page_icon="🩸", layout="wide")

# 2. SESSION STATE INITIALIZATION
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False

# 3. IMPORT PAGES
import auth
import dashboard

# 4. ROUTER LOGIC
if st.session_state.auth_status:
    # If Logged In -> Show the Dashboard
    dashboard.show_dashboard()
else:
    # If Logged Out -> Show Login
    auth.show_login_page()
