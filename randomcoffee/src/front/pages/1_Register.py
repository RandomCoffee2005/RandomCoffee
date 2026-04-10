import re

import streamlit as st

from ..api import APIError, get_client
from ..state import initialize_state, inject_global_styles, render_sidebar

st.set_page_config(page_title="Register • Random Coffee", page_icon="📝", layout="centered")

initialize_state()
inject_global_styles()
render_sidebar()

st.title("Register")

backend_enabled = st.session_state.backend["enabled"]
if backend_enabled:
    st.markdown(
        '<div class="backend-note"><b>Backend-connected flow.</b> ' +
        'The current backend has no separate registration endpoint. '
        'Registration is effectively completed by requesting OTP and then signing in; ' +
        'a new user is auto-created on successful login.</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="mock-note"><b>Mock flow.</b> OTP delivery and registration persistence are ' +
        'simulated only for the prototype.</div>',
        unsafe_allow_html=True,
    )

email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

with st.form("register_request_form"):
    email = st.text_input("Email", placeholder="name@example.com")
    request_otp = st.form_submit_button("Request OTP", use_container_width=True)

if request_otp:
    if not email or not re.match(email_pattern, email):
        st.error("Please enter a valid email address.")
    else:
        st.session_state.auth["current_email_input"] = email.strip()
        if backend_enabled:
            try:
                get_client().login_start(email.strip())
                st.session_state.auth["otp_sent"] = True
                st.success("OTP requested successfully. Check the configured mailbox.")
            except APIError as exc:
                st.error(str(exc))
        else:
            st.session_state.auth["otp_sent"] = True
            st.success("Mock OTP sent successfully. Use 123456 for the demo path.")

if st.session_state.auth.get("otp_sent"):
    with st.form("register_confirm_form"):
        st.text_input("Email", value=st.session_state.auth.get("current_email_input", ""),
                      disabled=True)
        otp = st.text_input("OTP code", placeholder="123456", max_chars=6)
        confirm = st.form_submit_button("Verify and continue", use_container_width=True)

    if confirm:
        email_value = st.session_state.auth.get("current_email_input", "")
        if backend_enabled:
            try:
                jwt = get_client().login(email_value, otp)
                st.session_state.auth["authenticated"] = True
                st.session_state.auth["otp_verified"] = True
                st.session_state.auth["jwt"] = jwt
                st.session_state.profile["email"] = email_value
                st.success("Registration/login completed. Continue to Profile.")
                st.page_link("pages/4_Profile.py", label="Open profile", icon="➡️")
            except APIError as exc:
                st.error(str(exc))
        else:
            if otp != "123456":
                st.error("Incorrect OTP. Registration failed in this mocked scenario.")
            else:
                st.session_state.auth["authenticated"] = True
                st.session_state.auth["otp_verified"] = True
                st.session_state.auth["jwt"] = "mock-jwt"
                st.session_state.profile["email"] = email_value
                st.success("Registration confirmed in mock mode.")
                st.page_link("pages/4_Profile.py", label="Open profile", icon="➡️")

st.markdown("### Notes")
if backend_enabled:
    st.info(
        "Backend behavior observed in the uploaded code: login_start issues OTP, and successful " +
        "/login auto-creates a new user if the email does not already exist."
    )
else:
    st.info('Prototype demo OTP is hardcoded to "123456".')
