from __future__ import annotations

import pytest

from spotify_tools.playlist import (
    ResolvedTrack,
    calculate_fuzzy_word_similarity,
    calculate_match_quality,
    calculate_string_similarity,
    create_playlist_from_tracks,
    format_artists,
    generate_default_name,
    normalize_string,
    parse_item,
    resolve_items,
    resolve_uri,
    search_album,
    search_auto,
    search_track,
)


class TestNormalizeString:
    def test_lowercase_conversion(self):
        assert normalize_string("Hello World") == "hello world"

    def test_remove_special_chars(self):
        assert normalize_string("Hello, World!") == "hello world"

    def test_remove_punctuation(self):
        assert normalize_string("Don't Stop Me Now") == "dont stop me now"

    def test_strip_whitespace(self):
        assert normalize_string("  hello world  ") == "hello world"

    def test_empty_string(self):
        assert normalize_string("") == ""

    def test_only_special_chars(self):
        assert normalize_string("!!!") == ""


class TestCalculateStringSimilarity:
    def test_identical_strings(self):
        similarity = calculate_string_similarity("hello", "hello")
        assert similarity == 1.0

    def test_completely_different(self):
        similarity = calculate_string_similarity("abc", "xyz")
        assert similarity < 0.2

    def test_similar_strings(self):
        similarity = calculate_string_similarity("hello", "helo")
        assert 0.7 < similarity < 1.0

    def test_case_insensitive(self):
        similarity = calculate_string_similarity("Hello", "hello")
        assert similarity == 1.0

    def test_punctuation_ignored(self):
        similarity = calculate_string_similarity("don't", "dont")
        assert similarity == 1.0

    def test_empty_strings(self):
        similarity = calculate_string_similarity("", "")
        assert similarity == 0.0

    def test_one_empty_string(self):
        similarity = calculate_string_similarity("hello", "")
        assert similarity == 0.0


class TestCalculateFuzzyWordSimilarity:
    def test_all_words_match(self):
        similarity = calculate_fuzzy_word_similarity("hello world", "hello world")
        assert similarity == 1.0

    def test_no_words_match(self):
        similarity = calculate_fuzzy_word_similarity("hello world", "foo bar")
        assert similarity == 0.0

    def test_partial_word_match(self):
        similarity = calculate_fuzzy_word_similarity("bohemian rhapsody", "bohemian rap")
        assert 0.4 < similarity < 0.8

    def test_word_order_doesnt_matter(self):
        sim1 = calculate_fuzzy_word_similarity("hello world", "world hello")
        assert sim1 == 1.0

    def test_extra_words_in_result(self):
        similarity = calculate_fuzzy_word_similarity("hello", "hello world foo bar")
        assert similarity == 1.0

    def test_typo_tolerance(self):
        similarity = calculate_fuzzy_word_similarity("bohemian", "bohemain")
        assert similarity > 0.6

    def test_empty_query(self):
        similarity = calculate_fuzzy_word_similarity("", "hello world")
        assert similarity == 0.0


class TestCalculateMatchQuality:
    def test_perfect_match(self):
        quality, reason = calculate_match_quality(
            "Bohemian Rhapsody", "Bohemian Rhapsody", "Queen"
        )
        assert quality > 0.8
        assert "Excellent" in reason or "Good" in reason

    def test_good_match_with_artist(self):
        quality, reason = calculate_match_quality(
            "Bohemian Rhapsody Queen", "Bohemian Rhapsody", "Queen"
        )
        assert quality > 0.7

    def test_fair_match(self):
        quality, reason = calculate_match_quality(
            "Bohemian", "Bohemian Rhapsody", "Queen"
        )
        assert 0.3 < quality < 0.8

    def test_poor_match(self):
        quality, reason = calculate_match_quality(
            "Completely Different Song", "Bohemian Rhapsody", "Queen"
        )
        assert quality < 0.3

    def test_empty_query(self):
        quality, reason = calculate_match_quality("", "Some Song", "Some Artist")
        assert quality == 0.0
        assert "Empty query" in reason

    def test_empty_result_name(self):
        quality, reason = calculate_match_quality("query", "", "Artist")
        assert quality == 0.0
        assert "No result found" in reason

    def test_quality_categories(self):
        test_cases = [
            ("exact match", "exact match", "artist", "Excellent"),
            ("good song", "good song name", "artist", "Good"),
            ("song", "completely different", "artist", "Weak"),
        ]

        for query, result_name, result_artist, expected_category in test_cases:
            quality, reason = calculate_match_quality(query, result_name, result_artist)
            assert isinstance(quality, float)
            assert 0.0 <= quality <= 1.0


