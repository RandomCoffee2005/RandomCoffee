import streamlit as st

from api import get_client
from state import initialize_state, inject_global_styles, render_sidebar

st.set_page_config(page_title="API Docs • Random Coffee", page_icon="🧩", layout="centered")

initialize_state()
inject_global_styles()
render_sidebar()

st.title("API / Developer Docs")

base_url = st.session_state.backend["base_url"].rstrip("/")
docs_url = f"{base_url}/docs"
openapi_url = f"{base_url}/openapi.json"

st.markdown(
    '<div class="backend-note"><b>Developer page.</b> ' +
    'This page points to the backend Swagger and ' +
    'OpenAPI endpoints required by the project PDF.</div>',
    unsafe_allow_html=True,
)

if st.session_state.backend["enabled"]:
    ok, message = get_client().healthcheck_docs()
    if ok:
        st.success(message)
    else:
        st.error(message)
else:
    st.warning("Backend mode is currently disabled. " +
               "Links below are still generated from the configured base URL.")

st.markdown("### Backend documentation endpoints")
st.code(docs_url, language="text")
st.code(openapi_url, language="text")
st.link_button("Open Swagger UI", docs_url, use_container_width=True)
st.link_button("Open OpenAPI JSON", openapi_url, use_container_width=True)

st.markdown("### Endpoints found in uploaded backend")
with st.container(border=True):
    st.write("- POST /login_start")
    st.write("- POST /login")
    st.write("- GET /myprofile")
    st.write("- PATCH /myprofile")
    st.write("- GET /profile/{user_id}")
    st.write("- GET /notifications")
    st.write("- POST /confirm")
    st.write("- POST /admin/pairing")

st.markdown("### Gap versus project PDF")
st.info(
    "The PDF expects matching details with partner interests, common-interest highlighting, " +
    "and optional feedback persistence. Those contracts are not present in the uploaded backend " +
    "yet, so Swagger will not show them until backend endpoints are added."
)
