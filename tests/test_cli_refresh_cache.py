from __future__ import annotations

import click
import pytest

from spotify_tools.commands.random_album import refresh_album_cache


@pytest.fixture
def mock_ctx():
    """Create a mock Click context for testing."""
    ctx = click.Context(click.Command("test"))
    ctx.obj = {"VERBOSE": 0}
    return ctx


def test_refresh_cache_basic(mock_ctx, temp_db, mock_spotify_client):
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

    refresh_album_cache(
        mock_ctx,
        mock_spotify_client,
        max_workers=5,
        show_progress=False,
        db_path=temp_db,
    )

    mock_spotify_client.current_user_saved_albums.assert_called()

    from spotify_tools import database
    albums = database.get_albums_by_year(db_path=temp_db)
    assert len(albums) == 2
    assert any(a.uri == "spotify:album:1" for a in albums)
    assert any(a.uri == "spotify:album:2" for a in albums)


def test_refresh_cache_with_max_workers(mock_ctx, temp_db, mock_spotify_client):
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

    refresh_album_cache(
        mock_ctx,
        mock_spotify_client,
        max_workers=10,
        show_progress=False,
        db_path=temp_db,
    )

    mock_spotify_client.current_user_saved_albums.assert_called()


def test_refresh_cache_empty_library(mock_ctx, temp_db, mock_spotify_client):
    mock_spotify_client.current_user_saved_albums.return_value = {
        "total": 0,
        "items": [],
        "next": None,
    }

    refresh_album_cache(
        mock_ctx,
        mock_spotify_client,
        max_workers=5,
        show_progress=False,
        db_path=temp_db,
    )

    mock_spotify_client.current_user_saved_albums.assert_called()

    from spotify_tools import database
    albums = database.get_albums_by_year(db_path=temp_db)
    assert len(albums) == 0


def test_refresh_cache_updates_existing_database(
    mock_ctx, temp_db, mock_spotify_client
):
    from spotify_tools import database

    mock_spotify_client.current_user_saved_albums.return_value = {
        "total": 1,
        "items": [
            {
                "added_at": "2023-01-15T10:00:00Z",
                "album": {
                    "uri": "spotify:album:new",
                    "name": "New Album",
                    "artists": [{"name": "New Artist"}],
                    "release_date": "2023-01-10",
                },
            }
        ],
        "next": None,
    }

    refresh_album_cache(
        mock_ctx,
        mock_spotify_client,
        max_workers=5,
        show_progress=False,
        db_path=temp_db,
    )

    mock_spotify_client.current_user_saved_albums.assert_called()

    albums = database.get_albums_by_year(db_path=temp_db)
    assert len(albums) == 1
    assert albums[0].uri == "spotify:album:new"


def test_refresh_cache_with_pagination(mock_ctx, temp_db, mock_spotify_client):
    page2 = {
        "total": 3,
        "items": [
            {
                "added_at": "2021-01-15T10:00:00Z",
                "album": {
                    "uri": "spotify:album:2",
                    "name": "Album 2",
                    "artists": [{"name": "Artist 2"}],
                    "release_date": "2021-01-10",
                },
            },
        ],
        "next": None,
    }

    mock_spotify_client.current_user_saved_albums.return_value = {
        "total": 3,
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
        ],
        "next": "next_url",
    }

    mock_spotify_client.next.return_value = page2

    refresh_album_cache(
        mock_ctx,
        mock_spotify_client,
        max_workers=5,
        show_progress=False,
        db_path=temp_db,
    )

    assert mock_spotify_client.current_user_saved_albums.call_count >= 1

    from spotify_tools import database
    albums = database.get_albums_by_year(db_path=temp_db)
    assert len(albums) >= 1
    assert any(a.uri == "spotify:album:1" for a in albums)
