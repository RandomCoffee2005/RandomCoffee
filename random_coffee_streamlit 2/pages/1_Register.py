import streamlit as st
from state import initialize_state, render_sidebar
import re

st.set_page_config(page_title="Register • Random Coffee", page_icon="📝", layout="centered")

initialize_state()
render_sidebar()

st.title("Registration")
st.markdown(
    '<div class="mock-note"><b>Mock flow.</b> Sending OTP and account creation are simulated only for the prototype.</div>',
    unsafe_allow_html=True,
)

email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

with st.form("register_form"):
    email = st.text_input("University or work email", placeholder="name@example.com")
    send_otp = st.form_submit_button("Send OTP", use_container_width=True)

if send_otp:
    if not email or not re.match(email_pattern, email):
        st.error("Please enter a valid email address.")
    else:
        st.session_state.auth["otp_sent"] = True
        st.session_state.auth["current_email_input"] = email
        st.success("Mock OTP sent to email. Use any 6-digit code to continue in the prototype.")

if st.session_state.auth.get("otp_sent"):
    with st.form("confirm_register_form"):
        st.text_input(
            "Email",
            value=st.session_state.auth.get("current_email_input", ""),
            disabled=True,
        )
        otp = st.text_input("Enter OTP", placeholder="123456", max_chars=6)
        confirm = st.form_submit_button("Confirm registration", use_container_width=True)

    if confirm:
        if len(otp) != 6 or not otp.isdigit():
            st.error("Invalid OTP. Enter a 6-digit code.")
        else:
            st.session_state.auth["authenticated"] = True
            st.session_state.auth["otp_verified"] = True
            st.session_state.profile["email"] = st.session_state.auth.get("current_email_input", "alex@example.com")
            st.success("Registration successful. In a real app you would now be redirected to profile editing.")
            st.page_link("pages/4_Profile.py", label="Go to profile", icon="➡️")

st.markdown("### Validation cases shown in UI")
st.caption("These are included because they are explicitly required in the project acceptance scenarios.")
with st.expander("See expected validation states"):
    st.write("- Invalid email → error message")
    st.write("- Empty field → error message")
    st.write("- Wrong OTP → error message")
    st.write("- Correct OTP → success and next step to profile")
