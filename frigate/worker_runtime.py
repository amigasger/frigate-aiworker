from __future__ import annotations

from typing import Any

from .ai_worker import AIWorkerClient, AIWorkerError


def get_camera_worker_client(config: Any, camera_name: str) -> AIWorkerClient | None:
    """Return a configured client for a camera, or None if local execution is required."""
    camera = config.cameras.get(camera_name)
    if camera is None:
        return None

    worker_name = getattr(camera, "worker", None)
    if not worker_name:
        return None

    workers = getattr(config, "workers", None)
    if workers is None:
        raise ValueError(
            f"Camera '{camera_name}' references worker '{worker_name}', but no workers config was loaded."
        )

    worker = workers.get_worker(worker_name)
    if worker is None:
        raise ValueError(
            f"Camera '{camera_name}' references worker '{worker_name}', but no such worker is configured."
        )

    return AIWorkerClient.from_worker_config(worker)


def validate_camera_worker_binding(config: Any, camera_name: str) -> None:
    """Validate that camera worker references are resolvable at startup."""
    camera = config.cameras.get(camera_name)
    if camera is None:
        return

    worker_name = getattr(camera, "worker", None)
    if not worker_name:
        return

    workers = getattr(config, "workers", None)
    if workers is None:
        raise ValueError(
            f"Camera '{camera_name}' references worker '{worker_name}', but workers are not configured."
        )

    if workers.get_worker(worker_name) is None:
        raise ValueError(
            f"Camera '{camera_name}' references worker '{worker_name}', but it is not configured under workers.nodes."
        )


def submit_camera_job(
    config: Any,
    camera_name: str,
    task: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Submit a job to a remote worker if configured; otherwise return None.

    This keeps local execution as the default behavior and only performs a remote
    dispatch when a worker is assigned to the camera.
    """
    client = get_camera_worker_client(config, camera_name)
    if client is None:
        return None

    try:
        return client.submit_job(camera=camera_name, task=task, payload=payload)
    except AIWorkerError:
        return None


def get_camera_stream_url(config: Any, camera_name: str, stream: str = "main") -> str | None:
    """Resolve a stream URL via the remote worker when configured."""
    client = get_camera_worker_client(config, camera_name)
    if client is None:
        return None

    try:
        return client.stream_url(camera=camera_name, stream=stream)
    except AIWorkerError:
        return None
