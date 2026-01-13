from __future__ import annotations

from unittest.mock import patch

from spotify_tools.cli import cli


def test_configure_with_flags(runner, temp_config_dir):
    result = runner.invoke(
        cli,
        [
            "configure",
            "--client-id",
            "test_id",
            "--client-secret",
            "test_secret",
            "--redirect-uri",
            "http://localhost:8888/callback",
        ],
    )

    assert result.exit_code == 0
    assert "Configuration saved" in result.output

    config_file = temp_config_dir / "config.toml"
    assert config_file.exists()


def test_configure_with_input(runner, temp_config_dir):
    result = runner.invoke(
        cli,
        ["configure"],
        input="test_id\ntest_secret\nhttp://localhost:8888/callback\n",
    )

    assert result.exit_code == 0
    assert "Configuration saved" in result.output


def test_configure_with_default_redirect_uri(runner, temp_config_dir):
    result = runner.invoke(
        cli,
        ["configure"],
        input="test_id\ntest_secret\n\n",
    )

    assert result.exit_code == 0
    assert "Configuration saved" in result.output

    config_file = temp_config_dir / "config.toml"
    content = config_file.read_text()
    assert "http://localhost:8888/callback" in content


def test_configure_updates_existing_config(runner, temp_config_dir):
    config_file = temp_config_dir / "config.toml"
    config_file.write_text(
        """client_id = "old_id"
client_secret = "old_secret"
redirect_uri = "http://old"
"""
    )

    result = runner.invoke(
        cli,
        [
            "configure",
            "--client-id",
            "new_id",
            "--client-secret",
            "new_secret",
            "--redirect-uri",
            "http://new",
        ],
    )

    assert result.exit_code == 0


def test_configure_with_error(runner, temp_config_dir):
    with patch(
        "spotify_tools.commands.configure.config.create_default_config"
    ) as mock_create:
        mock_create.side_effect = Exception("Test error")

        result = runner.invoke(
            cli,
            [
                "configure",
                "--client-id",
                "test_id",
                "--client-secret",
                "test_secret",
                "--redirect-uri",
                "http://localhost:8888/callback",
            ],
        )

        assert result.exit_code == 0
        assert "Error saving configuration" in result.output


def test_configure_creates_directory_if_missing(runner, tmp_path, monkeypatch):
    tmp_path / "new_config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    result = runner.invoke(
        cli,
        [
            "configure",
            "--client-id",
            "test_id",
            "--client-secret",
            "test_secret",
            "--redirect-uri",
            "http://localhost:8888/callback",
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / "spotify-tools" / "config.toml").exists()
