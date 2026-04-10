import streamlit as st

from ..api import APIError, get_client
from ..state import initialize_state, inject_global_styles, render_interest_chips, render_sidebar

st.set_page_config(page_title="Profile • Random Coffee", page_icon="👤", layout="centered")

initialize_state()
inject_global_styles()
render_sidebar()

st.title("Profile")

backend_enabled = st.session_state.backend["enabled"]
auth = st.session_state.auth
profile = st.session_state.profile

if backend_enabled:
    st.markdown(
        '<div class="backend-note"><b>Partially backend-connected profile.</b> ' +
        'Name, Telegram/contact alias, and account visibility map to '
        '<code>GET /myprofile</code> and <code>PATCH /myprofile</code>. ' +
        'Interests and About Me remain prototype-only fields ' +
        'because the backend does not expose them.</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="mock-note"><b>Mock profile editing.</b> ' +
        'Saving changes updates only Streamlit session state in mock mode.</div>',
        unsafe_allow_html=True,
    )

if backend_enabled and auth.get("authenticated") and auth.get("jwt"):
    try:
        remote = get_client().get_myprofile()
        st.session_state.profile["id"] = remote.get("id")
        st.session_state.profile["name"] = remote.get("name", "")
        st.session_state.profile["telegram"] = remote.get("contact_info", "")
    except APIError as exc:
        st.error(str(exc))

with st.form("profile_form"):
    name = st.text_input("Full name", value=profile.get("name", ""))
    interests_raw = st.text_input(
        "Interests (prototype-only, comma separated)",
        value=", ".join(profile.get("interests", [])),
        placeholder="Design, AI, Startups",
    )
    about_me = st.text_area(
        "About me (prototype-only)",
        value=profile.get("about_me", ""),
        height=120,
    )
    telegram = st.text_input("Telegram alias", value=profile.get("telegram", ""),
                             placeholder="@username")
    save = st.form_submit_button("Save profile", use_container_width=True)

if save:
    st.session_state.profile["interests"] = \
        [x.strip() for x in interests_raw.split(",") if x.strip()]
    st.session_state.profile["about_me"] = about_me
    st.session_state.profile["profile_complete"] = all([name.strip(), telegram.strip()])

    if backend_enabled and auth.get("authenticated") and auth.get("jwt"):
        try:
            get_client().update_myprofile(name=name.strip(), contact_info=telegram.strip())
            st.session_state.profile["name"] = name.strip()
            st.session_state.profile["telegram"] = telegram.strip()
            st.success("Backend-backed profile fields saved successfully.")
            st.info("Interests and About Me are still local prototype-only fields.")
            st.rerun()
        except APIError as exc:
            st.error(str(exc))
    else:
        st.session_state.profile["name"] = name.strip()
        st.session_state.profile["telegram"] = telegram.strip()
        st.success("Profile changes saved in mock session state.")
        st.rerun()

st.markdown("### Current profile card")
with st.container(border=True):
    st.write(f"**Name:** {st.session_state.profile.get('name', '—')}")
    st.write(f"**Email:** {st.session_state.profile.get('email', '—')}")
    st.write(f"**Telegram:** {st.session_state.profile.get('telegram', '—')}")
    st.write("**About me:**")
    st.write(st.session_state.profile.get("about_me", "—"))
    st.write("**Interests:**")
    interests = st.session_state.profile.get("interests", [])
    if interests:
        st.markdown(render_interest_chips(interests), unsafe_allow_html=True)
    else:
        st.caption("No interests entered.")

st.markdown("### Account visibility")
visible_for_matching = st.toggle(
    "Visible for weekly matching",
    value=st.session_state.profile.get("account_active", True),
)

if visible_for_matching != st.session_state.profile.get("account_active", True):
    if backend_enabled and auth.get("authenticated") and auth.get("jwt"):
        try:
            get_client().update_myprofile(is_active=visible_for_matching)
            st.session_state.profile["account_active"] = visible_for_matching
            st.success("Account visibility updated through backend.")
            st.rerun()
        except APIError as exc:
            st.error(str(exc))
    else:
        st.session_state.profile["account_active"] = visible_for_matching
        st.success("Account visibility updated in mock session state.")
        st.rerun()

if st.session_state.profile.get("account_active", True):
    st.success("Your profile is active and visible for weekly matching.")
else:
    st.warning("Your profile is hidden from matching.")

st.markdown("### Disable account")
if st.button("Disable account", use_container_width=True, type="secondary"):
    if backend_enabled and auth.get("authenticated") and auth.get("jwt"):
        try:
            get_client().update_myprofile(is_active=False)
            st.session_state.profile["account_active"] = False
            st.warning("Account disabled through backend.")
            st.rerun()
        except APIError as exc:
            st.error(str(exc))
    else:
        st.session_state.profile["account_active"] = False
        st.warning("Account disabled in UI state only.")
        st.rerun()
