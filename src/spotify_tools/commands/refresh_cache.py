"""
Refresh cache command for Spotify tools CLI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from spotify_tools import config, spotify
from spotify_tools.commands.random_album import refresh_album_cache

if TYPE_CHECKING:
    from click import Context


@click.command(name="refresh-cache")
@click.option("--max-workers", default=5, help="Maximum number of parallel workers.")
@click.pass_context
def refresh_cache(ctx: Context, max_workers: int) -> None:
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
