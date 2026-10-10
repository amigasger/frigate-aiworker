from pydantic import Field, field_validator

from .base import FrigateBaseModel

__all__ = ["WorkerNodeConfig", "WorkersConfig"]


class WorkerNodeConfig(FrigateBaseModel):
    """Configuration for a single AI worker node.
    
    A worker node handles AI detection and stream management tasks,
    allowing you to offload processing outside the main Frigate instance.
    """

    host: str = Field(
        ...,
        title="Worker Host",
        description="Hostname or IP address of the worker node",
    )
    port: int = Field(
        default=8971,
        title="Worker Port",
        description="Port number the worker node listens on (default 8971)",
        ge=1,
        le=65535,
    )
    api_url: str | None = Field(
        default=None,
        title="Override API URL",
        description="Optional override for the complete API URL (e.g., http://worker.local:8971). If not set, will be constructed from host and port.",
    )

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("host cannot be empty")
        return v.strip()

    def get_api_url(self) -> str:
        """Return the API URL for this worker node."""
        if self.api_url:
            return self.api_url.rstrip("/")
        return f"http://{self.host}:{self.port}"


class WorkersConfig(FrigateBaseModel):
    """Configuration for all AI worker nodes.
    
    Define named worker nodes that handle AI detection and streaming tasks.
    Cameras can then target specific workers for processing.
    """

    nodes: dict[str, WorkerNodeConfig] = Field(
        default_factory=dict,
        title="Worker Nodes",
        description="Dictionary of named worker nodes. Example: { 'ai-gpu-1': { 'host': '10.0.0.21', 'port': 8971 } }",
    )

    @field_validator("nodes")
    @classmethod
    def validate_node_names(cls, v: dict[str, WorkerNodeConfig]) -> dict[str, WorkerNodeConfig]:
        """Validate that worker node names are valid identifiers."""
        for name in v.keys():
            if not name or not name.replace("-", "").replace("_", "").isalnum():
                raise ValueError(
                    f"Invalid worker node name '{name}'. Must be alphanumeric with hyphens/underscores."
                )
        return v

    def get_worker(self, name: str) -> WorkerNodeConfig | None:
        """Get a worker node by name."""
        return self.nodes.get(name)

    def is_configured(self) -> bool:
        """Check if any worker nodes are configured."""
        return len(self.nodes) > 0
