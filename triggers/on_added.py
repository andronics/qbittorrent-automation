#!/usr/bin/env python3
"""
Legacy wrapper for on_added trigger.

This file provides backward compatibility for existing deployments.
The actual implementation has moved to src/qbittorrent_automation/cli/on_added.py

For new installations, use the console script instead:
    qbt-on-added <torrent_hash>

Or run as a Python module:
    python -m qbittorrent_automation.cli.on_added <torrent_hash>
"""

from qbittorrent_automation.cli.on_added import main

if __name__ == '__main__':
    main()
