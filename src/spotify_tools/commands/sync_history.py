"""
Sync play history command for Spotify tools CLI.
"""

import json

import click

from spotify_tools import config, database, spotify
from spotify_tools.cli_utils import echo_info, echo_verbose


def sync_play_history_logic(sp, ctx, limit, db_path=None):
    """
    Core business logic for syncing play history from Spotify.

    Args:
        sp: Spotify client instance
        ctx: Click context for logging
        limit: Maximum number of recently played tracks to fetch
        db_path: Optional database path for testing

    Returns:
        dict: Sync results with keys: plays_synced, new_plays, total_plays
    """
    # Get last sync time to avoid fetching duplicate data
    last_sync = database.get_last_sync_time(db_path=db_path)

    echo_verbose(ctx, f"Last sync: {last_sync or 'Never'}")
    echo_verbose(ctx, f"Fetching up to {limit} recently played tracks...")

    # Fetch recently played tracks
    kwargs = {"limit": min(limit, 50)}
    if last_sync:
        # Only fetch tracks played after last sync
        kwargs["after"] = int(
            __import__("datetime")
            .datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
            .timestamp()
            * 1000
        )

    recently_played = sp.current_user_recently_played(**kwargs)

    if not recently_played or "items" not in recently_played:
        echo_info("No recently played tracks found.")
        return {"plays_synced": 0, "new_plays": 0, "total_plays": database.get_total_play_count(db_path=db_path)}

    items = recently_played["items"]
    echo_verbose(ctx, f"Retrieved {len(items)} tracks")

    # Convert to our format
    plays = []
    for item in items:
        track = item["track"]
        album = track["album"]
        played_at = item["played_at"]

        plays.append(
            {
                "track_uri": track["uri"],
                "track_name": track["name"],
                "artists_json": json.dumps(
                    [artist["name"] for artist in track["artists"]]
                ),
                "album_uri": album["uri"],
                "album_name": album["name"],
                "album_artists_json": json.dumps(
                    [artist["name"] for artist in album["artists"]]
                ),
                "played_at": played_at,
            }
        )

    # Save to database and raw sync file
    if plays:
        # Save raw sync file for multi-machine support
        latest_play_time = plays[0]["played_at"]
        sync_file = database.save_raw_sync(plays, latest_play_time, db_path=db_path)
        echo_verbose(ctx, f"Saved raw sync to {sync_file}")

        # Save to database
        added_count = database.save_play_history(plays, db_path=db_path)
        echo_info(
            f"Synced {len(plays)} tracks, {added_count} new "
            f"({len(plays) - added_count} duplicates skipped)"
        )

        # Update last sync time to the most recent play
        database.set_last_sync_time(latest_play_time, db_path=db_path)
        echo_verbose(ctx, f"Updated last sync time to {latest_play_time}")

        # Show summary
        total_plays = database.get_total_play_count(db_path=db_path)
        echo_info(f"Total plays in database: {total_plays}")

        return {"plays_synced": len(plays), "new_plays": added_count, "total_plays": total_plays}
    else:
        echo_info("No new tracks to sync")
        return {"plays_synced": 0, "new_plays": 0, "total_plays": database.get_total_play_count(db_path=db_path)}


@click.command(name="sync-history")
@click.option(
    "--limit",
    default=50,
    type=int,
    help="Maximum number of recently played tracks to fetch (max 50).",
)
@click.pass_context
def sync_history(ctx, limit):
    """
    Sync play history from Spotify.

    Fetches recently played tracks from Spotify and stores them in the local
    database for play count tracking. Run this command regularly (e.g., via
    cron or systemd timer) to build your listening history over time.

    The Spotify API only provides the last ~50 recently played tracks, so
    frequent syncing is recommended to avoid missing data.
    """
    cache_dir = config.user_cache_dir()

    with spotify.create_spotify_client(cache_dir) as sp:
        sync_play_history_logic(sp, ctx, limit)
