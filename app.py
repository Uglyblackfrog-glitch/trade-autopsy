import streamlit as st

# 1. PAGE CONFIG (Must be first)
st.set_page_config(page_title="StockPostmortem.ai", page_icon="🩸", layout="wide")

# 2. SESSION STATE
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False

# 3. IMPORT PAGES
import auth
import dashboard

# 4. ROUTER LOGIC
if st.session_state.auth_status:
    # User is logged in -> Show the Dashboard
    dashboard.show_dashboard()
else:
    # User is NOT logged in -> Show Login
    auth.show_login_page()
