"""
Spotify client functionality with context manager support.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from . import config

if TYPE_CHECKING:
    from types import TracebackType


class SpotifyClient:
    """
    Spotify client with context manager support for proper resource management.
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize Spotify client."""
        self.cache_dir = cache_dir or config.user_cache_dir()
        self.client: spotipy.Spotify | None = None

    def __enter__(self) -> spotipy.Spotify:
        """Create and return the Spotify client."""
        conf = config.load_config()
        token_cache_path = Path(self.cache_dir / "token")

        self.client = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                scope=(
                    # Access user's saved albums for random selection
                    "user-library-read",
                    # Create and modify playlists via create-playlist command
                    "playlist-modify-private",
                    # Access recently played tracks for play history tracking
                    "user-read-recently-played",
                ),
                client_id=conf["client_id"],
                client_secret=conf["client_secret"],
                redirect_uri=conf["redirect_uri"],
                cache_handler=spotipy.CacheFileHandler(cache_path=token_cache_path),
            ),
        )
        return self.client

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Clean up resources."""
        self.client = None
        return False  # Don't suppress exceptions


def create_spotify_client(cache_dir: Path | None = None) -> SpotifyClient:
    """
    Create a Spotify client context manager.

    Args:
        cache_dir: Directory to store authentication token cache.

    Returns:
        SpotifyClient: Context manager for Spotify client.
    """
    return SpotifyClient(cache_dir)
