import json
import random

import click
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from .config import load_config, user_cache_dir


@click.command()
@click.version_option()
@click.argument("count", required=False, default=1)
def cli(count):
    conf = load_config()
    client_id = conf["client_id"]
    client_secret = conf["client_secret"]
    redirect_uri = conf["redirect_uri"]
    cache_dir = user_cache_dir()
    scope = "user-library-read"

    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            cache_handler=spotipy.CacheFileHandler(cache_path=cache_dir)
        )
    )

    probe = sp.current_user_saved_albums(limit=1)
    total_count = probe["total"]
    random_list = [random.randint(0, total_count) for i in range(count)]
    for random_index in random_list:
        results = sp.current_user_saved_albums(limit=1, offset=random_index)
        print("%s" % (results["items"][0]["album"]["uri"]))
