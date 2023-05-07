import os

from setuptools import setup

VERSION = "0.3"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="spotify-tools",
    description="Various tools working with Spotify",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Kai Weber",
    url="https://github.com/kwbr/spotify-tools",
    project_urls={
        "Issues": "https://github.com/kwbr/spotify-tools/issues",
        "CI": "https://github.com/kwbr/spotify-tools/actions",
        "Changelog": "https://github.com/kwbr/spotify-tools/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["spotify_tools"],
    entry_points="""
        [console_scripts]
        spt=spotify_tools.cli:cli
    """,
    install_requires=["click", "spotipy"],
    extras_require={
        "test": [
            "pytest",
        ]
    },
    python_requires=">=3.7",
)
