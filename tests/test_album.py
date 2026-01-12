from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from spotify_tools import album
from spotify_tools.types import Album


def test_get_total_album_count():
    sp = MagicMock()
    sp.current_user_saved_albums.return_value = {"total": 42}

    count = album.get_total_album_count(sp)

    assert count == 42
    sp.current_user_saved_albums.assert_called_once_with(limit=1)


def test_process_album_batch():
    batch = {
        "items": [
            {
                "added_at": "2020-01-15T10:00:00Z",
                "album": {
                    "uri": "spotify:album:1",
                    "name": "Test Album",
                    "artists": [{"name": "Test Artist"}],
                    "release_date": "2020-01-10",
                },
            }
        ]
    }
    albums_by_year = {}

    album.process_album_batch(batch, albums_by_year)

    assert "2020" in albums_by_year
    assert len(albums_by_year["2020"]) == 1
    assert albums_by_year["2020"][0]["name"] == "Test Album"


def test_process_album_batch_multiple_years():
    batch = {
        "items": [
            {
                "added_at": "2020-01-15T10:00:00Z",
                "album": {
                    "uri": "spotify:album:1",
                    "name": "Album 2020",
                    "artists": [{"name": "Artist"}],
                    "release_date": "2020-01-10",
                },
            },
            {
                "added_at": "2021-06-20T14:30:00Z",
                "album": {
                    "uri": "spotify:album:2",
                    "name": "Album 2021",
                    "artists": [{"name": "Artist"}],
                    "release_date": "2021-06-15",
                },
            },
        ]
    }
    albums_by_year = {}

    album.process_album_batch(batch, albums_by_year)

    assert "2020" in albums_by_year
    assert "2021" in albums_by_year
    assert len(albums_by_year["2020"]) == 1
    assert len(albums_by_year["2021"]) == 1


def test_extract_year_from_date():
    assert album.extract_year_from_date("2020-01-15") == 2020
    assert album.extract_year_from_date("2020") == 2020
    assert album.extract_year_from_date("1999-12-31") == 1999


def test_get_albums_by_year(temp_db):
    albums = album.get_albums_by_year(year=2020)

    assert len(albums) == 2
    assert all(isinstance(a, Album) for a in albums)


def test_get_albums_by_year_all(temp_db):
    albums = album.get_albums_by_year()

    assert len(albums) == 6
    assert all(isinstance(a, Album) for a in albums)


def test_count_total_albums_with_database(temp_db):
    count = album.count_total_albums()

    assert count == 6


def test_get_sorted_years(temp_db):
    years = album.get_sorted_years()

    assert years == [2020, 2021, 2022]


def test_fetch_all_albums_parallel_basic(mock_spotify_client, temp_cache_dir):
    mock_spotify_client.current_user_saved_albums.return_value = {
        "total": 2,
        "items": [
            {
                "added_at": "2020-01-15T10:00:00Z",
                "album": {
                    "uri": "spotify:album:1",
                    "name": "Album 1",
                    "artists": [{"name": "Artist"}],
                    "release_date": "2020-01-10",
                },
            },
            {
                "added_at": "2021-06-20T14:30:00Z",
                "album": {
                    "uri": "spotify:album:2",
                    "name": "Album 2",
                    "artists": [{"name": "Artist"}],
                    "release_date": "2021-06-15",
                },
            },
        ],
        "next": None,
    }

    result = album.fetch_all_albums_parallel(mock_spotify_client)

    assert isinstance(result, dict)
    assert len(result) >= 0


def test_fetch_all_albums_with_progress_callback(mock_spotify_client):
    mock_spotify_client.current_user_saved_albums.return_value = {
        "total": 1,
        "items": [
            {
                "added_at": "2020-01-15T10:00:00Z",
                "album": {
                    "uri": "spotify:album:1",
                    "name": "Album",
                    "artists": [{"name": "Artist"}],
                    "release_date": "2020-01-10",
                },
            }
        ],
        "next": None,
    }

    progress_calls = []

    def progress_callback(current, total):
        progress_calls.append((current, total))

    result = album.fetch_all_albums_parallel(
        mock_spotify_client, progress_callback=progress_callback
    )

    assert isinstance(result, dict)
    assert len(progress_calls) > 0


def test_fetch_all_albums_with_max_workers(mock_spotify_client):
    mock_spotify_client.current_user_saved_albums.return_value = {
        "total": 1,
        "items": [
            {
                "added_at": "2020-01-15T10:00:00Z",
                "album": {
                    "uri": "spotify:album:1",
                    "name": "Album",
                    "artists": [{"name": "Artist"}],
                    "release_date": "2020-01-10",
                },
            }
        ],
        "next": None,
    }

    result = album.fetch_all_albums_parallel(mock_spotify_client, max_workers=2)

    assert isinstance(result, dict)
