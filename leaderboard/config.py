"""Configuration management for storing auth tokens."""

import json
from pathlib import Path
from typing import Optional


CONFIG_DIR = Path.home() / ".leaderboard"
CONFIG_FILE = CONFIG_DIR / "config.json"


def ensure_config_dir():
    """Ensure configuration directory exists."""
    CONFIG_DIR.mkdir(exist_ok=True)


def save_token(token: str, username: str):
    """Save authentication token and user info."""
    ensure_config_dir()
    config = {
        "access_token": token,
        "username": username
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def load_token() -> Optional[str]:
    """Load authentication token."""
    if not CONFIG_FILE.exists():
        return None
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return config.get("access_token")
    except:
        return None


def load_config() -> Optional[dict]:
    """Load full configuration."""
    if not CONFIG_FILE.exists():
        return None
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return None


def clear_token():
    """Clear authentication token."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()

