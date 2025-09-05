# spotify-tools

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/s3-credentials/blob/master/LICENSE)

A CLI tool for enhancing music discovery on Spotify. Provides album randomization and playlist creation functionality that Spotify lacks natively.

## Installation

Install this tool using `pip`:

```
pip install git+https://github.com/kwbr/spotify-tools
```

Or with `uv`:

```
uv install git+https://github.com/kwbr/spotify-tools
```

## Setup

Before using the tool, configure your Spotify API credentials:

```console
spt configure
```

This will prompt you to enter your Spotify app credentials (client ID, client secret, redirect URI). You can create a Spotify app at https://developer.spotify.com/dashboard.

## Usage

The tool installs a `spt` cli command.

```console
$ spt --help
Usage: spt [OPTIONS] COMMAND [ARGS]...

  A tool for working with Spotify

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  configure      Set up Spotify API credentials
  create-playlist Create a playlist from tracks and albums
  list-albums    List albums from user's library
  random-album   Get random album from user's Library
  refresh-cache  Refresh the albums cache
```

### Random Album Discovery

Get a random album from your saved library:

```console
# Basic usage
spt random-album

# Filter by year or year range
spt random-album --year 2020
spt random-album --year 1990-2000

# Get multiple random albums
spt random-album --count 3

# Verbose output with album details
spt random-album -v
```

### Playlist Creation

Create playlists from tracks, albums, or a mix of both:

```console
# Create from individual items
spt create-playlist "Bohemian Rhapsody" "album:Dark Side of the Moon"

# Use prefixes for specific search types
spt create-playlist "track:Yesterday" "album:Abbey Road" "single:Hey Jude"

# Create from a file of track names/URIs
spt create-playlist --file my-tracks.txt --name "My Playlist"

# Use Spotify URIs directly
spt create-playlist spotify:track:123abc spotify:album:456def

# Dry run to see what would be added
spt create-playlist --dry-run "album:Dark Side of the Moon"

# Export resolved track URIs to a file
spt create-playlist --output backup.txt --name "My Mix" "Bohemian Rhapsody"
```

### Cache Management

The tool caches your album library for faster performance:

```console
# Refresh cache when your library changes
spt refresh-cache

# List cached albums by year
spt list-albums --year 2020
```

## Development

To contribute to this tool, first checkout the code and install dependencies:

### With uv (recommended)

```bash
cd spotify-tools
uv sync
```

### With pip

```bash
cd spotify-tools
python -m venv venv
source venv/bin/activate
pip install -e '.[test]'
```

### Development Commands

```bash
# Linting and formatting
uv run ruff check
uv run ruff format

# Type checking
uv run pyright

# Testing
uv run pytest

# Run the CLI in development
python -m spotify_tools
```
