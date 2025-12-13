"""Comprehensive tests for config.py - Configuration loading and management."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from qbt_rules.config import (
    expand_env_vars,
    load_yaml_file,
    Config,
    load_config,
)
from qbt_rules.errors import ConfigurationError


# ============================================================================
# expand_env_vars()
# ============================================================================

class TestExpandEnvVars:
    """Test expand_env_vars() function."""

    def test_simple_env_var(self):
        """Expand simple environment variable."""
        with patch.dict(os.environ, {'TEST_VAR': 'hello'}):
            result = expand_env_vars('${TEST_VAR}')
            assert result == 'hello'

    def test_env_var_with_default(self):
        """Use default when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            result = expand_env_vars('${MISSING_VAR:-default_value}')
            assert result == 'default_value'

    def test_env_var_with_default_override(self):
        """Env var overrides default."""
        with patch.dict(os.environ, {'PRESENT_VAR': 'actual'}):
            result = expand_env_vars('${PRESENT_VAR:-default}')
            assert result == 'actual'

    def test_multiple_vars_in_string(self):
        """Multiple env vars in one string."""
        with patch.dict(os.environ, {'VAR1': 'foo', 'VAR2': 'bar'}):
            result = expand_env_vars('${VAR1}/${VAR2}')
            assert result == 'foo/bar'

    def test_dict_expansion(self):
        """Recursively expand dict values."""
        with patch.dict(os.environ, {'HOST': 'localhost', 'PORT': '8080'}):
            data = {'server': {'host': '${HOST}', 'port': '${PORT}'}}
            result = expand_env_vars(data)
            assert result == {'server': {'host': 'localhost', 'port': '8080'}}

    def test_list_expansion(self):
        """Recursively expand list values."""
        with patch.dict(os.environ, {'VAR': 'value'}):
            data = ['${VAR}', 'plain', '${VAR}']
            result = expand_env_vars(data)
            assert result == ['value', 'plain', 'value']

    def test_nested_structures(self):
        """Expand nested dicts and lists."""
        with patch.dict(os.environ, {'VAR': 'test'}):
            data = {'outer': {'inner': ['${VAR}', '${VAR:-default}']}}
            result = expand_env_vars(data)
            assert result == {'outer': {'inner': ['test', 'test']}}

    def test_primitive_types_unchanged(self):
        """Primitive types are unchanged."""
        assert expand_env_vars(42) == 42
        assert expand_env_vars(True) is True
        assert expand_env_vars(None) is None
        assert expand_env_vars(3.14) == 3.14

    def test_empty_default(self):
        """Empty default value works."""
        with patch.dict(os.environ, {}, clear=True):
            result = expand_env_vars('${MISSING:-}')
            assert result == ''

    def test_no_expansion_needed(self):
        """String without variables is unchanged."""
        result = expand_env_vars('plain string')
        assert result == 'plain string'


# ============================================================================
# load_yaml_file()
# ============================================================================

