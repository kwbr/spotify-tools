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

The project uses pytest with a comprehensive test suite following Simon Willison's CLI testing patterns.

**Running Tests:**

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=spotify_tools --cov-report=html

# Run specific test file
uv run pytest tests/test_cli_random_album.py -v

# Run tests quietly (suppress warnings)
uv run pytest -q -W ignore::ResourceWarning
```

**Test Structure:**

```
tests/
├── conftest.py                    # Shared fixtures (CliRunner, temp DB, mocks)
├── test_cli_random_album.py      # Integration: random-album command (15 tests)
├── test_cli_list_albums.py       # Integration: list-albums command (18 tests)
├── test_database.py              # Unit: database operations (23 tests)
└── test_playlist.py              # Unit: fuzzy matching logic (48 tests)
```

**Current Coverage: 44%** (104 tests passing)

High-priority areas tested:

- ✅ random-album CLI (100%)
- ✅ list-albums CLI (96%)
- ✅ Database operations (63%)
- ✅ Fuzzy matching/playlist logic (46%)
- ✅ Core types and cache (84-86%)

**Testing Philosophy:**

- Uses Click's `CliRunner` for CLI integration tests
- Mocks Spotify API calls (no credentials needed)
- Real SQLite databases in temp directories
- Parametrized tests for multiple scenarios
- Fixtures in `conftest.py` handle setup/teardown

**Key Fixtures:**

- `runner` - CliRunner instance for invoking CLI commands
- `temp_db` - Temporary SQLite database with sample data
- `temp_cache_dir` - Temporary cache directory
- `sample_albums` - Realistic album test data
- `mock_spotify_client` - Mocked Spotify API responses

## Development Notes

- Python 3.13+ required
- Uses modern Python features: dataclasses, pathlib, type hints with `from __future__ import annotations`
- Follows strict linting rules via ruff configuration in pyproject.toml
- Type checking enabled via pyright with basic mode
- No test framework scripts in package.json; use `uv run pytest` directly
