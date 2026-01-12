from __future__ import annotations

import json
import sqlite3

from spotify_tools import database
from spotify_tools.types import Album


def test_initialize_db(temp_cache_dir):
    db_path = temp_cache_dir / "test.db"
    database.initialize_db(db_path)

    assert db_path.exists()

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='albums'"
        )
        assert cursor.fetchone() is not None

        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='metadata'"
        )
        assert cursor.fetchone() is not None
    finally:
        conn.close()


def test_save_albums(temp_db):
    albums_data = {
        "2023": [
            {
                "uri": "spotify:album:new1",
                "name": "New Test Album",
                "artists": ["New Test Artist"],
                "added_at": "2023-01-01T00:00:00Z",
            }
        ]
    }

    database.save_albums(albums_data, db_path=temp_db)

    with database.get_db_connection(db_path=temp_db) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM albums WHERE year = 2023")
        count = cursor.fetchone()[0]
        assert count == 1


def test_get_albums_by_year(temp_db):
    albums = database.get_albums_by_year(2020, db_path=temp_db)

    assert len(albums) == 2
    assert all(isinstance(album, Album) for album in albums)
    assert all("spotify:album:" in album.uri for album in albums)


def test_get_albums_by_year_all(temp_db):
    albums = database.get_albums_by_year(db_path=temp_db)

    assert len(albums) == 6
    assert all(isinstance(album, Album) for album in albums)


def test_get_random_albums(temp_db):
    albums = database.get_random_albums(count=3, db_path=temp_db)

    assert len(albums) == 3
    assert all(isinstance(album, Album) for album in albums)


def test_get_random_albums_with_year_filter(temp_db):
    albums = database.get_random_albums(count=5, year=2021, db_path=temp_db)

    assert len(albums) == 3
    assert all(isinstance(album, Album) for album in albums)


def test_get_random_albums_verbose_mode(temp_db):
    albums = database.get_random_albums(count=2, verbose=True, db_path=temp_db)

    assert len(albums) == 2
    assert all(album.name != "" for album in albums)
    assert all(len(album.artists) > 0 for album in albums)


def test_get_random_albums_non_verbose_mode(temp_db):
    albums = database.get_random_albums(count=2, verbose=False, db_path=temp_db)

    assert len(albums) == 2
    assert all(album.uri.startswith("spotify:album:") for album in albums)


def test_get_album_count(temp_db):
    count = database.get_album_count(db_path=temp_db)

    assert count == 6


def test_get_album_count_no_database(temp_cache_dir):
    nonexistent_db = temp_cache_dir / "nonexistent.db"
    count = database.get_album_count(db_path=nonexistent_db)

    assert count == 0


def test_database_exists(temp_db):
    assert database.database_exists(db_path=temp_db) is True


def test_database_exists_when_missing(temp_cache_dir):
    nonexistent_db = temp_cache_dir / "nonexistent.db"
    assert database.database_exists(db_path=nonexistent_db) is False


def test_get_years(temp_db):
    years = database.get_years(db_path=temp_db)

    assert years == [2020, 2021, 2022]


def test_get_album_count_by_year(temp_db):
    counts = database.get_album_count_by_year(db_path=temp_db)

    assert counts[2020] == 2
    assert counts[2021] == 3
    assert counts[2022] == 1


def test_save_play_history(temp_db):
    plays = [
        {
            "track_uri": "spotify:track:1",
            "track_name": "Test Track",
            "artists_json": json.dumps(["Test Artist"]),
            "album_uri": "spotify:album:1",
            "album_name": "Test Album",
            "album_artists_json": json.dumps(["Test Artist"]),
            "played_at": "2024-01-01T00:00:00Z",
        }
    ]

    added = database.save_play_history(plays, db_path=temp_db)

    assert added == 1


def test_save_play_history_duplicates(temp_db):
    plays = [
        {
            "track_uri": "spotify:track:1",
            "track_name": "Test Track",
            "artists_json": json.dumps(["Test Artist"]),
            "album_uri": "spotify:album:1",
            "album_name": "Test Album",
            "album_artists_json": json.dumps(["Test Artist"]),
            "played_at": "2024-01-01T00:00:00Z",
        }
    ]

    added1 = database.save_play_history(plays, db_path=temp_db)
    added2 = database.save_play_history(plays, db_path=temp_db)

    assert added1 == 1
    assert added2 == 0


def test_get_total_play_count(temp_db_with_play_history):
    count = database.get_total_play_count(db_path=temp_db_with_play_history)

    assert count == 3


def test_get_play_count_by_album(temp_db_with_play_history):
    counts = database.get_play_count_by_album(db_path=temp_db_with_play_history)

    assert "spotify:album:1" in counts
    assert counts["spotify:album:1"]["play_count"] == 2


def test_get_play_count_by_track(temp_db_with_play_history):
    counts = database.get_play_count_by_track(db_path=temp_db_with_play_history)

    assert "spotify:track:101" in counts
    assert counts["spotify:track:101"]["play_count"] == 2


def test_get_play_count_by_artist(temp_db_with_play_history):
    counts = database.get_play_count_by_artist(db_path=temp_db_with_play_history)

    assert "Artist A" in counts
    assert counts["Artist A"]["play_count"] == 2


def test_get_recently_played(temp_db_with_play_history):
    recent = database.get_recently_played(limit=10, db_path=temp_db_with_play_history)

    assert len(recent) == 3
    assert recent[0]["played_at"] == "2024-01-11T10:00:00Z"


def test_set_and_get_metadata(temp_db):
    with database.get_db_connection(db_path=temp_db) as conn:
        database.set_metadata(conn, "test_key", "test_value")
        value = database.get_metadata(conn, "test_key")

    assert value == "test_value"


def test_get_metadata_default(temp_db):
    with database.get_db_connection(db_path=temp_db) as conn:
        value = database.get_metadata(conn, "nonexistent", default="default_value")

    assert value == "default_value"
