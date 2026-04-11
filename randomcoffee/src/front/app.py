import streamlit as st

from api import get_client
from state import initialize_state, inject_global_styles, render_sidebar

st.set_page_config(page_title="Random Coffee", page_icon="☕", layout="centered")

initialize_state()
inject_global_styles()
render_sidebar()

st.title("Random Coffee")
st.write(
    "Weekly random coffee chats for students and staff. "

)

if st.session_state.backend["enabled"]:
    ok, message = get_client().healthcheck_docs()
    if ok:
        pass
    else:
        st.error(message)

st.markdown("### Main actions")
if st.session_state.auth.get("authenticated"):
    st.page_link("pages/3_Dashboard.py", label="Open dashboard", icon="☕")
    st.page_link("pages/4_Profile.py", label="Open profile", icon="👤")
else:
    st.page_link("pages/1_Register.py", label="Register", icon="📝")
    st.page_link("pages/2_Login.py", label="Login", icon="🔐")
