"""
Configuration loader with environment variable expansion
"""

import os
import re
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from qbt_rules.errors import ConfigurationError


def expand_env_vars(value: Any) -> Any:
    """
    Recursively expand environment variables in configuration values

    Supports format: ${VAR_NAME:-default_value}

    Args:
        value: Configuration value (can be str, dict, list, or primitive)

    Returns:
        Value with environment variables expanded

    Examples:
        >>> os.environ['TEST_VAR'] = 'hello'
        >>> expand_env_vars('${TEST_VAR:-default}')
        'hello'
        >>> expand_env_vars('${MISSING_VAR:-default}')
        'default'
    """
    if isinstance(value, str):
        # Pattern: ${VAR_NAME:-default} or ${VAR_NAME}
        pattern = r'\$\{([^}:]+)(?::-([^}]*))?\}'

        def replacer(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ''
            return os.environ.get(var_name, default_value)

        return re.sub(pattern, replacer, value)

    elif isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}

    elif isinstance(value, list):
        return [expand_env_vars(item) for item in value]

    else:
        # Primitive type (int, bool, None, etc.)
        return value


def load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """
    Load YAML file with error handling

    Args:
        file_path: Path to YAML file

    Returns:
        Parsed YAML as dictionary

    Raises:
        ConfigurationError: If file cannot be loaded
    """
    try:
        if not file_path.exists():
            raise ConfigurationError(
                str(file_path),
                f"File does not exist"
            )

        with open(file_path, 'r') as f:
            content = yaml.safe_load(f)

        if content is None:
            raise ConfigurationError(
                str(file_path),
                "File is empty"
            )

        return content

    except yaml.YAMLError as e:
        raise ConfigurationError(
            str(file_path),
            f"Invalid YAML syntax: {str(e)}"
        )
    except PermissionError:
        raise ConfigurationError(
            str(file_path),
            "Permission denied - cannot read file"
        )
    except Exception as e:
        raise ConfigurationError(
            str(file_path),
            f"Cannot read file: {str(e)}"
        )


class Config:
    """Configuration manager"""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration

        Args:
            config_dir: Directory containing config.yml and rules.yml
                       Defaults to /config
        """
        if config_dir is None:
            config_dir = Path(os.environ.get('CONFIG_DIR', '/config'))

        self.config_dir = config_dir
        self.config_file = config_dir / 'config.yml'
        self.rules_file = config_dir / 'rules.yml'

        # Load configurations
        self._load_config()
        self._load_rules()

    def _load_config(self):
        """Load config.yml with environment variable expansion"""
        logging.debug(f"Loading config from {self.config_file}")

        raw_config = load_yaml_file(self.config_file)
        self.config = expand_env_vars(raw_config)

        logging.debug(f"Configuration loaded successfully")

    def _load_rules(self):
        """Load rules.yml"""
        logging.debug(f"Loading rules from {self.rules_file}")

        raw_rules = load_yaml_file(self.rules_file)
        self.rules = raw_rules.get('rules', [])

        if not isinstance(self.rules, list):
            raise ConfigurationError(
                str(self.rules_file),
                "'rules' must be a list"
            )

        logging.debug(f"Loaded {len(self.rules)} rules")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key

        Args:
            key: Configuration key (e.g., 'qbittorrent.host')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_qbittorrent_config(self) -> Dict[str, str]:
        """Get qBittorrent connection configuration"""
        return {
            'host': self.get('qbittorrent.host', 'http://localhost:8080'),
            'user': self.get('qbittorrent.user', 'admin'),
            'pass': self.get('qbittorrent.pass', '')
        }

    def is_dry_run(self) -> bool:
        """Check if dry-run mode is enabled"""
        # ENV var takes precedence
        env_dry_run = os.environ.get('DRY_RUN', '').lower()
        if env_dry_run in ('true', '1', 'yes', 'on'):
            return True
        elif env_dry_run in ('false', '0', 'no', 'off'):
            return False

        # Fall back to config file
        config_value = self.get('engine.dry_run', False)

        # Handle string values from YAML
        if isinstance(config_value, str):
            return config_value.lower() in ('true', '1', 'yes', 'on')

        return bool(config_value)

    def get_log_level(self) -> str:
        """Get logging level"""
        return os.environ.get('LOG_LEVEL', self.get('logging.level', 'INFO')).upper()

    def get_log_file(self) -> Path:
        """
        Get log file path

        If path is relative, make it relative to CONFIG_DIR.
        If path is absolute, use as-is (backward compatibility).
        """
        log_file_str = os.environ.get('LOG_FILE', self.get('logging.file', 'logs/qbittorrent.log'))
        log_path = Path(log_file_str)

        # If relative path, make it relative to CONFIG_DIR
        if not log_path.is_absolute():
            log_path = self.config_dir / log_path

        return log_path

    def get_trace_mode(self) -> bool:
        """Check if trace mode is enabled (detailed logging with module/function/line)"""
        # ENV var takes precedence
        env_trace = os.environ.get('TRACE_MODE', '').lower()
        if env_trace in ('true', '1', 'yes', 'on'):
            return True
        elif env_trace in ('false', '0', 'no', 'off'):
            return False

        # Fall back to config file
        config_value = self.get('logging.trace_mode', False)

        # Handle string values from YAML
        if isinstance(config_value, str):
            return config_value.lower() in ('true', '1', 'yes', 'on')

        return bool(config_value)

    def get_rules(self) -> list:
        """Get list of rules"""
        return self.rules


def load_config(config_dir: Optional[Path] = None) -> Config:
    """
    Load configuration from directory

    Args:
        config_dir: Directory containing config.yml and rules.yml

    Returns:
        Config object
    """
    return Config(config_dir)
