"""
Rebuild history command for multi-machine sync support.
"""

import click

from spotify_tools import database
from spotify_tools.cli_utils import echo_info, echo_verbose


@click.command(name="rebuild-history")
@click.pass_context
def rebuild_history(ctx):
    """
    Rebuild play history database from raw sync files.

    This command is designed for multi-machine usage. Each machine saves
    raw sync files to ~/.cache/spotify-tools/syncs/. Sync this directory
    across machines (via Dropbox, iCloud, Git, rsync, etc.), then run
    this command to merge all syncs into a unified database.

    The rebuild process:
    1. Loads all JSON files from syncs/ directory
    2. Deduplicates by (track_uri, played_at)
    3. Clears and rebuilds the play_history table
    4. Updates last sync timestamp

    This is safe to run anytime and will produce identical results
    from the same set of sync files.
    """
    syncs_dir = database.get_syncs_dir()
    echo_verbose(ctx, f"Reading sync files from: {syncs_dir}")

    # Count sync files
    sync_files = list(syncs_dir.glob("*.json"))
    if not sync_files:
        echo_info("No sync files found. Run 'spt sync-history' first.")
        return

    echo_info(f"Found {len(sync_files)} sync file(s)")
    echo_verbose(ctx, "Rebuilding play history database...")

    # Rebuild from all sync files
    total_plays, unique_plays = database.rebuild_history_from_syncs()

    if unique_plays == 0:
        echo_info("No plays found in sync files.")
        return

    duplicates = total_plays - unique_plays
    echo_info(f"Loaded {total_plays} total plays")
    echo_info(f"Added {unique_plays} unique plays")
    echo_info(f"Skipped {duplicates} duplicates")
    echo_info("\nPlay history database successfully rebuilt!")
