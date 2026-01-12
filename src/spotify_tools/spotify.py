"""
Spotify client functionality with context manager support.
"""

from pathlib import Path

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from . import config


class SpotifyClient:
    """
    Spotify client with context manager support for proper resource management.
    """

    def __init__(self, cache_dir=None):
        """Initialize Spotify client."""
        self.cache_dir = cache_dir or config.user_cache_dir()
        self.client = None

    def __enter__(self):
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
                client_id=conf["spotify"]["client_id"],
                client_secret=conf["spotify"]["client_secret"],
                redirect_uri=conf["spotify"]["redirect_uri"],
                cache_handler=spotipy.CacheFileHandler(cache_path=token_cache_path),
            ),
        )
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources."""
        self.client = None
        return False  # Don't suppress exceptions


def create_spotify_client(cache_dir=None):
    """
    Create a Spotify client context manager.

    Args:
        cache_dir: Directory to store authentication token cache.

    Returns:
        SpotifyClient: Context manager for Spotify client.
    """
    return SpotifyClient(cache_dir)
