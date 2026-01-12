from __future__ import annotations

import click
import pytest

from spotify_tools.commands.sync_history import sync_play_history_logic


@pytest.fixture
def mock_ctx():
    """Create a mock Click context for testing."""
    ctx = click.Context(click.Command("test"))
    ctx.obj = {"VERBOSE": 0}
    return ctx


def test_sync_history_with_tracks(mock_ctx, temp_db, mock_spotify_client):
    mock_spotify_client.current_user_recently_played.return_value = {
        "items": [
            {
                "track": {
                    "uri": "spotify:track:test1",
                    "name": "Test Track",
                    "artists": [{"name": "Test Artist"}],
                    "album": {
                        "uri": "spotify:album:test1",
                        "name": "Test Album",
                        "artists": [{"name": "Test Artist"}],
                    },
                },
                "played_at": "2024-01-15T12:00:00Z",
            }
        ],
        "next": None,
    }

    result = sync_play_history_logic(mock_spotify_client, mock_ctx, limit=50, db_path=temp_db)

    assert result["plays_synced"] == 1
    assert result["new_plays"] == 1
    assert result["total_plays"] == 1


def test_sync_history_no_tracks(mock_ctx, temp_db, mock_spotify_client):
    mock_spotify_client.current_user_recently_played.return_value = {
        "items": [],
        "next": None,
    }

    result = sync_play_history_logic(mock_spotify_client, mock_ctx, limit=50, db_path=temp_db)

    assert result["plays_synced"] == 0
    assert result["new_plays"] == 0
    assert result["total_plays"] == 0


def test_sync_history_with_limit(mock_ctx, temp_db, mock_spotify_client):
    mock_spotify_client.current_user_recently_played.return_value = {
        "items": [],
        "next": None,
    }

    result = sync_play_history_logic(mock_spotify_client, mock_ctx, limit=10, db_path=temp_db)

    assert result["plays_synced"] == 0
    mock_spotify_client.current_user_recently_played.assert_called_once()
    call_kwargs = mock_spotify_client.current_user_recently_played.call_args[1]
    assert call_kwargs["limit"] == 10


def test_sync_history_max_limit(mock_ctx, temp_db, mock_spotify_client):
    mock_spotify_client.current_user_recently_played.return_value = {
        "items": [],
        "next": None,
    }

    result = sync_play_history_logic(mock_spotify_client, mock_ctx, limit=100, db_path=temp_db)

    # Should cap at 50
    call_kwargs = mock_spotify_client.current_user_recently_played.call_args[1]
    assert call_kwargs["limit"] == 50


def test_sync_history_multiple_tracks(mock_ctx, temp_db, mock_spotify_client):
    mock_spotify_client.current_user_recently_played.return_value = {
        "items": [
            {
                "track": {
                    "uri": "spotify:track:test1",
                    "name": "Test Track 1",
                    "artists": [{"name": "Test Artist"}],
                    "album": {
                        "uri": "spotify:album:test1",
                        "name": "Test Album",
                        "artists": [{"name": "Test Artist"}],
                    },
                },
                "played_at": "2024-01-15T12:00:00Z",
            },
            {
                "track": {
                    "uri": "spotify:track:test2",
                    "name": "Test Track 2",
                    "artists": [{"name": "Test Artist 2"}],
                    "album": {
                        "uri": "spotify:album:test2",
                        "name": "Test Album 2",
                        "artists": [{"name": "Test Artist 2"}],
                    },
                },
                "played_at": "2024-01-15T12:05:00Z",
            },
        ],
        "next": None,
    }

    result = sync_play_history_logic(mock_spotify_client, mock_ctx, limit=50, db_path=temp_db)

    assert result["plays_synced"] == 2
    assert result["new_plays"] == 2
    assert result["total_plays"] == 2
