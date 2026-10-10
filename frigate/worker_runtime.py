from __future__ import annotations

from typing import Any

from .config import FrigateConfig


def get_camera_worker_client(config: FrigateConfig, camera_name: str):
    """Return the configured worker client for a camera when a worker is assigned."""
    camera = config.cameras.get(camera_name)
    if camera is None:
        return None

    worker_name = getattr(camera, "worker", None)
    if not worker_name:
        return None

    worker = config.workers.get_worker(worker_name)
    if worker is None:
        raise ValueError(
            f"Camera '{camera_name}' references worker '{worker_name}', but no such worker is configured."
        )

    from frigate.ai_worker import AIWorkerClient

    return AIWorkerClient.from_worker_config(worker)


def validate_camera_worker_binding(config: FrigateConfig, camera_name: str) -> None:
    """Validate a camera's worker binding at startup."""
    camera = config.cameras.get(camera_name)
    if camera is None:
        return

    worker_name = getattr(camera, "worker", None)
    if not worker_name:
        return

    if not config.workers.get_worker(worker_name):
        raise ValueError(
            f"Camera '{camera_name}' references worker '{worker_name}', but that worker is not configured under workers.nodes."
        )


def submit_camera_job(
    config: FrigateConfig,
    camera_name: str,
    task: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Submit a remote job for a camera if one is assigned; fallback to local behavior when no worker is configured."""
    client = get_camera_worker_client(config, camera_name)
    if client is None:
        return None

    from frigate.ai_worker import AIWorkerError

    try:
        return client.submit_job(camera=camera_name, task=task, payload=payload)
    except AIWorkerError:
        return None


def get_camera_stream_url(
    config: FrigateConfig,
    camera_name: str,
    stream: str = "main",
) -> str | None:
    """Fetch a stream URL from the assigned worker when configured."""
    client = get_camera_worker_client(config, camera_name)
    if client is None:
        return None

    from frigate.ai_worker import AIWorkerError

    try:
        return client.stream_url(camera=camera_name, stream=stream)
    except AIWorkerError:
        return None
