import tomllib
import os
from pathlib import Path

def user_config_dir():
    config = os.environ.get('APPDATA') or os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
    path = Path(config) / "spotify-tools"
    return path


def load_config():
    config_dir = user_config_dir()
    with open(config_dir / "config.toml", "rb") as f:
        return tomllib.load(f)
