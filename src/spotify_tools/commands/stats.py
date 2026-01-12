"""
Stats command to view play history statistics.
"""

from datetime import datetime, timedelta

import click

from spotify_tools import database
from spotify_tools.cli_utils import echo_info


@click.command()
@click.option(
    "--type",
    "stat_type",
    type=click.Choice(
        ["summary", "albums", "tracks", "artists", "trends", "recent", "habits"],
        case_sensitive=False,
    ),
    default="summary",
    help="Type of statistics to display.",
)
@click.option(
    "--limit", default=20, type=int, help="Number of items to show (default: 20)."
)
@click.option(
    "--days",
    type=int,
    help="Filter to last N days (for trends/habits).",
)
@click.pass_context
def stats(ctx, stat_type, limit, days):
    """View play history statistics with various views and filters."""
    if not database.database_exists():
        echo_info("No play history found. Run 'spt sync-history' first.")
        return

    total_plays = database.get_total_play_count()
    if total_plays == 0:
        echo_info("No play history found. Run 'spt sync-history' to start tracking.")
        return

    if stat_type == "summary":
        show_summary()
    elif stat_type == "albums":
        show_top_albums(limit, days)
    elif stat_type == "tracks":
        show_top_tracks(limit, days)
    elif stat_type == "artists":
        show_top_artists(limit, days)
    elif stat_type == "trends":
        show_trends(days or 30)
    elif stat_type == "recent":
        show_recently_played(limit)
    elif stat_type == "habits":
        show_listening_habits()


def show_summary():
    """Show summary statistics."""
    total_plays = database.get_total_play_count()
    album_stats = database.get_play_count_by_album()
    track_stats = database.get_play_count_by_track()
    unique_artists = database.get_unique_artist_count()

    echo_info(f"Total plays tracked: {total_plays}")
    echo_info(f"Unique artists: {unique_artists}")
    echo_info(f"Unique albums played: {len(album_stats)}")
    echo_info(f"Unique tracks played: {len(track_stats)}")

    if album_stats:
        echo_info("\nTop 5 Albums:")
        for i, (uri, info) in enumerate(list(album_stats.items())[:5], 1):
            artists = ", ".join(info["artists"]) if info["artists"] else "Unknown"
            echo_info(
                f"  {i}. {info['name']} by {artists} - {info['play_count']} plays"
            )

    if track_stats:
        echo_info("\nTop 5 Tracks:")
        for i, (uri, info) in enumerate(list(track_stats.items())[:5], 1):
            artists = ", ".join(info["artists"])
            echo_info(
                f"  {i}. {info['name']} by {artists} - {info['play_count']} plays"
            )


def show_top_albums(limit: int, days: int | None):
    """Show top albums by play count."""
    if days:
        since = (datetime.now() - timedelta(days=days)).isoformat()
        plays = database.get_plays_in_time_range(since=since)
        album_counts = {}
        for play in plays:
            uri = play["album_uri"]
            if uri not in album_counts:
                album_counts[uri] = {
                    "name": play["album_name"],
                    "artists": play["album_artists"],
                    "count": 0,
                }
            album_counts[uri]["count"] += 1
        album_stats = sorted(
            album_counts.items(), key=lambda x: x[1]["count"], reverse=True
        )
        echo_info(f"Top {min(limit, len(album_stats))} Albums (Last {days} Days):\n")
        for i, (uri, info) in enumerate(album_stats[:limit], 1):
            artists = ", ".join(info["artists"]) if info["artists"] else "Unknown"
            echo_info(f"{i:3}. {info['name']} by {artists} - {info['count']} plays")
    else:
        album_stats = database.get_play_count_by_album()
        if not album_stats:
            echo_info("No album statistics found.")
            return
        echo_info(f"Top {min(limit, len(album_stats))} Albums (All Time):\n")
        for i, (uri, info) in enumerate(list(album_stats.items())[:limit], 1):
            artists = ", ".join(info["artists"]) if info["artists"] else "Unknown"
            echo_info(f"{i:3}. {info['name']} by {artists}")
            echo_info(f"     Plays: {info['play_count']}")
            echo_info(f"     Last played: {info['last_played']}")
            echo_info("")


