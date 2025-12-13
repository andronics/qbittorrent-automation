"""Tests for utility functions."""

import time

import pytest

from qbt_rules.utils import parse_tags, is_older_than, is_newer_than, is_larger_than, is_smaller_than


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


def test_is_larger_than_true():
    """Test is_larger_than returns True for larger size."""
    size = 2048**3  # 2 GB
    result = is_larger_than(size, 1024**3) # larger than 1 GB
    assert result is True
    

def test_is_larger_than_false():
    """Test is_larger_than returns False for smaller size."""
    size = 1024**2  # 1 MB
    result = is_larger_than(size, 1024**3) # larger than 1 GB
    assert result is False


def test_is_smaller_than_true():
    """Test is_smaller_than returns True for smaler size."""
    size = 1024**2  # 1 MB
    result = is_smaller_than(size, 1024**3) # smaler than 1 GB
    assert result is True
    

def test_is_smaller_than_false():
    """Test is_smaller_than returns False for smaller size."""
    size = 2048**3  # 2 GB
    result = is_smaller_than(size, 1024**3) # smaler than 1 GB
    assert result is False