import secrets
import random
import json
import time
from pathlib import Path

import click
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from . import config


@click.group()
@click.version_option()
def cli():
    """A tool for working with Spotify."""


def get_albums_cache_path():
    """Get path to the comprehensive albums cache file."""
    cache_dir = config.user_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "albums_cache.json"


def save_all_albums_to_cache(albums_by_year):
    """Save all albums to cache with year grouping."""
    cache_path = get_albums_cache_path()
    cache_data = {
        "timestamp": time.time(),
        "albums_by_year": albums_by_year
    }
    with open(cache_path, "w") as f:
        json.dump(cache_data, f)


def load_albums_from_cache():
    """Load all albums from cache if available."""
    cache_path = get_albums_cache_path()
    print(f"Looking for cache at: {cache_path}")  # Debug line
    if cache_path.exists():
        with open(cache_path, "r") as f:
            return json.load(f)
    return None


def fetch_all_albums(sp):
    """Fetch all albums from Spotify and organize them by year."""
    albums_by_year = {}

    # Fetch albums in batches of 50 (Spotify API limit)
    batch_size = 50
    probe = sp.current_user_saved_albums(limit=1)
    total_albums = probe["total"]

    with click.progressbar(
        length=total_albums,
        label='Fetching and organizing all albums',
    ) as bar:
        offset = 0
        while offset < total_albums:
            batch = sp.current_user_saved_albums(limit=batch_size, offset=offset)

            # Process albums and organize by year
            for item in batch["items"]:
                album = item["album"]
                release_date = album["release_date"]
                # Handle different date formats (YYYY, YYYY-MM, YYYY-MM-DD)
                album_year = int(release_date.split("-")[0])

                # Create year entry if it doesn't exist
                if album_year not in albums_by_year:
                    albums_by_year[album_year] = []

                # Save album info
                albums_by_year[album_year].append({
                    "uri": album["uri"],
                    "name": album["name"],
                    "artists": [artist["name"] for artist in album["artists"]],
                    "added_at": item["added_at"]
                })

            offset += batch_size
            bar.update(min(batch_size, total_albums - offset + batch_size))

    # Save all albums to cache
    save_all_albums_to_cache(albums_by_year)
    return albums_by_year


@cli.command()
@click.option("--count", default=1, help="Number of albums.")
@click.option("--year", type=int, help="Filter albums by release year.")
@click.option("--refresh", is_flag=True, help="Refresh the album cache.")
def random_album(count, year, refresh):
    """Get random album from user's Library.

    Returns random albums of the user's Library. Spotify lacks a randomization
    feature at the album level.

    When using --year, returns only albums released in the specified year.
    All albums are cached for faster subsequent runs. Use --refresh to update the cache.

    Inspired by https://shuffle.ninja/
    """
    cache_dir = config.user_cache_dir()
    conf = config.load_config()
    client_id = conf["client_id"]
    client_secret = conf["client_secret"]
    redirect_uri = conf["redirect_uri"]
    scope = "user-library-read"
    toke_cache_path = Path( cache_dir / "token" )

    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            cache_handler=spotipy.CacheFileHandler(cache_path=toke_cache_path),
        ),
    )

    # Check if we need to use the comprehensive cache
    if year is not None or refresh:
        # Try to load from cache first unless refresh is requested
        cache_data = None if refresh else load_albums_from_cache()

        if cache_data is not None:
            albums_by_year = cache_data["albums_by_year"]
            cache_age = time.time() - cache_data["timestamp"]
            days_old = int(cache_age / (60 * 60 * 24))
            hours_old = int((cache_age % (60 * 60 * 24)) / (60 * 60))

            if days_old > 0:
                click.echo(f"Using cached albums database ({days_old} days, {hours_old} hours old).")
            else:
                click.echo(f"Using cached albums database ({hours_old} hours old).")
        else:
            # Fetch all albums and organize by year
            albums_by_year = fetch_all_albums(sp)

        # Get albums for the specified year
        if year is not None:
            year_str = str(year)
            matching_albums = albums_by_year.get(year_str, [])

            if not matching_albums:
                click.echo(f"No albums from {year} found in your library.")
                return

            click.echo(f"Found {len(matching_albums)} albums from {year}.")

            # Select random albums from the filtered list
            selected_albums = random.sample(
                matching_albums,
                min(count, len(matching_albums))
            )

            for album in selected_albums:
                # Print album name and artists for better context
                artists = ", ".join(album.get("artists", ["Unknown"]))
                click.echo(f"{album['name']} by {artists}")
                click.echo(f"{album['uri']}")
        else:
            # If year not specified but refresh was requested, just report cache refresh
            click.echo(f"Album database refreshed with {sum(len(albums) for albums in albums_by_year.values())} albums.")
    else:
        # The original random selection logic when no year filter is specified and no refresh needed
        probe = sp.current_user_saved_albums(limit=1)
        total_count = probe["total"]
        random_list = [secrets.randbelow(total_count) for i in range(count)]
        for random_index in random_list:
            results = sp.current_user_saved_albums(limit=1, offset=random_index)
            album = results["items"][0]["album"]
            artists = ", ".join(artist["name"] for artist in album["artists"])
            click.echo(f"{album['uri']} - {album['name']} by {artists}")


@cli.command()
def list_years():
    """List all years with albums in your library and count per year."""
    cache_data = load_albums_from_cache()

    if cache_data is None:
        click.echo("No album cache found. Run 'spt random-album --refresh' to create one.")
        return

    albums_by_year = cache_data["albums_by_year"]
    years = sorted([int(year) for year in albums_by_year.keys()])

    total_albums = sum(len(albums) for albums in albums_by_year.values())
    click.echo(f"Total albums in library: {total_albums}\n")
    click.echo("Albums by year:")

    for year in years:
        count = len(albums_by_year[year])
        click.echo(f"{year}: {count} albums")
