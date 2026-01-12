from __future__ import annotations

import pytest

from spotify_tools.cli import cli


def test_random_album_basic(runner, temp_db):
    result = runner.invoke(cli, ["random-album"])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output


@pytest.mark.parametrize(
    "count,min_expected",
    [
        (1, 1),
        (3, 3),
        (5, 5),
    ],
)
def test_random_album_count(runner, temp_db, count, min_expected):
    result = runner.invoke(cli, ["random-album", "--count", str(count)])

    assert result.exit_code == 0
    uris = [line for line in result.output.strip().split("\n") if "spotify:album:" in line]
    assert len(uris) >= min_expected


@pytest.mark.parametrize("year", [2020, 2021, 2022])
def test_random_album_year_filter(runner, temp_db, year):
    result = runner.invoke(cli, ["random-album", "--year", str(year), "--count", "10"])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output


def test_random_album_year_filter_2020_specific(runner, temp_db):
    result = runner.invoke(cli, ["random-album", "--year", "2020", "--count", "10"])

    assert result.exit_code == 0
    uris = [line for line in result.output.strip().split("\n") if "spotify:album:" in line]
    assert len(uris) == 2


def test_random_album_year_filter_2021_specific(runner, temp_db):
    result = runner.invoke(cli, ["random-album", "--year", "2021", "--count", "10"])

    assert result.exit_code == 0
    uris = [line for line in result.output.strip().split("\n") if "spotify:album:" in line]
    assert len(uris) == 3


def test_random_album_verbose(runner, temp_db):
    result = runner.invoke(cli, ["-v", "random-album"])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output


def test_random_album_very_verbose(runner, temp_db):
    result = runner.invoke(cli, ["-vv", "random-album"])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output


def test_random_album_with_timing(runner, temp_db):
    result = runner.invoke(cli, ["random-album", "--timing"])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output


def test_random_album_count_and_year(runner, temp_db):
    result = runner.invoke(cli, ["random-album", "--count", "2", "--year", "2020"])

    assert result.exit_code == 0
    uris = [line for line in result.output.strip().split("\n") if "spotify:album:" in line]
    assert len(uris) == 2


def test_random_album_no_database(runner, temp_cache_dir):
    result = runner.invoke(cli, ["random-album"])

    assert result.exit_code != 0
    assert "No album cache found" in result.output or "cache" in result.output.lower()


def test_random_album_year_with_no_albums(runner, temp_db):
    result = runner.invoke(cli, ["random-album", "--year", "1999"])

    assert result.exit_code == 0
    assert result.output.strip() == "" or "No albums" in result.output
