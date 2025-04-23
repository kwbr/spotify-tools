"""
Command line interface for Spotify tools.
"""

import click

from . import album, cache, config, spotify


# CLI Setup and Output Functions


@click.group()
@click.option(
    "--verbose", "-v", count=True, help="Increase verbosity (can use multiple times)"
)
@click.version_option()
@click.pass_context
def cli(ctx, verbose):
    """A tool for working with Spotify."""
    ctx.ensure_object(dict)
    ctx.obj["VERBOSE"] = verbose


def echo_debug(ctx, message):
    """Echo debug message if verbose level >= 2."""
    if ctx.obj["VERBOSE"] >= 2:
        click.echo(f"DEBUG: {message}")


def echo_verbose(ctx, message):
    """Echo verbose message if verbose level >= 1."""
    if ctx.obj["VERBOSE"] >= 1:
        click.echo(f"INFO: {message}")


def echo_always(message):
    """Echo message regardless of verbosity level."""
    click.echo(message)


def create_progress_callback(progress_bar):
    """Create a progress callback function."""

    def update_progress(current, total):
        progress_bar.update(current - progress_bar.pos)

    return update_progress


# CLI Commands


@cli.command()
@click.option("--count", default=1, help="Number of albums.")
@click.option("--year", type=int, help="Filter albums by release year.")
@click.option("--refresh", is_flag=True, help="Refresh the album cache.")
@click.pass_context
def random_album(ctx, count, year, refresh):
    """Get random album from user's Library.

    Returns random albums of the user's Library. Spotify lacks a randomization
    feature at the album level.

    When using --year, returns only albums released in the specified year.
    All albums are cached for faster subsequent runs. Use --refresh to update the cache.

    Inspired by https://shuffle.ninja/
    """
    cache_dir = config.user_cache_dir()

    with spotify.create_spotify_client(cache_dir) as sp:
        if year is not None or refresh:
            handle_year_or_refresh_option(ctx, sp, year, count, refresh)
        else:
            handle_simple_random_selection(ctx, sp, count)


def handle_year_or_refresh_option(ctx, sp, year, count, refresh):
    """Handle when year filter or refresh is specified."""
    # Set up worker count before creating progress bar
    max_workers = ctx.obj.get("MAX_WORKERS", 5)

    # Try to load from cache first unless refresh is requested
    if refresh:
        echo_debug(ctx, "Bypassing cache due to refresh request")
        cache_data = None
    else:
        cache_data = cache.load_albums()
        echo_debug(ctx, f"Looking for cache: {'found' if cache_data else 'not found'}")

    if cache_data is not None:
        albums_by_year = cache_data["albums_by_year"]
        days, hours = cache.calculate_cache_age(cache_data["timestamp"])
        echo_verbose(ctx, cache.format_cache_age_message(days, hours))
    else:
        # Log parallel fetching information before progress bar
        echo_verbose(ctx, f"Using parallel fetching with {max_workers} workers")

        # Create progress bar for fetching albums
        with click.progressbar(
            length=album.get_total_album_count(sp),
            label="Fetching and organizing all albums",
        ) as bar:
            progress_callback = create_progress_callback(bar)

            albums_by_year = album.fetch_all_albums_parallel(
                sp, progress_callback, max_workers=max_workers
            )

    # Handle year filter if specified
    if year is not None:
        handle_year_filter(ctx, sp, albums_by_year, year, count)
    else:
        # Just report cache refresh
        total_albums = album.count_total_albums(albums_by_year)
        echo_verbose(ctx, f"Album database refreshed with {total_albums} albums.")


def handle_year_filter(ctx, sp, albums_by_year, year, count):
    """Handle filtering and selecting albums by year."""
    # Convert integer year parameter to string for dictionary lookup
    year_str = str(year)
    matching_album_dicts = albums_by_year.get(year_str, [])

    if not matching_album_dicts:
        echo_verbose(ctx, f"No albums from {year} found in your library.")
        return

    from spotify_tools.types import Album

    matching_albums = [Album(**album_dict) for album_dict in matching_album_dicts]

    echo_verbose(ctx, f"Found {len(matching_albums)} albums from {year}.")

    # Select and display random albums
    selected_albums = album.select_random_albums(matching_albums, count)
    for alb in selected_albums:
        output_album(ctx, alb)


def handle_simple_random_selection(ctx, sp, count):
    """Handle random album selection without year filter."""
    albums = album.get_random_albums_by_index(sp, count)

    for alb in albums:
        output_album(ctx, alb)


def output_album(ctx, alb):
    """
    Output album based on verbosity level.

    Args:
        ctx: Click context.
        alb: Album object.
    """
    # In any verbosity level, always output the URI
    echo_always(alb.uri)

    # Add album details in verbose mode
    if ctx.obj["VERBOSE"] >= 1:
        artists_str = alb.format_artists()
        echo_verbose(ctx, f"Album: {alb.name} by {artists_str}")


@cli.command()
@click.pass_context
def list_years(ctx):
    """List all years with albums in your library and count per year."""
    cache_data = cache.load_albums()

    if cache_data is None:
        echo_always(
            "No album cache found. Run 'spt random-album --refresh' to create one."
        )
        return

    albums_by_year = cache_data["albums_by_year"]
    years = album.get_sorted_years(albums_by_year)

    total_albums = album.count_total_albums(albums_by_year)
    echo_always(f"Total albums in library: {total_albums}\n")
    echo_always("Albums by year:")

    display_albums_by_year(albums_by_year, years)


def display_albums_by_year(albums_by_year, years):
    """Display album counts by year."""
    for year in years:
        year_str = str(year)
        count = len(albums_by_year[year_str])
        echo_always(f"{year}: {count} albums")


@cli.command()
@click.option(
    "--client-id", prompt="Spotify Client ID", help="Your Spotify API client ID."
)
@click.option(
    "--client-secret",
    prompt="Spotify Client Secret",
    help="Your Spotify API client secret.",
)
@click.option(
    "--redirect-uri",
    default="http://localhost:8888/callback",
    prompt="Redirect URI",
    help="Your Spotify API redirect URI.",
)
@click.pass_context
def configure(ctx, client_id, client_secret, redirect_uri):
    """Configure Spotify API credentials."""
    try:
        config_path = config.create_default_config(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )
        echo_always(f"Configuration saved to {config_path}")
    except Exception as e:
        echo_always(f"Error saving configuration: {e}")
        return 1
