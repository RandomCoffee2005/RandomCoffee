import streamlit as st

from api import APIError, get_client
from state import initialize_state, inject_global_styles, render_interest_chips, render_sidebar

st.set_page_config(page_title="Dashboard • Random Coffee", page_icon="☕", layout="centered")

initialize_state()
inject_global_styles()
render_sidebar()

st.title("Dashboard")

backend_enabled = st.session_state.backend["enabled"]
auth = st.session_state.auth
profile = st.session_state.profile
match = st.session_state.match

if not auth.get("authenticated"):
    st.warning("Dashboard is available only after registration or login.")
    col1, col2 = st.columns(2)
    with col1:
        st.page_link("pages/1_Register.py", label="Go to Register", icon="📝")
    with col2:
        st.page_link("pages/2_Login.py", label="Go to Login", icon="🔐")
    st.stop()

if backend_enabled:
    st.markdown(
        '<div class="backend-note"><b>Backend-connected dashboard.</b> This page reads <code>/notifications</code>, '
        '<code>/profile/{user_id}</code>, and <code>/confirm</code>.</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="mock-note"><b>Mock dashboard.</b> Match generation, notifications, and persistence are demo-only in mock mode.</div>',
        unsafe_allow_html=True,
    )

if backend_enabled and auth.get("authenticated") and auth.get("jwt"):
    try:
        client = get_client()
        notifications = client.get_notifications(n=1)
        if notifications:
            latest = notifications[0]
            partner_profile = client.get_profile(latest["partner_user_id"])
            st.session_state.match.update(
                {
                    "has_match": True,
                    "notification_id": latest.get("id"),
                    "partner_user_id": latest.get("partner_user_id"),
                    "name": latest.get("partner_name", "Unknown user"),
                    "telegram": partner_profile.get("contact_info", ""),
                    "meeting_confirmed": bool(latest.get("met")),
                    "created_at": latest.get("created_at"),
                    "week_key": latest.get("week_key"),
                    "interests": [],
                    "common_interests": [],
                }
            )
        else:
            st.session_state.match.update({"has_match": False, "notification_id": None})
    except APIError as exc:
        st.error(str(exc))

if not profile.get("account_active", True):
    st.error("Your account is currently disabled. Matching is unavailable while your profile is hidden.")

st.markdown("### Nearest meeting")

if not st.session_state.match.get("has_match"):
    st.info("No current match is available.")
else:
    with st.container(border=True):
        st.subheader(st.session_state.match.get("name", "Unknown user"))
        telegram = st.session_state.match.get("telegram") or "—"
        st.write(f"**Telegram:** {telegram}")

        if st.session_state.match.get("week_key"):
            st.write(f"**Week:** {st.session_state.match.get('week_key')}")

        if backend_enabled:
            st.write("**Partner interests**")
            st.caption("Not available from current backend API.")
            st.write("**Common interests**")
            st.caption("The PDF requires this, but the uploaded backend does not expose interests yet.")
        else:
            common = set(st.session_state.match.get("common_interests", []))
            st.write("**Partner interests**")
            st.markdown(
                render_interest_chips(st.session_state.match.get("interests", []), common),
                unsafe_allow_html=True,
            )
            st.write("**Common interests**")
            if common:
                st.markdown(
                    render_interest_chips(st.session_state.match.get("common_interests", []), common),
                    unsafe_allow_html=True,
                )
            else:
                st.caption("No common interests highlighted in this demo state.")

        if not st.session_state.match.get("meeting_confirmed"):
            if st.button("Meeting took place", use_container_width=True):
                if backend_enabled and st.session_state.match.get("notification_id"):
                    try:
                        get_client().confirm_meeting(st.session_state.match["notification_id"])
                        st.session_state.match["meeting_confirmed"] = True
                        st.success("Meeting confirmation saved through backend.")
                        st.rerun()
                    except APIError as exc:
                        st.error(str(exc))
                else:
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
                if backend_enabled:
                    st.warning("Current backend does not provide a feedback endpoint yet. Text is stored only in local UI state.")
                else:
                    st.success("Feedback submitted successfully in mock UI state.")

            if st.session_state.match.get("feedback_submitted"):
                st.info(st.session_state.match.get("feedback_text") or "No text entered.")

st.markdown("### Matching note")
st.caption(
    "The PDF requires weekly automatic matching, one partner per week, and common-interest highlighting. The current frontend shows those states, but the uploaded backend only exposes notification retrieval and confirmation."
)
