"""
Random album command for Spotify tools CLI.
"""

import click

from .. import album, cache, config, database, spotify
from ..cli_utils import (
    echo_always,
    echo_debug,
    echo_verbose,
    create_progress_callback,
    output_album,
)


@click.command()
@click.option("--count", default=1, help="Number of albums.")
@click.option("--year", type=int, help="Filter albums by release year.")
@click.pass_context
def random_album(ctx, count, year):
    """Get random album from user's Library.

    Returns random albums of the user's Library. Spotify lacks a randomization
    feature at the album level.

    When using --year, returns only albums released in the specified year.
    All albums are cached for faster subsequent runs. Use the refresh-cache command
    to update an existing cache.

    Inspired by https://shuffle.ninja/
    """
    # Check if we have a cache first
    cache_data = cache.load_albums()

    if cache_data is not None:
        # Use existing cache
        echo_debug(ctx, "Using existing album cache")
        days, hours = cache.calculate_cache_age()
        echo_verbose(ctx, cache.format_cache_age_message(days, hours))

        if year is not None:
            handle_year_filter_sql(ctx, year, count)
        else:
            handle_random_selection_sql(ctx, count)
    else:
        # No cache available, need to build one (requires Spotify client)
        echo_always(
            "No album cache found. Building cache now (this may take a while)..."
        )
        cache_dir = config.user_cache_dir()
        with spotify.create_spotify_client(cache_dir) as sp:
            refresh_album_cache(ctx, sp, max_workers=ctx.obj.get("MAX_WORKERS", 5))

        # Now that we have a cache, try again with recursive call
        random_album(ctx, count, year)


def refresh_album_cache(ctx, sp, max_workers=5, show_progress=True):
    """
    Refresh the album cache.

    Args:
        ctx: Click context.
        sp: Spotify client.
        max_workers: Maximum number of parallel workers.
        show_progress: Whether to show a progress bar.
    """
    echo_verbose(ctx, f"Using parallel fetching with {max_workers} workers")

    # Create progress bar for fetching albums
    total_albums = album.get_total_album_count(sp)

    if show_progress:
        with click.progressbar(
            length=total_albums,
            label="Fetching and organizing all albums",
        ) as bar:
            progress_callback = create_progress_callback(bar)

            albums_by_year = album.fetch_all_albums_parallel(
                sp, progress_callback, max_workers=max_workers
            )
    else:
        albums_by_year = album.fetch_all_albums_parallel(sp, max_workers=max_workers)

    # Report cache refresh
    total_albums = database.get_album_count()
    echo_always(f"Album database refreshed with {total_albums} albums.")

    # Don't need to return anything, we're saving directly to the database


def handle_year_filter_sql(ctx, year, count):
    """Handle filtering and selecting albums by year using SQLite."""
    # Use SQLite's ORDER BY RANDOM() directly for efficient random selection
    selected_albums = album.get_random_albums(count, year)
    
    if not selected_albums:
        echo_always(f"No albums from {year} found in your library.")
        return
        
    echo_verbose(ctx, f"Selected {len(selected_albums)} albums from {year}.")
    
    # Output selected albums
    for alb in selected_albums:
        output_album(ctx, alb)


def handle_random_selection_sql(ctx, count):
    """Handle random album selection without year filter using SQLite."""
    echo_debug(ctx, f"Selecting {count} random albums from all years using SQL")

    # Get random albums directly from the database
    selected_albums = album.get_random_albums(count)

    if selected_albums:
        for alb in selected_albums:
            output_album(ctx, alb)
    else:
        echo_always("No albums found in your library.")