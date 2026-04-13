import streamlit as st

from api import APIError, get_client, interest_ids_to_names
from state import initialize_state, inject_global_styles, render_interest_chips, render_sidebar
from interest_names import interest_list

st.set_page_config(page_title="Profile • Random Coffee", page_icon="👤", layout="centered")

initialize_state()
inject_global_styles()
render_sidebar()

auth = st.session_state.auth

if not auth.get("authenticated"):
    st.title("Profile")
    st.warning("Profile is available only after login.")

    col2 = st.columns(1)
    with col2:
        st.page_link("pages/2_Login.py", label="Go to Login", icon="🔐")

    st.stop()

st.title("Profile")

backend_enabled = st.session_state.backend["enabled"]
profile = st.session_state.profile

if backend_enabled and auth.get("jwt"):
    try:
        remote = get_client().get_myprofile()
        # st.write("DEBUG remote profile:", remote)

        st.session_state.profile["id"] = remote.get("id")
        st.session_state.profile["name"] = remote.get("name", "")
        st.session_state.profile["telegram"] = remote.get("contact_info", "")
        st.session_state.profile["about_me"] = remote.get(
            "about_me",
            st.session_state.profile.get("about_me", ""),
        )

        remote_interests = remote.get("interests", [])
        if isinstance(remote_interests, list):
            st.session_state.profile["interests"] = interest_ids_to_names(remote_interests)

        if "is_active" in remote:
            st.session_state.profile["account_active"] = bool(remote.get("is_active"))
    except APIError as exc:
        st.error(str(exc))

profile = st.session_state.profile

with st.form("profile_form"):
    name = st.text_input("Full name", value=profile.get("name", ""))

    interests_raw = st.multiselect(
        "Interests",
        options=interest_list,
        default=[item for item in profile.get("interests", []) if item in interest_list],
        help="Select one or more interests.",
    )

    about_me = st.text_area(
        "About me",
        value=profile.get("about_me", ""),
        height=120,
    )

    telegram = st.text_input(
        "Telegram alias",
        value=profile.get("telegram", ""),
        placeholder="@username",
    )

    save = st.form_submit_button("Save profile", use_container_width=True)

if save:
    parsed_interests = [x.strip() for x in interests_raw if x.strip()]

    st.session_state.profile["name"] = name.strip()
    st.session_state.profile["telegram"] = telegram.strip()
    st.session_state.profile["about_me"] = about_me.strip()
    st.session_state.profile["interests"] = parsed_interests
    st.session_state.profile["profile_complete"] = all([name.strip(), telegram.strip()])

    if backend_enabled and auth.get("jwt"):
        try:
            get_client().update_myprofile(
                name=name.strip(),
                contact_info=telegram.strip(),
                about_me=about_me.strip(),
                interests=parsed_interests,
            )
            st.success("Profile saved through backend.")
            st.rerun()
        except APIError as exc:
            st.error(str(exc))
    else:
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
    if backend_enabled and auth.get("jwt"):
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
