import secrets
import random
import json
import time
from pathlib import Path

import click
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from . import config


###===================================================================
### CLI Group Definition
###===================================================================

@click.group()
@click.option('--verbose', '-v', count=True, help="Increase verbosity (can use multiple times)")
@click.pass_context
def cli(ctx, verbose):
    """A tool for working with Spotify."""
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose


###===================================================================
### Echo Functions
###===================================================================

def echo_debug(ctx, message):
    """Echo debug message if verbose level >= 2."""
    if ctx.obj['VERBOSE'] >= 2:
        click.echo(f"DEBUG: {message}")


def echo_verbose(ctx, message):
    """Echo verbose message if verbose level >= 1."""
    if ctx.obj['VERBOSE'] >= 1:
        click.echo(f"INFO: {message}")


def echo_always(message):
    """Echo message regardless of verbosity level."""
    click.echo(message)


###===================================================================
### Constants
###===================================================================

def default_batch_size():
    """Spotify API limit for batch requests."""
    return 50


def default_ping_timeout():
    """Default timeout for API pings."""
    return 5000


###===================================================================
### Cache Management
###===================================================================

def get_albums_cache_path():
    """Get path to the comprehensive albums cache file."""
    cache_dir = config.user_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "albums_cache.json"


def save_all_albums_to_cache(albums_by_year):
    """Save all albums to cache with year grouping."""
    cache_path = get_albums_cache_path()
    cache_data = create_cache_data(albums_by_year)
    write_json_to_file(cache_path, cache_data)


def create_cache_data(albums_by_year):
    """Create a cache data structure with timestamp."""
    return {
        "timestamp": time.time(),
        "albums_by_year": albums_by_year
    }


def write_json_to_file(path, data):
    """Write JSON data to a file."""
    with open(path, "w") as f:
        json.dump(data, f)


def load_albums_from_cache(ctx):
    """Load all albums from cache if available."""
    cache_path = get_albums_cache_path()
    echo_debug(ctx, f"Looking for cache at: {cache_path}")
    if not cache_path.exists():
        return None
    return load_json_with_error_handling(cache_path, ctx)


def load_json_with_error_handling(path, ctx):
    """Load JSON from file with error handling."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        echo_debug(ctx, f"Error reading cache file: {e}")
        return None


###===================================================================
### Spotify API Interactions
###===================================================================

def create_spotify_client(cache_dir):
    """Create and configure a Spotify API client."""
    conf = config.load_config()
    token_cache_path = Path(cache_dir / "token")
    
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope="user-library-read",
            client_id=conf["client_id"],
            client_secret=conf["client_secret"],
            redirect_uri=conf["redirect_uri"],
            cache_handler=spotipy.CacheFileHandler(cache_path=token_cache_path),
        ),
    )


def fetch_all_albums(sp, ctx):
    """Fetch all albums from Spotify and organize them by year."""
    albums_by_year = {}
    total_albums = get_total_album_count(sp)
    
    with click.progressbar(
        length=total_albums,
        label='Fetching and organizing all albums',
    ) as bar:
        fetch_albums_in_batches(sp, total_albums, albums_by_year, bar)
    
    save_all_albums_to_cache(albums_by_year)
    return albums_by_year


def get_total_album_count(sp):
    """Get the total number of albums in the user's library."""
    probe = sp.current_user_saved_albums(limit=1)
    return probe["total"]


def fetch_albums_in_batches(sp, total_albums, albums_by_year, progress_bar):
    """Fetch albums in batches and organize by year."""
    batch_size = default_batch_size()
    offset = 0
    
    while offset < total_albums:
        batch = sp.current_user_saved_albums(limit=batch_size, offset=offset)
        process_album_batch(batch, albums_by_year)
        
        offset += batch_size
        progress_bar.update(min(batch_size, total_albums - offset + batch_size))


def process_album_batch(batch, albums_by_year):
    """Process a batch of albums and organize by year."""
    for item in batch["items"]:
        album = item["album"]
        album_year = extract_year_from_date(album["release_date"])
        
        ensure_year_entry_exists(albums_by_year, album_year)
        add_album_to_year(albums_by_year, album_year, album, item["added_at"])


def extract_year_from_date(date_string):
    """Extract year from a date string (handles YYYY, YYYY-MM, YYYY-MM-DD)."""
    return int(date_string.split("-")[0])


def ensure_year_entry_exists(albums_by_year, year):
    """Ensure a year entry exists in the albums dictionary."""
    if year not in albums_by_year:
        albums_by_year[year] = []


def add_album_to_year(albums_by_year, year, album, added_at):
    """Add an album to the appropriate year in the collection."""
    albums_by_year[year].append({
        "uri": album["uri"],
        "name": album["name"],
        "artists": extract_artist_names(album["artists"]),
        "added_at": added_at
    })