class TestLoadYamlFile:
    """Test load_yaml_file() function."""

    def test_valid_yaml(self, tmp_path):
        """Load valid YAML file."""
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text("key: value\nnumber: 42")

        result = load_yaml_file(yaml_file)
        assert result == {'key': 'value', 'number': 42}

    def test_nested_yaml(self, tmp_path):
        """Load nested YAML structure."""
        yaml_file = tmp_path / "nested.yml"
        yaml_file.write_text("""
outer:
  inner:
    key: value
  list:
    - item1
    - item2
""")

        result = load_yaml_file(yaml_file)
        assert result['outer']['inner']['key'] == 'value'
        assert result['outer']['list'] == ['item1', 'item2']

    def test_file_not_exists(self, tmp_path):
        """Raise error when file doesn't exist."""
        yaml_file = tmp_path / "nonexistent.yml"

        with pytest.raises(ConfigurationError) as exc_info:
            load_yaml_file(yaml_file)
        assert "does not exist" in str(exc_info.value)

    def test_empty_file(self, tmp_path):
        """Raise error when file is empty."""
        yaml_file = tmp_path / "empty.yml"
        yaml_file.write_text("")

        with pytest.raises(ConfigurationError) as exc_info:
            load_yaml_file(yaml_file)
        assert "empty" in str(exc_info.value).lower()

    def test_invalid_yaml_syntax(self, tmp_path):
        """Raise error for invalid YAML syntax."""
        yaml_file = tmp_path / "invalid.yml"
        yaml_file.write_text("key: value\n  invalid indentation\n  : bad")

        with pytest.raises(ConfigurationError) as exc_info:
            load_yaml_file(yaml_file)
        assert "YAML syntax" in str(exc_info.value)

    def test_permission_denied(self, tmp_path):
        """Raise error when permission denied."""
        yaml_file = tmp_path / "protected.yml"
        yaml_file.write_text("key: value")
        yaml_file.chmod(0o000)  # Remove all permissions

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                load_yaml_file(yaml_file)
            assert "Permission denied" in str(exc_info.value)
        finally:
            yaml_file.chmod(0o644)  # Restore permissions for cleanup

    def test_yaml_with_lists(self, tmp_path):
        """Load YAML with lists."""
        yaml_file = tmp_path / "lists.yml"
        yaml_file.write_text("""
items:
  - name: item1
    value: 1
  - name: item2
    value: 2
""")

        result = load_yaml_file(yaml_file)
        assert len(result['items']) == 2
        assert result['items'][0]['name'] == 'item1'

    def test_yaml_with_multiline_strings(self, tmp_path):
        """Load YAML with multiline strings."""
        yaml_file = tmp_path / "multiline.yml"
        yaml_file.write_text("""
description: |
  This is a
  multiline
  string
""")

        result = load_yaml_file(yaml_file)
        assert 'This is a' in result['description']
        assert 'multiline' in result['description']


# ============================================================================
# Config class
# ============================================================================

class TestConfig:
    """Test Config class."""

    def test_init_with_custom_dir(self, tmp_config_dir):
        """Initialize with custom config directory."""
        config = Config(tmp_config_dir)
        assert config.config_dir == tmp_config_dir
        assert config.config_file == tmp_config_dir / 'config.yml'
        assert config.rules_file == tmp_config_dir / 'rules.yml'

    def test_init_with_env_var(self, tmp_config_dir):
        """Initialize with CONFIG_DIR environment variable."""
        with patch.dict(os.environ, {'CONFIG_DIR': str(tmp_config_dir)}):
            config = Config()
            assert config.config_dir == tmp_config_dir

    def test_load_config_success(self, tmp_config_dir):
        """Successfully load config.yml."""
        config = Config(tmp_config_dir)
        assert config.config is not None
        assert 'qbittorrent' in config.config

    def test_load_rules_success(self, tmp_config_dir):
        """Successfully load rules.yml."""
        config = Config(tmp_config_dir)
        assert config.rules is not None
        assert isinstance(config.rules, list)
        assert len(config.rules) > 0

    def test_missing_config_file(self, tmp_path):
        """Raise error when config.yml missing."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(ConfigurationError):
            Config(empty_dir)

    def test_invalid_rules_not_list(self, tmp_path):
        """Raise error when rules is not a list."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        (config_dir / "config.yml").write_text("qbittorrent:\n  host: localhost")
        (config_dir / "rules.yml").write_text("rules: not_a_list")

        with pytest.raises(ConfigurationError) as exc_info:
            Config(config_dir)
        assert "must be a list" in str(exc_info.value)

    def test_get_simple_key(self, tmp_config_dir):
        """Get simple configuration key."""
        config = Config(tmp_config_dir)
        # Based on tmp_config_dir fixture
        assert config.get('qbittorrent.host') == 'http://localhost:8080'

    def test_get_nested_key(self, tmp_config_dir):
        """Get nested configuration key."""
        config = Config(tmp_config_dir)
        assert config.get('qbittorrent.username') == 'admin'

    def test_get_with_default(self, tmp_config_dir):
        """Get with default value for missing key."""
        config = Config(tmp_config_dir)
        assert config.get('nonexistent.key', 'default') == 'default'

    def test_get_missing_key_no_default(self, tmp_config_dir):
        """Get missing key returns None without default."""
        config = Config(tmp_config_dir)
        assert config.get('nonexistent.key') is None

    def test_get_qbittorrent_config(self, tmp_config_dir):
        """Get qBittorrent configuration."""
        config = Config(tmp_config_dir)
        qbt_config = config.get_qbittorrent_config()

        assert 'host' in qbt_config
        assert 'user' in qbt_config
        assert 'pass' in qbt_config
        assert qbt_config['host'] == 'http://localhost:8080'

    def test_get_qbittorrent_config_with_defaults(self, tmp_path):
        """Get qBittorrent config with missing values uses defaults."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        (config_dir / "config.yml").write_text("logging:\n  level: INFO")
        (config_dir / "rules.yml").write_text("rules: []")

        config = Config(config_dir)
        qbt_config = config.get_qbittorrent_config()

        assert qbt_config['host'] == 'http://localhost:8080'
        assert qbt_config['user'] == 'admin'
        assert qbt_config['pass'] == ''

    def test_is_dry_run_false_by_default(self, tmp_config_dir):
        """Dry run is false by default."""
        config = Config(tmp_config_dir)
        assert config.is_dry_run() is False

    def test_is_dry_run_from_config(self, tmp_path):
        """Read dry run from config file."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        (config_dir / "config.yml").write_text("""
