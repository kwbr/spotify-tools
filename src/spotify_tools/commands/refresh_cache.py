"""
Refresh cache command for Spotify tools CLI.
"""

import click

from .. import config, spotify
from .random_album import refresh_album_cache


@click.command(name="refresh-cache")
@click.option("--max-workers", default=5, help="Maximum number of parallel workers.")
@click.pass_context
def refresh_cache(ctx, max_workers):
    """Force a refresh of the album cache.

    This command updates an existing cache or creates a new one by fetching all albums
    from your Spotify library. While the random-album command will automatically create
    a cache if needed, this command can be used to manually update the cache when
    you've added new albums to your Spotify library.

    The cache is stored in a SQLite database for efficient access.
    """
    cache_dir = config.user_cache_dir()

    with spotify.create_spotify_client(cache_dir) as sp:
        refresh_album_cache(ctx, sp, max_workers=max_workers)