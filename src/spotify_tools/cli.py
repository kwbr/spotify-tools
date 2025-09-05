"""
Command line interface for Spotify tools.
"""

from pathlib import Path

import click

from . import album, cache, config, playlist, spotify
from .types import Album

# CLI Setup and Output Functions


@click.group()
@click.option(
    "--verbose", "-v", count=True, help="Increase verbosity (can use multiple times)"
)
@click.version_option()
@click.pass_context
def cli(ctx, verbose):
    """A tool for working with Spotify."""
    ctx.ensure_object(dict)
    ctx.obj["VERBOSE"] = verbose


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


# CLI Commands


@cli.command()
@click.option("--count", default=1, help="Number of albums.")
@click.option("--year", type=int, help="Filter albums by release year.")
@click.pass_context
def random_album(ctx, count, year):
    """Get random album from user's Library.

    Returns random albums of the user's Library. Spotify lacks a randomization
    feature at the album level.

    When using --year, returns only albums released in the specified year.
    All albums are cached for faster subsequent runs. Use the refresh-cache command
    to update an existing cache.

    Inspired by https://shuffle.ninja/
    """
    # Check if we have a cache first
    cache_data = cache.load_albums()

    if cache_data is not None:
        # Use existing cache
        echo_debug(ctx, "Using existing album cache")
        days, hours = cache.calculate_cache_age(cache_data["timestamp"])
        echo_verbose(ctx, cache.format_cache_age_message(days, hours))
        albums_by_year = cache_data["albums_by_year"]
    else:
        # No cache available, need to build one (requires Spotify client)
        echo_always(
            "No album cache found. Building cache now (this may take a while)..."
        )
        cache_dir = config.user_cache_dir()
        with spotify.create_spotify_client(cache_dir) as sp:
            albums_by_year = refresh_album_cache(
                ctx, sp, max_workers=ctx.obj.get("MAX_WORKERS", 5)
            )

    # Now handle the album selection using the cache
    if year is not None:
        # Filter by year
        handle_year_filter(ctx, albums_by_year, year, count)
    else:
        # No filter, get random albums from all years
        handle_simple_random_selection(ctx, albums_by_year, count)


def refresh_album_cache(ctx, sp, max_workers=5, show_progress=True):
    """
    Refresh the album cache and return the albums by year.

    Args:
        ctx: Click context.
        sp: Spotify client.
        max_workers: Maximum number of parallel workers.
        show_progress: Whether to show a progress bar.

    Returns:
        dict: Albums organized by year.
    """
    echo_verbose(ctx, f"Using parallel fetching with {max_workers} workers")

    # Create progress bar for fetching albums
    total_albums = album.get_total_album_count(sp)

    if show_progress:
        with click.progressbar(
            length=total_albums,
            label="Fetching and organizing all albums",
        ) as bar:
            progress_callback = create_progress_callback(bar)

            albums_by_year = album.fetch_all_albums_parallel(
                sp, progress_callback, max_workers=max_workers
            )
    else:
        albums_by_year = album.fetch_all_albums_parallel(sp, max_workers=max_workers)

    # Report cache refresh
    total_albums = album.count_total_albums(albums_by_year)
    echo_always(f"Album database refreshed with {total_albums} albums.")

    return albums_by_year


@cli.command(name="refresh-cache")
@click.option("--max-workers", default=5, help="Maximum number of parallel workers.")
@click.pass_context
def refresh_cache(ctx, max_workers):
    """Force a refresh of the album cache.

    This command updates an existing cache or creates a new one by fetching all albums
    from your Spotify library. While the random-album command will automatically create
    a cache if needed, this command can be used to manually update the cache when
    you've added new albums to your Spotify library.
    """
    cache_dir = config.user_cache_dir()

    with spotify.create_spotify_client(cache_dir) as sp:
        refresh_album_cache(ctx, sp, max_workers=max_workers)


