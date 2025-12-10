"""Tests for configuration loading and validation."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from qbt_rules.config import expand_env_vars, load_config, Config
from qbt_rules.errors import ConfigurationError


def test_expand_env_vars_simple():
    """Test environment variable expansion in strings."""
    os.environ["TEST_VAR"] = "test_value"
    result = expand_env_vars("${TEST_VAR}")
    assert result == "test_value"


def test_expand_env_vars_in_dict():
    """Test environment variable expansion in dictionaries."""
    os.environ["TEST_USER"] = "admin"
    os.environ["TEST_PASS"] = "secret"

    data = {
        "username": "${TEST_USER}",
        "password": "${TEST_PASS}",
        "host": "localhost"
    }

    result = expand_env_vars(data)
    assert result["username"] == "admin"
    assert result["password"] == "secret"
    assert result["host"] == "localhost"


def test_expand_env_vars_missing_var():
    """Test that missing environment variables raise an error."""
    with pytest.raises(ConfigurationError, match="Environment variable .* not found"):
        expand_env_vars("${NONEXISTENT_VAR}")


def test_config_get_qbittorrent_config(tmp_path):
    """Test getting qBittorrent configuration."""
    config_data = {
        "qbittorrent": {
            "host": "http://localhost:8080",
            "username": "admin",
            "password": "adminpass"
        }
    }

    config_file = tmp_path / "config.yml"
    with open(config_file, "w") as f:
        yaml.safe_dump(config_data, f)

    config = Config(str(tmp_path))
    qbt_config = config.get_qbittorrent_config()

    assert qbt_config["host"] == "http://localhost:8080"
    assert qbt_config["user"] == "admin"
    assert qbt_config["pass"] == "adminpass"


def test_config_missing_qbittorrent_section(tmp_path):
    """Test that missing qbittorrent section raises an error."""
    config_data = {"other": {}}

    config_file = tmp_path / "config.yml"
    with open(config_file, "w") as f:
        yaml.safe_dump(config_data, f)

    config = Config(str(tmp_path))

    with pytest.raises(ConfigurationError, match="qbittorrent.*not found"):
        config.get_qbittorrent_config()


def test_config_dry_run_mode(tmp_path):
    """Test dry-run mode detection."""
    config_data = {
        "qbittorrent": {"host": "http://localhost:8080"},
        "dry_run": True
    }

    config_file = tmp_path / "config.yml"
    with open(config_file, "w") as f:
        yaml.safe_dump(config_data, f)

    config = Config(str(tmp_path))
    assert config.is_dry_run() is True


def test_config_trace_mode(tmp_path):
    """Test trace mode detection."""
    config_data = {
        "qbittorrent": {"host": "http://localhost:8080"},
        "trace": True
    }

    config_file = tmp_path / "config.yml"
    with open(config_file, "w") as f:
        yaml.safe_dump(config_data, f)

    config = Config(str(tmp_path))
    assert config.get_trace_mode() is True
