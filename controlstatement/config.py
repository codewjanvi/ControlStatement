"""Configuration management for ControlStatement with strict privacy enforcement."""

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional


@dataclass
class AppConfig:
    """Application settings with local privacy validation."""

    local_model_endpoint: str = "http://localhost:11434"
    local_model_name: str = "gemma4:e2b"
    default_currency: str = "INR"
    request_timeout: int = 90
    log_level: str = "INFO"

    def __post_init__(self):
        # Strict privacy check: local inference only
        parsed = urlparse(self.local_model_endpoint)
        hostname = (parsed.hostname or "").lower()
        allowed_local_hosts = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
        if hostname not in allowed_local_hosts:
            raise ValueError(
                f"Privacy Violation Error: Model endpoint '{self.local_model_endpoint}' is not on localhost. "
                f"ControlStatement strictly forbids sending financial data to external hosts."
            )


def load_env_file(env_path: Optional[Path] = None) -> dict:
    """Parse key=value pairs from a local .env file without external dependencies."""
    if env_path is None:
        env_path = Path.cwd() / ".env"

    if not env_path.is_file():
        return {}

    env_vars = {}
    with open(env_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val:
                env_vars[key] = val
    return env_vars


def get_config(env_path: Optional[Path] = None) -> AppConfig:
    """Load configuration from environment variables and local .env file."""
    file_vars = load_env_file(env_path)

    def get_var(key: str, default: str) -> str:
        return os.environ.get(key) or file_vars.get(key) or default

    endpoint = get_var("LOCAL_MODEL_ENDPOINT", "http://localhost:11434")
    model_name = get_var("LOCAL_MODEL_NAME", "gemma4:e2b")
    currency = get_var("DEFAULT_CURRENCY", "INR")
    log_level = get_var("LOG_LEVEL", "INFO")

    return AppConfig(
        local_model_endpoint=endpoint,
        local_model_name=model_name,
        default_currency=currency,
        log_level=log_level,
    )
