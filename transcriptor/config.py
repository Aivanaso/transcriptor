"""Configuration management for Transcriptor."""

import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "model_size": "small",
    "language": "es",
    "hotkey": "Key.f12",
    "auto_paste": True,
    "notifications": True,
    "compute_type": "int8",
    "device": "cpu",
    "audio_device": None,
    "paste_shortcut": "auto",
}


def get_config_dir() -> Path:
    """Return the configuration directory, creating it if needed."""
    config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "transcriptor"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    """Return the path to the config file."""
    return get_config_dir() / "config.json"


def load_config() -> dict:
    """Load config from disk. Creates default config if file doesn't exist."""
    path = get_config_path()
    if path.exists():
        with open(path, "r") as f:
            stored = json.load(f)
        # Merge with defaults so new keys are always present
        config = {**DEFAULT_CONFIG, **stored}
    else:
        config = DEFAULT_CONFIG.copy()
        save_config(config)
    return config


def save_config(config: dict) -> None:
    """Write config to disk."""
    path = get_config_path()
    with open(path, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
