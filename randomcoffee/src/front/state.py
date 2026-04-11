from __future__ import annotations

import streamlit as st

DEFAULT_PROFILE = {
    "id": None,
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
    "notification_id": None,
    "partner_user_id": None,
    "name": "Maya Chen",
    "interests": ["Design", "AI", "Books", "Photography"],
    "telegram": "@maya_chen",
    "common_interests": ["Design", "Books"],
    "meeting_confirmed": False,
    "feedback_submitted": False,
    "feedback_text": "",
    "created_at": None,
    "week_key": None,
}

DEFAULT_AUTH = {
    "authenticated": False,
    "otp_sent": False,
    "otp_verified": False,
    "current_email_input": "",
    "current_otp_input": "",
    "jwt": None,
}

DEFAULT_BACKEND = {
    "enabled": False,
    "base_url": "http://backend:8080",
    "status": None,
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
    if "backend" not in st.session_state:
        st.session_state.backend = DEFAULT_BACKEND.copy()
    if "ui_mode" not in st.session_state:
        st.session_state.ui_mode = "Normal"


def reset_demo_state() -> None:
    st.session_state.profile = DEFAULT_PROFILE.copy()
    st.session_state.match = DEFAULT_MATCH.copy()
    st.session_state.auth = DEFAULT_AUTH.copy()
    st.session_state.ui_mode = "Normal"


def logout() -> None:
    st.session_state.profile = DEFAULT_PROFILE.copy()
    st.session_state.match = DEFAULT_MATCH.copy()
    st.session_state.auth = DEFAULT_AUTH.copy()
    st.session_state.ui_mode = "Normal"


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
        auth["jwt"] = "mock-jwt"
        match["has_match"] = False
    elif mode == "Logged in, active match":
        auth["authenticated"] = True
        auth["jwt"] = "mock-jwt"
    elif mode == "Meeting confirmed":
        auth["authenticated"] = True
        auth["jwt"] = "mock-jwt"
        match["meeting_confirmed"] = True
    elif mode == "Feedback submitted":
        auth["authenticated"] = True
        auth["jwt"] = "mock-jwt"
        match["meeting_confirmed"] = True
        match["feedback_submitted"] = True
        match["feedback_text"] = "Great conversation about design systems and startup life."
    elif mode == "Disabled account":
        auth["authenticated"] = True
        auth["jwt"] = "mock-jwt"
        profile["account_active"] = False

    st.session_state.profile = profile
    st.session_state.match = match
    st.session_state.auth = auth
    st.session_state.ui_mode = mode


def render_interest_chips(interests: list[str], highlight: set[str] | None = None) -> str:
    highlight = highlight or set()
    parts: list[str] = []
    for item in interests:
        css_class = "common-interest" if item in highlight else "interest-chip"
        parts.append(f'<span class="{css_class}">{item}</span>')
    return "".join(parts)


def render_sidebar() -> None:
    initialize_state()
    with st.sidebar:
        st.title("☕ Random Coffee")
        st.caption("Single-column Streamlit prototype")

        st.markdown("### Navigation")
        st.page_link("app.py", label="Home", icon="🏠")
        if st.session_state.auth.get("authenticated"):
            st.page_link("pages/3_Dashboard.py", label="Dashboard", icon="☕")
            st.page_link("pages/4_Profile.py", label="Profile", icon="👤")
        else:
            st.page_link("pages/1_Register.py", label="Register", icon="📝")
            st.page_link("pages/2_Login.py", label="Login", icon="🔐")
        if st.session_state.auth.get("authenticated"):
            if st.button("Log out", use_container_width=True):
                logout()
                st.switch_page("app.py")

        st.markdown("### Backend")
        enabled = st.toggle(
            "Use backend API",
            value=st.session_state.backend["enabled"],
            help="When enabled, supported pages call the FastAPI backend instead of demo-only " +
            "mock state.",
        )
        st.session_state.backend["enabled"] = enabled
        base_url = st.text_input(
            "Backend base URL",
            value=st.session_state.backend["base_url"],
            placeholder="http://127.0.0.1:8000",
        )
        st.session_state.backend["base_url"] = base_url.strip()

        # st.markdown("### Demo controls")
        # selected_mode = st.selectbox(
        #     "Mock state",
        #     MOCK_MODES,
        #     index=MOCK_MODES.index(
        #         st.session_state.ui_mode if st.session_state.ui_mode in MOCK_MODES else "Normal"
        #     ),
        #     disabled=enabled,
        # )

        # col1, col2 = st.columns(2)
        # with col1:
        #     if st.button("Apply", use_container_width=True, disabled=enabled):
        #         apply_mock_mode(selected_mode)
        #         st.rerun()
        # with col2:
        #     if st.button("Reset", use_container_width=True):
        #         reset_demo_state()
        #         st.rerun()

        if enabled:
            st.info("Backend mode is active. " +
                    "Unsupported fields stay visibly marked as prototype-only.")
        else:
            st.warning("Mock mode is active. No backend requests are sent.")


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 760px;
            padding-top: 1.25rem;
            padding-bottom: 3rem;
        }
        .mock-note {
            background: #fff8e1;
            border: 1px solid #f1d58a;
            border-radius: 12px;
            padding: 0.75rem 0.9rem;
            margin-bottom: 1rem;
        }
        .backend-note {
            background: #eef6ff;
            border: 1px solid #bfdcff;
            border-radius: 12px;
            padding: 0.75rem 0.9rem;
            margin-bottom: 1rem;
        }
        .interest-chip, .common-interest {
            display: inline-block;
            padding: 0.35rem 0.65rem;
            margin: 0.15rem 0.3rem 0.15rem 0;
            border-radius: 999px;
            font-size: 0.92rem;
            border: 1px solid #d9d9d9;
            background: #f6f6f6;
        }
        .common-interest {
            border-color: #a8d5ba;
            background: #e9f7ef;
            font-weight: 700;
        }
        iframe {
            width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
