"""
Configuration management for Spotify tools.
"""

import os
import sys
import tomllib
from pathlib import Path


def user_cache_dir():
    """
    Get the user's cache directory according to platform standards.

    Returns:
        Path: User's cache directory.
    """
    if sys.platform == "win32":
        base = os.environ.get(
            "LOCALAPPDATA", Path("~").expanduser() / "AppData" / "Local"
        )
    else:
        base = os.environ.get("XDG_CACHE_HOME", Path("~/.cache").expanduser())

    return Path(base) / "spotify-tools"


def user_config_dir():
    """
    Get the user's config directory according to platform standards.

    Returns:
        Path: User's config directory.
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", Path("~").expanduser() / "AppData" / "Roaming")
    else:
        base = os.environ.get("XDG_CONFIG_HOME", Path("~/.config").expanduser())

    return Path(base) / "spotify-tools"


def load_config():
    """
    Load configuration from the config file.

    Returns:
        dict: Configuration values.

    Raises:
        FileNotFoundError: If config file is not found.
    """
    config_dir = user_config_dir()
    config_path = config_dir / "config.toml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found at {config_path}. "
            f"Please create it with Spotify API credentials."
        )

    with config_path.open("rb") as f:
        return tomllib.load(f)


def create_default_config(client_id=None, client_secret=None, redirect_uri=None):
    """
    Create default configuration file.

    Args:
        client_id: Spotify API client ID.
        client_secret: Spotify API client secret.
        redirect_uri: Spotify API redirect URI.

    Returns:
        Path: Path to the created config file.
    """
    config_dir = user_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.toml"

    if not config_path.exists():
        with config_path.open("w") as f:
            f.write("[spotify]\n")
            f.write(f'client_id = "{client_id or ""}"\n')
            f.write(f'client_secret = "{client_secret or ""}"\n')
            f.write(
                f'redirect_uri = "{redirect_uri or "http://localhost:8888/callback"}"\n'
            )

    return config_path
