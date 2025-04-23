import secrets
import random

import click
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from . import config


@click.group()
@click.version_option()
def cli():
    """A tool for working with Spotify."""


@cli.command()
@click.option("--count", default=1, help="Number of albums.")
@click.option("--year", type=int, help="Filter albums by release year.")
def random_album(count, year):
    """Get random album from user's Library.

    Returns random albums of the user's Library. Spotify lacks a randomization
    feature at the album level.

    When using --year, returns only albums released in the specified year.

    Inspired by https://shuffle.ninja/
    """
    cache_dir = config.user_cache_dir()
    conf = config.load_config()
    client_id = conf["client_id"]
    client_secret = conf["client_secret"]
    redirect_uri = conf["redirect_uri"]
    scope = "user-library-read"

    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            cache_handler=spotipy.CacheFileHandler(cache_path=cache_dir),
        ),
    )

    # If no year filter, use the original random selection logic
    if year is None:
        probe = sp.current_user_saved_albums(limit=1)
        total_count = probe["total"]
        random_list = [secrets.randbelow(total_count) for i in range(count)]
        for random_index in random_list:
            results = sp.current_user_saved_albums(limit=1, offset=random_index)
            click.echo("{}".format(results["items"][0]["album"]["uri"]))
    else:
        # When filtering by year, we need to gather all matching albums first
        matching_albums = []

        # Fetch albums in batches of 50 (Spotify API limit)
        batch_size = 50
        probe = sp.current_user_saved_albums(limit=1)
        total_albums = probe["total"]

        with click.progressbar(
            length=total_albums,
            label=f'Filtering albums from {year}',
        ) as bar:
            offset = 0
            while offset < total_albums:
                batch = sp.current_user_saved_albums(limit=batch_size, offset=offset)

                # Filter albums by release year
                for item in batch["items"]:
                    album = item["album"]
                    release_date = album["release_date"]
                    # Handle different date formats (YYYY, YYYY-MM, YYYY-MM-DD)
                    album_year = int(release_date.split("-")[0])

                    if album_year == year:
                        matching_albums.append(album)

                offset += batch_size
                bar.update(min(batch_size, total_albums - offset + batch_size))

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
            click.echo("{}".format(album["uri"]))
