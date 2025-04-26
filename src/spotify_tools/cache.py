"""
Cache management for Spotify data.
"""

import json
import time
from pathlib import Path

from . import config


def get_albums_cache_path():
    """
    Get path to the comprehensive albums cache file.

    Returns:
        Path: Path to the albums cache file.
    """
    cache_dir = config.user_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "albums_cache.json"


def save_albums(albums_by_year):
    """
    Save albums to cache with year grouping.

    Args:
        albums_by_year: Dictionary of albums organized by year.
    """
    cache_path = get_albums_cache_path()
    cache_data = _create_cache_data(albums_by_year)
    _write_json_to_file(cache_path, cache_data)


def _create_cache_data(albums_by_year):
    """Create a cache data structure with timestamp."""
    return {"timestamp": time.time(), "albums_by_year": albums_by_year}


def _write_json_to_file(path, data):
    """Write JSON data to a file."""
    with Path.open(path, "w") as f:
        json.dump(data, f)


def load_albums():
    """
    Load all albums from cache if available.

    Returns:
        dict or None: Cache data if available, None otherwise.
    """
    cache_path = get_albums_cache_path()
    if not cache_path.exists():
        return None

    return _load_json_with_error_handling(cache_path)


def _load_json_with_error_handling(path):
    """Load JSON from file with error handling."""
    try:
        with Path.open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None


def calculate_cache_age(timestamp):
    """
    Calculate the age of the cache in days and hours.

    Args:
        timestamp: Timestamp of the cache.

    Returns:
        tuple: (days, hours) age of the cache.
    """
    age_seconds = time.time() - timestamp
    days = int(age_seconds / (60 * 60 * 24))
    hours = int((age_seconds % (60 * 60 * 24)) / (60 * 60))
    return days, hours


def format_cache_age_message(days, hours):
    """
    Format a message about cache age.

    Args:
        days: Days component of cache age.
        hours: Hours component of cache age.

    Returns:
        str: Formatted message about cache age.
    """
    if days > 0:
        return f"Using cached albums database ({days} days, {hours} hours old)."
    return f"Using cached albums database ({hours} hours old)."
