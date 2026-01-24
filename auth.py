import streamlit as st
import time
from supabase import create_client

# 1. Initialize Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

def show_login_page():
    # Helper CSS for the login form
    st.markdown("""
    <style>
        .stTextInput input { background-color: #1f2e38; color: white; border: 1px solid #475569; }
        div[data-baseweb="tab-list"] { gap: 20px; }
        .stButton button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<h1 style='text-align: center; color: white; margin-bottom: 20px;'>STOCK<span style='color:#ff4d4d'>POSTMORTEM</span>.AI</h1>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["LOG IN", "SIGN UP"])

        # --- LOGIN TAB ---
        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("LOG IN", type="primary"):
                try:
                    # Supabase Login
                    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.auth_status = True
                    st.session_state.user_email = response.user.email
                    st.success("Login Successful!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Login Failed: {e}")

        # --- SIGNUP TAB ---
        with tab2:
            new_email = st.text_input("Enter Email", key="signup_email")
            new_pass = st.text_input("Create Password", type="password", key="signup_pass")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("CREATE ACCOUNT"):
                if not new_email or not new_pass:
                    st.error("Please fill in all fields.")
                else:
                    try:
                        # CHANGE THIS TO YOUR LIVE URL
                        site_url = "https://msoh38dzzavctjnmexncps.streamlit.app"
                        
                        response = supabase.auth.sign_up({
                            "email": new_email, 
                            "password": new_pass,
                            "options": {
                                "email_redirect_to": site_url 
                            }
                        })
                        
                        if response.user and response.user.identities and len(response.user.identities) > 0:
                            st.success("✅ Account created! CHECK YOUR GMAIL for the verification link.")
                            st.info(f"Link will redirect to: {site_url}")
                        else:
                            st.warning("User already exists or check your spam folder.")
                            
                    except Exception as e:
                        st.error(f"Error: {e}")
