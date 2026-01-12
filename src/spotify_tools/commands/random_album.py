"""
Random album command for Spotify tools CLI.
"""

import click

from spotify_tools import album, cache, database, perf
from spotify_tools.cli_utils import (
    create_progress_callback,
    echo_debug,
    echo_info,
    echo_verbose,
    output_album,
)


@click.command()
@click.option("--count", default=1, help="Number of albums.")
@click.option("--year", type=int, help="Filter albums by release year.")
@click.option("--timing", is_flag=True, help="Show timing information.")
@click.pass_context
def random_album(ctx, count, year, timing):
    """Get random album from user's Library.

    Returns random albums of the user's Library. Spotify lacks a randomization
    feature at the album level.

    When using --year, returns only albums released in the specified year.
    All albums are cached for faster subsequent runs. Use the refresh-cache command
    to update an existing cache.

    Inspired by https://shuffle.ninja/
    """
    # Configure timing output
    if not timing:
        # Monkey patch the measure_time context manager to do nothing
        perf.measure_time = lambda name="Operation": perf.silent_timer(name)
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
        # No cache available, exit with error
        echo_info("Error: No album cache found. Please run 'spt refresh-cache' first.")
        raise click.Abort()


def refresh_album_cache(ctx, sp, max_workers=5, show_progress=True, db_path=None):
    """
    Refresh the album cache.

    Args:
        ctx: Click context.
        sp: Spotify client.
        max_workers: Maximum number of parallel workers.
        show_progress: Whether to show a progress bar.
        db_path: Optional database path for testing.
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

            album.fetch_all_albums_parallel(
                sp, progress_callback, max_workers=max_workers, db_path=db_path
            )
    else:
        album.fetch_all_albums_parallel(sp, max_workers=max_workers, db_path=db_path)

    # Report cache refresh
    total_albums = database.get_album_count(db_path=db_path)
    echo_info(f"Album database refreshed with {total_albums} albums.")


def handle_year_filter_sql(ctx, year, count):
    """Handle filtering and selecting albums by year using SQLite."""
    # Use SQLite's ORDER BY RANDOM() directly for efficient random selection
    # Pass verbosity level to optimize the query
    verbose = ctx.obj["VERBOSE"] >= 1
    with perf.measure_time(
        f"get_random_albums(count={count}, year={year}, verbose={verbose})"
    ):
        selected_albums = album.get_random_albums(count, year, verbose)

    if not selected_albums:
        echo_info(f"No albums from {year} found in your library.")
        return

    echo_verbose(ctx, f"Selected {len(selected_albums)} albums from {year}.")

    # Output selected albums
    for alb in selected_albums:
        output_album(ctx, alb)


def handle_random_selection_sql(ctx, count):
    """Handle random album selection without year filter using SQLite."""
    echo_debug(ctx, f"Selecting {count} random albums from all years using SQL")

    # Get random albums directly from the database
    # Pass verbosity level to optimize the query
    verbose = ctx.obj["VERBOSE"] >= 1
    with perf.measure_time(f"get_random_albums(count={count}, verbose={verbose})"):
        selected_albums = album.get_random_albums(count, verbose=verbose)

    if selected_albums:
        for alb in selected_albums:
            output_album(ctx, alb)
    else:
        echo_info("No albums found in your library.")
