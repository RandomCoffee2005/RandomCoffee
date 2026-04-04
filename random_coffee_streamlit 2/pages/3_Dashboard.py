import streamlit as st
from state import initialize_state, render_sidebar

st.set_page_config(page_title="Dashboard • Random Coffee", page_icon="☕", layout="centered")

initialize_state()
render_sidebar()

st.title("Dashboard")
st.markdown(
    '<div class="mock-note"><b>Mock dashboard.</b> Match generation, notifications, and persistence are not implemented yet. Data below is demo-only.</div>',
    unsafe_allow_html=True,
)

auth = st.session_state.auth
profile = st.session_state.profile
match = st.session_state.match

if not auth.get("authenticated"):
    st.warning("This page represents an authenticated area. Use the Login or Register page for the demo flow.")

if not profile.get("account_active", True):
    st.error("Your account is currently disabled. Matching is unavailable while your profile is hidden.")

st.markdown("### Nearest meeting")

if not match.get("has_match"):
    st.info("No current match is available in this mocked state. Weekly matching would normally assign at most one partner.")
else:
    common = set(match.get("common_interests", []))
    all_interests = match.get("interests", [])

    with st.container(border=True):
        st.subheader(match.get("name", "Unknown user"))
        st.write("**Telegram:** " + match.get("telegram", "—"))

        st.write("**Partner interests**")
        rendered = []
        for interest in all_interests:
            if interest in common:
                rendered.append(f'<span class="common-interest">{interest}</span>')
            else:
                rendered.append(f'<span class="interest-chip">{interest}</span>')
        st.markdown("".join(rendered), unsafe_allow_html=True)

        st.write("**Common interests**")
        if common:
            st.markdown(
                "".join([f'<span class="common-interest">{x}</span>' for x in match.get("common_interests", [])]),
                unsafe_allow_html=True,
            )
        else:
            st.caption("No common interests highlighted in this demo state.")

        if not match.get("meeting_confirmed"):
            if st.button("Meeting took place", use_container_width=True):
                st.session_state.match["meeting_confirmed"] = True
                st.success("Meeting confirmation saved in UI state only.")
                st.rerun()
        else:
            st.success("Meeting confirmed.")

        if st.session_state.match.get("meeting_confirmed"):
            with st.form("feedback_form"):
                feedback = st.text_area(
                    "Optional feedback",
                    value=st.session_state.match.get("feedback_text", ""),
                    placeholder="How did the meeting go?",
                    height=120,
                )
                submit_feedback = st.form_submit_button("Submit feedback", use_container_width=True)

            if submit_feedback:
                st.session_state.match["feedback_text"] = feedback
                st.session_state.match["feedback_submitted"] = True
                st.success("Feedback submitted successfully. In the real system this would be saved to the database within 2 seconds.")

            if st.session_state.match.get("feedback_submitted"):
                st.info("Current mock feedback saved in session state:")
                st.write(st.session_state.match.get("feedback_text") or "No text entered.")

st.markdown("### Weekly matching note")
st.caption(
    "This prototype visually represents the acceptance scenario where active users with complete profiles receive a weekly match and do not get paired with someone they have already confirmed a meeting with."
)
