#!/usr/bin/env python3
"""
On Added webhook trigger for qBittorrent automation
Called by qBittorrent when a torrent is added

Usage:
  Configure in qBittorrent:
  Tools → Options → Downloads → Run external program on torrent added
  Command: python3 /app/triggers/on_added.py "%I"

  Where %I is the torrent hash
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.arguments import create_parser, process_args, handle_utility_args, validate_torrent_hash
from lib.config import load_config
from lib.api import QBittorrentAPI
from lib.engine import QBittorrentEngine
from lib.errors import handle_errors
from lib.logging import setup_logging, get_logger


@handle_errors
def main():
    """Main entry point for on_added webhook trigger"""
    # Parse arguments
    parser = create_parser("On Added Webhook", trigger_type="webhook")
    args = parser.parse_args()

    # Process arguments and get config directory
    config_dir = process_args(args)

    # Load configuration
    config = load_config(config_dir)

    # Setup logging with trace mode
    trace_mode = config.get_trace_mode()
    setup_logging(config, trace_mode)

    logger = get_logger(__name__)

    # Handle utility arguments (--validate, --list-rules)
    if handle_utility_args(args, config):
        sys.exit(0)

    # Validate torrent hash (required for actual execution)
    if not args.torrent_hash:
        logger.error("Usage: on_added.py <torrent_hash>")
        logger.error("This script should be called by qBittorrent with torrent hash as argument")
        sys.exit(1)

    try:
        torrent_hash = validate_torrent_hash(args.torrent_hash)
    except ValueError as e:
        logger.error(f"Invalid torrent hash: {e}")
        sys.exit(1)

    logger.info(f"on_added webhook triggered for torrent: {torrent_hash}")

    # Initialize API client
    qbt_config = config.get_qbittorrent_config()
    api = QBittorrentAPI(
        host=qbt_config['host'],
        username=qbt_config['user'],
        password=qbt_config['pass']
    )

    # Initialize and run engine for this specific torrent
    dry_run = config.is_dry_run()
    engine = QBittorrentEngine(api, config, dry_run)
    engine.run(trigger='on_added', torrent_hash=torrent_hash)

    sys.exit(0)


if __name__ == '__main__':
    main()
