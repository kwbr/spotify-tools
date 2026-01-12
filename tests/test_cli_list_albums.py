from __future__ import annotations

import pytest

from spotify_tools.cli import cli


def test_list_albums_basic(runner, temp_db):
    result = runner.invoke(cli, ["list-albums"])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output


def test_list_albums_contains_all_albums(runner, temp_db):
    result = runner.invoke(cli, ["list-albums"])

    assert result.exit_code == 0
    assert "spotify:album:1" in result.output
    assert "spotify:album:2" in result.output
    assert "spotify:album:3" in result.output
    assert "spotify:album:4" in result.output
    assert "spotify:album:5" in result.output
    assert "spotify:album:6" in result.output


@pytest.mark.parametrize("sort_option", ["added", "name", "artist"])
def test_list_albums_sort_options(runner, temp_db, sort_option):
    result = runner.invoke(cli, ["list-albums", "--sort", sort_option])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output


def test_list_albums_sort_by_added(runner, temp_db):
    result = runner.invoke(cli, ["list-albums", "--sort", "added"])

    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    uris = [line for line in lines if "spotify:album:" in line]
    assert len(uris) == 6


def test_list_albums_sort_by_name(runner, temp_db):
    result = runner.invoke(cli, ["list-albums", "--sort", "name"])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output


def test_list_albums_sort_by_artist(runner, temp_db):
    result = runner.invoke(cli, ["list-albums", "--sort", "artist"])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output


@pytest.mark.parametrize("year", [2020, 2021, 2022])
def test_list_albums_year_filter(runner, temp_db, year):
    result = runner.invoke(cli, ["list-albums", "--year", str(year)])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output


def test_list_albums_year_2020_count(runner, temp_db):
    result = runner.invoke(cli, ["list-albums", "--year", "2020"])

    assert result.exit_code == 0
    lines = [line for line in result.output.strip().split("\n") if "spotify:album:" in line]
    assert len(lines) == 2


def test_list_albums_year_2021_count(runner, temp_db):
    result = runner.invoke(cli, ["list-albums", "--year", "2021"])

    assert result.exit_code == 0
    lines = [line for line in result.output.strip().split("\n") if "spotify:album:" in line]
    assert len(lines) == 3


def test_list_albums_verbose(runner, temp_db):
    result = runner.invoke(cli, ["-v", "list-albums"])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output


def test_list_albums_very_verbose(runner, temp_db):
    result = runner.invoke(cli, ["-vv", "list-albums"])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output


def test_list_albums_no_database(runner, temp_cache_dir):
    result = runner.invoke(cli, ["list-albums"])

    assert result.exit_code == 0
    assert "No album cache found" in result.output


def test_list_albums_year_with_no_albums(runner, temp_db):
    result = runner.invoke(cli, ["list-albums", "--year", "1999"])

    assert result.exit_code == 0
    lines = [line for line in result.output.strip().split("\n") if "spotify:album:" in line]
    assert len(lines) == 0


def test_list_albums_year_and_sort(runner, temp_db):
    result = runner.invoke(cli, ["list-albums", "--year", "2021", "--sort", "name"])

    assert result.exit_code == 0
    lines = [line for line in result.output.strip().split("\n") if "spotify:album:" in line]
    assert len(lines) == 3
