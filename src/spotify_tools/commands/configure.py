"""
Configure command for Spotify tools CLI.
"""

import click

from spotify_tools import config
from spotify_tools.cli_utils import echo_always


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
def configure(ctx, client_id, client_secret, redirect_uri):
    """Configure Spotify API credentials."""
    try:
        config_path = config.create_default_config(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )
        echo_always(f"Configuration saved to {config_path}")
    except Exception as e:
        echo_always(f"Error saving configuration: {e}")
        return 1
