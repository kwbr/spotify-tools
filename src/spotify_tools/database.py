"""
SQLite database operations for efficient album storage and retrieval.
"""

import contextlib
import json
import sqlite3
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from . import perf
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


def initialize_db(db_path: Path | None = None) -> None:
    """
    Initialize the SQLite database with the necessary schema.

    Args:
        db_path: Path to the database file. If None, uses default path.
    """
    db_path = db_path or get_db_path()

    conn = sqlite3.connect(db_path)
    try:
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

        # Create play_history table for tracking listening history
        conn.execute("""
        CREATE TABLE IF NOT EXISTS play_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_uri TEXT NOT NULL,
            track_name TEXT NOT NULL,
            artists_json TEXT NOT NULL,
            album_uri TEXT NOT NULL,
            album_name TEXT NOT NULL,
            album_artists_json TEXT,
            played_at TEXT NOT NULL,
            UNIQUE(track_uri, played_at)
        )
        """)

        # Create indexes for efficient querying
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_play_history_played_at "
            "ON play_history(played_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_play_history_album_uri "
            "ON play_history(album_uri)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_play_history_track_uri "
            "ON play_history(track_uri)"
        )

        # Set creation timestamp
        set_metadata(conn, "created_at", str(time.time()))
        conn.commit()
    finally:
        conn.close()


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
    conn: sqlite3.Connection, key: str, default: str | None = None
) -> str | None:
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


def save_albums(
    albums_by_year: dict[str, list[dict[str, Any]]], db_path: Path | None = None
) -> None:
    """
    Save albums to the SQLite database.

    Args:
        albums_by_year: Dictionary of albums organized by year.
        db_path: Path to the database file. If None, uses default path.
    """
    db_path = db_path or get_db_path()

    # Initialize database (creates tables if not exists)
    initialize_db(db_path)

    conn = sqlite3.connect(db_path)
    try:
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
        conn.commit()
    finally:
        conn.close()


@contextlib.contextmanager
def get_db_connection(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """
    Get a connection to the SQLite database that properly closes on exit.

    Args:
        db_path: Path to the database file. If None, uses default path.

    Yields:
        sqlite3.Connection: Database connection (will be closed on exit).
    """
    db_path = db_path or get_db_path()

    # Check if database exists, initialize if not
    if not db_path.exists():
        initialize_db(db_path)

    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def database_exists(db_path: Path | None = None) -> bool:
    """
    Check if the album database exists.

    Args:
        db_path: Path to the database file. If None, uses default path.

    Returns:
        bool: True if database exists, False otherwise.
    """
    db_path = db_path or get_db_path()
    if not db_path.exists():
        return False

    # Verify it's a valid SQLite database with our schema
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='albums'"
        )
        return cursor.fetchone() is not None
    except sqlite3.Error:
        return False
    finally:
        if conn:
            conn.close()


def get_album_count(db_path: Path | None = None) -> int:
    """
    Get the total number of albums in the database.

    Args:
        db_path: Path to the database file. If None, uses default path.

    Returns:
        int: Total album count.
    """
    if not database_exists(db_path):
        return 0

    with get_db_connection(db_path) as conn:
        # Try to get from metadata first for speed
        count_str = get_metadata(conn, "total_count")
        if count_str:
            return int(count_str)

        # Fall back to counting
        cursor = conn.execute("SELECT COUNT(*) FROM albums")
        return cursor.fetchone()[0]


