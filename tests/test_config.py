from __future__ import annotations

import sys
from pathlib import Path

import pytest

from spotify_tools import config


def test_user_cache_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))

    cache_dir = config.user_cache_dir()

    assert cache_dir == tmp_path / "spotify-tools"


def test_user_cache_dir_default(monkeypatch):
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)

    cache_dir = config.user_cache_dir()

    assert "spotify-tools" in str(cache_dir)
    assert cache_dir.name == "spotify-tools"


def test_user_config_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config_dir = config.user_config_dir()

    assert config_dir == tmp_path / "spotify-tools"


def test_user_config_dir_default(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    config_dir = config.user_config_dir()

    assert "spotify-tools" in str(config_dir)
    assert config_dir.name == "spotify-tools"


def test_load_config_file_not_found(temp_config_dir):
    with pytest.raises(FileNotFoundError) as exc_info:
        config.load_config()

    assert "Configuration file not found" in str(exc_info.value)


def test_load_config_success(temp_config_dir):
    config_file = temp_config_dir / "config.toml"
    config_content = """[spotify]
client_id = "test_id"
client_secret = "test_secret"
redirect_uri = "http://localhost:8888/callback"
"""
    config_file.write_text(config_content)

    loaded_config = config.load_config()

    assert "spotify" in loaded_config
    assert loaded_config["spotify"]["client_id"] == "test_id"
    assert loaded_config["spotify"]["client_secret"] == "test_secret"
    assert loaded_config["spotify"]["redirect_uri"] == "http://localhost:8888/callback"


def test_load_config_invalid_toml(temp_config_dir):
    config_file = temp_config_dir / "config.toml"
    config_file.write_text("invalid toml [[[")

    with pytest.raises(Exception):
        config.load_config()


def test_create_default_config(temp_config_dir):
    config_path = config.create_default_config(
        client_id="test_id",
        client_secret="test_secret",
        redirect_uri="http://localhost:9999/callback",
    )

    assert config_path.exists()
    assert config_path.name == "config.toml"

    content = config_path.read_text()
    assert "client_id" in content
    assert "test_id" in content
    assert "test_secret" in content
    assert "http://localhost:9999/callback" in content


def test_create_default_config_no_params(temp_config_dir):
    config_path = config.create_default_config()

    assert config_path.exists()

    content = config_path.read_text()
    assert "[spotify]" in content
    assert "client_id" in content
    assert "client_secret" in content
    assert "redirect_uri" in content


def test_create_default_config_creates_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config_path = config.create_default_config(client_id="test")

    assert config_path.parent.exists()
    assert config_path.exists()


def test_create_default_config_idempotent(temp_config_dir):
    config_path1 = config.create_default_config(client_id="first")
    content1 = config_path1.read_text()

    config_path2 = config.create_default_config(client_id="second")
    content2 = config_path2.read_text()

    assert content1 == content2
    assert "first" in content1
    assert "second" not in content2


def test_load_config_with_additional_sections(temp_config_dir):
    config_file = temp_config_dir / "config.toml"
    config_content = """[spotify]
client_id = "test_id"
client_secret = "test_secret"

[other]
key = "value"
"""
    config_file.write_text(config_content)

    loaded_config = config.load_config()

    assert "spotify" in loaded_config
    assert "other" in loaded_config
    assert loaded_config["other"]["key"] == "value"
