import os
from pathlib import Path

import tomllib


def user_cache_dir():
    config = (
        os.environ.get("LOCALAPPDATA")
        or os.environ.get("XDG_CAHE_HOME")
        or Path("~/.cache").expanduser()
    )
    return Path(config) / "spotify-tools"


def user_config_dir():
    config = (
        os.environ.get("APPDATA")
        or os.environ.get("XDG_CONFIG_HOME")
        or Path("~/.config").expanduser()
    )
    return Path(config) / "spotify-tools"


def load_config():
    config_dir = user_config_dir()
    with Path(config_dir / "config.toml").open("rb") as f:
        return tomllib.load(f)