class TestParseItem:
    def test_track_uri(self):
        item_type, query = parse_item("spotify:track:abc123")
        assert item_type == "uri"
        assert query == "spotify:track:abc123"

    def test_album_uri(self):
        item_type, query = parse_item("spotify:album:xyz789")
        assert item_type == "uri"
        assert query == "spotify:album:xyz789"

    def test_album_prefix(self):
        item_type, query = parse_item("album:Dark Side of the Moon")
        assert item_type == "album"
        assert query == "Dark Side of the Moon"

    def test_single_prefix(self):
        item_type, query = parse_item("single:Bohemian Rhapsody")
        assert item_type == "album"
        assert query == "Bohemian Rhapsody"

    def test_track_prefix(self):
        item_type, query = parse_item("track:Bohemian Rhapsody")
        assert item_type == "track"
        assert query == "Bohemian Rhapsody"

    def test_auto_detection(self):
        item_type, query = parse_item("Bohemian Rhapsody")
        assert item_type == "auto"
        assert query == "Bohemian Rhapsody"

    def test_strip_whitespace(self):
        item_type, query = parse_item("  album:Test Album  ")
        assert item_type == "album"
        assert query == "Test Album"

    def test_empty_string(self):
        item_type, query = parse_item("")
        assert item_type == "auto"
        assert query == ""


class TestFormatArtists:
    def test_single_artist(self):
        track = {"artists": [{"name": "Queen"}]}
        result = format_artists(track)
        assert result == "Queen"

    def test_multiple_artists(self):
        track = {"artists": [{"name": "Queen"}, {"name": "David Bowie"}]}
        result = format_artists(track)
        assert result == "Queen, David Bowie"

    def test_empty_artists_list(self):
        track = {"artists": []}
        result = format_artists(track)
        assert result == ""

    def test_three_artists(self):
        track = {
            "artists": [
                {"name": "Artist 1"},
                {"name": "Artist 2"},
                {"name": "Artist 3"},
            ]
        }
        result = format_artists(track)
        assert result == "Artist 1, Artist 2, Artist 3"


class TestEdgeCases:
    def test_unicode_characters(self):
        similarity = calculate_string_similarity("Beyoncé", "Beyonce")
        assert similarity > 0.8

    def test_very_long_strings(self):
        long_str = "a" * 1000
        similarity = calculate_string_similarity(long_str, long_str)
        assert similarity == 1.0

    def test_numbers_in_strings(self):
        similarity = calculate_string_similarity("Summer of 69", "Summer of 69")
        assert similarity == 1.0

    def test_special_album_names(self):
        quality, reason = calculate_match_quality(
            "(What's the Story) Morning Glory?",
            "What's the Story Morning Glory",
            "Oasis",
        )
        assert quality > 0.7

    @pytest.mark.parametrize(
        "query,expected_type",
        [
            ("track:Song Name", "track"),
            ("album:Album Name", "album"),
            ("single:Single Name", "album"),
            ("spotify:track:123", "uri"),
            ("Just A Song", "auto"),
        ],
    )
    def test_parse_item_parametrized(self, query, expected_type):
        item_type, _ = parse_item(query)
        assert item_type == expected_type


