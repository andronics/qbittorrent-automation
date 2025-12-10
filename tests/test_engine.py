"""Tests for the rules engine."""

import pytest

from qbittorrent_automation.engine import RulesEngine
from qbittorrent_automation.errors import OperatorError


def test_evaluate_operator_equals():
    """Test equality operator."""
    from qbittorrent_automation.engine import evaluate_operator

    assert evaluate_operator("==", "test", "test") is True
    assert evaluate_operator("==", "test", "other") is False
    assert evaluate_operator("==", 1, 1) is True
    assert evaluate_operator("==", 1, 2) is False


def test_evaluate_operator_not_equals():
    """Test inequality operator."""
    from qbittorrent_automation.engine import evaluate_operator

    assert evaluate_operator("!=", "test", "other") is True
    assert evaluate_operator("!=", "test", "test") is False


def test_evaluate_operator_greater_than():
    """Test greater than operator."""
    from qbittorrent_automation.engine import evaluate_operator

    assert evaluate_operator(">", 10, 5) is True
    assert evaluate_operator(">", 5, 10) is False
    assert evaluate_operator(">", 5, 5) is False


def test_evaluate_operator_less_than():
    """Test less than operator."""
    from qbittorrent_automation.engine import evaluate_operator

    assert evaluate_operator("<", 5, 10) is True
    assert evaluate_operator("<", 10, 5) is False
    assert evaluate_operator("<", 5, 5) is False


def test_evaluate_operator_contains():
    """Test contains operator."""
    from qbittorrent_automation.engine import evaluate_operator

    assert evaluate_operator("contains", "hello world", "world") is True
    assert evaluate_operator("contains", "hello world", "foo") is False


def test_evaluate_operator_not_contains():
    """Test not_contains operator."""
    from qbittorrent_automation.engine import evaluate_operator

    assert evaluate_operator("not_contains", "hello world", "foo") is True
    assert evaluate_operator("not_contains", "hello world", "world") is False


def test_evaluate_operator_matches():
    """Test regex matches operator."""
    from qbittorrent_automation.engine import evaluate_operator

    assert evaluate_operator("matches", "Test.S01E05.1080p", r".*S\d{2}E\d{2}.*") is True
    assert evaluate_operator("matches", "Test.Movie.2024", r".*S\d{2}E\d{2}.*") is False


def test_evaluate_operator_in():
    """Test 'in' operator with list."""
    from qbittorrent_automation.engine import evaluate_operator

    assert evaluate_operator("in", "uploading", ["uploading", "downloading"]) is True
    assert evaluate_operator("in", "paused", ["uploading", "downloading"]) is False


def test_evaluate_operator_not_in():
    """Test 'not_in' operator with list."""
    from qbittorrent_automation.engine import evaluate_operator

    assert evaluate_operator("not_in", "paused", ["uploading", "downloading"]) is True
    assert evaluate_operator("not_in", "uploading", ["uploading", "downloading"]) is False


def test_evaluate_operator_invalid():
    """Test that invalid operator raises error."""
    from qbittorrent_automation.engine import evaluate_operator

    with pytest.raises(OperatorError, match="Unknown operator"):
        evaluate_operator("invalid_op", "value", "test")
