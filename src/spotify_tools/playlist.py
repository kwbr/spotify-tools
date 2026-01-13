"""
Playlist creation functionality for Spotify tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol


class SpotifyClient(Protocol):
    """Protocol for Spotify client objects matching spotipy's interface."""

    def search(
        self,
        q: str,
        limit: int = 10,
        offset: int = 0,
        type: str = "track",
        market: str | None = None,
    ) -> dict[str, Any]: ...

    def album_tracks(
        self, album_id: str, limit: int = 50, offset: int = 0, market: str | None = None
    ) -> dict[str, Any]: ...

    def track(self, track_id: str, market: str | None = None) -> dict[str, Any]: ...

    def album(self, album_id: str, market: str | None = None) -> dict[str, Any]: ...

    def current_user(self) -> dict[str, Any]: ...

    def user_playlist_create(
        self,
        user: str,
        name: str,
        public: bool = True,
        collaborative: bool = False,
        description: str = "",
    ) -> dict[str, Any]: ...

    def playlist_add_items(
        self, playlist_id: str, items: list[str], position: int | None = None
    ) -> dict[str, Any]: ...

    def current_user_saved_albums(
        self, limit: int = 20, offset: int = 0, market: str | None = None
    ) -> dict[str, Any]: ...

    def current_user_recently_played(
        self, limit: int = 50, after: int | None = None, before: int | None = None
    ) -> dict[str, Any]: ...


@dataclass
class ResolvedTrack:
    """Represents a resolved track with metadata."""

    uri: str
    name: str
    artists: str
    source_query: str  # Original query that resolved to this track


@dataclass
class SearchResult:
    """Represents a search result with quality assessment."""

    query: str
    search_type: str  # "track", "album", "auto"
    found_item: dict[str, Any] | None
    match_quality: float  # 0.0 to 1.0, higher is better
    quality_reason: str  # Human readable explanation
    resolved_tracks: list[ResolvedTrack]


def format_artists(track: dict[str, Any]) -> str:
    """Format artist names from a track object."""
    return ", ".join([artist["name"] for artist in track["artists"]])


def normalize_string(s: str) -> str:
    """Normalize string for comparison (lowercase, remove special chars)."""
    import re

    return re.sub(r"[^\w\s]", "", s.lower()).strip()


def calculate_string_similarity(s1: str, s2: str) -> float:
    """Calculate character-level similarity using SequenceMatcher."""
    from difflib import SequenceMatcher

    # Normalize both strings for comparison
    norm_s1 = normalize_string(s1)
    norm_s2 = normalize_string(s2)

    if not norm_s1 or not norm_s2:
        return 0.0

    # Calculate similarity ratio
    matcher = SequenceMatcher(None, norm_s1, norm_s2)
    return matcher.ratio()


def calculate_fuzzy_word_similarity(query: str, result_text: str) -> float:
    """Calculate word-level fuzzy similarity using close matches."""
    from difflib import get_close_matches

    # Normalize and split into words
    query_words = normalize_string(query).split()
    result_words = normalize_string(result_text).split()

    if not query_words or not result_words:
        return 0.0

    # Find close matches for each query word
    matched_words = 0
    for query_word in query_words:
        # Look for close matches with cutoff of 0.6 (60% similarity)
        close_matches = get_close_matches(query_word, result_words, n=1, cutoff=0.6)
        if close_matches:
            matched_words += 1

    return matched_words / len(query_words)


def calculate_match_quality(
    query: str, result_name: str, result_artists: str
) -> tuple[float, str]:
    """
    Calculate match quality between search query and result using hybrid similarity.

    Returns:
        tuple: (quality_score 0.0-1.0, explanation)
    """
    if not result_name:
        return 0.0, "No result found"

    if not query:
        return 0.0, "Empty query"

    # Combine result name and artists for comparison
    result_full = f"{result_name} {result_artists}".strip()

    # Calculate different similarity metrics
    string_sim = calculate_string_similarity(query, result_full)
    fuzzy_word_sim = calculate_fuzzy_word_similarity(query, result_full)

    # Weighted combination: prioritize string similarity for format differences
    overall_quality = (0.6 * string_sim) + (0.4 * fuzzy_word_sim)

    # Determine quality category and reason
    if overall_quality >= 0.8:
        reason = f"Excellent match (str: {string_sim:.2f}, word: {fuzzy_word_sim:.2f})"
    elif overall_quality >= 0.6:
        reason = f"Good match (str: {string_sim:.2f}, word: {fuzzy_word_sim:.2f})"
    elif overall_quality >= 0.3:
        reason = f"Fair match (str: {string_sim:.2f}, word: {fuzzy_word_sim:.2f})"
    elif overall_quality >= 0.1:
        reason = f"Weak match (str: {string_sim:.2f}, word: {fuzzy_word_sim:.2f})"
    else:
        reason = f"Poor match (str: {string_sim:.2f}, word: {fuzzy_word_sim:.2f})"

    return overall_quality, reason


