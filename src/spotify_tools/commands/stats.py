"""
Stats command to view play history statistics.
"""

import click

from spotify_tools import database
from spotify_tools.cli_utils import echo_info


@click.command()
@click.option(
    "--type",
    "stat_type",
    type=click.Choice(["albums", "tracks", "summary"], case_sensitive=False),
    default="summary",
    help="Type of statistics to display.",
)
@click.option(
    "--limit",
    default=20,
    type=int,
    help="Number of items to show for albums/tracks (default: 20).",
)
@click.pass_context
def stats(ctx, stat_type, limit):
    """
    View play history statistics.

    Show statistics based on your tracked play history. Run sync-history
    regularly to keep your statistics up to date.
    """
    if not database.database_exists():
        echo_info("No play history found. Run 'spt sync-history' first.")
        return

    total_plays = database.get_total_play_count()

    if total_plays == 0:
        echo_info("No play history found. Run 'spt sync-history' to start tracking.")
        return

    if stat_type == "summary":
        show_summary()
    elif stat_type == "albums":
        show_top_albums(limit)
    elif stat_type == "tracks":
        show_top_tracks(limit)


def show_summary():
    """Show summary statistics."""
    total_plays = database.get_total_play_count()
    album_stats = database.get_play_count_by_album()
    track_stats = database.get_play_count_by_track()

    echo_info(f"Total plays tracked: {total_plays}")
    echo_info(f"Unique albums played: {len(album_stats)}")
    echo_info(f"Unique tracks played: {len(track_stats)}")

    if album_stats:
        echo_info("\nTop 5 Albums:")
        for i, (uri, info) in enumerate(list(album_stats.items())[:5], 1):
            artists = ", ".join(info["artists"]) if info["artists"] else "Unknown"
            echo_info(
                f"  {i}. {info['name']} by {artists} - {info['play_count']} plays"
            )

    if track_stats:
        echo_info("\nTop 5 Tracks:")
        for i, (uri, info) in enumerate(list(track_stats.items())[:5], 1):
            artists = ", ".join(info["artists"])
            echo_info(
                f"  {i}. {info['name']} by {artists} - {info['play_count']} plays"
            )


def show_top_albums(limit: int):
    """Show top albums by play count."""
    album_stats = database.get_play_count_by_album()

    if not album_stats:
        echo_info("No album statistics found.")
        return

    echo_info(f"Top {min(limit, len(album_stats))} Albums by Play Count:\n")

    for i, (uri, info) in enumerate(list(album_stats.items())[:limit], 1):
        artists = ", ".join(info["artists"]) if info["artists"] else "Unknown"
        echo_info(f"{i:3}. {info['name']} by {artists}")
        echo_info(f"     Plays: {info['play_count']}")
        echo_info(f"     Last played: {info['last_played']}")
        echo_info(f"     URI: {uri}")
        echo_info("")


def show_top_tracks(limit: int):
    """Show top tracks by play count."""
    track_stats = database.get_play_count_by_track()

    if not track_stats:
        echo_info("No track statistics found.")
        return

    echo_info(f"Top {min(limit, len(track_stats))} Tracks by Play Count:\n")

    for i, (uri, info) in enumerate(list(track_stats.items())[:limit], 1):
        artists = ", ".join(info["artists"])
        echo_info(f"{i:3}. {info['name']} by {artists}")
        echo_info(f"     Album: {info['album_name']}")
        echo_info(f"     Plays: {info['play_count']}")
        echo_info(f"     Last played: {info['last_played']}")
        echo_info(f"     URI: {uri}")
        echo_info("")
