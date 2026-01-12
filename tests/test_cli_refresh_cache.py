from __future__ import annotations

from unittest.mock import patch

import pytest

from spotify_tools.cli import cli


def test_refresh_cache_basic(runner, temp_cache_dir, mock_spotify_client):
    with patch("spotify_tools.commands.refresh_cache.spotify.create_spotify_client") as mock_create:
        mock_create.return_value.__enter__.return_value = mock_spotify_client
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

        result = runner.invoke(cli, ["refresh-cache"])

        assert result.exit_code == 0


def test_refresh_cache_with_max_workers(runner, temp_cache_dir, mock_spotify_client):
    with patch("spotify_tools.commands.refresh_cache.spotify.create_spotify_client") as mock_create:
        mock_create.return_value.__enter__.return_value = mock_spotify_client
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

        result = runner.invoke(cli, ["refresh-cache", "--max-workers", "10"])

        assert result.exit_code == 0


def test_refresh_cache_empty_library(runner, temp_cache_dir, mock_spotify_client):
    with patch("spotify_tools.commands.refresh_cache.spotify.create_spotify_client") as mock_create:
        mock_create.return_value.__enter__.return_value = mock_spotify_client
        mock_spotify_client.current_user_saved_albums.return_value = {
            "total": 0,
            "items": [],
            "next": None,
        }

        result = runner.invoke(cli, ["refresh-cache"])

        assert result.exit_code == 0


def test_refresh_cache_no_config(runner, temp_cache_dir):
    with patch("spotify_tools.commands.refresh_cache.spotify.create_spotify_client") as mock_create:
        mock_create.side_effect = FileNotFoundError("No config")

        result = runner.invoke(cli, ["refresh-cache"])

        assert result.exit_code != 0


def test_refresh_cache_updates_existing_database(runner, temp_db, mock_spotify_client):
    with patch("spotify_tools.commands.refresh_cache.spotify.create_spotify_client") as mock_create:
        mock_create.return_value.__enter__.return_value = mock_spotify_client
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

        result = runner.invoke(cli, ["refresh-cache"])

        assert result.exit_code == 0
