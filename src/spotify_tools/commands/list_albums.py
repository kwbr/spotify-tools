"""
List albums command for Spotify tools CLI.
"""

import click

from .. import cache
from ..cli_utils import echo_always


@click.command()
@click.option("--count-by-year", is_flag=True, help="List album count by year.")
@click.pass_context
def list_albums(ctx, count_by_year):
    """List all albums in your library and count per year."""
    cache_data = cache.load_albums()

    if cache_data is None:
        echo_always("No album cache found. Run 'spt refresh-cache' to create one.")
        return

    # Use the album counts from cache_data (no redundant query)
    album_counts = cache_data["album_counts"]
    total_albums = sum(album_counts.values())
    years = sorted(album_counts.keys())

    # Always show album counts by year - no need for different paths
    echo_always(f"Total albums in library: {total_albums}\n")
    echo_always("Albums by year:")

    for year in years:
        echo_always(f"{year}: {album_counts[year]} albums")
