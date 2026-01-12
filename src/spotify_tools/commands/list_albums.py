"""
List albums command for Spotify tools CLI.
"""

import click

from spotify_tools import album, database
from spotify_tools.cli_utils import echo_always, output_album


@click.command()
@click.option(
    "--sort",
    type=click.Choice(["added", "name", "artist"], case_sensitive=False),
    default="added",
    help=(
        "Sort albums by: added (date added), name (album name), "
        "or artist (artist name)."
    ),
)
@click.option("--year", type=int, help="Filter albums by release year.")
@click.pass_context
def list_albums(ctx, sort, year):
    """List all albums in your library with sorting options."""
    if not database.database_exists():
        echo_always("No album cache found. Run 'spt refresh-cache' to create one.")
        return

    albums = album.get_albums_by_year(year)

    if not albums:
        if year:
            echo_always(f"No albums from {year} found in your library.")
        else:
            echo_always("No albums found in your library.")
        return

    if sort == "added":
        albums.sort(key=lambda a: a.added_at)
    elif sort == "name":
        albums.sort(key=lambda a: a.name.lower())
    elif sort == "artist":
        albums.sort(
            key=lambda a: (
                a.artists[0].lower() if a.artists else "",
                a.name.lower(),
            )
        )

    year_filter = f" from {year}" if year else ""
    echo_always(f"Total albums{year_filter}: {len(albums)}\n")

    for alb in albums:
        output_album(ctx, alb)
