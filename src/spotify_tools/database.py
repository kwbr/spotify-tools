"""
SQLite database operations for efficient album storage and retrieval.
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from .types import Album


def get_db_path() -> Path:
    """
    Get the path to the SQLite database file.

    Returns:
        Path: Path to the SQLite database file.
    """
    from . import config

    cache_dir = config.user_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "albums.db"


def initialize_db(db_path: Optional[Path] = None) -> None:
    """
    Initialize the SQLite database with the necessary schema.

    Args:
        db_path: Path to the database file. If None, uses default path.
    """
    db_path = db_path or get_db_path()

    with sqlite3.connect(db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uri TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            artists_json TEXT NOT NULL,
            year INTEGER NOT NULL,
            added_at TEXT NOT NULL
        )
        """)

        # Create index on year for efficient filtering
        conn.execute("CREATE INDEX IF NOT EXISTS idx_albums_year ON albums(year)")

        # Set creation timestamp
        set_metadata(conn, "created_at", str(time.time()))


def set_metadata(conn: sqlite3.Connection, key: str, value: str) -> None:
    """
    Set a metadata key-value pair in the database.

    Args:
        conn: SQLite connection.
        key: Metadata key.
        value: Metadata value.
    """
    conn.execute(
        "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", (key, value)
    )


def get_metadata(
    conn: sqlite3.Connection, key: str, default: Optional[str] = None
) -> Optional[str]:
    """
    Get a metadata value from the database.

    Args:
        conn: SQLite connection.
        key: Metadata key.
        default: Default value if key not found.

    Returns:
        str or None: The metadata value.
    """
    cursor = conn.execute("SELECT value FROM metadata WHERE key = ?", (key,))
    result = cursor.fetchone()
    return result[0] if result else default


def save_albums(albums_by_year: Dict[str, List[Dict[str, Any]]]) -> None:
    """
    Save albums to the SQLite database.

    Args:
        albums_by_year: Dictionary of albums organized by year.
    """
    db_path = get_db_path()

    # Initialize database (creates tables if not exists)
    initialize_db(db_path)

    with sqlite3.connect(db_path) as conn:
        # Clear existing data
        conn.execute("DELETE FROM albums")

        # Insert all albums
        for year_str, albums in albums_by_year.items():
            for album_dict in albums:
                conn.execute(
                    """
                    INSERT INTO albums (uri, name, artists_json, year, added_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        album_dict["uri"],
                        album_dict["name"],
                        json.dumps(album_dict["artists"]),
                        int(year_str),
                        album_dict["added_at"],
                    ),
                )

        # Set updated timestamp
        set_metadata(conn, "updated_at", str(time.time()))

        # Store total count for quick access
        total_count = conn.execute("SELECT COUNT(*) FROM albums").fetchone()[0]
        set_metadata(conn, "total_count", str(total_count))


def get_db_connection() -> sqlite3.Connection:
    """
    Get a connection to the SQLite database.

    Returns:
        sqlite3.Connection: Database connection.
    """
    db_path = get_db_path()

    # Check if database exists, initialize if not
    if not db_path.exists():
        initialize_db(db_path)

    return sqlite3.connect(db_path)


def database_exists() -> bool:
    """
    Check if the album database exists.

    Returns:
        bool: True if database exists, False otherwise.
    """
    db_path = get_db_path()
    if not db_path.exists():
        return False

    # Verify it's a valid SQLite database with our schema
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='albums'"
            )
            return cursor.fetchone() is not None
    except sqlite3.Error:
        return False


def get_album_count() -> int:
    """
    Get the total number of albums in the database.

    Returns:
        int: Total album count.
    """
    if not database_exists():
        return 0

    with get_db_connection() as conn:
        # Try to get from metadata first for speed
        count_str = get_metadata(conn, "total_count")
        if count_str:
            return int(count_str)

        # Fall back to counting
        cursor = conn.execute("SELECT COUNT(*) FROM albums")
        return cursor.fetchone()[0]


def get_albums_by_year(year: int) -> List[Album]:
    """
    Get all albums for a specific year.

    Args:
        year: The year to filter by.

    Returns:
        List[Album]: List of Album objects.
    """
    if not database_exists():
        return []

    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT uri, name, artists_json, added_at FROM albums WHERE year = ?",
            (year,),
        )

        albums = []
        for row in cursor.fetchall():
            uri, name, artists_json, added_at = row
            albums.append(
                Album(
                    uri=uri,
                    name=name,
                    artists=json.loads(artists_json),
                    added_at=added_at,
                )
            )

        return albums


def get_random_albums(count: int, year: Optional[int] = None) -> List[Album]:
    """
    Get random albums, optionally filtered by year.

    Args:
        count: Number of albums to return.
        year: Optional year filter.

    Returns:
        List[Album]: List of random Album objects.
    """
    if not database_exists():
        return []

    with get_db_connection() as conn:
        query = "SELECT uri, name, artists_json, added_at FROM albums"
        params = []

        if year is not None:
            query += " WHERE year = ?"
            params.append(year)

        # Add random selection and limit
        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(count)

        cursor = conn.execute(query, params)

        albums = []
        for row in cursor.fetchall():
            uri, name, artists_json, added_at = row
            albums.append(
                Album(
                    uri=uri,
                    name=name,
                    artists=json.loads(artists_json),
                    added_at=added_at,
                )
            )

        return albums


def get_years() -> List[int]:
    """
    Get a list of all years in the database.

    Returns:
        List[int]: List of years.
    """
    if not database_exists():
        return []

    with get_db_connection() as conn:
        cursor = conn.execute("SELECT DISTINCT year FROM albums ORDER BY year")
        return [row[0] for row in cursor.fetchall()]


def get_album_count_by_year() -> Dict[int, int]:
    """
    Get album counts grouped by year.

    Returns:
        Dict[int, int]: Dictionary with year as key and count as value.
    """
    if not database_exists():
        return {}

    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT year, COUNT(*) FROM albums GROUP BY year ORDER BY year"
        )
        return {row[0]: row[1] for row in cursor.fetchall()}


def calculate_cache_age() -> Tuple[int, int]:
    """
    Calculate the age of the cache in days and hours.

    Returns:
        tuple: (days, hours) age of the cache.
    """
    if not database_exists():
        return (0, 0)

    with get_db_connection() as conn:
        timestamp_str = get_metadata(conn, "updated_at")
        if not timestamp_str:
            return (0, 0)

        timestamp = float(timestamp_str)
        age_seconds = time.time() - timestamp
        days = int(age_seconds / (60 * 60 * 24))
        hours = int((age_seconds % (60 * 60 * 24)) / (60 * 60))
        return (days, hours)
