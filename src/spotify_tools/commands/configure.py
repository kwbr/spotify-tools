"""
Configure command for Spotify tools CLI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from spotify_tools import config
from spotify_tools.cli_utils import echo_info

if TYPE_CHECKING:
    from click import Context


@click.command()
@click.option(
    "--client-id", prompt="Spotify Client ID", help="Your Spotify API client ID."
)
@click.option(
    "--client-secret",
    prompt="Spotify Client Secret",
    help="Your Spotify API client secret.",
)
@click.option(
    "--redirect-uri",
    default="http://localhost:8888/callback",
    prompt="Redirect URI",
    help="Your Spotify API redirect URI.",
)
@click.pass_context
def configure(
    ctx: Context, client_id: str, client_secret: str, redirect_uri: str
) -> int | None:
    """Configure Spotify API credentials."""
    try:
        config_path = config.create_default_config(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )
        echo_info(f"Configuration saved to {config_path}")
    except Exception as e:
        echo_info(f"Error saving configuration: {e}")
        return 1