def parse_item(item_string: str) -> tuple[str, str]:
    """
    Parse an item string to determine type and extract query.

    Args:
        item_string: Input string like "Bohemian Rhapsody", "album:Dark Side", etc.
                    Also supports Spotify URIs like "spotify:track:123"
                    "single:" searches for releases (like albums) with fewer tracks

    Returns:
        tuple: (item_type, query) where item_type is "track", "album", "uri", or "auto"
    """
    item_string = item_string.strip()

    # Handle Spotify URIs
    if item_string.startswith("spotify:"):
        return "uri", item_string

    # Handle album/release prefixes (albums, singles, EPs)
    if item_string.startswith("album:"):
        return "album", item_string[6:].strip()
    if item_string.startswith("single:"):
        return "album", item_string[7:].strip()  # Treat singles like albums

    # Handle track prefixes (individual tracks)
    if item_string.startswith("track:"):
        return "track", item_string[6:].strip()

    return "auto", item_string


def search_track(sp: SpotifyClient, query: str) -> SearchResult:
    """
    Search for a track with detailed result information.

    Returns:
        SearchResult with quality assessment
    """
    try:
        results = sp.search(q=query, type="track", limit=1)
        tracks = results["tracks"]["items"]

        if tracks:
            track = tracks[0]
            artists_str = format_artists(track)
            quality, reason = calculate_match_quality(query, track["name"], artists_str)

            resolved_track = ResolvedTrack(
                uri=track["uri"],
                name=track["name"],
                artists=artists_str,
                source_query=f"track:{query}",
            )

            return SearchResult(
                query=query,
                search_type="track",
                found_item=track,
                match_quality=quality,
                quality_reason=reason,
                resolved_tracks=[resolved_track] if quality > 0.2 else [],
            )
        return SearchResult(
            query=query,
            search_type="track",
            found_item=None,
            match_quality=0.0,
            quality_reason="No results found",
            resolved_tracks=[],
        )

    except Exception as e:
        return SearchResult(
            query=query,
            search_type="track",
            found_item=None,
            match_quality=0.0,
            quality_reason=f"Search error: {e}",
            resolved_tracks=[],
        )


def search_album(sp: SpotifyClient, query: str) -> SearchResult:
    """
    Search for an album with detailed result information.

    Returns:
        SearchResult with quality assessment
    """
    try:
        results = sp.search(q=query, type="album", limit=1)
        albums = results["albums"]["items"]

        if albums:
            album = albums[0]
            album_artists = ", ".join([artist["name"] for artist in album["artists"]])
            quality, reason = calculate_match_quality(
                query, album["name"], album_artists
            )

            resolved_tracks = []
            if quality > 0.2:  # Only resolve tracks for decent matches
                try:
                    tracks_result = sp.album_tracks(album["id"])
                    for track in tracks_result["items"]:
                        resolved_tracks.append(
                            ResolvedTrack(
                                uri=track["uri"],
                                name=track["name"],
                                artists=format_artists(track),
                                source_query=f"album:{query}",
                            )
                        )
                except Exception:
                    pass  # Skip track resolution on error

            return SearchResult(
                query=query,
                search_type="album",
                found_item=album,
                match_quality=quality,
                quality_reason=reason,
                resolved_tracks=resolved_tracks,
            )
        return SearchResult(
            query=query,
            search_type="album",
            found_item=None,
            match_quality=0.0,
            quality_reason="No results found",
            resolved_tracks=[],
        )

    except Exception as e:
        return SearchResult(
            query=query,
            search_type="album",
            found_item=None,
            match_quality=0.0,
            quality_reason=f"Search error: {e}",
            resolved_tracks=[],
        )


