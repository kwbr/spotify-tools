"""
Cache management for Spotify data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from . import database


def save_albums(
    albums_by_year: dict[str, list[dict[str, Any]]], db_path: Path | None = None
) -> None:
    """
    Save albums to SQLite database with year grouping.

    Args:
        albums_by_year: Dictionary of albums organized by year.
        db_path: Optional database path for testing.
    """
    # Forward to SQLite implementation
    database.save_albums(albums_by_year, db_path=db_path)


def load_albums() -> dict[str, Any] | None:
    """
    Load album data from cache if available.

    This function uses the SQLite database for storage.
    Returns None if the database doesn't exist to trigger cache creation.

    Returns:
        dict or None: Cache data if available, None otherwise.
    """
    # Check if database exists
    if not database.database_exists():
        return None

    # Get album counts by year
    album_counts = database.get_album_count_by_year()

    # Return just the album counts - no need for empty placeholder structures
    return {"album_counts": album_counts}


def calculate_cache_age() -> tuple[int, int]:
    """
    Calculate the age of the cache in days and hours.

    Returns:
        tuple: (days, hours) age of the cache.
    """
    # Forward to database implementation
    return database.calculate_cache_age()


def format_cache_age_message(days: int, hours: int) -> str:
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
