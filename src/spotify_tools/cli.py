"""
Command line interface for Spotify tools.
"""

import click

from .commands import (
    configure,
    create_playlist,
    list_albums,
    random_album,
    refresh_cache,
)


@click.group()
@click.option(
    "--verbose", "-v", count=True, help="Increase verbosity (can use multiple times)"
)
@click.version_option()
@click.pass_context
def cli(ctx, verbose):
    """A tool for working with Spotify."""
    ctx.ensure_object(dict)
    ctx.obj["VERBOSE"] = verbose


# Register all commands
cli.add_command(random_album)
cli.add_command(refresh_cache)
cli.add_command(list_albums)
cli.add_command(create_playlist)
cli.add_command(configure)