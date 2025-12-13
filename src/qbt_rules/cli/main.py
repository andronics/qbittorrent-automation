#!/usr/bin/env python3
"""
Unified CLI entry point for qbt-rules
Consolidates all trigger types into a single command
"""

import sys

from qbt_rules.arguments import create_parser, process_args, handle_utility_args, validate_torrent_hash
from qbt_rules.config import load_config
from qbt_rules.api import QBittorrentAPI
from qbt_rules.engine import RulesEngine
from qbt_rules.errors import handle_errors
from qbt_rules.logging import setup_logging


@handle_errors
def main():
    """Main entry point for unified qbt-rules CLI"""
    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()

    # Process arguments and get config directory
    config_dir = process_args(args)

    # Load configuration
    config = load_config(config_dir)

    # Setup logging with trace mode
    trace_mode = config.get_trace_mode()
    setup_logging(config, trace_mode)

    # Handle utility arguments (--validate, --list-rules)
    if handle_utility_args(args, config):
        sys.exit(0)

    # Determine trigger and torrent_hash
    trigger = args.trigger if args.trigger else 'manual'
    torrent_hash = args.torrent_hash if hasattr(args, 'torrent_hash') and args.torrent_hash else None

    # Validate torrent hash if provided
    if torrent_hash:
        try:
            torrent_hash = validate_torrent_hash(torrent_hash)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Special handling: if --torrent-hash provided without --trigger,
    # use trigger-agnostic mode (trigger=None)
    if torrent_hash and not args.trigger:
        trigger = None

    # Initialize API client
    qbt_config = config.get_qbittorrent_config()
    api = QBittorrentAPI(
        host=qbt_config['host'],
        username=qbt_config['user'],
        password=qbt_config['pass']
    )

    # Initialize and run engine
    dry_run = config.is_dry_run()
    engine = RulesEngine(api, config, dry_run)
    engine.run(trigger=trigger, torrent_hash=torrent_hash)

    sys.exit(0)


if __name__ == '__main__':
    main()
