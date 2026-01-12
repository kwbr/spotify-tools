from __future__ import annotations

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
    assert "Total plays" in result.output or "plays" in result.output.lower()


def test_stats_albums(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "albums"])

    assert result.exit_code == 0
    assert "Top" in result.output and "Albums" in result.output
    assert "Album 2020" in result.output


def test_stats_albums_with_limit(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "albums", "--limit", "5"])

    assert result.exit_code == 0
    assert "Top" in result.output and "Albums" in result.output


def test_stats_tracks(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "tracks"])

    assert result.exit_code == 0
    assert "Top" in result.output and "Tracks" in result.output
    assert "Track One" in result.output or "Track Two" in result.output


def test_stats_tracks_with_limit(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "tracks", "--limit", "10"])

    assert result.exit_code == 0
    assert "Top" in result.output and "Tracks" in result.output


def test_stats_artists(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "artists"])

    assert result.exit_code == 0
    assert "Top" in result.output and "Artists" in result.output
    assert "Artist A" in result.output or "Artist B" in result.output


def test_stats_artists_with_limit(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "artists", "--limit", "15"])

    assert result.exit_code == 0
    assert "Top" in result.output and "Artists" in result.output


def test_stats_trends(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "trends"])

    assert result.exit_code == 0
    assert (
        "Play Activity" in result.output
        or "Total plays" in result.output
        or "No trend data" in result.output
    )


def test_stats_trends_with_days(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "trends", "--days", "7"])

    assert result.exit_code == 0
    assert (
        "Play Activity" in result.output
        or "Last 7 Days" in result.output
        or "No trend data" in result.output
    )


def test_stats_recent(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "recent"])

    assert result.exit_code == 0
    assert "Last" in result.output and "Plays" in result.output
    assert "2024-01-" in result.output


def test_stats_recent_with_limit(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "recent", "--limit", "5"])

    assert result.exit_code == 0
    assert "Last" in result.output and "Plays" in result.output


def test_stats_habits(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats", "--type", "habits"])

    assert result.exit_code == 0
    assert "Listening by" in result.output


def test_stats_default_type(runner, temp_db_with_play_history):
    result = runner.invoke(cli, ["stats"])

    assert result.exit_code == 0
    assert "Total plays" in result.output or "plays" in result.output.lower()
