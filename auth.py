import streamlit as st
import time

def show_login_page():
    # Helper to clean session
    if "auth_status" not in st.session_state:
        st.session_state.auth_status = None

    # --- CUSTOM CSS FOR LOGIN ---
    st.markdown("""
    <style>
        .stTextInput > div > div > input {
            background-color: #1f2e38; color: white; border: 1px solid #475569;
        }
        .stButton > button {
            width: 100%; border-radius: 8px; font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- UI LAYOUT ---
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<h1 style='text-align: center; color: white; margin-bottom: 30px;'>STOCK<span style='color:#ff4d4d'>POSTMORTEM</span>.AI</h1>", unsafe_allow_html=True)
        
        # Tabs for Login vs Signup
        tab1, tab2 = st.tabs(["LOGIN", "SIGN UP"])

        # --- LOGIN TAB ---
        with tab1:
            email = st.text_input("Email Address", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("LOG IN", type="primary"):
                # ---------------------------------------------------------
                # TODO: CONNECT BACKEND HERE (Firebase / Supabase / SQL)
                # ---------------------------------------------------------
                if email == "admin@gmail.com" and password == "1234":
                    st.success("Welcome back!")
                    time.sleep(1)
                    st.session_state.auth_status = True
                    st.rerun() # Refresh to show dashboard
                else:
                    st.error("Invalid credentials")

        # --- SIGNUP TAB ---
        with tab2:
            new_email = st.text_input("Enter Email", key="signup_email")
            new_pass = st.text_input("Create Password", type="password", key="signup_pass")
            confirm_pass = st.text_input("Confirm Password", type="password", key="signup_conf")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("CREATE ACCOUNT"):
                if new_pass != confirm_pass:
                    st.error("Passwords do not match!")
                elif not new_email:
                    st.error("Email is required")
                else:
                    # ---------------------------------------------------------
                    # TODO: ADD GMAIL VERIFICATION CODE HERE
                    # ---------------------------------------------------------
                    with st.spinner("Sending verification email..."):
                        time.sleep(2) # Fake delay
                        st.success(f"Verification link sent to {new_email}! (Check Spam)")