def get_albums_by_year(year: int | None = None, db_path: Path | None = None) -> list[Album]:
    """
    Get all albums, optionally filtered by a specific year.

    Args:
        year: Optional year to filter by. If None, returns all albums.
        db_path: Path to the database file. If None, uses default path.

    Returns:
        List[Album]: List of Album objects.
    """
    if not database_exists(db_path):
        return []

    with get_db_connection(db_path) as conn:
        if year is not None:
            cursor = conn.execute(
                "SELECT uri, name, artists_json, added_at FROM albums WHERE year = ?",
                (year,),
            )
        else:
            cursor = conn.execute(
                "SELECT uri, name, artists_json, added_at FROM albums"
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


def get_random_albums(
    count: int, year: int | None = None, verbose: bool = False, db_path: Path | None = None
) -> list[Album]:
    """
    Get random albums, optionally filtered by year.

    Args:
        count: Number of albums to return.
        year: Optional year filter.
        verbose: If True, fetch all album data. If False (default),
            optimize for URI-only.
        db_path: Path to the database file. If None, uses default path.

    Returns:
        List[Album]: List of random Album objects.
    """
    if not database_exists(db_path):
        return []

    with get_db_connection(db_path) as conn:
        params = []
        where_clause = ""

        if year is not None:
            where_clause = "WHERE year = ?"
            params.append(year)

        # Only fetch URI if not in verbose mode (huge performance optimization)
        if not verbose:
            # Simplified query that only retrieves URIs
            query = f"""SELECT uri FROM albums
                      {where_clause} ORDER BY RANDOM() LIMIT ?"""
            params.append(count)

            with perf.measure_time("Execute optimized URI-only query"):
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

            albums = []
            for row in rows:
                albums.append(Album.from_uri_only(row[0]))

            return albums
        # Full query with all fields when in verbose mode
        query = f"""
            WITH album_data AS (
                SELECT
                    uri,
                    name,
                    artists_json,
                    added_at
                FROM albums
                {where_clause}
                ORDER BY RANDOM()
                LIMIT ?
            )
            SELECT
                uri,
                name,
                json_extract(artists_json, '$') AS artists_array,
                added_at
            FROM album_data
            """

        params.append(count)

        with perf.measure_time("Execute full query with JSON"):
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        albums = []
        with perf.measure_time("Process query results"):
            for row in rows:
                uri, name, artists_array, added_at = row
                # SQLite returns JSON as a string that's already parsed
                # by the json_extract function
                albums.append(
                    Album(
                        uri=uri,
                        name=name,
                        artists=json.loads(
                            artists_array
                        ),  # Still need to parse the extracted JSON array
                        added_at=added_at,
                    )
                )

        return albums


def get_years(db_path: Path | None = None) -> list[int]:
    """
    Get a list of all years in the database.

    Args:
        db_path: Path to the database file. If None, uses default path.

    Returns:
        List[int]: List of years.
    """
    if not database_exists(db_path):
        return []

    with get_db_connection(db_path) as conn:
        cursor = conn.execute("SELECT DISTINCT year FROM albums ORDER BY year")
        return [row[0] for row in cursor.fetchall()]


def get_album_count_by_year(db_path: Path | None = None) -> dict[int, int]:
    """
    Get album counts grouped by year.

    Args:
        db_path: Path to the database file. If None, uses default path.

    Returns:
        Dict[int, int]: Dictionary with year as key and count as value.
    """
    if not database_exists(db_path):
        return {}

    with get_db_connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT year, COUNT(*) FROM albums GROUP BY year ORDER BY year"
        )
        return {row[0]: row[1] for row in cursor.fetchall()}


def calculate_cache_age() -> tuple[int, int]:
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


