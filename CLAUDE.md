# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

This project uses modern Python tooling with `uv` as the package manager:

```bash
# Install dependencies (development setup)
pip install -e '.[test]'

# With uv (if available)
uv sync

# Linting and formatting
uv run ruff check
uv run ruff format

# Type checking
uv run pyright

# Testing
uv run pytest

# Run the CLI tool in development
python -m spotify_tools
# or after installation
spt --help
```

## Project Architecture

**spotify-tools** is a CLI application for enhancing music discovery on Spotify. It provides album randomization functionality that Spotify lacks natively.

### Core Modules

- **`cli.py`** - Click-based command-line interface with commands for `random-album`, `refresh-cache`, `list-albums`, and `configure`
- **`spotify.py`** - Spotify API client with context manager for proper resource management using spotipy
- **`album.py`** - Core album functionality including parallel fetching, caching, and selection logic
- **`cache.py`** - JSON-based caching system for album data, organized by release year
- **`config.py`** - Configuration management with platform-specific directories using platformdirs
- **`types.py`** - Album dataclass with Spotify API response conversion methods

### Key Design Patterns

- **Caching Strategy**: Albums are cached by release year in `~/.cache/spotify-tools/albums_cache.json` to avoid repeated API calls
- **Parallel Processing**: Uses `ThreadPoolExecutor` with configurable max workers (default: 5) to batch Spotify API requests while respecting rate limits
- **Context Manager**: Spotify client uses proper resource management with `__enter__`/`__exit__`
- **Modular CLI**: Commands are organized with shared utilities for output formatting based on verbosity levels

### Configuration

The tool requires Spotify API credentials stored in `~/.config/spotify-tools/config.toml`:

```toml
[spotify]
client_id = "your_client_id"
client_secret = "your_client_secret"
redirect_uri = "http://localhost:8888/callback"
```

Use `spt configure` to set up credentials interactively.

### Cache Management

- Albums are organized by release year for efficient filtering
- Cache includes timestamp for age tracking
- Use `spt refresh-cache` to update when library changes
- The `check_albums_cache.sh` script provides detailed cache analysis with jq

### Testing

The project uses pytest but the test suite is currently minimal. When adding tests, follow the existing module structure in the `tests/` directory.

## Development Notes

- Python 3.13+ required
- Uses modern Python features: dataclasses, pathlib, type hints with `from __future__ import annotations`
- Follows strict linting rules via ruff configuration in pyproject.toml
- Type checking enabled via pyright with basic mode
- No test framework scripts in package.json; use `uv run pytest` directly