qbittorrent:
  host: localhost
engine:
  dry_run: true
""")
        (config_dir / "rules.yml").write_text("rules: []")

        config = Config(config_dir)
        assert config.is_dry_run() is True

    def test_is_dry_run_from_env_var(self, tmp_config_dir):
        """Environment variable overrides config file."""
        with patch.dict(os.environ, {'DRY_RUN': 'true'}):
            config = Config(tmp_config_dir)
            assert config.is_dry_run() is True

    def test_is_dry_run_env_var_variations(self, tmp_config_dir):
        """Test various env var values for dry run."""
        for value in ['true', '1', 'yes', 'on', 'TRUE', 'YES']:
            with patch.dict(os.environ, {'DRY_RUN': value}):
                config = Config(tmp_config_dir)
                assert config.is_dry_run() is True, f"Failed for value: {value}"

        for value in ['false', '0', 'no', 'off', 'FALSE', 'NO']:
            with patch.dict(os.environ, {'DRY_RUN': value}):
                config = Config(tmp_config_dir)
                assert config.is_dry_run() is False, f"Failed for value: {value}"

    def test_is_dry_run_string_value_from_config(self, tmp_path):
        """Dry run handles string 'true' from YAML config (covers line 194)."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        (config_dir / "config.yml").write_text("""
qbittorrent:
  host: localhost
engine:
  dry_run: "true"
""")
        (config_dir / "rules.yml").write_text("rules: []")

        config = Config(config_dir)
        assert config.is_dry_run() is True

    def test_get_log_level_default(self, tmp_config_dir):
        """Get default log level."""
        config = Config(tmp_config_dir)
        assert config.get_log_level() == 'INFO'

    def test_get_log_level_from_env(self, tmp_config_dir):
        """Log level from environment variable."""
        with patch.dict(os.environ, {'LOG_LEVEL': 'debug'}):
            config = Config(tmp_config_dir)
            assert config.get_log_level() == 'DEBUG'

    def test_get_log_file_default(self, tmp_config_dir):
        """Get default log file path."""
        config = Config(tmp_config_dir)
        log_file = config.get_log_file()

        # Should be relative to config_dir
        assert log_file.is_absolute()
        assert log_file.parent.name == 'logs'

    def test_get_log_file_absolute_path(self, tmp_path):
        """Absolute log file path is used as-is."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        abs_log_path = "/var/log/qbt-rules.log"
        (config_dir / "config.yml").write_text(f"""
qbittorrent:
  host: localhost
logging:
  file: {abs_log_path}
""")
        (config_dir / "rules.yml").write_text("rules: []")

        config = Config(config_dir)
        assert str(config.get_log_file()) == abs_log_path

    def test_get_log_file_from_env(self, tmp_config_dir):
        """Log file from environment variable."""
        with patch.dict(os.environ, {'LOG_FILE': '/tmp/custom.log'}):
            config = Config(tmp_config_dir)
            assert str(config.get_log_file()) == '/tmp/custom.log'

    def test_get_trace_mode_false_by_default(self, tmp_config_dir):
        """Trace mode is false by default."""
        config = Config(tmp_config_dir)
        assert config.get_trace_mode() is False

    def test_get_trace_mode_from_config(self, tmp_path):
        """Read trace mode from config file."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        (config_dir / "config.yml").write_text("""
