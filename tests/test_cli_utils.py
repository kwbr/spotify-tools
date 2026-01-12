from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import click
import pytest

from spotify_tools import cli_utils
from spotify_tools.playlist import SearchResult


def test_echo_debug_verbose_2(runner):
    ctx = click.Context(click.Command("test"))
    ctx.obj = {"VERBOSE": 2}

    cli_utils.echo_debug(ctx, "Debug message")


def test_echo_debug_not_verbose():
    ctx = click.Context(click.Command("test"))
    ctx.obj = {"VERBOSE": 0}

    cli_utils.echo_debug(ctx, "Debug message")


def test_echo_verbose_verbose_1():
    ctx = click.Context(click.Command("test"))
    ctx.obj = {"VERBOSE": 1}

    cli_utils.echo_verbose(ctx, "Verbose message")


def test_echo_verbose_not_verbose():
    ctx = click.Context(click.Command("test"))
    ctx.obj = {"VERBOSE": 0}

    cli_utils.echo_verbose(ctx, "Verbose message")


def test_echo_info():
    cli_utils.echo_info("Info message")


def test_echo_always():
    cli_utils.echo_always("Always message")


def test_create_progress_callback():
    progress_bar = MagicMock()
    progress_bar.pos = 0

    callback = cli_utils.create_progress_callback(progress_bar)
    callback(5, 10)

    progress_bar.update.assert_called_once_with(5)


def test_create_progress_callback_incremental():
    progress_bar = MagicMock()
    progress_bar.pos = 3

    callback = cli_utils.create_progress_callback(progress_bar)
    callback(7, 10)

    progress_bar.update.assert_called_once_with(4)


def test_extract_tracks_from_search_results_with_tracks():
    track1 = MagicMock(uri="spotify:track:1")
    track2 = MagicMock(uri="spotify:track:2")

    result1 = SearchResult(
        query="Query 1",
        search_type="track",
        found_item={},
        match_quality=0.8,
        quality_reason="Good match",
        resolved_tracks=[track1],
    )
    result2 = SearchResult(
        query="Query 2",
        search_type="track",
        found_item={},
        match_quality=0.8,
        quality_reason="Good match",
        resolved_tracks=[track2],
    )

    resolved_tracks, skipped_items = cli_utils.extract_tracks_from_search_results(
        [result1, result2]
    )

    assert len(resolved_tracks) == 2
    assert len(skipped_items) == 0
    assert resolved_tracks[0].uri == "spotify:track:1"
    assert resolved_tracks[1].uri == "spotify:track:2"


def test_extract_tracks_from_search_results_with_skipped():
    track1 = MagicMock(uri="spotify:track:1")

    result1 = SearchResult(
        query="Query 1",
        search_type="track",
        found_item={},
        match_quality=0.8,
        quality_reason="Good match",
        resolved_tracks=[track1],
    )
    result2 = SearchResult(
        query="Query 2",
        search_type="track",
        found_item=None,
        match_quality=0.0,
        quality_reason="No results",
        resolved_tracks=[],
    )

    resolved_tracks, skipped_items = cli_utils.extract_tracks_from_search_results(
        [result1, result2]
    )

    assert len(resolved_tracks) == 1
    assert len(skipped_items) == 1
    assert resolved_tracks[0].uri == "spotify:track:1"
    assert skipped_items[0] == "Query 2"


def test_extract_tracks_from_search_results_all_skipped():
    result1 = SearchResult(
        query="Query 1",
        search_type="track",
        found_item=None,
        match_quality=0.0,
        quality_reason="No results",
        resolved_tracks=[],
    )
    result2 = SearchResult(
        query="Query 2",
        search_type="track",
        found_item=None,
        match_quality=0.0,
        quality_reason="No results",
        resolved_tracks=[],
    )

    resolved_tracks, skipped_items = cli_utils.extract_tracks_from_search_results(
        [result1, result2]
    )

    assert len(resolved_tracks) == 0
    assert len(skipped_items) == 2
    assert skipped_items == ["Query 1", "Query 2"]


def test_write_uris_to_file(tmp_path):
    output_file = tmp_path / "output.txt"

    track1 = MagicMock(uri="spotify:track:1")
    track2 = MagicMock(uri="spotify:track:2")

    result = cli_utils.write_uris_to_file(output_file, [track1, track2])

    assert result is True
    assert output_file.exists()
    content = output_file.read_text()
    assert "spotify:track:1\n" in content
    assert "spotify:track:2\n" in content


def test_write_uris_to_file_empty_list(tmp_path):
    output_file = tmp_path / "output.txt"

    result = cli_utils.write_uris_to_file(output_file, [])

    assert result is True
    assert output_file.exists()
    assert output_file.read_text() == ""


def test_write_uris_to_file_invalid_path():
    result = cli_utils.write_uris_to_file("/nonexistent/dir/file.txt", [])

    assert result is False


def test_output_album_basic():
    ctx = click.Context(click.Command("test"))
    ctx.obj = {"VERBOSE": 0}

    album = MagicMock()
    album.uri = "spotify:album:123"
    album.name = "Test Album"
    album.format_artists.return_value = "Test Artist"

    cli_utils.output_album(ctx, album)


def test_output_album_verbose():
    ctx = click.Context(click.Command("test"))
    ctx.obj = {"VERBOSE": 1}

    album = MagicMock()
    album.uri = "spotify:album:123"
    album.name = "Test Album"
    album.format_artists.return_value = "Test Artist"

    cli_utils.output_album(ctx, album)