def extract_artist_names(artists_data):
    """Extract artist names from artist data objects."""
    return [artist["name"] for artist in artists_data]


###===================================================================
### Cache Age Calculation
###===================================================================

def calculate_cache_age(timestamp):
    """Calculate the age of the cache in days and hours."""
    age_seconds = time.time() - timestamp
    days = int(age_seconds / (60 * 60 * 24))
    hours = int((age_seconds % (60 * 60 * 24)) / (60 * 60))
    return days, hours


def format_cache_age_message(days, hours):
    """Format a message about cache age."""
    if days > 0:
        return f"Using cached albums database ({days} days, {hours} hours old)."
    return f"Using cached albums database ({hours} hours old)."


###===================================================================
### Album Selection
###===================================================================

def select_random_albums(albums, count):
    """Select random albums from a list, respecting count limit."""
    return random.sample(
        albums,
        min(count, len(albums))
    )


def get_random_indexes(total, count):
    """Generate random indexes within a range."""
    return [secrets.randbelow(total) for i in range(count)]


def output_album(album, ctx):
    """Output album based on verbosity level."""
    # In any verbosity level, always output the URI
    echo_always(album['uri'])
    
    # Add album details in verbose mode
    if ctx.obj['VERBOSE'] >= 1:
        artists = join_artists(album.get("artists", ["Unknown"]))
        echo_verbose(ctx, f"Album: {album['name']} by {artists}")


def join_artists(artists):
    """Join artist names into a comma-separated string."""
    return ", ".join(artists)


###===================================================================
### CLI Commands
###===================================================================

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
    sp = create_spotify_client(cache_dir)
    
    if year is not None or refresh:
        handle_year_or_refresh_option(sp, year, count, refresh, ctx)
    else:
        handle_simple_random_selection(sp, count, ctx)


def handle_year_or_refresh_option(sp, year, count, refresh, ctx):
    """Handle when year filter or refresh is specified."""
    # Try to load from cache first unless refresh is requested
    cache_data = None if refresh else load_albums_from_cache(ctx)
    
    if cache_data is not None:
        albums_by_year = cache_data["albums_by_year"]
        days, hours = calculate_cache_age(cache_data["timestamp"])
        echo_verbose(ctx, format_cache_age_message(days, hours))
    else:
        albums_by_year = fetch_all_albums(sp, ctx)
    
    # Handle year filter if specified
    if year is not None:
        handle_year_filter(albums_by_year, year, count, ctx)
    else:
        # Just report cache refresh
        total_albums = count_total_albums(albums_by_year)
        echo_verbose(ctx, f"Album database refreshed with {total_albums} albums.")


def handle_year_filter(albums_by_year, year, count, ctx):
    """Handle filtering and selecting albums by year."""
    year_str = str(year)
    matching_albums = albums_by_year.get(year_str, [])
    
    if not matching_albums:
        echo_verbose(ctx, f"No albums from {year} found in your library.")
        return
    
    echo_verbose(ctx, f"Found {len(matching_albums)} albums from {year}.")
    
    # Select and display random albums
    selected_albums = select_random_albums(matching_albums, count)
    for album in selected_albums:
        output_album(album, ctx)


def handle_simple_random_selection(sp, count, ctx):
    """Handle random album selection without year filter."""
    total_count = get_total_album_count(sp)
    random_indexes = get_random_indexes(total_count, count)
    
    for index in random_indexes:
        album = fetch_single_album(sp, index)
        output_album(album, ctx)


def fetch_single_album(sp, index):
    """Fetch a single album by index."""
    results = sp.current_user_saved_albums(limit=1, offset=index)
    return results["items"][0]["album"]


def count_total_albums(albums_by_year):
    """Count the total number of albums across all years."""
    return sum(len(albums) for albums in albums_by_year.values())


@cli.command()
@click.pass_context
def list_years(ctx):
    """List all years with albums in your library and count per year."""
    cache_data = load_albums_from_cache(ctx)
    
    if cache_data is None:
        echo_always("No album cache found. Run 'spt random-album --refresh' to create one.")
        return
    
    albums_by_year = cache_data["albums_by_year"]
    years = get_sorted_years(albums_by_year)
    
    total_albums = count_total_albums(albums_by_year)
    echo_always(f"Total albums in library: {total_albums}\n")
    echo_always("Albums by year:")
    
    display_albums_by_year(albums_by_year, years)


def get_sorted_years(albums_by_year):
    """Get a sorted list of years from the albums dictionary."""
    return sorted([int(year) for year in albums_by_year.keys()])


def display_albums_by_year(albums_by_year, years):
    """Display album counts by year."""
    for year in years:
        year_str = str(year)
        count = len(albums_by_year[year_str])
        echo_always(f"{year}: {count} albums")
