from __future__ import annotations

import pytest

from spotify_tools.cli import cli


def test_stats_no_database(runner, temp_cache_dir):
    result = runner.invoke(cli, ["stats"])

    assert result.exit_code == 0
    assert "No play history found" in result.output


def test_stats_empty_database(runner, temp_db):
    result = runner.invoke(cli, ["stats"])

    assert result.exit_code == 0
    assert "No play history found" in result.output


def test_stats_summary(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "summary"])

    assert result.exit_code == 0
    assert "Total plays" in result.output or "Summary" in result.output or result.output


def test_stats_albums(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "albums"])

    assert result.exit_code == 0


def test_stats_albums_with_limit(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "albums", "--limit", "5"])

    assert result.exit_code == 0


def test_stats_tracks(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "tracks"])

    assert result.exit_code == 0


def test_stats_tracks_with_limit(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "tracks", "--limit", "10"])

    assert result.exit_code == 0


def test_stats_artists(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "artists"])

    assert result.exit_code == 0


def test_stats_artists_with_limit(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "artists", "--limit", "15"])

    assert result.exit_code == 0


def test_stats_trends(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "trends"])

    assert result.exit_code == 0


def test_stats_trends_with_days(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "trends", "--days", "7"])

    assert result.exit_code == 0


def test_stats_recent(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "recent"])

    assert result.exit_code == 0


def test_stats_recent_with_limit(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "recent", "--limit", "5"])

    assert result.exit_code == 0


def test_stats_habits(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "habits"])

    assert result.exit_code == 0


@pytest.mark.parametrize(
    "stat_type",
    ["summary", "albums", "tracks", "artists", "trends", "recent", "habits"],
)
def test_stats_all_types(runner, temp_db_with_play_history, stat_type):
    result = runner.invoke(cli, ["stats", "--type", stat_type])

    assert result.exit_code == 0


def test_stats_default_type(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats"])

    assert result.exit_code == 0
