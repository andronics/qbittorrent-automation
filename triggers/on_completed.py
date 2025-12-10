#!/usr/bin/env python3
"""
Legacy wrapper for on_completed trigger.

This file provides backward compatibility for existing deployments.
The actual implementation has moved to src/qbittorrent_automation/cli/on_completed.py

For new installations, use the console script instead:
    qbt-on-completed <torrent_hash>

Or run as a Python module:
    python -m qbittorrent_automation.cli.on_completed <torrent_hash>
"""

from qbittorrent_automation.cli.on_completed import main

if __name__ == '__main__':
    main()