def handle_year_filter(ctx, albums_by_year, year, count):
    """Handle filtering and selecting albums by year."""
    # Convert integer year parameter to string for dictionary lookup
    year_str = str(year)
    matching_album_dicts = albums_by_year.get(year_str, [])

    if not matching_album_dicts:
        echo_always(f"No albums from {year} found in your library.")
        return

    matching_albums = [Album(**album_dict) for album_dict in matching_album_dicts]

    echo_verbose(ctx, f"Found {len(matching_albums)} albums from {year}.")

    # Select and display random albums
    selected_albums = album.select_random_albums(matching_albums, count)
    for alb in selected_albums:
        output_album(ctx, alb)


def handle_simple_random_selection(ctx, albums_by_year, count):
    """Handle random album selection without year filter using the provided cache data.

    Args:
        ctx: Click context.
        albums_by_year: Dictionary of albums organized by year.
        count: Number of albums to select.
    """
    echo_debug(ctx, f"Selecting {count} random albums from all years")

    # Flatten all albums into a single list
    all_albums = []
    for year_albums in albums_by_year.values():
        all_albums.extend([album.Album(**a) for a in year_albums])

    if all_albums:
        selected_albums = album.select_random_albums(all_albums, count)
        for alb in selected_albums:
            output_album(ctx, alb)
    else:
        echo_always("No albums found in your library.")


def output_album(ctx, alb):
    """
    Output album based on verbosity level.

    Args:
        ctx: Click context.
        alb: Album object.
    """
    # In any verbosity level, always output the URI
    echo_always(alb.uri)

    # Add album details in verbose mode
    if ctx.obj["VERBOSE"] >= 1:
        artists_str = alb.format_artists()
        echo_verbose(ctx, f"Album: {alb.name} by {artists_str}")


@cli.command()
@click.option("--count-by-year", is_flag=True, help="List album count by year.")
@click.pass_context
def list_albums(ctx, count_by_year):
    """List all albums in your library and count per year."""
    cache_data = cache.load_albums()

    if cache_data is None:
        echo_always("No album cache found. Run 'spt refresh-cache' to create one.")
        return

    albums_by_year = cache_data["albums_by_year"]
    years = album.get_sorted_years(albums_by_year)

    if count_by_year:
        total_albums = album.count_total_albums(albums_by_year)
        echo_always(f"Total albums in library: {total_albums}\n")
        echo_always("Albums by year:")
        display_albums_by_year(albums_by_year, years)
    else:
        display_albums(albums_by_year, years)


def display_albums(albums_by_year, years):
    for year in years:
        year_str = str(year)
        albums = [Album(**album_dict) for album_dict in albums_by_year[year_str]]
        for alb in albums:
            artists_str = alb.format_artists()
            echo_always(f"{alb.uri}: {alb.name} by {artists_str} ({year})")


def display_albums_by_year(albums_by_year, years):
    """Display album counts by year."""
    for year in years:
        year_str = str(year)
        count = len(albums_by_year[year_str])
        echo_always(f"{year}: {count} albums")


