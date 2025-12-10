#!/usr/bin/env python3
"""
Legacy wrapper for manual trigger.

This file provides backward compatibility for existing deployments.
The actual implementation has moved to src/qbt_rules/cli/manual.py

For new installations, use the console script instead:
    qbt-manual [options]

Or run as a Python module:
    python -m qbt_rules.cli.manual [options]
"""

from qbt_rules.cli.manual import main

if __name__ == '__main__':
    main()
