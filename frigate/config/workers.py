from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator

from .base import FrigateBaseModel

__all__ = ["WorkerNodeConfig", "WorkersConfig"]


class WorkerNodeConfig(FrigateBaseModel):
    """Configuration for a single AI worker node."""

    host: str = Field(
        ...,
        title="Worker host",
        description="Hostname or IP address of the remote AI worker node.",
    )
    port: int = Field(
        default=8971,
        ge=1,
        le=65535,
        title="Worker port",
        description="Port the AI worker is listening on.",
    )
    api_url: str | None = Field(
        default=None,
        title="Worker API URL",
        description="Override the full API base URL for the worker node.",
    )

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        value = v.strip()
        if not value:
            raise ValueError("Worker host cannot be empty.")
        return value.removeprefix("http://").removeprefix("https://")

    def get_api_url(self) -> str:
        if self.api_url:
            return self.api_url.rstrip("/")

        host = self.host.strip()
        if host.startswith("http://") or host.startswith("https://"):
            return host.rstrip("/")

        return f"http://{host}:{self.port}".rstrip("/")


class WorkersConfig(FrigateBaseModel):
    """Named AI worker node registry used by cameras for remote detection and stream management."""

    nodes: dict[str, WorkerNodeConfig] = Field(
        default_factory=dict,
        title="AI worker nodes",
        description="Map of named AI worker nodes. Cameras can reference a worker by name with camera.worker.",
    )

    def get_worker(self, name: str) -> WorkerNodeConfig | None:
        return self.nodes.get(name)

    def is_configured(self) -> bool:
        return bool(self.nodes)


def _patch_camera_worker_field() -> None:
    try:
        from .camera import CameraConfig
    except Exception:
        return

    if "worker" not in CameraConfig.model_fields:
        CameraConfig.model_fields["worker"] = Field(
            default=None,
            title="AI worker node",
            description="The named AI worker node responsible for AI detection and stream management for this camera.",
        )


def _patch_frigate_config_workers_field() -> None:
    try:
        from .config import FrigateConfig
    except Exception:
        return

    if "workers" not in FrigateConfig.model_fields:
        FrigateConfig.model_fields["workers"] = Field(
            default_factory=WorkersConfig,
            title="AI worker nodes",
            description="Global registry of AI worker nodes available to cameras.",
        )


_patch_camera_worker_field()
_patch_frigate_config_workers_field()