def search_auto(sp: SpotifyClient, query: str) -> SearchResult:
    """
    Auto search with detailed result information (try tracks first, then albums).

    Returns:
        SearchResult with the best match found
    """
    from dataclasses import replace

    # Try track search first
    track_result = search_track(sp, query)
    if track_result.match_quality > 0.4:  # Good track match
        return replace(track_result, search_type="auto (found track)")

    # Try album search
    album_result = search_album(sp, query)
    if album_result.match_quality > 0.4:  # Good album match
        return replace(album_result, search_type="auto (found album)")

    # Return the better of the two poor matches
    if track_result.match_quality >= album_result.match_quality:
        return replace(track_result, search_type="auto (weak track match)")
    return replace(album_result, search_type="auto (weak album match)")


def resolve_uri(sp: SpotifyClient, uri: str) -> list[ResolvedTrack] | None:
    """
    Resolve a Spotify URI to track(s).

    Args:
        sp: Spotify client
        uri: Spotify URI like "spotify:track:123" or "spotify:album:456"

    Returns:
        list or None: List of ResolvedTrack objects, or None if resolution failed
    """
    try:
        if uri.startswith("spotify:track:"):
            track_id = uri.split(":")[-1]
            track = sp.track(track_id)
            if track:
                return [
                    ResolvedTrack(
                        uri=track["uri"],
                        name=track["name"],
                        artists=format_artists(track),
                        source_query=uri,
                    )
                ]
        elif uri.startswith("spotify:album:"):
            album_id = uri.split(":")[-1]
            album = sp.album(album_id)
            if album:
                resolved_tracks = []
                for track in album["tracks"]["items"]:
                    resolved_tracks.append(
                        ResolvedTrack(
                            uri=track["uri"],
                            name=track["name"],
                            artists=format_artists(track),
                            source_query=uri,
                        )
                    )
                return resolved_tracks
    except Exception:
        pass
    return None


def resolve_items(sp: SpotifyClient, items: list[str]) -> list[SearchResult]:
    """
    Resolve a list of item strings to tracks with detailed search information.

    Args:
        sp: Spotify client
        items: List of item strings to resolve

    Returns:
        list: List of SearchResult objects with quality assessment
    """
    search_results = []

    for item in items:
        item_type, query = parse_item(item)

        if item_type == "uri":
            # Handle URI resolution (create SearchResult for consistency)
            tracks = resolve_uri(sp, query)
            if tracks:
                search_results.append(
                    SearchResult(
                        query=query,
                        search_type="uri",
                        found_item={"uri": query, "type": "uri"},
                        match_quality=1.0,
                        quality_reason="Direct URI match",
                        resolved_tracks=tracks,
                    )
                )
            else:
                search_results.append(
                    SearchResult(
                        query=query,
                        search_type="uri",
                        found_item=None,
                        match_quality=0.0,
                        quality_reason="Invalid or inaccessible URI",
                        resolved_tracks=[],
                    )
                )

        elif item_type == "track":
            result = search_track(sp, query)
            search_results.append(result)

        elif item_type == "album":  # Includes "single:" items
            result = search_album(sp, query)
            search_results.append(result)

        else:  # auto search
            result = search_auto(sp, query)
            search_results.append(result)

    return search_results


def create_playlist_from_tracks(
    sp: SpotifyClient, tracks: list[ResolvedTrack], name: str | None = None
) -> str:
    """
    Create a playlist from resolved tracks.

    Args:
        sp: Spotify client
        tracks: List of ResolvedTrack objects
        name: Optional playlist name (generates default if None)

    Returns:
        str: Created playlist ID
    """
    if not name:
        name = generate_default_name()

    # Get current user info
    user = sp.current_user()
    user_id = user["id"]

    # Create the playlist
    playlist = sp.user_playlist_create(
        user_id, name, public=False, description="Created with spotify-tools"
    )
    playlist_id = playlist["id"]

    # Extract URIs from resolved tracks
    track_uris = [track.uri for track in tracks]

    # Add tracks to playlist in batches (Spotify API limit is 100 per request)
    batch_size = 100
    for i in range(0, len(track_uris), batch_size):
        batch = track_uris[i : i + batch_size]
        sp.playlist_add_items(playlist_id, batch)

    return playlist_id


def generate_default_name() -> str:
    """
    Generate a default playlist name with current timestamp.

    Returns:
        str: Playlist name like "Playlist 2024-01-15 14:30"
    """
    now = datetime.now()
    return f"Playlist {now.strftime('%Y-%m-%d %H:%M')}"
