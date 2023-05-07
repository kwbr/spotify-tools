# spotify-tools

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/s3-credentials/blob/master/LICENSE)

Collection of helpers I use to enhance my music listening experience with Spotify.

## Installation 

Install this tool using `pip`:

    pip install git+https://github.com/kwbr/spotify-tools

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
  random-album  Get random album from user's Library
```

## Hacking

To contribute to this tool, first checkout the code. Then create a new virtual environment:

    cd spotify-tools
    python -m venv venv
    source venv/bin/activate

Now install the dependencies and test dependencies:

    pip install -e '.[test]'
