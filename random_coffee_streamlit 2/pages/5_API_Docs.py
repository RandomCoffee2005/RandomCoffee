import streamlit as st
from state import initialize_state, render_sidebar

st.set_page_config(page_title="API Docs • Random Coffee", page_icon="🧩", layout="centered")

initialize_state()
render_sidebar()

st.title("API / Developer Docs")
st.markdown(
    '<div class="mock-note"><b>Developer-facing placeholder.</b> This page exists to represent the project requirement for Swagger UI and OpenAPI JSON availability.</div>',
    unsafe_allow_html=True,
)

st.markdown("### Expected backend documentation endpoints")
st.code("/docs", language="text")
st.code("/openapi.json", language="text")

st.markdown("### Endpoints expected by the project description")
with st.container(border=True):
    st.write("- Registration with OTP")
    st.write("- Login with OTP")
    st.write("- Profile read/update")
    st.write("- Weekly matching trigger / retrieval")
    st.write("- Meeting confirmation")
    st.write("- Optional feedback submission")
    st.write("- Account disable / hide profile")

st.info(
    "In the final system, Swagger UI should list request/response schemas for all core endpoints, and /openapi.json should return a valid OpenAPI specification importable into Postman or Swagger Editor."
)
