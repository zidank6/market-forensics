"""Configuration loading utilities."""

import json
from pathlib import Path
from typing import Any


def load_config(config_path: str | Path) -> dict[str, Any]:
    """Load configuration from a JSON file.

    Args:
        config_path: Path to the configuration file.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file does not exist.
        json.JSONDecodeError: If config file is not valid JSON.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        return json.load(f)


def get_default_config_path() -> Path:
    """Get the path to the default configuration file."""
    return Path(__file__).parent.parent.parent.parent / "config" / "default.json"
