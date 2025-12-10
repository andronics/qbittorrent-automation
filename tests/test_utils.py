"""Tests for utility functions."""

import time

import pytest

from qbittorrent_automation.utils import parse_tags, is_older_than, is_newer_than


def test_parse_tags_empty():
    """Test parsing empty tag string."""
    result = parse_tags("")
    assert result == []


def test_parse_tags_single():
    """Test parsing single tag."""
    result = parse_tags("movies")
    assert result == ["movies"]


def test_parse_tags_multiple():
    """Test parsing multiple tags."""
    result = parse_tags("movies, hd, private")
    assert set(result) == {"movies", "hd", "private"}


def test_parse_tags_with_spaces():
    """Test parsing tags with extra spaces."""
    result = parse_tags("  movies  ,  hd  ,  private  ")
    assert set(result) == {"movies", "hd", "private"}


def test_is_older_than_true():
    """Test is_older_than returns True for old timestamp."""
    old_timestamp = int(time.time()) - 86400  # 1 day ago
    result = is_older_than(old_timestamp, 3600)  # older than 1 hour
    assert result is True


def test_is_older_than_false():
    """Test is_older_than returns False for recent timestamp."""
    recent_timestamp = int(time.time()) - 1800  # 30 minutes ago
    result = is_older_than(recent_timestamp, 3600)  # older than 1 hour
    assert result is False


def test_is_newer_than_true():
    """Test is_newer_than returns True for recent timestamp."""
    recent_timestamp = int(time.time()) - 1800  # 30 minutes ago
    result = is_newer_than(recent_timestamp, 3600)  # newer than 1 hour
    assert result is True


def test_is_newer_than_false():
    """Test is_newer_than returns False for old timestamp."""
    old_timestamp = int(time.time()) - 86400  # 1 day ago
    result = is_newer_than(old_timestamp, 3600)  # newer than 1 hour
    assert result is False
