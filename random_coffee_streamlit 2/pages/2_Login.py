import streamlit as st
from state import initialize_state, render_sidebar
import re

st.set_page_config(page_title="Login • Random Coffee", page_icon="🔐", layout="centered")

initialize_state()
render_sidebar()

st.title("Login")
st.markdown(
    '<div class="mock-note"><b>Mock flow.</b> OTP delivery and authentication are simulated only for the prototype.</div>',
    unsafe_allow_html=True,
)

email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

with st.form("login_request_form"):
    email = st.text_input("Email", placeholder="name@example.com")
    request_otp = st.form_submit_button("Request OTP", use_container_width=True)

if request_otp:
    if not email or not re.match(email_pattern, email):
        st.error("Invalid email. You are not logged in.")
    else:
        st.session_state.auth["otp_sent"] = True
        st.session_state.auth["current_email_input"] = email
        st.success("Mock OTP requested successfully. Delivery is simulated in this prototype.")

if st.session_state.auth.get("otp_sent"):
    with st.form("login_confirm_form"):
        st.text_input(
            "Email",
            value=st.session_state.auth.get("current_email_input", ""),
            disabled=True,
        )
        otp = st.text_input("OTP code", placeholder="123456", max_chars=6)
        login_submit = st.form_submit_button("Log in", use_container_width=True)

    if login_submit:
        if otp != "123456":
            st.error("Incorrect OTP. Authentication failed in this mocked scenario.")
        else:
            st.session_state.auth["authenticated"] = True
            st.session_state.auth["otp_verified"] = True
            st.session_state.profile["email"] = st.session_state.auth.get("current_email_input", "alex@example.com")
            st.success("Logged in successfully. In a real app you would be redirected to the main dashboard.")
            st.page_link("pages/3_Dashboard.py", label="Open dashboard", icon="➡️")

st.markdown("### Demo hint")
st.info('For the login success path, use OTP: "123456". This is intentionally hardcoded as a visible mock value.')
