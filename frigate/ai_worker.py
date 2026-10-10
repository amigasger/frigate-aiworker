from __future__ import annotations

from typing import Any

import httpx


class AIWorkerError(RuntimeError):
    """Raised when a remote AI worker request fails."""


class AIWorkerClient:
    """Minimal HTTP client for communicating with a remote AI worker node."""

    def __init__(self, api_url: str, *, timeout: float = 10.0) -> None:
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout

    @classmethod
    def from_worker_config(cls, worker_config: Any) -> "AIWorkerClient":
        return cls(worker_config.get_api_url())

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{self.api_url}{path if path.startswith('/') else '/' + path}"
        try:
            response = httpx.request(method, url, timeout=self.timeout, **kwargs)
        except httpx.HTTPError as exc:
            raise AIWorkerError(f"Failed to call AI worker: {exc}") from exc

        if response.is_error:
            raise AIWorkerError(
                f"AI worker request failed: {method.upper()} {url} -> {response.status_code} {response.text}"
            )

        return response

    def healthcheck(self) -> dict[str, Any]:
        resp = self._request("GET", "/api/health")
        return resp.json() if resp.content else {}

    def submit_job(
        self,
        *,
        camera: str,
        task: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"camera": camera, "task": task}
        if payload:
            body["payload"] = payload

        resp = self._request("POST", "/api/worker/job", json=body)
        if not resp.content:
            return {}
        return resp.json()

    def stream_url(self, *, camera: str, stream: str = "main") -> str | None:
        resp = self._request(
            "GET",
            "/api/worker/stream",
            params={"camera": camera, "stream": stream},
        )
        if not resp.content:
            return None

        data = resp.json()
        if isinstance(data, dict):
            return data.get("url") or data.get("stream_url")
        return str(data)
