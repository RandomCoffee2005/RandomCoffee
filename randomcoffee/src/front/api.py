from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
import streamlit as st
from interest_names import interest_list

REQUEST_TIMEOUT_SECONDS = 8

INTEREST_NAME_TO_ID = {name.lower(): idx for idx, name in enumerate(interest_list)}


def interest_names_to_ids(names: list[str]) -> list[int]:
    result: list[int] = []
    for name in names:
        key = name.strip().lower()
        if key in INTEREST_NAME_TO_ID:
            result.append(INTEREST_NAME_TO_ID[key])
    return result


def interest_ids_to_names(ids: list[Any]) -> list[str]:
    result: list[str] = []
    for raw in ids:
        try:
            idx = int(raw)
        except (TypeError, ValueError):
            continue
        if 0 <= idx < len(interest_list):
            result.append(interest_list[idx])
    return result


class APIError(Exception):
    pass


@dataclass
class APIClient:
    base_url: str
    jwt: str | None = None

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}{path}"

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if self.jwt:
            headers["Authorization"] = f"Bearer {self.jwt}"
        return headers

    def _request(self, method: str, path: str, json: dict[str, Any] | None = None) -> Any:
        try:
            response = requests.request(
                method=method,
                url=self._url(path),
                json=json,
                headers=self._headers(),
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise APIError(f"Backend connection failed: {exc}") from exc

        content_type = response.headers.get("content-type", "")
        is_json = "application/json" in content_type.lower()
        body: Any = response.json() if is_json and response.content else None

        if response.status_code >= 400:
            if isinstance(body, dict):
                detail = body.get("detail") or body.get("error") or str(body)
            else:
                detail = response.text or f"HTTP {response.status_code}"
            raise APIError(detail)

        return body

    def healthcheck_docs(self) -> tuple[bool, str]:
        try:
            response = requests.get(self._url("/openapi.json"), timeout=REQUEST_TIMEOUT_SECONDS)
            if response.status_code == 200:
                return True, "OpenAPI reachable"
            return False, f"OpenAPI returned {response.status_code}"
        except requests.RequestException as exc:
            return False, f"Backend unreachable: {exc}"

    def login_start(self, email: str) -> None:
        self._request("POST", "/login_start", {"email": email})

    def login(self, email: str, otp: str) -> str:
        payload = self._request("POST", "/login", {"email": email, "otp": otp})
        if not isinstance(payload, dict) or "jwt" not in payload:
            raise APIError("Backend did not return JWT")
        return str(payload["jwt"])

    def get_myprofile(self) -> dict[str, Any]:
        payload = self._request("GET", "/myprofile")
        return payload if isinstance(payload, dict) else {}

    def update_myprofile(
        self,
        name: str | None = None,
        contact_info: str | None = None,
        about_me: str | None = None,
        interests: list[str] | None = None,
        is_active: bool | None = None,
    ) -> None:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if contact_info is not None:
            body["contact_info"] = contact_info
        if about_me is not None:
            body["about_me"] = about_me
        if interests is not None:
            body["interests"] = interest_names_to_ids(interests)
        if is_active is not None:
            body["is_active"] = is_active
        self._request("PATCH", "/myprofile", body)

    def get_notifications(
        self,
        status: str | None = None,
        n: int | None = None,
    ) -> list[dict[str, Any]]:
        params = []
        if status:
            params.append(f"status={status}")
        if n is not None:
            params.append(f"n={n}")
        query = f"?{'&'.join(params)}" if params else ""
        payload = self._request("GET", f"/notifications{query}")
        return payload if isinstance(payload, list) else []

    def get_profile(self, user_id: str) -> dict[str, Any]:
        payload = self._request("GET", f"/profile/{user_id}")
        return payload if isinstance(payload, dict) else {}

    def confirm_meeting(self, notification_id: str) -> None:
        self._request("POST", "/confirm", {"notification_id": notification_id})

    def trigger_pairing(self) -> None:
        self._request("POST", "/admin/pairing")


def get_client() -> APIClient:
    return APIClient(
        base_url=st.session_state.backend["base_url"],
        jwt=st.session_state.auth.get("jwt"),
    )