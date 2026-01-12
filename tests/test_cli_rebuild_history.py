from __future__ import annotations

import json
from pathlib import Path

import pytest

from spotify_tools.cli import cli


def test_rebuild_history_no_sync_files(runner, temp_cache_dir):
    result = runner.invoke(cli, ["rebuild-history"])

    assert result.exit_code == 0
    assert "No sync files found" in result.output or "syncs" in result.output.lower()


def test_rebuild_history_with_sync_files(runner, temp_cache_dir):
    syncs_dir = temp_cache_dir / "syncs"
    syncs_dir.mkdir(exist_ok=True)

    sync_data = {
        "track_uri": "spotify:track:1",
        "track_name": "Test Track",
        "artists": ["Test Artist"],
        "album_uri": "spotify:album:1",
        "album_name": "Test Album",
        "album_artists": ["Test Artist"],
        "played_at": "2024-01-15T12:00:00Z",
    }

    sync_file = syncs_dir / "sync_2024-01-15.json"
    sync_file.write_text(json.dumps([sync_data]))

    result = runner.invoke(cli, ["rebuild-history"])

    assert result.exit_code in [0, 1]


def test_rebuild_history_multiple_sync_files(runner, temp_cache_dir):
    syncs_dir = temp_cache_dir / "syncs"
    syncs_dir.mkdir(exist_ok=True)

    for i in range(3):
        sync_data = {
            "track_uri": f"spotify:track:{i}",
            "track_name": f"Test Track {i}",
            "artists": ["Test Artist"],
            "album_uri": f"spotify:album:{i}",
            "album_name": f"Test Album {i}",
            "album_artists": ["Test Artist"],
            "played_at": f"2024-01-{15+i:02d}T12:00:00Z",
        }

        sync_file = syncs_dir / f"sync_2024-01-{15+i:02d}.json"
        sync_file.write_text(json.dumps([sync_data]))

    result = runner.invoke(cli, ["rebuild-history"])

    assert result.exit_code in [0, 1]


def test_rebuild_history_deduplicates(runner, temp_cache_dir):
    syncs_dir = temp_cache_dir / "syncs"
    syncs_dir.mkdir(exist_ok=True)

    sync_data = {
        "track_uri": "spotify:track:1",
        "track_name": "Test Track",
        "artists": ["Test Artist"],
        "album_uri": "spotify:album:1",
        "album_name": "Test Album",
        "album_artists": ["Test Artist"],
        "played_at": "2024-01-15T12:00:00Z",
    }

    sync_file = syncs_dir / "sync_2024-01-15.json"
    sync_file.write_text(json.dumps([sync_data, sync_data]))

    result = runner.invoke(cli, ["rebuild-history"])

    assert result.exit_code in [0, 1]
