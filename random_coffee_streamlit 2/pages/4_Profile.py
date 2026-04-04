import streamlit as st
from state import initialize_state, render_sidebar

st.set_page_config(page_title="Profile • Random Coffee", page_icon="👤", layout="centered")

initialize_state()
render_sidebar()

st.title("Profile")
st.markdown(
    '<div class="mock-note"><b>Mock profile editing.</b> Saving changes updates only the Streamlit session state for demo purposes.</div>',
    unsafe_allow_html=True,
)

profile = st.session_state.profile

with st.form("profile_form"):
    name = st.text_input("Full name", value=profile.get("name", ""))
    interests_raw = st.text_input(
        "Interests (comma separated)",
        value=", ".join(profile.get("interests", [])),
        placeholder="Design, AI, Startups",
    )
    about_me = st.text_area("About me", value=profile.get("about_me", ""), height=120)
    telegram = st.text_input("Telegram alias", value=profile.get("telegram", ""), placeholder="@username")
    save = st.form_submit_button("Save profile", use_container_width=True)

if save:
    st.session_state.profile["name"] = name
    st.session_state.profile["interests"] = [x.strip() for x in interests_raw.split(",") if x.strip()]
    st.session_state.profile["about_me"] = about_me
    st.session_state.profile["telegram"] = telegram
    st.session_state.profile["profile_complete"] = all([name.strip(), telegram.strip(), about_me.strip()])
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
        st.markdown(
            "".join([f'<span class="interest-chip">{interest}</span>' for interest in interests]),
            unsafe_allow_html=True,
        )
    else:
        st.caption("No interests entered.")

st.markdown("### Account visibility")
if st.session_state.profile.get("account_active", True):
    st.success("Your profile is active and visible for weekly matching.")
    if st.button("Disable account", use_container_width=True):
        st.session_state.profile["account_active"] = False
        st.warning("Account disabled in UI state only. The profile is now hidden from matching in this prototype.")
        st.rerun()
else:
    st.warning("Your account is disabled and hidden from matching.")
    if st.button("Re-enable account", use_container_width=True):
        st.session_state.profile["account_active"] = True
        st.success("Account re-enabled in UI state only.")
        st.rerun()
