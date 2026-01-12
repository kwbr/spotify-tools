from __future__ import annotations

import click
import pytest

from spotify_tools.commands.create_playlist import (
    create_playlist_logic,
    read_items_from_file,
)


@pytest.fixture
def mock_ctx():
    """Create a mock Click context for testing."""
    ctx = click.Context(click.Command("test"))
    ctx.obj = {"VERBOSE": 0}
    return ctx


def test_create_playlist_no_items(mock_ctx, mock_spotify_client):
    result = create_playlist_logic(mock_spotify_client, mock_ctx, [])

    assert result["success"] is False
    assert result["error"] == "no_items"


def test_create_playlist_dry_run_with_items(mock_ctx, mock_spotify_client):
    mock_spotify_client.search.return_value = {
        "tracks": {
            "items": [
                {
                    "uri": "spotify:track:1",
                    "name": "Test Track",
                    "artists": [{"name": "Test Artist"}],
                }
            ]
        }
    }

    result = create_playlist_logic(
        mock_spotify_client, mock_ctx, ["Test Track"], dry_run=True
    )

    assert result["success"] is True
    assert result["dry_run"] is True
    assert result["tracks_found"] >= 0


def test_create_playlist_with_track(mock_ctx, mock_spotify_client):
    mock_spotify_client.search.return_value = {
        "tracks": {
            "items": [
                {
                    "uri": "spotify:track:1",
                    "name": "Test Track",
                    "artists": [{"name": "Test Artist"}],
                }
            ]
        }
    }
    mock_spotify_client.current_user.return_value = {"id": "user123"}
    mock_spotify_client.user_playlist_create.return_value = {"id": "playlist123"}

    result = create_playlist_logic(
        mock_spotify_client, mock_ctx, ["track:Test Track"], name="Test Playlist"
    )

    assert result["success"] is True
    assert result["playlist_id"] == "playlist123"
    assert result["tracks_count"] >= 0


def test_create_playlist_with_name(mock_ctx, mock_spotify_client):
    mock_spotify_client.search.return_value = {
        "tracks": {
            "items": [
                {
                    "uri": "spotify:track:1",
                    "name": "Test Track",
                    "artists": [{"name": "Test Artist"}],
                }
            ]
        }
    }
    mock_spotify_client.current_user.return_value = {"id": "user123"}
    mock_spotify_client.user_playlist_create.return_value = {"id": "playlist123"}

    result = create_playlist_logic(
        mock_spotify_client, mock_ctx, ["Test Track"], name="My Playlist"
    )

    assert result["success"] is True
    mock_spotify_client.user_playlist_create.assert_called_once()


def test_create_playlist_with_uri(mock_ctx, mock_spotify_client):
    mock_spotify_client.track.return_value = {
        "uri": "spotify:track:1",
        "name": "Test Track",
        "artists": [{"name": "Test Artist"}],
    }
    mock_spotify_client.current_user.return_value = {"id": "user123"}
    mock_spotify_client.user_playlist_create.return_value = {"id": "playlist123"}

    result = create_playlist_logic(mock_spotify_client, mock_ctx, ["spotify:track:1"])

    assert result["success"] is True
    assert result["playlist_id"] == "playlist123"


def test_create_playlist_multiple_items(mock_ctx, mock_spotify_client):
    mock_spotify_client.search.return_value = {
        "tracks": {
            "items": [
                {
                    "uri": "spotify:track:1",
                    "name": "Test Track",
                    "artists": [{"name": "Test Artist"}],
                }
            ]
        }
    }
    mock_spotify_client.current_user.return_value = {"id": "user123"}
    mock_spotify_client.user_playlist_create.return_value = {"id": "playlist123"}

    result = create_playlist_logic(
        mock_spotify_client,
        mock_ctx,
        ["track:Track 1", "track:Track 2"],
        name="Multi Playlist",
    )

    assert result["success"] is True
    assert result["playlist_id"] == "playlist123"


def test_create_playlist_with_album(mock_ctx, mock_spotify_client):
    mock_spotify_client.search.return_value = {
        "albums": {
            "items": [
                {
                    "id": "album1",
                    "uri": "spotify:album:1",
                    "name": "Test Album",
                    "artists": [{"name": "Test Artist"}],
                }
            ]
        }
    }
    mock_spotify_client.album_tracks.return_value = {
        "items": [
            {
                "uri": "spotify:track:1",
                "name": "Track 1",
                "artists": [{"name": "Test Artist"}],
            }
        ]
    }
    mock_spotify_client.current_user.return_value = {"id": "user123"}
    mock_spotify_client.user_playlist_create.return_value = {"id": "playlist123"}

    result = create_playlist_logic(mock_spotify_client, mock_ctx, ["album:Test Album"])

    assert result["success"] is True
    assert result["playlist_id"] == "playlist123"


def test_read_items_from_file(tmp_path):
    test_file = tmp_path / "items.txt"
    test_file.write_text("track:Song 1\ntrack:Song 2\n\ntrack:Song 3\n")

    items = read_items_from_file(test_file)

    assert len(items) == 3
    assert items[0] == "track:Song 1"
    assert items[1] == "track:Song 2"
    assert items[2] == "track:Song 3"


def test_read_items_from_file_empty_lines(tmp_path):
    test_file = tmp_path / "items.txt"
    test_file.write_text("\n\ntrack:Song 1\n\n")

    items = read_items_from_file(test_file)

    assert len(items) == 1
    assert items[0] == "track:Song 1"
