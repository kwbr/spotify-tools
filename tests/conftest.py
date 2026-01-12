from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import responses
from click.testing import CliRunner
from freezegun import freeze_time

from spotify_tools import database
from spotify_tools.types import Album


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def temp_cache_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))

    from spotify_tools import config
    cache_dir = config.user_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)

    return cache_dir


@pytest.fixture
def temp_config_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    from spotify_tools import config
    config_dir = config.user_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    return config_dir


@pytest.fixture
def temp_db(temp_cache_dir):
    db_path = temp_cache_dir / "albums.db"

    database.initialize_db(db_path)

    sample_data = {
        "2020": [
            {
                "uri": "spotify:album:1",
                "name": "Album 2020 One",
                "artists": ["Artist A"],
                "added_at": "2020-01-15T10:00:00Z",
            },
            {
                "uri": "spotify:album:2",
                "name": "Album 2020 Two",
                "artists": ["Artist B", "Artist C"],
                "added_at": "2020-06-20T14:30:00Z",
            },
        ],
        "2021": [
            {
                "uri": "spotify:album:3",
                "name": "Album 2021 One",
                "artists": ["Artist A"],
                "added_at": "2021-03-10T08:00:00Z",
            },
            {
                "uri": "spotify:album:4",
                "name": "Album 2021 Two",
                "artists": ["Artist D"],
                "added_at": "2021-11-05T16:45:00Z",
            },
            {
                "uri": "spotify:album:5",
                "name": "Album 2021 Three",
                "artists": ["Artist E", "Artist F"],
                "added_at": "2021-12-25T20:00:00Z",
            },
        ],
        "2022": [
            {
                "uri": "spotify:album:6",
                "name": "Album 2022 One",
                "artists": ["Artist G"],
                "added_at": "2022-02-14T12:00:00Z",
            },
        ],
    }

    database.save_albums(sample_data, db_path=db_path)

    return db_path


@pytest.fixture
def temp_db_with_play_history(temp_db):
    play_history = [
        {
            "track_uri": "spotify:track:101",
            "track_name": "Track One",
            "artists_json": json.dumps(["Artist A"]),
            "album_uri": "spotify:album:1",
            "album_name": "Album 2020 One",
            "album_artists_json": json.dumps(["Artist A"]),
            "played_at": "2024-01-10T10:00:00Z",
        },
        {
            "track_uri": "spotify:track:102",
            "track_name": "Track Two",
            "artists_json": json.dumps(["Artist B"]),
            "album_uri": "spotify:album:2",
            "album_name": "Album 2020 Two",
            "album_artists_json": json.dumps(["Artist B", "Artist C"]),
            "played_at": "2024-01-10T11:00:00Z",
        },
        {
            "track_uri": "spotify:track:101",
            "track_name": "Track One",
            "artists_json": json.dumps(["Artist A"]),
            "album_uri": "spotify:album:1",
            "album_name": "Album 2020 One",
            "album_artists_json": json.dumps(["Artist A"]),
            "played_at": "2024-01-11T10:00:00Z",
        },
    ]

    database.save_play_history(play_history, db_path=temp_db)

    return temp_db


@pytest.fixture
def sample_albums():
    return [
        Album(
            uri="spotify:album:test1",
            name="Test Album 1",
            artists=["Test Artist 1"],
            added_at="2020-01-01T00:00:00Z",
        ),
        Album(
            uri="spotify:album:test2",
            name="Test Album 2",
            artists=["Test Artist 2", "Test Artist 3"],
            added_at="2021-01-01T00:00:00Z",
        ),
        Album(
            uri="spotify:album:test3",
            name="Test Album 3",
            artists=["Test Artist 1"],
            added_at="2022-01-01T00:00:00Z",
        ),
    ]


@pytest.fixture
def mock_spotify_api_albums():
    return {
        "items": [
            {
                "added_at": "2020-01-15T10:00:00Z",
                "album": {
                    "uri": "spotify:album:mock1",
                    "name": "Mock Album 1",
                    "artists": [{"name": "Mock Artist 1"}],
                    "release_date": "2020-01-10",
                },
            },
            {
                "added_at": "2021-03-10T08:00:00Z",
                "album": {
                    "uri": "spotify:album:mock2",
                    "name": "Mock Album 2",
                    "artists": [{"name": "Mock Artist 2"}, {"name": "Mock Artist 3"}],
                    "release_date": "2021-03-05",
                },
            },
        ],
        "next": None,
        "total": 2,
    }


@pytest.fixture
def mock_spotify_api_recently_played():
    return {
        "items": [
            {
                "track": {
                    "uri": "spotify:track:recent1",
                    "name": "Recent Track 1",
                    "artists": [{"name": "Artist A"}],
                    "album": {
                        "uri": "spotify:album:recentalbum1",
                        "name": "Recent Album 1",
                        "artists": [{"name": "Artist A"}],
                    },
                },
                "played_at": "2024-01-15T12:00:00Z",
            },
            {
                "track": {
                    "uri": "spotify:track:recent2",
                    "name": "Recent Track 2",
                    "artists": [{"name": "Artist B"}],
                    "album": {
                        "uri": "spotify:album:recentalbum2",
                        "name": "Recent Album 2",
                        "artists": [{"name": "Artist B"}],
                    },
                },
                "played_at": "2024-01-15T12:05:00Z",
            },
        ],
        "next": None,
    }


@pytest.fixture
def mock_spotify_client():
    mock = MagicMock()
    mock.current_user_saved_albums.return_value = {
        "items": [],
        "next": None,
        "total": 0,
    }
    mock.current_user_recently_played.return_value = {"items": [], "next": None}
    mock.search.return_value = {"tracks": {"items": []}, "albums": {"items": []}}
    mock.user_playlist_create.return_value = {
        "id": "mock_playlist_id",
        "uri": "spotify:playlist:mock_playlist_id",
    }
    return mock


@pytest.fixture
def mock_config_file(temp_config_dir):
    config_file = temp_config_dir / "config.toml"
    config_content = """[spotify]
client_id = "test_client_id"
client_secret = "test_client_secret"
redirect_uri = "http://localhost:8888/callback"
"""
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def frozen_time_2024():
    with freeze_time("2024-01-15 12:00:00"):
        yield
