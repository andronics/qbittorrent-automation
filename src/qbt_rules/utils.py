"""
Shared utility functions for qBittorrent automation
"""

import re
import time
import logging
from typing import List, Dict, Any


def parse_tags(torrent: Dict) -> List[str]:
    """
    Parse tags from torrent dictionary into list

    Args:
        torrent: Torrent dictionary from qBittorrent API

    Returns:
        List of tag strings
    """
    tags_str = torrent.get('tags', '')
    if not tags_str:
        return []
    return [tag.strip() for tag in tags_str.split(',') if tag.strip()]


def parse_duration(duration: str) -> int:
    """
    Parse human-readable duration to seconds

    Args:
        duration: Duration string like "30 days", "12 hours", "5 minutes"

    Returns:
        Duration in seconds

    Examples:
        >>> parse_duration("30 days")
        2592000
        >>> parse_duration("12 hours")
        43200
        >>> parse_duration("5 minutes")
        300
    """
    duration = duration.lower().strip()

    # Extract number and unit
    match = re.match(r'(\d+)\s*(second|minute|hour|day|week|month|year)s?', duration)
    if not match:
        logging.warning(f"Invalid duration format: {duration}, defaulting to 0")
        return 0

    amount = int(match.group(1))
    unit = match.group(2)

    multipliers = {
        'second': 1,
        'minute': 60,
        'hour': 3600,
        'day': 86400,
        'week': 604800,
        'month': 2592000,  # 30 days
        'year': 31536000   # 365 days
    }

    return amount * multipliers.get(unit, 0)


def is_older_than(timestamp: int, duration: str) -> bool:
    """
    Check if timestamp is older than duration

    Args:
        timestamp: Unix timestamp in seconds
        duration: Duration string like "30 days"

    Returns:
        True if timestamp is older than duration
    """
    if timestamp <= 0:
        return False

    age_seconds = time.time() - timestamp
    duration_seconds = parse_duration(duration)
    return age_seconds > duration_seconds


def is_newer_than(timestamp: int, duration: str) -> bool:
    """
    Check if timestamp is newer than duration

    Args:
        timestamp: Unix timestamp in seconds
        duration: Duration string like "30 days"

    Returns:
        True if timestamp is newer than duration
    """
    if timestamp <= 0:
        return False

    age_seconds = time.time() - timestamp
    duration_seconds = parse_duration(duration)
    return age_seconds < duration_seconds


def format_bytes(bytes_count: int) -> str:
    """
    Format bytes into human-readable string

    Args:
        bytes_count: Number of bytes

    Returns:
        Formatted string like "1.5 GB"
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.2f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.2f} PB"


def format_speed(bytes_per_second: int) -> str:
    """
    Format speed into human-readable string

    Args:
        bytes_per_second: Speed in bytes per second

    Returns:
        Formatted string like "1.5 MB/s"
    """
    return f"{format_bytes(bytes_per_second)}/s"


def format_duration(seconds: int) -> str:
    """
    Format seconds into human-readable duration

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string like "2d 5h 30m"
    """
    if seconds < 60:
        return f"{seconds}s"

    parts = []

    days = seconds // 86400
    if days > 0:
        parts.append(f"{days}d")
        seconds %= 86400

    hours = seconds // 3600
    if hours > 0:
        parts.append(f"{hours}h")
        seconds %= 3600

    minutes = seconds // 60
    if minutes > 0:
        parts.append(f"{minutes}m")

    return " ".join(parts)


def validate_field_name(field: str) -> bool:
    """
    Validate that field name uses correct dot notation

    Args:
        field: Field name to validate

    Returns:
        True if valid

    Raises:
        ValueError if invalid format
    """
    if '.' not in field:
        return False

    prefix = field.split('.', 1)[0]
    valid_prefixes = ['info', 'trackers', 'files', 'peers', 'properties', 'transfer', 'webseeds']

    return prefix in valid_prefixes
