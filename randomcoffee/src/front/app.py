import streamlit as st

from .api import get_client
from .state import initialize_state, inject_global_styles, render_sidebar

st.set_page_config(page_title="Random Coffee", page_icon="☕", layout="centered")

initialize_state()
inject_global_styles()
render_sidebar()

st.title("Random Coffee")
st.write(
    "Weekly random coffee chats for students and staff. This prototype is designed as a clean, " +
    "single-column UI with explicit separation between " +
    "backend-backed features and demo-only states."
)

if st.session_state.backend["enabled"]:
    ok, message = get_client().healthcheck_docs()
    if ok:
        st.markdown(f'<div class="backend-note"><b>Backend mode.</b> {message}.</div>',
                    unsafe_allow_html=True)
    else:
        st.error(message)
else:
    st.markdown(
        '<div class="mock-note"><b>Mock mode.</b> No backend requests are sent. ' +
        'Use the sidebar to switch to backend mode.</div>',
        unsafe_allow_html=True,
    )

st.markdown("### Main actions")
if st.session_state.auth.get("authenticated"):
    st.page_link("pages/3_Dashboard.py", label="Open dashboard", icon="☕")
    st.page_link("pages/4_Profile.py", label="Open profile", icon="👤")
else:
    st.page_link("pages/1_Register.py", label="Register", icon="📝")
    st.page_link("pages/2_Login.py", label="Login", icon="🔐")
# st.page_link("pages/5_API_Docs.py", label="API Docs", icon="🧩")

st.markdown("### Covered requirements")
st.write("- Registration / login form for unauthenticated users")
st.write("- OTP flow UI")
st.write("- Profile editing")
st.write("- Account visibility toggle and disable account")
st.write("- Match card and meeting confirmation")
st.write("- Developer-facing API docs access")

st.markdown("### Current backend gap")
st.info(
    "The uploaded backend does not currently expose interests, about-me text, " +
    "common-interest matching, or feedback persistence. " +
    "Those UI sections remain clearly marked as prototype-only " +
    "until matching backend endpoints exist."
)
