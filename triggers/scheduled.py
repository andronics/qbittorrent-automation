#!/usr/bin/env python3
"""
Legacy wrapper for scheduled trigger.

This file provides backward compatibility for existing deployments.
The actual implementation has moved to src/qbt_rules/cli/scheduled.py

For new installations, use the console script instead:
    qbt-scheduled [options]

Or run as a Python module:
    python -m qbt_rules.cli.scheduled [options]
"""

from qbt_rules.cli.scheduled import main

if __name__ == '__main__':
    main()