def show_top_tracks(limit: int, days: int | None):
    """Show top tracks by play count."""
    if days:
        since = (datetime.now() - timedelta(days=days)).isoformat()
        plays = database.get_plays_in_time_range(since=since)
        track_counts = {}
        for play in plays:
            uri = play["track_uri"]
            if uri not in track_counts:
                track_counts[uri] = {
                    "name": play["track_name"],
                    "artists": play["artists"],
                    "album_name": play["album_name"],
                    "count": 0,
                }
            track_counts[uri]["count"] += 1
        track_stats = sorted(
            track_counts.items(), key=lambda x: x[1]["count"], reverse=True
        )
        echo_info(f"Top {min(limit, len(track_stats))} Tracks (Last {days} Days):\n")
        for i, (uri, info) in enumerate(track_stats[:limit], 1):
            artists = ", ".join(info["artists"])
            echo_info(f"{i:3}. {info['name']} by {artists} - {info['count']} plays")
    else:
        track_stats = database.get_play_count_by_track()
        if not track_stats:
            echo_info("No track statistics found.")
            return
        echo_info(f"Top {min(limit, len(track_stats))} Tracks (All Time):\n")
        for i, (uri, info) in enumerate(list(track_stats.items())[:limit], 1):
            artists = ", ".join(info["artists"])
            echo_info(f"{i:3}. {info['name']} by {artists}")
            echo_info(f"     Album: {info['album_name']}")
            echo_info(f"     Plays: {info['play_count']}")
            echo_info(f"     Last played: {info['last_played']}")
            echo_info("")


def show_top_artists(limit: int, days: int | None):
    """Show top artists by play count."""
    if days:
        since = (datetime.now() - timedelta(days=days)).isoformat()
        plays = database.get_plays_in_time_range(since=since)
        artist_counts = {}
        for play in plays:
            for artist in play["artists"]:
                artist_counts[artist] = artist_counts.get(artist, 0) + 1
        artist_stats = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)
        echo_info(f"Top {min(limit, len(artist_stats))} Artists (Last {days} Days):\n")
        for i, (artist, count) in enumerate(artist_stats[:limit], 1):
            echo_info(f"{i:3}. {artist} - {count} plays")
    else:
        artist_stats = database.get_play_count_by_artist()
        if not artist_stats:
            echo_info("No artist statistics found.")
            return
        echo_info(f"Top {min(limit, len(artist_stats))} Artists (All Time):\n")
        for i, (artist, info) in enumerate(list(artist_stats.items())[:limit], 1):
            echo_info(f"{i:3}. {artist}")
            echo_info(f"     Total plays: {info['play_count']}")
            echo_info(f"     Unique tracks: {info['track_count']}")
            echo_info(f"     Unique albums: {info['album_count']}")
            echo_info(f"     Last played: {info['last_played']}")
            echo_info("")


def show_trends(days: int):
    """Show play trends over time."""
    trends = database.get_play_trends_by_day(days)
    if not trends:
        echo_info("No trend data found.")
        return

    echo_info(f"Play Activity (Last {days} Days):\n")
    max_plays = max(trends.values())
    for date, count in trends.items():
        bar_length = int((count / max_plays) * 40) if max_plays > 0 else 0
        bar = "█" * bar_length
        echo_info(f"{date}: {bar} {count}")

    total = sum(trends.values())
    avg = total / len(trends) if trends else 0
    echo_info(f"\nTotal plays: {total}")
    echo_info(f"Average per day: {avg:.1f}")
    echo_info(f"Most active day: {max(trends.items(), key=lambda x: x[1])[0]}")


def show_recently_played(limit: int):
    """Show recently played tracks."""
    plays = database.get_recently_played(limit)
    if not plays:
        echo_info("No recent plays found.")
        return

    echo_info(f"Last {len(plays)} Plays:\n")
    for play in plays:
        artists = ", ".join(play["artists"])
        dt = datetime.fromisoformat(play["played_at"].replace("Z", "+00:00"))
        time_str = dt.strftime("%Y-%m-%d %H:%M")
        echo_info(f"{time_str} - {play['track_name']} by {artists}")


def show_listening_habits():
    """Show listening habits (time of day, day of week)."""
    by_hour = database.get_plays_by_hour()
    by_day = database.get_plays_by_day_of_week()

    if by_hour:
        echo_info("Listening by Hour of Day:\n")
        max_plays = max(by_hour.values())
        for hour in range(24):
            count = by_hour.get(hour, 0)
            bar_length = int((count / max_plays) * 30) if max_plays > 0 else 0
            bar = "█" * bar_length
            echo_info(f"{hour:2d}:00 {bar} {count}")

    if by_day:
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        echo_info("\nListening by Day of Week:\n")
        max_plays = max(by_day.values())
        for day_num in range(7):
            count = by_day.get(day_num, 0)
            bar_length = int((count / max_plays) * 30) if max_plays > 0 else 0
            bar = "█" * bar_length
            echo_info(f"{days[day_num]}: {bar} {count}")
