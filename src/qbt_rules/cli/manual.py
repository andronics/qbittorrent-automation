#!/usr/bin/env python3
"""
Manual/CLI trigger for qBittorrent automation
Use this for manual execution or testing
"""

import sys

from qbt_rules.arguments import create_parser, process_args, handle_utility_args
from qbt_rules.config import load_config
from qbt_rules.api import QBittorrentAPI
from qbt_rules.engine import RulesEngine
from qbt_rules.errors import handle_errors
from qbt_rules.logging import setup_logging


@handle_errors
def main():
    """Main entry point for manual trigger"""
    # Parse arguments
    parser = create_parser("Manual Trigger", trigger_type="manual")
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
    engine.run(trigger='manual')

    sys.exit(0)


if __name__ == '__main__':
    main()
