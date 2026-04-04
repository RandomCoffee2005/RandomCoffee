import streamlit as st

DEFAULT_PROFILE = {
    "email": "alex@example.com",
    "name": "Alex Johnson",
    "interests": ["Design", "Startups", "Books", "Travel"],
    "about_me": "Frontend developer interested in meeting people outside my usual circle.",
    "telegram": "@alexj",
    "account_active": True,
    "profile_complete": True,
}

DEFAULT_MATCH = {
    "has_match": True,
    "name": "Maya Chen",
    "interests": ["Design", "AI", "Books", "Photography"],
    "telegram": "@maya_chen",
    "common_interests": ["Design", "Books"],
    "meeting_confirmed": False,
    "feedback_submitted": False,
    "feedback_text": "",
}

DEFAULT_AUTH = {
    "authenticated": False,
    "otp_sent": False,
    "otp_verified": False,
    "current_email_input": "",
    "current_otp_input": "",
}

MOCK_MODES = [
    "Normal",
    "Guest view",
    "OTP sent",
    "Wrong OTP",
    "Logged in, no match",
    "Logged in, active match",
    "Meeting confirmed",
    "Feedback submitted",
    "Disabled account",
]


def initialize_state() -> None:
    if "profile" not in st.session_state:
        st.session_state.profile = DEFAULT_PROFILE.copy()
    if "match" not in st.session_state:
        st.session_state.match = DEFAULT_MATCH.copy()
    if "auth" not in st.session_state:
        st.session_state.auth = DEFAULT_AUTH.copy()
    if "ui_mode" not in st.session_state:
        st.session_state.ui_mode = "Normal"
    if "flash" not in st.session_state:
        st.session_state.flash = None


def apply_mock_mode(mode: str) -> None:
    profile = DEFAULT_PROFILE.copy()
    match = DEFAULT_MATCH.copy()
    auth = DEFAULT_AUTH.copy()

    if mode == "Guest view":
        auth["authenticated"] = False
    elif mode == "OTP sent":
        auth["otp_sent"] = True
        auth["current_email_input"] = "alex@example.com"
    elif mode == "Wrong OTP":
        auth["otp_sent"] = True
        auth["current_email_input"] = "alex@example.com"
        auth["current_otp_input"] = "000000"
    elif mode == "Logged in, no match":
        auth["authenticated"] = True
        profile["email"] = "alex@example.com"
        match["has_match"] = False
    elif mode == "Logged in, active match":
        auth["authenticated"] = True
    elif mode == "Meeting confirmed":
        auth["authenticated"] = True
        match["meeting_confirmed"] = True
    elif mode == "Feedback submitted":
        auth["authenticated"] = True
        match["meeting_confirmed"] = True
        match["feedback_submitted"] = True
        match["feedback_text"] = "Great conversation about design systems and startup life."
    elif mode == "Disabled account":
        auth["authenticated"] = True
        profile["account_active"] = False

    st.session_state.profile = profile
    st.session_state.match = match
    st.session_state.auth = auth
    st.session_state.ui_mode = mode


def render_sidebar() -> None:
    initialize_state()
    with st.sidebar:
        st.title("☕ Random Coffee")
        st.caption("Streamlit prototype with mocked states")

        selected_mode = st.selectbox(
            "Mock state",
            MOCK_MODES,
            index=MOCK_MODES.index(st.session_state.ui_mode if st.session_state.ui_mode in MOCK_MODES else "Normal"),
        )

        if st.button("Apply mock state", use_container_width=True):
            apply_mock_mode(selected_mode)
            st.rerun()

        if st.button("Reset demo data", use_container_width=True):
            st.session_state.profile = DEFAULT_PROFILE.copy()
            st.session_state.match = DEFAULT_MATCH.copy()
            st.session_state.auth = DEFAULT_AUTH.copy()
            st.session_state.ui_mode = "Normal"
            st.rerun()
