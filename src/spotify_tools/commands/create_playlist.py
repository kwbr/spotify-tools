"""
Create playlist command for Spotify tools CLI.
"""

from pathlib import Path

import click

from spotify_tools import config, playlist, spotify
from spotify_tools.cli_utils import (
    echo_info,
    echo_verbose,
    extract_tracks_from_search_results,
    write_uris_to_file,
)


def read_items_from_file(file_path):
    """
    Read items from a file.

    Args:
        file_path: Path to file containing items (one per line)

    Returns:
        list: List of item strings

    Raises:
        Exception: If file cannot be read
    """
    with Path(file_path).open() as f:
        return [line.strip() for line in f if line.strip()]


def create_playlist_logic(sp, ctx, all_items, name=None, dry_run=False, output=None):
    """
    Core business logic for creating a playlist from items.

    Args:
        sp: Spotify client instance
        ctx: Click context for logging
        all_items: List of item strings to process
        name: Optional playlist name
        dry_run: If True, only analyze without creating
        output: Optional file path to write URIs

    Returns:
        dict: Results with keys: success, playlist_id (if created), tracks_count, skipped_count
    """
    if not all_items:
        echo_info("No items specified. Provide items as arguments or use --file.")
        return {"success": False, "error": "no_items"}

    echo_verbose(ctx, f"Processing {len(all_items)} items...")

    if dry_run:
        return _handle_dry_run(sp, ctx, all_items, name, output)
    else:
        return _handle_create_playlist(sp, ctx, all_items, name, output)


def _handle_dry_run(sp, ctx, all_items, name, output):
    """Handle dry-run mode: show detailed search results."""
    search_results = playlist.resolve_items(sp, all_items)

    echo_info("Search Quality Analysis")
    echo_info("-" * 40)

    all_resolved_tracks = []
    poor_matches = []

    for i, result in enumerate(search_results, 1):
        # Track poor matches
        if result.match_quality < 0.4:
            poor_matches.append(result)

        echo_info(f"{i:2}. Query: {result.query}")
        echo_info(f"    Type: {result.search_type}")

        if result.found_item:
            is_album_type = (
                result.search_type == "album"
                or "album" in result.search_type
            )
            if is_album_type:
                item_name = result.found_item.get("name", "Unknown")
                artists_list = result.found_item.get("artists", [])
                artists = ", ".join(
                    [artist["name"] for artist in artists_list]
                )
                echo_info(f'    Found: "{item_name}" by {artists}')
            else:
                item_name = result.found_item.get("name", "Unknown")
                artists_list = result.found_item.get("artists", [])
                artists = ", ".join(
                    [artist["name"] for artist in artists_list]
                )
                echo_info(f'    Found: "{item_name}" by {artists}')
        else:
            echo_info("    Found: No results")

        quality_text = (
            f"{result.match_quality:.2f} - {result.quality_reason}"
        )
        echo_info(f"    Quality: {quality_text}")
        echo_info(f"    Tracks: {len(result.resolved_tracks)} added")
        echo_info("")

        # Collect all resolved tracks
        all_resolved_tracks.extend(result.resolved_tracks)

    # Summary
    echo_info("-" * 40)
    echo_info("Summary:")
    echo_info(f"  Items processed: {len(search_results)}")
    echo_info(f"  Tracks found: {len(all_resolved_tracks)}")
    echo_info(f"  Poor matches: {len(poor_matches)}")

    if poor_matches:
        echo_info("")
        echo_info("Poor quality matches:")
        for result in poor_matches:
            echo_info(f'  "{result.query}" -> {result.quality_reason}')

    # Show command to create playlist with URIs from good matches only
    good_tracks = [
        track
        for result in search_results
        if result.match_quality >= 0.3
        for track in result.resolved_tracks
    ]

    if good_tracks:
        echo_info("")
        if output:
            # Write URIs to file and show file-based command
            if write_uris_to_file(output, good_tracks):
                echo_info(f"Good match URIs written to: {output}")
                echo_info("Command to create playlist:")
                name_part = f' --name "{name}"' if name else ""
                cmd = f"spt create-playlist --file {output}{name_part}"
                echo_info(cmd)
            else:
                echo_info(f"Error writing to file: {output}")
        else:
            # Show command with URIs (existing behavior)
            echo_info("Command to create playlist (good matches only):")
            uris = [track.uri for track in good_tracks]
            uri_args = " ".join(f'"{uri}"' for uri in uris)
            playlist_name_part = f' --name "{name}"' if name else ""
            echo_info(
                f"spt create-playlist{playlist_name_part} {uri_args}"
            )

    return {
        "success": True,
        "dry_run": True,
        "tracks_found": len(all_resolved_tracks),
        "poor_matches": len(poor_matches),
    }