def save_play_history(plays: list[dict[str, Any]], db_path: Path | None = None) -> int:
    """
    Save play history entries to the database.

    Args:
        plays: List of play history dictionaries with keys:
            track_uri, track_name, artists_json, album_uri,
            album_name, played_at
        db_path: Path to the database file. If None, uses default path.

    Returns:
        int: Number of new entries added (excludes duplicates).
    """
    db_path = db_path or get_db_path()

    if not database_exists(db_path):
        initialize_db(db_path)

    # Ensure play_history table exists (for existing databases)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS play_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_uri TEXT NOT NULL,
            track_name TEXT NOT NULL,
            artists_json TEXT NOT NULL,
            album_uri TEXT NOT NULL,
            album_name TEXT NOT NULL,
            album_artists_json TEXT,
            played_at TEXT NOT NULL,
            UNIQUE(track_uri, played_at)
        )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_play_history_played_at "
            "ON play_history(played_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_play_history_album_uri "
            "ON play_history(album_uri)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_play_history_track_uri "
            "ON play_history(track_uri)"
        )

        # Add album_artists_json column if it doesn't exist (migration)
        with contextlib.suppress(sqlite3.OperationalError):
            conn.execute("ALTER TABLE play_history ADD COLUMN album_artists_json TEXT")
        conn.commit()
    finally:
        conn.close()

    added_count = 0
    with get_db_connection(db_path) as conn:
        for play in plays:
            try:
                conn.execute(
                    """
                    INSERT INTO play_history
                    (track_uri, track_name, artists_json, album_uri,
                     album_name, album_artists_json, played_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        play["track_uri"],
                        play["track_name"],
                        play["artists_json"],
                        play["album_uri"],
                        play["album_name"],
                        play.get("album_artists_json"),
                        play["played_at"],
                    ),
                )
                added_count += 1
            except sqlite3.IntegrityError:
                # Duplicate entry (same track_uri and played_at), skip
                pass

    return added_count


def get_last_sync_time() -> str | None:
    """
    Get the timestamp of the last play history sync.

    Returns:
        str | None: ISO timestamp of last sync, or None if never synced.
    """
    if not database_exists():
        return None

    with get_db_connection() as conn:
        return get_metadata(conn, "last_play_history_sync")


def set_last_sync_time(timestamp: str) -> None:
    """
    Set the timestamp of the last play history sync.

    Args:
        timestamp: ISO timestamp string.
    """
    if not database_exists():
        initialize_db()

    with get_db_connection() as conn:
        set_metadata(conn, "last_play_history_sync", timestamp)


def get_play_count_by_album(db_path: Path | None = None) -> dict[str, dict[str, Any]]:
    """
    Get play counts grouped by album.

    Args:
        db_path: Path to the database file. If None, uses default path.

    Returns:
        dict: Dictionary with album_uri as key and dict with album info:
            {album_uri: {name, artists, play_count, last_played}}
    """
    if not database_exists(db_path):
        return {}

    with get_db_connection(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT album_uri, album_name, album_artists_json, COUNT(*) as play_count,
                   MAX(played_at) as last_played
            FROM play_history
            GROUP BY album_uri, album_name, album_artists_json
            ORDER BY play_count DESC
            """
        )

        return {
            row[0]: {
                "name": row[1],
                "artists": json.loads(row[2]) if row[2] else [],
                "play_count": row[3],
                "last_played": row[4],
            }
            for row in cursor.fetchall()
        }


