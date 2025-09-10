"""
Shared utility functions for the CLI commands.
"""

from pathlib import Path
import click

from . import perf


# Output and display functions


def echo_debug(ctx, message):
    """Echo debug message if verbose level >= 2."""
    if ctx.obj["VERBOSE"] >= 2:
        click.echo(f"DEBUG: {message}")


def echo_verbose(ctx, message):
    """Echo verbose message if verbose level >= 1."""
    if ctx.obj["VERBOSE"] >= 1:
        click.echo(f"INFO: {message}")


def echo_always(message):
    """Echo message regardless of verbosity level."""
    click.echo(message)


def create_progress_callback(progress_bar):
    """Create a progress callback function."""

    def update_progress(current, total):
        progress_bar.update(current - progress_bar.pos)

    return update_progress


def extract_tracks_from_search_results(search_results):
    """Extract resolved tracks and skipped items from search results."""
    resolved_tracks = []
    skipped_items = []

    for result in search_results:
        if result.resolved_tracks:  # Has tracks to add
            resolved_tracks.extend(result.resolved_tracks)
        else:  # No tracks found, consider it skipped
            skipped_items.append(result.query)

    return resolved_tracks, skipped_items


def write_uris_to_file(file_path, resolved_tracks):
    """Write track URIs to a file, one per line."""
    try:
        with Path(file_path).open("w") as f:
            for track in resolved_tracks:
                f.write(f"{track.uri}\n")
        return True
    except Exception:
        return False


def output_album(ctx, alb):
    """
    Output album based on verbosity level.

    Args:
        ctx: Click context.
        alb: Album object.
    """
    # In any verbosity level, always output the URI
    with perf.measure_time("echo_uri"):
        echo_always(alb.uri)

    # Add album details in verbose mode
    if ctx.obj["VERBOSE"] >= 1:
        with perf.measure_time("format_and_echo_album_details"):
            artists_str = alb.format_artists()
            echo_verbose(ctx, f"Album: {alb.name} by {artists_str}")
