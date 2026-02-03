"""
Minimal configuration loader for vadocs.

Loads configuration from YAML files. This is a PoC implementation -
future versions will support pyproject.toml [tool.vadocs] sections.

Usage:
    from vadocs.config import load_config

    config = load_config(Path("adr_config.yaml"))
    validator = AdrValidator()
    errors = validator.validate(doc, config)
"""

from pathlib import Path

import yaml


def load_config(config_path: Path) -> dict:
    """Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        yaml.YAMLError: If config file has invalid YAML.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    content = config_path.read_text(encoding="utf-8")
    return yaml.safe_load(content) or {}
