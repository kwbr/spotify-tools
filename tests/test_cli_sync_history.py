from __future__ import annotations

from unittest.mock import patch

import pytest

from spotify_tools.cli import cli


def test_sync_history_no_config(runner, temp_cache_dir):
    with patch("spotify_tools.commands.sync_history.spotify.create_spotify_client") as mock_create:
        mock_create.side_effect = FileNotFoundError("No config")

        result = runner.invoke(cli, ["sync-history"])

        assert result.exit_code != 0


def test_sync_history_with_mock_api(runner, temp_db, mock_spotify_client):
    with patch("spotify_tools.commands.sync_history.spotify.create_spotify_client") as mock_create:
        mock_create.return_value.__enter__.return_value = mock_spotify_client
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

        result = runner.invoke(cli, ["sync-history"])

        assert result.exit_code == 0


def test_sync_history_with_limit(runner, temp_db, mock_spotify_client):
    with patch("spotify_tools.commands.sync_history.spotify.create_spotify_client") as mock_create:
        mock_create.return_value.__enter__.return_value = mock_spotify_client
        mock_spotify_client.current_user_recently_played.return_value = {
            "items": [],
            "next": None,
        }

        result = runner.invoke(cli, ["sync-history", "--limit", "10"])

        assert result.exit_code == 0


def test_sync_history_default_limit(runner, temp_db, mock_spotify_client):
    with patch("spotify_tools.commands.sync_history.spotify.create_spotify_client") as mock_create:
        mock_create.return_value.__enter__.return_value = mock_spotify_client
        mock_spotify_client.current_user_recently_played.return_value = {
            "items": [],
            "next": None,
        }

        result = runner.invoke(cli, ["sync-history"])

        assert result.exit_code == 0


def test_sync_history_max_limit(runner, temp_db, mock_spotify_client):
    with patch("spotify_tools.commands.sync_history.spotify.create_spotify_client") as mock_create:
        mock_create.return_value.__enter__.return_value = mock_spotify_client
        mock_spotify_client.current_user_recently_played.return_value = {
            "items": [],
            "next": None,
        }

        result = runner.invoke(cli, ["sync-history", "--limit", "50"])

        assert result.exit_code == 0
