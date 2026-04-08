# Random Coffee — Streamlit Prototype

Multipage Streamlit prototype for the Random Coffee учебный проект.

## What is connected to backend

This frontend can work in two modes:

1. **Mock mode** — demo-only UI state.
2. **Backend mode** — calls the available FastAPI endpoints.

Currently supported by the backend archive:

- `POST /login_start`
- `POST /login`
- `GET /myprofile`
- `PATCH /myprofile`
- `GET /notifications`
- `POST /confirm`
- `GET /profile/{user_id}`
- `POST /admin/pairing`
- `GET /docs`
- `GET /openapi.json`

## Important mismatch between PDF requirements and current backend

The PDF requires interests, about me, common-interest highlighting, and optional feedback persistence. The current backend does **not** expose fields/endpoints for those yet, so these remain explicitly marked as **prototype-only UI fields**.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Backend URL

Set the backend base URL in the sidebar, for example:

- `http://127.0.0.1:8000`

