# Random Coffee — Streamlit UI Prototype

This is a **UI-only prototype** for the Software Quality & Reliability course project.
It implements multiple Streamlit pages with navigation and mocked states, but **does not** contain backend logic, real OTP, database persistence, or a real matching algorithm.

## Structure

- `app.py` — landing page, global demo state, sidebar controls
- `pages/1_Register.py` — registration + mocked OTP flow
- `pages/2_Login.py` — login + mocked OTP flow
- `pages/3_Dashboard.py` — current match, meeting confirmation, optional feedback
- `pages/4_Profile.py` — profile editing and account disable/enable
- `pages/5_API_Docs.py` — placeholder for `/docs` and `/openapi.json`

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- All buttons and forms are **mocked** and intentionally labelled as such.
- Session state is used only to simulate flows for demo purposes.
- The layout is intentionally simple and single-column to stay readable on narrow screens.
