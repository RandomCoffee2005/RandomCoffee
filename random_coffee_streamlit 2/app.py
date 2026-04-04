import streamlit as st
from state import initialize_state, render_sidebar

st.set_page_config(
    page_title="Random Coffee",
    page_icon="☕",
    layout="centered",
    initial_sidebar_state="expanded",
)

initialize_state()

st.markdown(
    """
    <style>
        .block-container {
            max-width: 760px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }
        .mock-note {
            border: 1px solid #d9d9d9;
            border-radius: 12px;
            padding: 0.85rem 1rem;
            margin: 0.75rem 0 1rem 0;
            background: #fafafa;
            font-size: 0.95rem;
        }
        .card {
            border: 1px solid #e6e6e6;
            border-radius: 16px;
            padding: 1rem;
            background: white;
            margin-bottom: 1rem;
        }
        .interest-chip {
            display: inline-block;
            padding: 0.25rem 0.6rem;
            border-radius: 999px;
            border: 1px solid #d0d7de;
            margin: 0.15rem 0.25rem 0.15rem 0;
            font-size: 0.9rem;
        }
        .common-interest {
            display: inline-block;
            padding: 0.25rem 0.6rem;
            border-radius: 999px;
            margin: 0.15rem 0.25rem 0.15rem 0;
            font-size: 0.9rem;
            font-weight: 700;
            border: 1px solid #7c3aed;
            background: #f5f3ff;
            color: #5b21b6;
        }
        .small-muted {
            color: #666;
            font-size: 0.9rem;
        }
        button[kind="primary"] {
            min-height: 44px;
        }
        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button {
            min-height: 44px;
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

render_sidebar()

st.title("Random Coffee")
st.subheader("Weekly random meetings for new connections")


profile = st.session_state.profile
auth = st.session_state.auth
match = st.session_state.match

if auth.get("authenticated"):
    st.success(f"Signed in as {profile.get('email', 'user@example.com')}")
else:
    st.info("You are currently in guest mode. Use Register or Login from the left navigation.")