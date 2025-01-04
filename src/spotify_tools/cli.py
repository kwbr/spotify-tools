import secrets

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
def random_album(count):
    """Get random album from user's Library.

    Returns random albums of the user's Library. Spotify lacks a randomization
    feature at the album level.

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

    probe = sp.current_user_saved_albums(limit=1)
    total_count = probe["total"]
    random_list = [secrets.randbelow(total_count) for i in range(count)]
    for random_index in random_list:
        results = sp.current_user_saved_albums(limit=1, offset=random_index)
        click.echo("{}".format(results["items"][0]["album"]["uri"]))
