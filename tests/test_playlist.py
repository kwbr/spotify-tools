from __future__ import annotations

import pytest

from spotify_tools.playlist import (
    calculate_fuzzy_word_similarity,
    calculate_match_quality,
    calculate_string_similarity,
    format_artists,
    normalize_string,
    parse_item,
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
