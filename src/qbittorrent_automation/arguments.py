"""
Centralized argument parsing for qBittorrent automation triggers
Provides consistent CLI interface across all triggers
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional

from qbittorrent_automation.__version__ import __version__, __description__


def smart_config_default() -> str:
    """
    Determine smart default for config directory

    Returns ./config if it exists (bare metal), otherwise /config (Docker)
    """
    local_config = Path('./config')
    if local_config.exists() and local_config.is_dir():
        return './config'
    return '/config'


def create_base_parser(description: str) -> argparse.ArgumentParser:
    """
    Create base argument parser with common arguments

    Args:
        description: Description for the parser

    Returns:
        ArgumentParser with common arguments added
    """
    parser = argparse.ArgumentParser(
        description=f'qBittorrent Automation - {description}',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Common configuration arguments
    parser.add_argument(
        '--config-dir',
        type=Path,
        default=None,
        help=f'Path to configuration directory (default: {smart_config_default()} or CONFIG_DIR env var)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate changes without making them (useful for testing)'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging verbosity (default: from config or INFO)'
    )

    parser.add_argument(
        '--trace',
        action='store_true',
        help='Enable trace mode with detailed logging (module/function/line)'
    )

    # Utility arguments
    parser.add_argument(
        '--version',
        action='version',
        version=f'qBittorrent Automation v{__version__}'
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate configuration and rules files without running'
    )

    parser.add_argument(
        '--list-rules',
        action='store_true',
        help='List all rules with priorities and exit'
    )

    return parser


def create_parser(description: str, trigger_type: str = 'manual') -> argparse.ArgumentParser:
    """
    Create argument parser for a specific trigger type

    Args:
        description: Description for this trigger
        trigger_type: Type of trigger ('manual', 'scheduled', 'webhook')

    Returns:
        Configured ArgumentParser
    """
    parser = create_base_parser(description)

    # Add trigger-specific arguments
    if trigger_type == 'webhook':
        parser.add_argument(
            'torrent_hash',
            nargs='?',  # Optional for backward compatibility with env-only usage
            help='Torrent hash from qBittorrent webhook (40-character hex string)'
        )

    # Add trigger-specific epilog with examples
    if trigger_type == 'manual':
        parser.epilog = '''
Examples:
  # Run all rules
  python triggers/manual.py

  # Run in dry-run mode
  python triggers/manual.py --dry-run

  # Use custom config directory
  python triggers/manual.py --config-dir /path/to/config

  # Enable trace mode for detailed logging
  python triggers/manual.py --trace

  # Validate configuration without running
  python triggers/manual.py --validate

  # List all rules
  python triggers/manual.py --list-rules
        '''
    elif trigger_type == 'scheduled':
        parser.epilog = '''
Examples:
  # Run from cron (uses environment variables)
  */15 * * * * cd /app && python3 triggers/scheduled.py

  # Test with dry-run override
  python triggers/scheduled.py --dry-run

  # Validate before deploying to cron
  python triggers/scheduled.py --validate
        '''
    elif trigger_type == 'webhook':
        parser.epilog = '''
Examples:
  # Called by qBittorrent webhook (automatic)
  python triggers/on_added.py abc123def456...

  # Test manually with specific torrent
  python triggers/on_added.py --dry-run abc123def456...

  # Validate webhook configuration
  python triggers/on_added.py --validate
        '''

    return parser


def validate_torrent_hash(torrent_hash: Optional[str]) -> str:
    """
    Validate torrent hash format

    Args:
        torrent_hash: Hash to validate

    Returns:
        Validated hash

    Raises:
        ValueError: If hash is invalid
    """
    if not torrent_hash:
        raise ValueError("Torrent hash is required")

    # qBittorrent uses 40-character SHA-1 hashes (hex)
    if len(torrent_hash) != 40:
        raise ValueError(f"Invalid torrent hash length: {len(torrent_hash)} (expected 40)")

    # Check if all characters are valid hex
    try:
        int(torrent_hash, 16)
    except ValueError:
        raise ValueError(f"Invalid torrent hash format: must be hexadecimal")

    return torrent_hash.lower()


def process_args(args: argparse.Namespace) -> Path:
    """
    Process parsed arguments and set environment variables

    Args:
        args: Parsed arguments from argparse

    Returns:
        Path to configuration directory
    """
    # Set environment variables from command-line arguments
    if args.dry_run:
        os.environ['DRY_RUN'] = 'true'

    if args.log_level:
        os.environ['LOG_LEVEL'] = args.log_level

    if args.trace:
        os.environ['TRACE_MODE'] = 'true'

    # Determine config directory
    if args.config_dir:
        config_dir = args.config_dir
    elif 'CONFIG_DIR' in os.environ:
        config_dir = Path(os.environ['CONFIG_DIR'])
    else:
        config_dir = Path(smart_config_default())

    return config_dir


def handle_utility_args(args: argparse.Namespace, config) -> bool:
    """
    Handle utility arguments (--validate, --list-rules)

    Args:
        args: Parsed arguments
        config: Loaded configuration object

    Returns:
        True if a utility argument was handled (should exit), False otherwise
    """
    from lib.logging import get_logger
    logger = get_logger(__name__)

    # Handle --validate
    if args.validate:
        logger.info("Validating configuration and rules...")

        try:
            # Check qBittorrent config
            qbt_config = config.get_qbittorrent_config()
            required = ['host', 'user', 'pass']
            missing = [k for k in required if not qbt_config.get(k)]
            if missing:
                logger.error(f"Missing qBittorrent configuration: {', '.join(missing)}")
                return True

            logger.info(f"✓ qBittorrent connection configured: {qbt_config['host']}")

            # Check rules
            rules = config.get_rules()
            if not rules:
                logger.warning("No rules defined in rules.yml")
            else:
                logger.info(f"✓ Loaded {len(rules)} rules")

                # Validate each rule
                for i, rule in enumerate(rules, 1):
                    name = rule.get('name', f'Rule {i}')
                    if not rule.get('conditions'):
                        logger.warning(f"  ⚠ '{name}': No conditions defined")
                    if not rule.get('actions'):
                        logger.warning(f"  ⚠ '{name}': No actions defined")
                    else:
                        logger.info(f"  ✓ '{name}'")

            logger.info("\nValidation complete! Configuration is valid.")

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return True

        return True

    # Handle --list-rules
    if args.list_rules:
        rules = config.get_rules()

        if not rules:
            logger.info("No rules defined in rules.yml")
            return True

        # Rules execute in file order (no sorting)
        logger.info(f"\nRules ({len(rules)} total, execute in file order):\n")
        logger.info(f"{'#':<5} {'Enabled':<10} {'Stop':<8} {'Trigger':<15} {'Name'}")
        logger.info("-" * 80)

        for index, rule in enumerate(rules, 1):
            enabled = '✓' if rule.get('enabled', True) else '✗'
            stop = '✓' if rule.get('stop_on_match', False) else '-'

            # Get trigger filter
            conditions = rule.get('conditions', {})
            trigger_filter = conditions.get('trigger', 'all')
            if isinstance(trigger_filter, list):
                trigger_filter = ','.join(trigger_filter)

            name = rule.get('name', 'Unnamed')

            logger.info(f"{index:<5} {enabled:<10} {stop:<8} {trigger_filter:<15} {name}")

        logger.info("")
        return True

    return False
