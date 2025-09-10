"""
Album module implementation using the Album type.
"""

import concurrent.futures
import json
import random
import secrets
import threading
from typing import Dict, List, Optional, Any

from . import cache, database
from .types import Album


def get_total_album_count(sp) -> int:
    """
    Get the total number of albums in the user's library.

    Args:
        sp: Spotify client.

    Returns:
        int: Total number of albums.
    """
    probe = sp.current_user_saved_albums(limit=1)
    return probe["total"]


def fetch_all_albums_parallel(sp, progress_callback=None, max_workers=5):
    """
    Fetch all albums from Spotify in parallel and organize them by year.

    Args:
        sp: Spotify client.
        progress_callback: Optional callback function for progress updates.
        max_workers: Maximum number of concurrent workers (to avoid rate limits).

    Returns:
        dict: Albums organized by year.
    """
    albums_by_year = {}
    albums_lock = threading.Lock()  # Lock for thread safety
    total_albums = get_total_album_count(sp)
    batch_size = 50  # Spotify API limit

    # Calculate offsets for all batches
    offsets = list(range(0, total_albums, batch_size))
    completed_batches = 0

    # Create a partial function for fetching a batch with specified offset
    def fetch_batch(offset):
        nonlocal completed_batches
        batch = sp.current_user_saved_albums(limit=batch_size, offset=offset)

        # Thread-safe update of the shared dictionary
        with albums_lock:
            process_album_batch(batch, albums_by_year)

        # Thread-safe progress update
        with albums_lock:
            completed_batches += 1
            if progress_callback:
                progress_value = min(completed_batches * batch_size, total_albums)
                progress_callback(progress_value, total_albums)

        return True

    # Use ThreadPoolExecutor to limit concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all batches to the executor
        futures = [executor.submit(fetch_batch, offset) for offset in offsets]

        # Wait for all futures to complete
        concurrent.futures.wait(futures)

    # Check for any exceptions
    for future in futures:
        exception = future.exception()
        if exception:
            raise exception

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
        # Create Album object
        album = Album.from_spotify_response(item)

        # Extract year from release date
        album_year = extract_year_from_date(item["album"]["release_date"])
        year_str = str(album_year)

        if year_str not in albums_by_year:
            albums_by_year[year_str] = []

        # Store the dictionary representation for serialization
        albums_by_year[year_str].append(album.to_dict())


def extract_year_from_date(date_string):
    """Extract year from a date string (handles YYYY, YYYY-MM, YYYY-MM-DD)."""
    return int(date_string.split("-")[0])


def get_random_albums_by_index(sp, count):
    """
    Get random albums by generating random indexes.

    Args:
        sp: Spotify client.
        count: Number of albums to select.

    Returns:
        list: List of Album objects.
    """
    total_count = get_total_album_count(sp)
    random_indexes = get_random_indexes(total_count, count)

    albums = []
    for index in random_indexes:
        item = fetch_single_album(sp, index)
        album = Album.from_spotify_response(item)
        albums.append(album)

    return albums


def get_random_indexes(total, count):
    """Generate random indexes within a range."""
    return [secrets.randbelow(total) for _ in range(count)]


def fetch_single_album(sp, index):
    """
    Fetch a single album by index.

    Returns:
        dict: The full album item from the API
    """
    results = sp.current_user_saved_albums(limit=1, offset=index)
    return results["items"][0]


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


def get_random_albums(count: int, year: Optional[int] = None) -> List[Album]:
    """
    Get random albums efficiently using the SQLite database.

    This is the preferred method for getting random albums when
    the SQLite database is available.

    Args:
        count: Number of albums to select.
        year: Optional year filter.

    Returns:
        list: List of randomly selected Album objects.
    """
    return database.get_random_albums(count, year)


def get_albums_by_year(year: int) -> List[Album]:
    """
    Get all albums for a specific year using the SQLite database.

    Args:
        year: Year to filter by.

    Returns:
        list: List of Album objects for the specified year.
    """
    return database.get_albums_by_year(year)


def count_total_albums(albums_by_year=None):
    """Count the total number of albums across all years.

    Args:
        albums_by_year: Optional dictionary of albums organized by year.
        If None, gets the count from the database.

    Returns:
        int: Total number of albums.
    """
    if albums_by_year is None:
        # Get the count from the database
        return database.get_album_count()

    # We have actual album data
    return sum(len(albums) for albums in albums_by_year.values())


def get_sorted_years():
    """Get a sorted list of years from the database.

    Returns:
        list: Sorted list of years.
    """
    return database.get_years()
