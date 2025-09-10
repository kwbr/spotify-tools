"""
Type definitions for album data.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Album:
    """
    Consistent representation of a Spotify album.
    """

    uri: str
    name: str
    artists: list[str]
    added_at: str

    @classmethod
    def from_spotify_response(cls, item: dict[str, Any]) -> "Album":
        """
        Create an Album instance from a Spotify API response item.

        Args:
            item: Album item from Spotify API response.

        Returns:
            Album: Standardized album representation.
        """
        album = item["album"]
        return cls(
            uri=album["uri"],
            name=album["name"],
            artists=[artist["name"] for artist in album["artists"]],
            added_at=item["added_at"],
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the album to a dictionary for storage or serialization.

        Returns:
            dict: Dictionary representation of the album.
        """
        return {
            "uri": self.uri,
            "name": self.name,
            "artists": self.artists,
            "added_at": self.added_at,
        }

    @classmethod
    def from_uri_only(cls, uri: str) -> "Album":
        """
        Create a minimal Album instance from just a URI.

        This is used for performance optimization when only the URI is needed.

        Args:
            uri: Spotify URI for the album.

        Returns:
            Album: Minimal album representation.
        """
        return cls(
            uri=uri,
            name="",  # Empty placeholder
            artists=[],  # Empty artist list
            added_at="",  # Empty placeholder
        )

    def format_artists(self) -> str:
        """
        Format the list of artists as a comma-separated string.

        Returns:
            str: Comma-separated artist names.
        """
        return ", ".join(self.artists)