qbittorrent:
  host: localhost
logging:
  trace_mode: true
""")
        (config_dir / "rules.yml").write_text("rules: []")

        config = Config(config_dir)
        assert config.get_trace_mode() is True

    def test_get_trace_mode_from_env(self, tmp_config_dir):
        """Trace mode from environment variable."""
        with patch.dict(os.environ, {'TRACE_MODE': 'true'}):
            config = Config(tmp_config_dir)
            assert config.get_trace_mode() is True

    def test_get_trace_mode_env_variations(self, tmp_config_dir):
        """Test various env var values for trace mode."""
        for value in ['true', '1', 'yes', 'on']:
            with patch.dict(os.environ, {'TRACE_MODE': value}):
                config = Config(tmp_config_dir)
                assert config.get_trace_mode() is True

    def test_get_trace_mode_env_false_values(self, tmp_config_dir):
        """Trace mode handles false env var values (covers line 225)."""
        for value in ['false', '0', 'no', 'off']:
            with patch.dict(os.environ, {'TRACE_MODE': value}):
                config = Config(tmp_config_dir)
                assert config.get_trace_mode() is False, f"Failed for value: {value}"

    def test_get_trace_mode_string_value_from_config(self, tmp_path):
        """Trace mode handles string 'true' from YAML config (covers line 232)."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        (config_dir / "config.yml").write_text("""
qbittorrent:
  host: localhost
logging:
  trace_mode: "true"
""")
        (config_dir / "rules.yml").write_text("rules: []")

        config = Config(config_dir)
        assert config.get_trace_mode() is True

    def test_get_rules(self, tmp_config_dir):
        """Get list of rules."""
        config = Config(tmp_config_dir)
        rules = config.get_rules()

        assert isinstance(rules, list)
        assert len(rules) > 0
        assert 'name' in rules[0]

    def test_env_var_expansion_in_config(self, tmp_path):
        """Environment variables are expanded in config."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        (config_dir / "config.yml").write_text("""
qbittorrent:
  host: ${QB_HOST:-http://localhost:8080}
  username: ${QB_USER:-admin}
""")
        (config_dir / "rules.yml").write_text("rules: []")

        with patch.dict(os.environ, {'QB_HOST': 'http://custom:9090', 'QB_USER': 'myuser'}):
            config = Config(config_dir)
            assert config.get('qbittorrent.host') == 'http://custom:9090'
            assert config.get('qbittorrent.username') == 'myuser'

    def test_env_var_expansion_with_defaults(self, tmp_path):
        """Environment variable defaults work in config."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        (config_dir / "config.yml").write_text("""
qbittorrent:
  host: ${QB_HOST:-http://localhost:8080}
""")
        (config_dir / "rules.yml").write_text("rules: []")

        with patch.dict(os.environ, {}, clear=True):
            config = Config(config_dir)
            assert config.get('qbittorrent.host') == 'http://localhost:8080'


# ============================================================================
# load_config()
# ============================================================================

class TestLoadConfig:
    """Test load_config() convenience function."""

    def test_load_config_returns_config_object(self, tmp_config_dir):
        """load_config() returns Config object."""
        config = load_config(tmp_config_dir)
        assert isinstance(config, Config)
        assert config.config_dir == tmp_config_dir

    def test_load_config_without_args(self, tmp_config_dir):
        """load_config() without args uses environment/default."""
        with patch.dict(os.environ, {'CONFIG_DIR': str(tmp_config_dir)}):
            config = load_config()
            assert isinstance(config, Config)