def _handle_create_playlist(sp, ctx, all_items, name, output):
    """Handle normal mode: create playlist."""
    search_results = playlist.resolve_items(sp, all_items)
    resolved_tracks, skipped_items = extract_tracks_from_search_results(
        search_results
    )

    # Create playlist from resolved tracks
    playlist_id = playlist.create_playlist_from_tracks(
        sp, resolved_tracks, name
    )
    tracks_added = len(resolved_tracks)

    # Report results
    echo_info("Playlist created successfully!")
    echo_info(f"Playlist ID: {playlist_id}")
    echo_info(f"Tracks added: {tracks_added}")

    # Write URIs to output file if requested
    if output:
        if write_uris_to_file(output, resolved_tracks):
            echo_info(f"Resolved URIs written to: {output}")
        else:
            echo_info(f"Warning: Could not write to file: {output}")

    if skipped_items:
        echo_info(f"Skipped {len(skipped_items)} items (not found):")
        for item in skipped_items:
            echo_info(f"  - {item}")

    # Show playlist URL in verbose mode
    if ctx.obj["VERBOSE"] >= 1:
        playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
        echo_verbose(ctx, f"Playlist URL: {playlist_url}")

    return {
        "success": True,
        "playlist_id": playlist_id,
        "tracks_count": tracks_added,
        "skipped_count": len(skipped_items),
    }


@click.command(name="create-playlist")
@click.argument("items", nargs=-1)
@click.option("--name", help="Playlist name (default: timestamp-based name)")
@click.option(
    "--file", "file_path", type=click.Path(exists=True), help="Read items from file"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what tracks would be added without creating playlist",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Write resolved track URIs to file (works in both dry-run and create modes)",
)
@click.pass_context
def create_playlist(ctx, items, name, file_path, dry_run, output):
    """Create a playlist from tracks and albums.

    Specify items as free-form text, "track:Name", "album:Name", "single:Name",
    or Spotify URIs.
    Items can be provided as arguments or read from a file.

    Examples:
      spt create-playlist "Bohemian Rhapsody" "album:Dark Side of the Moon"
      spt create-playlist --file my-tracks.txt --name "My Playlist"
      spt create-playlist --dry-run "single:Some EP" "track:Yesterday"
      spt create-playlist --dry-run --output resolved.txt "album:Dark Side"
      spt create-playlist --output backup.txt --name "My Mix" "Bohemian Rhapsody"
      spt create-playlist spotify:track:123abc spotify:album:456def
    """
    all_items = list(items)

    # Read items from file if provided
    if file_path:
        try:
            file_items = read_items_from_file(file_path)
            all_items.extend(file_items)
        except Exception as e:
            echo_info(f"Error reading file {file_path}: {e}")
            return 1

    cache_dir = config.user_cache_dir()
    try:
        with spotify.create_spotify_client(cache_dir) as sp:
            result = create_playlist_logic(sp, ctx, all_items, name, dry_run, output)
            if not result["success"]:
                return 1
    except Exception as e:
        error_context = "resolving tracks" if dry_run else "creating playlist"
        echo_info(f"Error {error_context}: {e}")
        return 1
