from __future__ import annotations

from typing import Any

import httpx


class AIWorkerError(RuntimeError):
    """Raised when a remote AI worker request fails."""


class AIWorkerClient:
    """Minimal HTTP client for a remote Frigate AI worker node.

    A worker node is treated as a generic execution endpoint for AI detection and
    stream management. The main Frigate instance can offload work by naming a
    remote worker in the camera config.
    """

    def __init__(self, api_url: str, *, timeout: float = 10.0) -> None:
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout

    @classmethod
    def from_worker_config(cls, worker_config: Any) -> "AIWorkerClient":
        return cls(worker_config.get_api_url())

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{self.api_url}{path}"
        request_kwargs = {"timeout": self.timeout, **kwargs}
        try:
            return httpx.request(method, url, **request_kwargs)
        except httpx.HTTPError as exc:  # pragma: no cover - defensive
            raise AIWorkerError(f"Failed to contact AI worker at {url}: {exc}") from exc

    def healthcheck(self) -> dict[str, Any]:
        response = self._request("GET", "/api/health")
        if response.status_code >= 400:
            raise AIWorkerError(
                f"AI worker healthcheck failed with status {response.status_code}: {response.text}"
            )
        return response.json()

    def submit_job(
        self,
        *,
        camera: str,
        task: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._request(
            "POST",
            "/api/worker/job",
            json={"camera": camera, "task": task, "payload": payload or {}},
        )
        if response.status_code >= 400:
            raise AIWorkerError(
                f"AI worker job submission failed with status {response.status_code}: {response.text}"
            )
        try:
            return response.json()
        except ValueError as exc:
            raise AIWorkerError("AI worker returned an invalid JSON response") from exc

    def stream_url(self, *, camera: str, stream: str = "main") -> str:
        response = self._request(
            "GET",
            "/api/worker/stream",
            params={"camera": camera, "stream": stream},
        )
        if response.status_code >= 400:
            raise AIWorkerError(
                f"AI worker stream request failed with status {response.status_code}: {response.text}"
            )
        data = response.json()
        return data.get("url")
