#!/usr/bin/env python3
"""
Scheduled trigger for qBittorrent automation
Use this for cron jobs and periodic execution
"""

import sys

from qbittorrent_automation.arguments import create_parser, process_args, handle_utility_args
from qbittorrent_automation.config import load_config
from qbittorrent_automation.api import QBittorrentAPI
from qbittorrent_automation.engine import RulesEngine
from qbittorrent_automation.errors import handle_errors
from qbittorrent_automation.logging import setup_logging


@handle_errors
def main():
    """Main entry point for scheduled trigger"""
    # Parse arguments (all optional for backward compatibility)
    parser = create_parser("Scheduled Trigger", trigger_type="scheduled")
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
    engine.run(trigger='scheduled')

    sys.exit(0)


if __name__ == '__main__':
    main()
