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

    expected_order = [
        "spotify:album:1",
        "spotify:album:2",
        "spotify:album:3",
        "spotify:album:4",
        "spotify:album:5",
        "spotify:album:6",
    ]

    for i, expected_uri in enumerate(expected_order):
        assert expected_uri in uris[i]


def test_list_albums_sort_by_name(runner, temp_db):
    result = runner.invoke(cli, ["list-albums", "--sort", "name"])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output

    expected_uris_order = [
        "spotify:album:1",
        "spotify:album:2",
        "spotify:album:3",
        "spotify:album:5",
        "spotify:album:4",
        "spotify:album:6",
    ]

    lines = result.output.strip().split("\n")
    uris = [line for line in lines if "spotify:album:" in line]

    for i, expected_uri in enumerate(expected_uris_order):
        assert expected_uri in uris[i]


def test_list_albums_sort_by_artist(runner, temp_db):
    result = runner.invoke(cli, ["list-albums", "--sort", "artist"])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output

    expected_uris_order = [
        "spotify:album:1",
        "spotify:album:3",
        "spotify:album:2",
        "spotify:album:4",
        "spotify:album:5",
        "spotify:album:6",
    ]

    lines = result.output.strip().split("\n")
    uris = [line for line in lines if "spotify:album:" in line]

    for i, expected_uri in enumerate(expected_uris_order):
        assert expected_uri in uris[i]


@pytest.mark.parametrize("year", [2020, 2021, 2022])
def test_list_albums_year_filter(runner, temp_db, year):
    result = runner.invoke(cli, ["list-albums", "--year", str(year)])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output

    expected_uris = {
        2020: ["spotify:album:1", "spotify:album:2"],
        2021: ["spotify:album:3", "spotify:album:4", "spotify:album:5"],
        2022: ["spotify:album:6"],
    }

    uris = [line for line in result.output.strip().split("\n") if "spotify:album:" in line]
    for uri in uris:
        assert any(expected_uri in uri for expected_uri in expected_uris[year])

    for expected_uri in expected_uris[year]:
        assert any(expected_uri in uri for uri in uris)


def test_list_albums_year_2020_count(runner, temp_db):
    result = runner.invoke(cli, ["list-albums", "--year", "2020"])

    assert result.exit_code == 0
    lines = [
        line for line in result.output.strip().split("\n") if "spotify:album:" in line
    ]
    assert len(lines) == 2


def test_list_albums_year_2021_count(runner, temp_db):
    result = runner.invoke(cli, ["list-albums", "--year", "2021"])

    assert result.exit_code == 0
    lines = [
        line for line in result.output.strip().split("\n") if "spotify:album:" in line
    ]
    assert len(lines) == 3


def test_list_albums_verbose(runner, temp_db):
    result = runner.invoke(cli, ["-v", "list-albums"])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output

    expected_album_names = [
        "Album 2020 One",
        "Album 2020 Two",
        "Album 2021 One",
        "Album 2021 Two",
        "Album 2021 Three",
        "Album 2022 One",
    ]
    expected_artists = ["Artist A", "Artist B", "Artist C", "Artist D", "Artist E", "Artist F", "Artist G"]

    for album_name in expected_album_names:
        assert album_name in result.output

    for artist in expected_artists:
        assert artist in result.output


def test_list_albums_very_verbose(runner, temp_db):
    result = runner.invoke(cli, ["-vv", "list-albums"])

    assert result.exit_code == 0
    assert "spotify:album:" in result.output

    expected_album_names = [
        "Album 2020 One",
        "Album 2020 Two",
        "Album 2021 One",
        "Album 2021 Two",
        "Album 2021 Three",
        "Album 2022 One",
    ]

    for album_name in expected_album_names:
        assert album_name in result.output

    assert "added_at" in result.output.lower() or "2020" in result.output


def test_list_albums_no_database(runner, temp_cache_dir):
    result = runner.invoke(cli, ["list-albums"])

    assert result.exit_code == 0
    assert "No album cache found" in result.output


def test_list_albums_year_with_no_albums(runner, temp_db):
    result = runner.invoke(cli, ["list-albums", "--year", "1999"])

    assert result.exit_code == 0
    lines = [
        line for line in result.output.strip().split("\n") if "spotify:album:" in line
    ]
    assert len(lines) == 0


def test_list_albums_year_and_sort(runner, temp_db):
    result = runner.invoke(cli, ["list-albums", "--year", "2021", "--sort", "name"])

    assert result.exit_code == 0
    lines = [
        line for line in result.output.strip().split("\n") if "spotify:album:" in line
    ]
    assert len(lines) == 3
