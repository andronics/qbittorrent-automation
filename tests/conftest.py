"""Pytest configuration and fixtures."""

import pytest
from typing import Dict, Any


@pytest.fixture
def mock_qbt_config() -> Dict[str, Any]:
    """Mock qBittorrent configuration."""
    return {
        "host": "http://localhost:8080",
        "user": "admin",
        "pass": "adminpass",
    }


@pytest.fixture
def mock_torrent_info() -> Dict[str, Any]:
    """Mock torrent info from qBittorrent API."""
    return {
        "hash": "abc123def456",
        "name": "Example.Torrent.1080p",
        "size": 1073741824,  # 1 GB
        "progress": 1.0,
        "dlspeed": 0,
        "upspeed": 524288,  # 512 KB/s
        "downloaded": 1073741824,
        "uploaded": 2147483648,  # 2 GB
        "ratio": 2.0,
        "num_complete": 5,
        "num_incomplete": 2,
        "num_leechs": 2,
        "num_seeds": 5,
        "state": "uploading",
        "category": "",
        "tags": "",
        "added_on": 1700000000,
        "completion_on": 1700010000,
        "last_activity": 1700020000,
        "availability": 1.0,
    }


@pytest.fixture
def mock_rule() -> Dict[str, Any]:
    """Mock rule configuration."""
    return {
        "name": "Test rule",
        "enabled": True,
        "stop_on_match": False,
        "conditions": {
            "all": [
                {"field": "info.ratio", "operator": ">=", "value": 1.0}
            ]
        },
        "actions": [
            {"type": "add_tag", "params": {"tag": "test"}}
        ]
    }
