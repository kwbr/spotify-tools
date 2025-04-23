"""
Album-related functionality for Spotify tools.
"""

import random
import secrets

from . import cache


def get_total_album_count(sp):
    """
    Get the total number of albums in the user's library.

    Args:
        sp: Spotify client.

    Returns:
        int: Total number of albums.
    """
    probe = sp.current_user_saved_albums(limit=1)
    return probe["total"]


def fetch_all_albums(sp, progress_callback=None):
    """
    Fetch all albums from Spotify and organize them by year.

    Args:
        sp: Spotify client.
        progress_callback: Optional callback function for progress updates.

    Returns:
        dict: Albums organized by year.
    """
    albums_by_year = {}
    total_albums = get_total_album_count(sp)
    batch_size = 50  # Spotify API limit
    offset = 0

    while offset < total_albums:
        batch = sp.current_user_saved_albums(limit=batch_size, offset=offset)
        process_album_batch(batch, albums_by_year)

        offset += batch_size

        if progress_callback:
            progress_value = min(offset, total_albums)
            progress_callback(progress_value, total_albums)

    # Save to cache
    cache.save_albums(albums_by_year)
    return albums_by_year


def process_album_batch(batch, albums_by_year):
    """
    Process a batch of albums and organize by year.

    Args:
        batch: Batch of albums from Spotify API.
        albums_by_year: Dictionary to populate with albums by year.
    """
    for item in batch["items"]:
        album = item["album"]
        album_year = extract_year_from_date(album["release_date"])

        # Convert year to string for consistent dictionary keys
        year_str = str(album_year)

        if year_str not in albums_by_year:
            albums_by_year[year_str] = []

        albums_by_year[year_str].append(
            {
                "uri": album["uri"],
                "name": album["name"],
                "artists": extract_artist_names(album["artists"]),
                "added_at": item["added_at"],
            }
        )


def extract_year_from_date(date_string):
    """Extract year from a date string (handles YYYY, YYYY-MM, YYYY-MM-DD)."""
    return int(date_string.split("-")[0])


def extract_artist_names(artists_data):
    """Extract artist names from artist data objects."""
    return [artist["name"] for artist in artists_data]


def select_random_albums(albums, count):
    """
    Select random albums from a list, respecting count limit.

    Args:
        albums: List of albums to select from.
        count: Number of albums to select.

    Returns:
        list: Selected random albums.
    """
    return random.sample(albums, min(count, len(albums)))


def get_random_indexes(total, count):
    """Generate random indexes within a range."""
    return [secrets.randbelow(total) for _ in range(count)]


def get_random_albums_by_index(sp, count):
    """
    Get random albums by generating random indexes.

    Args:
        sp: Spotify client.
        count: Number of albums to select.

    Returns:
        list: List of albums.
    """
    total_count = get_total_album_count(sp)
    random_indexes = get_random_indexes(total_count, count)

    albums = []
    for index in random_indexes:
        album = fetch_single_album(sp, index)
        albums.append(album)

    return albums


def fetch_single_album(sp, index):
    """Fetch a single album by index."""
    results = sp.current_user_saved_albums(limit=1, offset=index)
    return results["items"][0]["album"]


def get_albums_by_year(sp, year, count=None, from_cache=True):
    """
    Get albums by year, optionally selecting random ones.

    Args:
        sp: Spotify client.
        year: Year to filter by.
        count: Optional number of random albums to select.
        from_cache: Whether to use cached data.

    Returns:
        list: Albums from the specified year.
    """
    # Try to load from cache first if requested
    cache_data = cache.load_albums() if from_cache else None

    if cache_data is None:
        albums_by_year = fetch_all_albums(sp)
    else:
        albums_by_year = cache_data["albums_by_year"]

    # Convert year to string for dictionary lookup
    year_str = str(year)
    matching_albums = albums_by_year.get(year_str, [])

    if count and matching_albums:
        return select_random_albums(matching_albums, count)

    return matching_albums


def count_total_albums(albums_by_year):
    """Count the total number of albums across all years."""
    return sum(len(albums) for albums in albums_by_year.values())


def get_sorted_years(albums_by_year):
    """Get a sorted list of years from the albums dictionary."""
    return sorted([int(year) for year in albums_by_year.keys()])


def format_album_output(album, verbose=False):
    """
    Format album information for output.

    Args:
        album: Album data.
        verbose: Whether to include detailed information.

    Returns:
        str: Formatted album information.
    """
    # Base output is just the URI
    output = album["uri"]

    # Add album details in verbose mode
    if verbose:
        artists = ", ".join(album.get("artists", ["Unknown"]))
        output = f"{output}\nAlbum: {album['name']} by {artists}"

    return output
