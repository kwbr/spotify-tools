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
        days, hours = cache.calculate_cache_age(cache_data["timestamp"])
        echo_verbose(ctx, cache.format_cache_age_message(days, hours))
        albums_by_year = cache_data["albums_by_year"]
    else:
        # No cache available, need to build one (requires Spotify client)
        echo_always("No album cache found. Building cache now (this may take a while)...")
        cache_dir = config.user_cache_dir()
        with spotify.create_spotify_client(cache_dir) as sp:
            albums_by_year = refresh_album_cache(
                ctx, 
                sp, 
                max_workers=ctx.obj.get("MAX_WORKERS", 5)
            )
    
    # Now handle the album selection using the cache
    if year is not None:
        # Filter by year
        handle_year_filter(ctx, albums_by_year, year, count)
    else:
        # No filter, get random albums from all years
        handle_simple_random_selection(ctx, albums_by_year, count)


def refresh_album_cache(ctx, sp, max_workers=5, show_progress=True):
    """
    Refresh the album cache and return the albums by year.
    
    Args:
        ctx: Click context.
        sp: Spotify client.
        max_workers: Maximum number of parallel workers.
        show_progress: Whether to show a progress bar.
        
    Returns:
        dict: Albums organized by year.
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
        albums_by_year = album.fetch_all_albums_parallel(
            sp, max_workers=max_workers
        )
    
    # Report cache refresh
    total_albums = album.count_total_albums(albums_by_year)
    echo_always(f"Album database refreshed with {total_albums} albums.")
    
    return albums_by_year


@cli.command(name="refresh-cache")
@click.option("--max-workers", default=5, help="Maximum number of parallel workers.")
@click.pass_context
def refresh_cache(ctx, max_workers):
    """Force a refresh of the album cache.
    
    This command updates an existing cache or creates a new one by fetching all albums
    from your Spotify library. While the random-album command will automatically create 
    a cache if needed, this command can be used to manually update the cache when 
    you've added new albums to your Spotify library.
    """
    cache_dir = config.user_cache_dir()
    
    with spotify.create_spotify_client(cache_dir) as sp:
        refresh_album_cache(ctx, sp, max_workers=max_workers)


def handle_year_filter(ctx, albums_by_year, year, count):
    """Handle filtering and selecting albums by year."""
    # Convert integer year parameter to string for dictionary lookup
    year_str = str(year)
    matching_album_dicts = albums_by_year.get(year_str, [])

    if not matching_album_dicts:
        echo_always(f"No albums from {year} found in your library.")
        return

    matching_albums = [Album(**album_dict) for album_dict in matching_album_dicts]

    echo_verbose(ctx, f"Found {len(matching_albums)} albums from {year}.")

    # Select and display random albums
    selected_albums = album.select_random_albums(matching_albums, count)
    for alb in selected_albums:
        output_album(ctx, alb)


def handle_simple_random_selection(ctx, albums_by_year, count):
    """Handle random album selection without year filter using the provided cache data.
    
    Args:
        ctx: Click context.
        albums_by_year: Dictionary of albums organized by year.
        count: Number of albums to select.
    """
    echo_debug(ctx, f"Selecting {count} random albums from all years")
    
    # Flatten all albums into a single list
    all_albums = []
    for year_albums in albums_by_year.values():
        all_albums.extend([album.Album(**a) for a in year_albums])
    
    if all_albums:
        selected_albums = album.select_random_albums(all_albums, count)
        for alb in selected_albums:
            output_album(ctx, alb)
    else:
        echo_always("No albums found in your library.")


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
            "No album cache found. Run 'spt refresh-cache' to create one."
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