def get_play_count_by_track(db_path: Path | None = None) -> dict[str, dict[str, Any]]:
    """
    Get play counts grouped by track.

    Args:
        db_path: Path to the database file. If None, uses default path.

    Returns:
        dict: Dictionary with track_uri as key and dict with track info:
            {track_uri: {name, artists, album_name, play_count, last_played}}
    """
    if not database_exists(db_path):
        return {}

    with get_db_connection(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT track_uri, track_name, artists_json, album_name,
                   COUNT(*) as play_count, MAX(played_at) as last_played
            FROM play_history
            GROUP BY track_uri, track_name, artists_json, album_name
            ORDER BY play_count DESC
            """
        )

        return {
            row[0]: {
                "name": row[1],
                "artists": json.loads(row[2]),
                "album_name": row[3],
                "play_count": row[4],
                "last_played": row[5],
            }
            for row in cursor.fetchall()
        }


def get_total_play_count(db_path: Path | None = None) -> int:
    """
    Get the total number of plays recorded.

    Args:
        db_path: Path to the database file. If None, uses default path.

    Returns:
        int: Total play count.
    """
    if not database_exists(db_path):
        return 0

    with get_db_connection(db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM play_history")
        return cursor.fetchone()[0]


def get_play_count_by_artist(db_path: Path | None = None) -> dict[str, dict[str, Any]]:
    """
    Get play counts grouped by artist.

    Args:
        db_path: Path to the database file. If None, uses default path.

    Returns:
        dict: Dictionary with artist name as key and dict with artist info:
            {artist: {play_count, last_played, album_count, track_count}}
    """
    if not database_exists(db_path):
        return {}

    with get_db_connection(db_path) as conn:
        # Flatten artists from JSON arrays and aggregate
        cursor = conn.execute(
            """
            WITH artist_plays AS (
                SELECT
                    json_each.value as artist,
                    played_at,
                    album_uri,
                    track_uri
                FROM play_history, json_each(play_history.artists_json)
            )
            SELECT
                artist,
                COUNT(*) as play_count,
                MAX(played_at) as last_played,
                COUNT(DISTINCT album_uri) as album_count,
                COUNT(DISTINCT track_uri) as track_count
            FROM artist_plays
            GROUP BY artist
            ORDER BY play_count DESC
            """
        )

        return {
            row[0]: {
                "play_count": row[1],
                "last_played": row[2],
                "album_count": row[3],
                "track_count": row[4],
            }
            for row in cursor.fetchall()
        }


def get_plays_in_time_range(
    since: str | None = None, until: str | None = None
) -> list[dict[str, Any]]:
    """
    Get plays within a specific time range.

    Args:
        since: ISO timestamp for start of range (inclusive).
        until: ISO timestamp for end of range (inclusive).

    Returns:
        list: List of play dictionaries with full details.
    """
    if not database_exists():
        return []

    with get_db_connection() as conn:
        conditions = []
        params = []

        if since:
            conditions.append("played_at >= ?")
            params.append(since)
        if until:
            conditions.append("played_at <= ?")
            params.append(until)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        cursor = conn.execute(
            f"""
            SELECT track_uri, track_name, artists_json, album_uri,
                   album_name, album_artists_json, played_at
            FROM play_history
            {where_clause}
            ORDER BY played_at DESC
            """,
            params,
        )

        return [
            {
                "track_uri": row[0],
                "track_name": row[1],
                "artists": json.loads(row[2]),
                "album_uri": row[3],
                "album_name": row[4],
                "album_artists": json.loads(row[5]) if row[5] else [],
                "played_at": row[6],
            }
            for row in cursor.fetchall()
        ]


def get_play_trends_by_day(days: int = 30) -> dict[str, int]:
    """
    Get play counts grouped by day for the last N days.

    Args:
        days: Number of days to include.

    Returns:
        dict: Dictionary with date string (YYYY-MM-DD) as key and play count.
    """
    if not database_exists():
        return {}

    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT DATE(played_at) as play_date, COUNT(*) as play_count
            FROM play_history
            WHERE played_at >= datetime('now', ? || ' days')
            GROUP BY play_date
            ORDER BY play_date
            """,
            (f"-{days}",),
        )

        return {row[0]: row[1] for row in cursor.fetchall()}


def get_recently_played(limit: int = 50, db_path: Path | None = None) -> list[dict[str, Any]]:
    """
    Get recently played tracks with full details.

    Args:
        limit: Number of recent plays to return.
        db_path: Path to the database file. If None, uses default path.

    Returns:
        list: List of play dictionaries with full details.
    """
    if not database_exists(db_path):
        return []

    with get_db_connection(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT track_uri, track_name, artists_json, album_uri,
                   album_name, album_artists_json, played_at
            FROM play_history
            ORDER BY played_at DESC
            LIMIT ?
            """,
            (limit,),
        )

        return [
            {
                "track_uri": row[0],
                "track_name": row[1],
                "artists": json.loads(row[2]),
                "album_uri": row[3],
                "album_name": row[4],
                "album_artists": json.loads(row[5]) if row[5] else [],
                "played_at": row[6],
            }
            for row in cursor.fetchall()
        ]


def get_plays_by_hour() -> dict[int, int]:
    """
    Get play counts grouped by hour of day (0-23).

    Returns:
        dict: Dictionary with hour (0-23) as key and play count.
    """
    if not database_exists():
        return {}

    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT CAST(strftime('%H', played_at) AS INTEGER) as hour,
                   COUNT(*) as play_count
            FROM play_history
            GROUP BY hour
            ORDER BY hour
            """
        )

        return {row[0]: row[1] for row in cursor.fetchall()}


