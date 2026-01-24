import streamlit as st

# 1. PAGE CONFIG (Must be first)
st.set_page_config(page_title="StockPostmortem.ai", page_icon="🩸", layout="wide")

# 2. Session Setup
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False

# 3. Import Pages
import auth
import dashboard

# 4. Routing
if st.session_state.auth_status:
    dashboard.show_dashboard()
else:
    auth.show_login_page()