class TestSearchFunctions:
    def test_search_track_found(self, mock_spotify_client):
        mock_spotify_client.search.return_value = {
            "tracks": {
                "items": [
                    {
                        "uri": "spotify:track:1",
                        "name": "Test Track",
                        "artists": [{"name": "Test Artist"}],
                    }
                ]
            }
        }

        result = search_track(mock_spotify_client, "Test Track")

        assert result.search_type == "track"
        assert result.match_quality > 0
        assert len(result.resolved_tracks) == 1

    def test_search_track_not_found(self, mock_spotify_client):
        mock_spotify_client.search.return_value = {"tracks": {"items": []}}

        result = search_track(mock_spotify_client, "Nonexistent Track")

        assert result.search_type == "track"
        assert result.match_quality == 0.0
        assert len(result.resolved_tracks) == 0

    def test_search_track_error(self, mock_spotify_client):
        mock_spotify_client.search.side_effect = Exception("API Error")

        result = search_track(mock_spotify_client, "Test Track")

        assert result.search_type == "track"
        assert result.match_quality == 0.0
        assert "Search error" in result.quality_reason

    def test_search_album_found(self, mock_spotify_client):
        mock_spotify_client.search.return_value = {
            "albums": {
                "items": [
                    {
                        "id": "album1",
                        "uri": "spotify:album:1",
                        "name": "Test Album",
                        "artists": [{"name": "Test Artist"}],
                    }
                ]
            }
        }
        mock_spotify_client.album_tracks.return_value = {
            "items": [
                {
                    "uri": "spotify:track:1",
                    "name": "Track 1",
                    "artists": [{"name": "Test Artist"}],
                }
            ]
        }

        result = search_album(mock_spotify_client, "Test Album")

        assert result.search_type == "album"
        assert result.match_quality > 0
        assert len(result.resolved_tracks) > 0

    def test_search_album_not_found(self, mock_spotify_client):
        mock_spotify_client.search.return_value = {"albums": {"items": []}}

        result = search_album(mock_spotify_client, "Nonexistent Album")

        assert result.search_type == "album"
        assert result.match_quality == 0.0
        assert len(result.resolved_tracks) == 0

    def test_search_album_error(self, mock_spotify_client):
        mock_spotify_client.search.side_effect = Exception("API Error")

        result = search_album(mock_spotify_client, "Test Album")

        assert result.search_type == "album"
        assert result.match_quality == 0.0
        assert "Search error" in result.quality_reason

    def test_search_album_track_resolution_error(self, mock_spotify_client):
        mock_spotify_client.search.return_value = {
            "albums": {
                "items": [
                    {
                        "id": "album1",
                        "uri": "spotify:album:1",
                        "name": "Test Album",
                        "artists": [{"name": "Test Artist"}],
                    }
                ]
            }
        }
        mock_spotify_client.album_tracks.side_effect = Exception("Track fetch error")

        result = search_album(mock_spotify_client, "Test Album")

        assert result.search_type == "album"
        assert result.match_quality > 0
        assert len(result.resolved_tracks) == 0

    def test_search_auto_finds_track(self, mock_spotify_client):
        mock_spotify_client.search.return_value = {
            "tracks": {
                "items": [
                    {
                        "uri": "spotify:track:1",
                        "name": "Test Track",
                        "artists": [{"name": "Test Artist"}],
                    }
                ]
            }
        }

        result = search_auto(mock_spotify_client, "Test Track")

        assert "track" in result.search_type
        assert result.match_quality > 0

    def test_search_auto_finds_album(self, mock_spotify_client):
        mock_spotify_client.search.side_effect = [
            {"tracks": {"items": []}},
            {
                "albums": {
                    "items": [
                        {
                            "id": "album1",
                            "uri": "spotify:album:1",
                            "name": "Test Album",
                            "artists": [{"name": "Test Artist"}],
                        }
                    ]
                }
            },
        ]
        mock_spotify_client.album_tracks.return_value = {
            "items": [
                {
                    "uri": "spotify:track:1",
                    "name": "Track 1",
                    "artists": [{"name": "Test Artist"}],
                }
            ]
        }

        result = search_auto(mock_spotify_client, "Test Album")

        assert "album" in result.search_type
        assert result.match_quality > 0


class TestResolveUri:
    def test_resolve_track_uri(self, mock_spotify_client):
        mock_spotify_client.track.return_value = {
            "uri": "spotify:track:1",
            "name": "Test Track",
            "artists": [{"name": "Test Artist"}],
        }

        tracks = resolve_uri(mock_spotify_client, "spotify:track:1")

        assert tracks is not None
        assert len(tracks) == 1
        assert tracks[0].uri == "spotify:track:1"

    def test_resolve_album_uri(self, mock_spotify_client):
        mock_spotify_client.album.return_value = {
            "uri": "spotify:album:1",
            "name": "Test Album",
            "tracks": {
                "items": [
                    {
                        "uri": "spotify:track:1",
                        "name": "Track 1",
                        "artists": [{"name": "Test Artist"}],
                    },
                    {
                        "uri": "spotify:track:2",
                        "name": "Track 2",
                        "artists": [{"name": "Test Artist"}],
                    },
                ]
            },
        }

        tracks = resolve_uri(mock_spotify_client, "spotify:album:1")

        assert tracks is not None
        assert len(tracks) == 2

    def test_resolve_uri_error(self, mock_spotify_client):
        mock_spotify_client.track.side_effect = Exception("API Error")

        tracks = resolve_uri(mock_spotify_client, "spotify:track:1")

        assert tracks is None

    def test_resolve_invalid_uri(self, mock_spotify_client):
        tracks = resolve_uri(mock_spotify_client, "invalid:uri")

        assert tracks is None


