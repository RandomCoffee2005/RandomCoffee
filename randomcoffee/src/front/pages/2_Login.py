import re

import streamlit as st

from ..api import APIError, get_client
from ..state import initialize_state, inject_global_styles, render_sidebar

st.set_page_config(page_title="Login • Random Coffee", page_icon="🔐", layout="centered")

initialize_state()
inject_global_styles()
render_sidebar()

st.title("Login")

backend_enabled = st.session_state.backend["enabled"]
if backend_enabled:
    st.markdown(
        '<div class="backend-note"><b>Backend-connected flow.</b> This page calls ' +
        '<code>/login_start</code> and <code>/login</code>.</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="mock-note"><b>Mock flow.</b> OTP delivery and authentication ' +
        'are simulated only for the prototype.</div>',
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
        st.session_state.auth["current_email_input"] = email.strip()
        if backend_enabled:
            try:
                get_client().login_start(email.strip())
                st.session_state.auth["otp_sent"] = True
                st.success("OTP requested successfully.")
            except APIError as exc:
                st.error(str(exc))
        else:
            st.session_state.auth["otp_sent"] = True
            st.success("Mock OTP requested successfully. Delivery is simulated in this prototype.")

if st.session_state.auth.get("otp_sent"):
    with st.form("login_confirm_form"):
        st.text_input("Email", value=st.session_state.auth.get("current_email_input", ""),
                      disabled=True)
        otp = st.text_input("OTP code", placeholder="123456", max_chars=6)
        login_submit = st.form_submit_button("Log in", use_container_width=True)

    if login_submit:
        email_value = st.session_state.auth.get("current_email_input", "")
        if backend_enabled:
            try:
                jwt = get_client().login(email_value, otp)
                st.session_state.auth["authenticated"] = True
                st.session_state.auth["otp_verified"] = True
                st.session_state.auth["jwt"] = jwt
                st.session_state.profile["email"] = email_value
                st.success("Logged in successfully.")
                st.page_link("pages/3_Dashboard.py", label="Open dashboard", icon="➡️")
            except APIError as exc:
                st.error(str(exc))
        else:
            if otp != "123456":
                st.error("Incorrect OTP. Authentication failed in this mocked scenario.")
            else:
                st.session_state.auth["authenticated"] = True
                st.session_state.auth["otp_verified"] = True
                st.session_state.auth["jwt"] = "mock-jwt"
                st.session_state.profile["email"] = email_value
                st.success("Logged in successfully.")
                st.page_link("pages/3_Dashboard.py", label="Open dashboard", icon="➡️")

st.markdown("### Notes")
if backend_enabled:
    st.info("On backend errors, the exact API message is surfaced in the UI.")
else:
    st.info('For the mock success path, use OTP: "123456".')
