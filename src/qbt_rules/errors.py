"""
User-friendly error handling for qBittorrent automation
Provides clear, actionable error messages without Python stack traces
"""

import sys
from typing import Optional

from qbt_rules.logging import get_logger

logger = get_logger(__name__)


class QBittorrentError(Exception):
    """Base exception for all qBittorrent automation errors"""

    def __init__(self, code: str, message: str, details: Optional[dict] = None, fix: Optional[str] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        self.fix = fix
        super().__init__(self.format_error())

    def format_error(self) -> str:
        """Format error message for user display"""
        lines = [self.message]

        if self.details:
            for key, value in self.details.items():
                lines.append(f"  • {key}: {value}")

        if self.fix:
            lines.append(f"  • Fix: {self.fix}")

        return "\n".join(lines)


class AuthenticationError(QBittorrentError):
    """Authentication with qBittorrent failed"""

    def __init__(self, host: str, response_text: Optional[str] = None):
        details = {"Host": host}
        if response_text:
            details["Response"] = response_text

        super().__init__(
            code="AUTH-001",
            message="Cannot connect to qBittorrent",
            details=details,
            fix="Check QBITTORRENT_HOST, QBITTORRENT_USER, and QBITTORRENT_PASS environment variables"
        )


class ConnectionError(QBittorrentError):
    """Cannot reach qBittorrent server"""

    def __init__(self, host: str, original_error: str):
        super().__init__(
            code="CONN-001",
            message="Cannot reach qBittorrent server",
            details={
                "Host": host,
                "Error": str(original_error)
            },
            fix="Check that qBittorrent is running and the host/port are correct"
        )


class APIError(QBittorrentError):
    """qBittorrent API call failed"""

    def __init__(self, endpoint: str, status_code: int, response_text: Optional[str] = None):
        details = {
            "Endpoint": endpoint,
            "Status Code": status_code
        }
        if response_text:
            details["Response"] = response_text[:200]  # Limit response length

        super().__init__(
            code="API-001",
            message="qBittorrent API request failed",
            details=details,
            fix="Check qBittorrent logs for more details"
        )


class ConfigurationError(QBittorrentError):
    """Configuration file error"""

    def __init__(self, file_path: str, reason: str):
        super().__init__(
            code="CFG-001",
            message=f"Cannot load configuration",
            details={
                "File": file_path,
                "Problem": reason
            },
            fix="Check that the configuration file exists and has valid YAML syntax"
        )


class LoggingSetupError(QBittorrentError):
    """Cannot setup file logging"""

    def __init__(self, log_path: str, reason: str, config_dir: Optional[str] = None):
        details = {
            "Log Path": log_path,
            "Problem": reason
        }
        if config_dir:
            details["CONFIG_DIR"] = config_dir

        super().__init__(
            code="LOG-001",
            message="Cannot setup file logging",
            details=details,
            fix="Set LOG_FILE environment variable to a writable path (e.g., LOG_FILE=./logs/qbittorrent.log), or ensure CONFIG_DIR points to a writable location"
        )


class RuleValidationError(QBittorrentError):
    """Rule configuration is invalid"""

    def __init__(self, rule_name: str, reason: str):
        super().__init__(
            code="RULE-001",
            message=f"Invalid rule configuration",
            details={
                "Rule": rule_name,
                "Problem": reason
            },
            fix="Check the rule syntax in rules.yml"
        )


class FieldError(QBittorrentError):
    """Invalid field reference in condition"""

    def __init__(self, field: str, reason: str):
        valid_prefixes = "info.*, trackers.*, files.*, peers.*, properties.*, transfer.*, webseeds.*"
        super().__init__(
            code="FIELD-001",
            message=f"Invalid field reference",
            details={
                "Field": field,
                "Problem": reason,
                "Valid prefixes": valid_prefixes
            },
            fix="Use dot notation with API prefix (e.g., 'info.name', 'trackers.url')"
        )


class OperatorError(QBittorrentError):
    """Unknown operator in condition"""

    def __init__(self, operator: str, field: str):
        valid_operators = "==, !=, >, <, >=, <=, contains, not_contains, matches, in, not_in, older_than, newer_than"
        super().__init__(
            code="OP-001",
            message=f"Unknown operator",
            details={
                "Operator": operator,
                "Field": field,
                "Valid operators": valid_operators
            },
            fix="Use one of the supported operators"
        )


def handle_errors(func):
    """Decorator for user-friendly error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except QBittorrentError as e:
            # Our custom errors - display nicely
            logger.error(str(e))
            sys.exit(1)
        except KeyboardInterrupt:
            logger.info("\nOperation cancelled by user")
            sys.exit(0)
        except Exception as e:
            # Unexpected error - show generic message
            logger.error("Unexpected error occurred")
            logger.error(f"  • Error: {type(e).__name__}: {str(e)}")
            logger.error("  • Fix: Please report this issue with the error details above")
            logger.debug("Full stack trace:", exc_info=True)
            sys.exit(1)
    return wrapper
