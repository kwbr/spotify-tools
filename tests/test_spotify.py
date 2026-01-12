from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from spotify_tools import spotify


def test_spotify_client_init(temp_cache_dir):
    client = spotify.SpotifyClient(cache_dir=temp_cache_dir)

    assert client.cache_dir == temp_cache_dir
    assert client.client is None


def test_spotify_client_init_default_cache_dir():
    with patch("spotify_tools.spotify.config.user_cache_dir") as mock_cache_dir:
        mock_cache_dir.return_value = Path("/test/cache")

        client = spotify.SpotifyClient()

        assert client.cache_dir == Path("/test/cache")


def test_spotify_client_enter(temp_cache_dir, temp_config_dir):
    config_file = temp_config_dir / "config.toml"
    config_file.write_text(
        """[spotify]
client_id = "test_id"
client_secret = "test_secret"
redirect_uri = "http://localhost:8888/callback"
"""
    )

    with (
        patch("spotify_tools.spotify.spotipy.Spotify") as mock_spotify,
        patch("spotify_tools.spotify.config.load_config") as mock_load,
    ):
        mock_load.return_value = {
            "client_id": "test_id",
            "client_secret": "test_secret",
            "redirect_uri": "http://localhost:8888/callback",
        }
        mock_instance = MagicMock()
        mock_spotify.return_value = mock_instance

        client = spotify.SpotifyClient(cache_dir=temp_cache_dir)
        result = client.__enter__()

        assert result == mock_instance
        assert client.client == mock_instance
        mock_spotify.assert_called_once()


def test_spotify_client_exit():
    client = spotify.SpotifyClient()
    client.client = MagicMock()

    result = client.__exit__(None, None, None)

    assert result is False
    assert client.client is None


def test_spotify_client_exit_with_exception():
    client = spotify.SpotifyClient()
    client.client = MagicMock()

    result = client.__exit__(ValueError, ValueError("test"), None)

    assert result is False
    assert client.client is None


def test_spotify_client_context_manager(temp_cache_dir, temp_config_dir):
    config_file = temp_config_dir / "config.toml"
    config_file.write_text(
        """[spotify]
client_id = "test_id"
client_secret = "test_secret"
redirect_uri = "http://localhost:8888/callback"
"""
    )

    with (
        patch("spotify_tools.spotify.spotipy.Spotify") as mock_spotify,
        patch("spotify_tools.spotify.config.load_config") as mock_load,
    ):
        mock_load.return_value = {
            "client_id": "test_id",
            "client_secret": "test_secret",
            "redirect_uri": "http://localhost:8888/callback",
        }
        mock_instance = MagicMock()
        mock_spotify.return_value = mock_instance

        with spotify.SpotifyClient(cache_dir=temp_cache_dir) as sp:
            assert sp == mock_instance


def test_create_spotify_client_default():
    with patch("spotify_tools.spotify.config.user_cache_dir") as mock_cache_dir:
        mock_cache_dir.return_value = Path("/test/cache")

        client = spotify.create_spotify_client()

        assert isinstance(client, spotify.SpotifyClient)
        assert client.cache_dir == Path("/test/cache")


def test_create_spotify_client_custom_dir(temp_cache_dir):
    client = spotify.create_spotify_client(cache_dir=temp_cache_dir)

    assert isinstance(client, spotify.SpotifyClient)
    assert client.cache_dir == temp_cache_dir


def test_spotify_client_token_cache_path(temp_cache_dir, temp_config_dir):
    config_file = temp_config_dir / "config.toml"
    config_file.write_text(
        """[spotify]
client_id = "test_id"
client_secret = "test_secret"
redirect_uri = "http://localhost:8888/callback"
"""
    )

    with (
        patch("spotify_tools.spotify.spotipy.Spotify") as mock_spotify,
        patch("spotify_tools.spotify.config.load_config") as mock_load,
    ):
        mock_load.return_value = {
            "client_id": "test_id",
            "client_secret": "test_secret",
            "redirect_uri": "http://localhost:8888/callback",
        }
        mock_instance = MagicMock()
        mock_spotify.return_value = mock_instance

        client = spotify.SpotifyClient(cache_dir=temp_cache_dir)
        result = client.__enter__()

        assert result == mock_instance
        mock_spotify.assert_called_once()