@cli.command(name="create-playlist")
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
            with Path(file_path).open() as f:
                file_items = [line.strip() for line in f if line.strip()]
                all_items.extend(file_items)
        except Exception as e:
            echo_always(f"Error reading file {file_path}: {e}")
            return 1

    if not all_items:
        echo_always("No items specified. Provide items as arguments or use --file.")
        return 1

    echo_verbose(ctx, f"Processing {len(all_items)} items...")

    cache_dir = config.user_cache_dir()
    try:
        with spotify.create_spotify_client(cache_dir) as sp:
            if dry_run:
                # Dry-run mode: show detailed search results
                search_results = playlist.resolve_items(sp, all_items)

                echo_always("Search Quality Analysis")
                echo_always("-" * 40)

                all_resolved_tracks = []
                poor_matches = []

                for i, result in enumerate(search_results, 1):
                    # Track poor matches
                    if result.match_quality < 0.4:
                        poor_matches.append(result)

                    echo_always(f"{i:2}. Query: {result.query}")
                    echo_always(f"    Type: {result.search_type}")

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
                            echo_always(f'    Found: "{item_name}" by {artists}')
                        else:
                            item_name = result.found_item.get("name", "Unknown")
                            artists_list = result.found_item.get("artists", [])
                            artists = ", ".join(
                                [artist["name"] for artist in artists_list]
                            )
                            echo_always(f'    Found: "{item_name}" by {artists}')
                    else:
                        echo_always("    Found: No results")

                    quality_text = (
                        f"{result.match_quality:.2f} - {result.quality_reason}"
                    )
                    echo_always(f"    Quality: {quality_text}")
                    echo_always(f"    Tracks: {len(result.resolved_tracks)} added")
                    echo_always("")

                    # Collect all resolved tracks
                    all_resolved_tracks.extend(result.resolved_tracks)

                # Summary
                echo_always("-" * 40)
                echo_always("Summary:")
                echo_always(f"  Items processed: {len(search_results)}")
                echo_always(f"  Tracks found: {len(all_resolved_tracks)}")
                echo_always(f"  Poor matches: {len(poor_matches)}")

                if poor_matches:
                    echo_always("")
                    echo_always("Poor quality matches:")
                    for result in poor_matches:
                        echo_always(f'  "{result.query}" -> {result.quality_reason}')

                # Show command to create playlist with URIs from good matches only
                good_tracks = [
                    track
                    for result in search_results
                    if result.match_quality >= 0.3
                    for track in result.resolved_tracks
                ]

                if good_tracks:
                    echo_always("")
                    if output:
                        # Write URIs to file and show file-based command
                        if write_uris_to_file(output, good_tracks):
                            echo_always(f"Good match URIs written to: {output}")
                            echo_always("Command to create playlist:")
                            name_part = f' --name "{name}"' if name else ""
                            cmd = f"spt create-playlist --file {output}{name_part}"
                            echo_always(cmd)
                        else:
                            echo_always(f"Error writing to file: {output}")
                    else:
                        # Show command with URIs (existing behavior)
                        echo_always("Command to create playlist (good matches only):")
                        uris = [track.uri for track in good_tracks]
                        uri_args = " ".join(f'"{uri}"' for uri in uris)
                        playlist_name_part = f' --name "{name}"' if name else ""
                        echo_always(
                            f"spt create-playlist{playlist_name_part} {uri_args}"
                        )
            else:
                # Normal mode: create playlist
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
                echo_always("Playlist created successfully!")
                echo_always(f"Playlist ID: {playlist_id}")
                echo_always(f"Tracks added: {tracks_added}")

                # Write URIs to output file if requested
                if output:
                    if write_uris_to_file(output, resolved_tracks):
                        echo_always(f"Resolved URIs written to: {output}")
                    else:
                        echo_always(f"Warning: Could not write to file: {output}")

                if skipped_items:
                    echo_always(f"Skipped {len(skipped_items)} items (not found):")
                    for item in skipped_items:
                        echo_always(f"  - {item}")

                # Show playlist URL in verbose mode
                if ctx.obj["VERBOSE"] >= 1:
                    playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
                    echo_verbose(ctx, f"Playlist URL: {playlist_url}")

    except Exception as e:
        error_context = "resolving tracks" if dry_run else "creating playlist"
        echo_always(f"Error {error_context}: {e}")
        return 1


@cli.command()
@click.option(
    "--client-id", prompt="Spotify Client ID", help="Your Spotify API client ID."
)
@click.option(
    "--client-secret",
    prompt="Spotify Client Secret",
    help="Your Spotify API client secret.",
)
@click.option(
    "--redirect-uri",
    default="http://localhost:8888/callback",
    prompt="Redirect URI",
    help="Your Spotify API redirect URI.",
)
@click.pass_context
def configure(ctx, client_id, client_secret, redirect_uri):
    """Configure Spotify API credentials."""
    try:
        config_path = config.create_default_config(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )
        echo_always(f"Configuration saved to {config_path}")
    except Exception as e:
        echo_always(f"Error saving configuration: {e}")
        return 1
