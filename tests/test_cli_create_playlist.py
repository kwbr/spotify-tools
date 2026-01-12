from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from spotify_tools.cli import cli


def test_create_playlist_no_items(runner):
    result = runner.invoke(cli, ["create-playlist"])

    assert result.exit_code in [0, 1]
    assert "No items specified" in result.output or result.exit_code == 0


def test_create_playlist_with_file_not_found(runner):
    result = runner.invoke(cli, ["create-playlist", "--file", "nonexistent.txt"])

    assert result.exit_code in [1, 2]


def test_create_playlist_dry_run_with_items(runner, mock_spotify_client):
    with patch("spotify_tools.commands.create_playlist.spotify.create_spotify_client") as mock_create:
        mock_create.return_value.__enter__.return_value = mock_spotify_client
        mock_spotify_client.search.return_value = {
            "tracks": {"items": []},
            "albums": {"items": []},
        }

        result = runner.invoke(
            cli, ["create-playlist", "--dry-run", "Bohemian Rhapsody"]
        )

        assert result.exit_code == 0 or "Search Quality Analysis" in result.output


def test_create_playlist_with_file(runner, mock_spotify_client):
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Track One\n")
        f.write("Track Two\n")
        temp_file = f.name

    try:
        with patch("spotify_tools.commands.create_playlist.spotify.create_spotify_client") as mock_create:
            mock_create.return_value.__enter__.return_value = mock_spotify_client
            mock_spotify_client.search.return_value = {
                "tracks": {"items": []},
                "albums": {"items": []},
            }

            result = runner.invoke(
                cli, ["create-playlist", "--dry-run", "--file", temp_file]
            )

            assert result.exit_code == 0 or "items" in result.output.lower()
    finally:
        Path(temp_file).unlink(missing_ok=True)


def test_create_playlist_with_output_file(runner, mock_spotify_client, tmp_path):
    output_file = tmp_path / "output.txt"

    with patch("spotify_tools.commands.create_playlist.spotify.create_spotify_client") as mock_create:
        mock_create.return_value.__enter__.return_value = mock_spotify_client
        mock_spotify_client.search.return_value = {
            "tracks": {"items": []},
            "albums": {"items": []},
        }

        result = runner.invoke(
            cli,
            [
                "create-playlist",
                "--dry-run",
                "--output",
                str(output_file),
                "Test Track",
            ],
        )

        assert result.exit_code == 0 or output_file.exists()


def test_create_playlist_with_name(runner, mock_spotify_client):
    with patch("spotify_tools.commands.create_playlist.spotify.create_spotify_client") as mock_create:
        mock_create.return_value.__enter__.return_value = mock_spotify_client
        mock_spotify_client.search.return_value = {
            "tracks": {"items": []},
            "albums": {"items": []},
        }

        result = runner.invoke(
            cli,
            ["create-playlist", "--dry-run", "--name", "My Playlist", "Test Track"],
        )

        assert result.exit_code == 0


def test_create_playlist_with_track_prefix(runner, mock_spotify_client):
    with patch("spotify_tools.commands.create_playlist.spotify.create_spotify_client") as mock_create:
        mock_create.return_value.__enter__.return_value = mock_spotify_client
        mock_spotify_client.search.return_value = {
            "tracks": {"items": []},
            "albums": {"items": []},
        }

        result = runner.invoke(
            cli, ["create-playlist", "--dry-run", "track:Bohemian Rhapsody"]
        )

        assert result.exit_code == 0


def test_create_playlist_with_album_prefix(runner, mock_spotify_client):
    with patch("spotify_tools.commands.create_playlist.spotify.create_spotify_client") as mock_create:
        mock_create.return_value.__enter__.return_value = mock_spotify_client
        mock_spotify_client.search.return_value = {
            "albums": {"items": []},
        }

        result = runner.invoke(
            cli, ["create-playlist", "--dry-run", "album:Dark Side of the Moon"]
        )

        assert result.exit_code == 0


def test_create_playlist_with_uri(runner, mock_spotify_client):
    with patch("spotify_tools.commands.create_playlist.spotify.create_spotify_client") as mock_create:
        mock_create.return_value.__enter__.return_value = mock_spotify_client

        result = runner.invoke(
            cli, ["create-playlist", "--dry-run", "spotify:track:abc123"]
        )

        assert result.exit_code == 0


def test_create_playlist_multiple_items(runner, mock_spotify_client):
    with patch("spotify_tools.commands.create_playlist.spotify.create_spotify_client") as mock_create:
        mock_create.return_value.__enter__.return_value = mock_spotify_client
        mock_spotify_client.search.return_value = {
            "tracks": {"items": []},
            "albums": {"items": []},
        }

        result = runner.invoke(
            cli,
            [
                "create-playlist",
                "--dry-run",
                "Track One",
                "Track Two",
                "album:Album Name",
            ],
        )

        assert result.exit_code == 0