def get_plays_by_day_of_week() -> dict[int, int]:
    """
    Get play counts grouped by day of week (0=Sunday, 6=Saturday).

    Returns:
        dict: Dictionary with day number as key and play count.
    """
    if not database_exists():
        return {}

    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT CAST(strftime('%w', played_at) AS INTEGER) as day_of_week,
                   COUNT(*) as play_count
            FROM play_history
            GROUP BY day_of_week
            ORDER BY day_of_week
            """
        )

        return {row[0]: row[1] for row in cursor.fetchall()}


def get_unique_artist_count() -> int:
    """
    Get the count of unique artists played.

    Returns:
        int: Number of unique artists.
    """
    if not database_exists():
        return 0

    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT COUNT(DISTINCT json_each.value)
            FROM play_history, json_each(play_history.artists_json)
            """
        )
        return cursor.fetchone()[0]


def get_syncs_dir() -> Path:
    """
    Get the directory for storing raw sync files.

    Returns:
        Path: Path to the syncs directory.
    """
    from . import config

    syncs_dir = config.user_cache_dir() / "syncs"
    syncs_dir.mkdir(parents=True, exist_ok=True)
    return syncs_dir


def save_raw_sync(plays: list[dict[str, Any]], timestamp: str) -> Path:
    """
    Save raw sync data to a JSON file.

    Args:
        plays: List of play dictionaries.
        timestamp: ISO timestamp for the sync.

    Returns:
        Path: Path to the saved file.
    """
    import socket

    syncs_dir = get_syncs_dir()
    hostname = socket.gethostname().replace("/", "-").replace("\\", "-")
    filename = f"{timestamp.replace(':', '-')}_{hostname}.json"
    filepath = syncs_dir / filename

    with filepath.open("w") as f:
        json.dump({"timestamp": timestamp, "plays": plays}, f, indent=2)

    return filepath


def load_all_syncs() -> list[dict[str, Any]]:
    """
    Load all raw sync files and return all plays.

    Returns:
        list: All plays from all sync files.
    """
    syncs_dir = get_syncs_dir()
    all_plays = []

    for filepath in sorted(syncs_dir.glob("*.json")):
        try:
            with filepath.open() as f:
                data = json.load(f)
                all_plays.extend(data.get("plays", []))
        except (json.JSONDecodeError, KeyError):
            # Skip malformed files
            continue

    return all_plays


def rebuild_history_from_syncs() -> tuple[int, int]:
    """
    Rebuild play_history table from all raw sync files.

    Deduplicates by (track_uri, played_at) and rebuilds the database.

    Returns:
        tuple: (total_plays_loaded, unique_plays_added)
    """
    all_plays = load_all_syncs()
    if not all_plays:
        return (0, 0)

    # Deduplicate by (track_uri, played_at)
    seen = set()
    unique_plays = []
    for play in all_plays:
        key = (play["track_uri"], play["played_at"])
        if key not in seen:
            seen.add(key)
            unique_plays.append(play)

    # Clear existing play_history
    if not database_exists():
        initialize_db()

    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM play_history")

        # Insert all unique plays
        for play in unique_plays:
            conn.execute(
                """
                INSERT INTO play_history
                (track_uri, track_name, artists_json, album_uri,
                 album_name, album_artists_json, played_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    play["track_uri"],
                    play["track_name"],
                    play["artists_json"],
                    play["album_uri"],
                    play["album_name"],
                    play.get("album_artists_json"),
                    play["played_at"],
                ),
            )

        # Update last sync time to most recent play
        if unique_plays:
            latest = max(unique_plays, key=lambda p: p["played_at"])
            set_metadata(conn, "last_play_history_sync", latest["played_at"])
        conn.commit()
    finally:
        conn.close()

    return (len(all_plays), len(unique_plays))