class TestResolveItems:
    def test_resolve_items_track(self, mock_spotify_client):
        mock_spotify_client.search.return_value = {
            "tracks": {
                "items": [
                    {
                        "uri": "spotify:track:1",
                        "name": "Test Track",
                        "artists": [{"name": "Test Artist"}],
                    }
                ]
            }
        }

        results = resolve_items(mock_spotify_client, ["track:Test Track"])

        assert len(results) == 1
        assert results[0].search_type == "track"

    def test_resolve_items_album(self, mock_spotify_client):
        mock_spotify_client.search.return_value = {
            "albums": {
                "items": [
                    {
                        "id": "album1",
                        "uri": "spotify:album:1",
                        "name": "Test Album",
                        "artists": [{"name": "Test Artist"}],
                    }
                ]
            }
        }
        mock_spotify_client.album_tracks.return_value = {
            "items": [
                {
                    "uri": "spotify:track:1",
                    "name": "Track 1",
                    "artists": [{"name": "Test Artist"}],
                }
            ]
        }

        results = resolve_items(mock_spotify_client, ["album:Test Album"])

        assert len(results) == 1
        assert results[0].search_type == "album"

    def test_resolve_items_uri(self, mock_spotify_client):
        mock_spotify_client.track.return_value = {
            "uri": "spotify:track:1",
            "name": "Test Track",
            "artists": [{"name": "Test Artist"}],
        }

        results = resolve_items(mock_spotify_client, ["spotify:track:1"])

        assert len(results) == 1
        assert results[0].search_type == "uri"
        assert results[0].match_quality == 1.0

    def test_resolve_items_invalid_uri(self, mock_spotify_client):
        mock_spotify_client.track.side_effect = Exception("Not found")

        results = resolve_items(mock_spotify_client, ["spotify:track:invalid"])

        assert len(results) == 1
        assert results[0].match_quality == 0.0


class TestCreatePlaylist:
    def test_create_playlist_from_tracks(self, mock_spotify_client):
        mock_spotify_client.current_user.return_value = {"id": "user123"}
        mock_spotify_client.user_playlist_create.return_value = {
            "id": "playlist123"
        }

        track = ResolvedTrack(
            uri="spotify:track:1",
            name="Test Track",
            artists="Test Artist",
            source_query="test",
        )

        playlist_id = create_playlist_from_tracks(
            mock_spotify_client, [track], name="Test Playlist"
        )

        assert playlist_id == "playlist123"
        mock_spotify_client.user_playlist_create.assert_called_once()
        mock_spotify_client.playlist_add_items.assert_called_once()

    def test_create_playlist_default_name(self, mock_spotify_client):
        mock_spotify_client.current_user.return_value = {"id": "user123"}
        mock_spotify_client.user_playlist_create.return_value = {
            "id": "playlist123"
        }

        track = ResolvedTrack(
            uri="spotify:track:1",
            name="Test Track",
            artists="Test Artist",
            source_query="test",
        )

        playlist_id = create_playlist_from_tracks(mock_spotify_client, [track])

        assert playlist_id == "playlist123"

    def test_create_playlist_large_batch(self, mock_spotify_client):
        mock_spotify_client.current_user.return_value = {"id": "user123"}
        mock_spotify_client.user_playlist_create.return_value = {
            "id": "playlist123"
        }

        tracks = [
            ResolvedTrack(
                uri=f"spotify:track:{i}",
                name=f"Track {i}",
                artists="Test Artist",
                source_query="test",
            )
            for i in range(150)
        ]

        playlist_id = create_playlist_from_tracks(mock_spotify_client, tracks)

        assert playlist_id == "playlist123"
        assert mock_spotify_client.playlist_add_items.call_count == 2


class TestGenerateDefaultName:
    def test_generate_default_name_format(self):
        name = generate_default_name()

        assert name.startswith("Playlist ")
        assert len(name) > len("Playlist ")

    def test_generate_default_name_includes_datetime(self):
        import re

        name = generate_default_name()

        assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", name)
