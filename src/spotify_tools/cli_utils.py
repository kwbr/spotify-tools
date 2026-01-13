"""
Shared utility functions for the CLI commands.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import click

if TYPE_CHECKING:
    from collections.abc import Callable

    from click import Context

    from .playlist import ResolvedTrack, SearchResult
    from .types import Album


class ProgressBar(Protocol):
    """Protocol for Click progress bar objects."""

    pos: int

    def update(self, n_steps: int) -> None: ...


# Output and display functions


def echo_debug(ctx: Context, message: str) -> None:
    """Echo debug message if verbose level >= 2."""
    if ctx.obj["VERBOSE"] >= 2:
        click.echo(f"DEBUG: {message}", err=True)


def echo_verbose(ctx: Context, message: str) -> None:
    """Echo verbose message if verbose level >= 1."""
    if ctx.obj["VERBOSE"] >= 1:
        click.echo(f"INFO: {message}", err=True)


def echo_info(message: str) -> None:
    """Echo informational message to stderr."""
    click.echo(message, err=True)


def echo_always(message: str) -> None:
    """Echo message to stdout regardless of verbosity level."""
    click.echo(message)


def create_progress_callback(progress_bar: ProgressBar) -> Callable[[int, int], None]:
    """Create a progress callback function."""

    def update_progress(current: int, total: int) -> None:
        progress_bar.update(current - progress_bar.pos)

    return update_progress


def extract_tracks_from_search_results(
    search_results: list[SearchResult],
) -> tuple[list[ResolvedTrack], list[str]]:
    """Extract resolved tracks and skipped items from search results."""
    resolved_tracks = []
    skipped_items = []

    for result in search_results:
        if result.resolved_tracks:  # Has tracks to add
            resolved_tracks.extend(result.resolved_tracks)
        else:  # No tracks found, consider it skipped
            skipped_items.append(result.query)

    return resolved_tracks, skipped_items


def write_uris_to_file(file_path: str, resolved_tracks: list[ResolvedTrack]) -> bool:
    """Write track URIs to a file, one per line."""
    try:
        with Path(file_path).open("w") as f:
            for track in resolved_tracks:
                f.write(f"{track.uri}\n")
        return True
    except Exception:
        return False


def output_album(ctx: Context, alb: Album) -> None:
    """
    Output album based on verbosity level.

    Args:
        ctx: Click context.
        alb: Album object.
    """
    echo_always(alb.uri)

    if ctx.obj["VERBOSE"] >= 1:
        artists_str = alb.format_artists()
        echo_verbose(ctx, f"Album: {alb.name} by {artists_str}")
